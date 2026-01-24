import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import minimize_scalar
import matplotlib.pyplot as plt

class GBMParameters:
    """GBM-tuned params from public lit (BraTS/Swanson models)."""
    D_T = 0.001  # cm²/day
    D_C_base = 0.0001
    D_E = 0.00005  # ECM
    D_M = 0.0001  # MDSC
    D_pH = 0.0002  # pH
    r_T = 0.012  # day⁻¹
    r_C = 0.27   # IL-21 boost (MD Anderson lit)
    k_CT = 1.5   # Base; switchable
    gamma = 0.01 # Escape
    h_T = 0.01
    h_C = 0.05   # ~14 day half-life
    alpha = 1.8  # Fractional
    ecm_strength = 0.20
    ph_strength = 0.15
    mdsc_strength = 0.15
    exh_penalty = 0.10
    ecm_deg_rate = 0.15
    mdsc_dep_rate = 2.0
    ph_buf_rate = 1.0
    ecm_start, ecm_end = -7, 0
    mdsc_start, mdsc_end = -7, 60  # Extended
    ph_start, ph_end = -3, 7
    dose = 0.5   # Optimized later
    dim = '1D'   # Or '2D'
    noise_sigma = 0.01  # For stochastic
    random_seed = 42  # For reproducibility

# Initialize RNG globally for proper stochasticity
_rng = None

def initialize_rng(seed=42):
    """Initialize random number generator once."""
    global _rng
    _rng = np.random.default_rng(seed)
    return _rng

def frac_lap(u, dx, alpha, dim='1D', Nx=51):
    """Fractional Laplacian via FFT with stability checks."""
    if dim == '1D':
        k = np.fft.fftfreq(Nx, d=dx)
        # Avoid division by zero and excessive growth
        k_safe = np.where(np.abs(k) < 1e-10, 1e-10, k)
        lap_k = - (2 * np.pi * np.abs(k_safe))**alpha
        # Cap maximum eigenvalue for stability
        lap_k = np.clip(lap_k, -1e6, 0)
        u_hat = np.fft.fft(u)
        lap_u = np.real(np.fft.ifft(lap_k * u_hat))
    elif dim == '2D':
        u_2d = u.reshape((Nx, Nx))
        kx = np.fft.fftfreq(Nx, d=dx)
        ky = np.fft.fftfreq(Nx, d=dx)
        KX, KY = np.meshgrid(kx, ky)
        k_mag = np.sqrt(KX**2 + KY**2)
        k_mag = np.where(k_mag < 1e-10, 1e-10, k_mag)
        lap_k = - (2 * np.pi * k_mag)**alpha
        lap_k = np.clip(lap_k, -1e6, 0)
        u_hat = np.fft.fftn(u_2d)
        lap_u = np.real(np.fft.ifftn(lap_k * u_hat)).flatten()
    
    # Check for NaN/Inf after computation - fail explicitly if unstable
    if np.any(np.isnan(lap_u)) or np.any(np.isinf(lap_u)):
        raise ValueError("Numerical instability in fractional Laplacian - reduce time step or alpha")
    
    return lap_u

def lap_fd(u, dx, dim='1D', Nx=51):
    """Standard finite difference Laplacian."""
    if dim == '1D':
        lap = np.zeros_like(u)
        lap[1:-1] = (u[2:] - 2*u[1:-1] + u[:-2]) / dx**2
        lap[0] = lap[1]; lap[-1] = lap[-2]
        return lap
    elif dim == '2D':
        u_2d = u.reshape((Nx, Nx))
        lap = np.zeros_like(u_2d)
        lap[1:-1,1:-1] = (u_2d[2:,1:-1] + u_2d[:-2,1:-1] + u_2d[1:-1,2:] + u_2d[1:-1,:-2] - 4*u_2d[1:-1,1:-1]) / dx**2
        lap[0,:] = lap[1,:]; lap[-1,:] = lap[-2,:]
        lap[:,0] = lap[:,1]; lap[:,-1] = lap[:,-2]
        return lap.flatten()

def rhs(t, Y, params, dim, Nx, dx, r, D_C_spatial):
    """Right-hand side of PDE system."""
    global _rng
    if _rng is None:
        initialize_rng(params.random_seed)
    
    N = len(Y) // 5
    T, C, E, M, pH = [Y[i*N:(i+1)*N] for i in range(5)]
    T, C, E, M, pH = [np.maximum(x, 0) for x in [T, C, E, M, pH]]  # Prevent negatives
    pH = np.clip(pH, 6.0, 7.4)  # Physical bounds
    
    # Interventions
    ecm_int = params.ecm_deg_rate if params.ecm_start <= t <= params.ecm_end else 0
    mdsc_int = params.mdsc_dep_rate if params.mdsc_start <= t <= params.mdsc_end else 0
    ph_int = params.ph_buf_rate if params.ph_start <= t <= params.ph_end else 0
    
    # Penalties
    ecm_pen = params.ecm_strength * E
    ph_pen = params.ph_strength * (7.4 - pH) / 0.9
    mdsc_pen = params.mdsc_strength * (M / 10.0)
    exh_pen = params.exh_penalty * C
    total_pen = ecm_pen + ph_pen + mdsc_pen + exh_pen
    eff = np.clip(1.0 - total_pen, 0.05, 1.0)  # Clipped
    
    # Switchable k_CT (UCSF E-SYNC)
    k_switch = params.k_CT if 0 <= t <= 30 else params.k_CT * 0.5
    
    # Stochastic noise (applied consistently to all variables)
    noise_T = 1 + params.noise_sigma * _rng.normal(0, 1, N)
    noise_C = 1 + params.noise_sigma * _rng.normal(0, 1, N)
    noise_E = 1 + params.noise_sigma * 0.5 * _rng.normal(0, 1, N)  # Less noisy
    noise_M = 1 + params.noise_sigma * 0.5 * _rng.normal(0, 1, N)
    noise_pH = 1 + params.noise_sigma * 0.3 * _rng.normal(0, 1, N)
    
    # Reactions with stochastic terms
    dT_reac = (params.r_T * T * (1 - T) - k_switch * C * T * (1 - params.gamma * T) * eff - params.h_T * T) * noise_T
    dC_reac = (params.r_C * C * (T / (T + 0.5)) - params.h_C * C) * noise_C
    dE_reac = (0.001 - ecm_int * E * (1 + 0.1 * T)) * noise_E
    dM_reac = (1.0 * T - 0.1 * M - mdsc_int * M) * noise_M
    dpH_reac = (-0.1 * T + ph_int * (7.4 - pH)) * noise_pH
    
    # Diffusion (use fractional if alpha != 2, otherwise standard)
    try:
        if params.alpha != 2:
            dT_diff = params.D_T * frac_lap(T, dx, params.alpha, dim, Nx)
            dC_diff = D_C_spatial * frac_lap(C, dx, params.alpha, dim, Nx)
        else:
            dT_diff = params.D_T * lap_fd(T, dx, dim, Nx)
            dC_diff = D_C_spatial * lap_fd(C, dx, dim, Nx)
    except ValueError as e:
        # Fallback to standard diffusion if fractional becomes unstable
        print(f"Warning at t={t:.2f}: {e}. Falling back to standard diffusion.")
        dT_diff = params.D_T * lap_fd(T, dx, dim, Nx)
        dC_diff = D_C_spatial * lap_fd(C, dx, dim, Nx)
    
    # Always use standard Laplacian for E, M, pH (more stable)
    dE_diff = params.D_E * lap_fd(E, dx, dim, Nx)
    dM_diff = params.D_M * lap_fd(M, dx, dim, Nx)
    dpH_diff = params.D_pH * lap_fd(pH, dx, dim, Nx)
    
    # Infusion
    infusion = np.zeros(N)
    if -0.5 <= t <= 0.5:
        infusion = params.dose * np.exp(- r**2 / 0.5**2)
    dC_reac += infusion
    
    dY = [dT_diff + dT_reac, dC_diff + dC_reac, dE_diff + dE_reac, dM_diff + dM_reac, dpH_diff + dpH_reac]
    # Prevent excessive decay that leads to negative values
    dY = [np.maximum(d, -var) for d, var in zip(dY, [T, C, E, M, pH])]
    return np.concatenate(dY)

# Grid setup
params = GBMParameters()
L = 10.0
Nx = 51  # Fine
dx = L / (Nx - 1)
if params.dim == '1D':
    x = np.linspace(0, L, Nx)
    r = np.abs(x - L/2)
    N = Nx
else:
    x = y = np.linspace(0, L, Nx)
    X, Y = np.meshgrid(x, y)
    r = np.sqrt((X - L/2)**2 + (Y - L/2)**2).flatten()
    N = Nx * Nx

D_C_spatial = params.D_C_base * (1 - 0.5 * np.exp(- r**2 / 2.0**2 ))

# IC
T0 = np.exp(- r**2 / 1.0**2 )
T0 /= np.max(T0)
C0 = np.zeros(N)
E0 = 0.65 * np.ones(N)
M0 = 10.0 * np.ones(N)
pH0 = 6.5 * np.ones(N)
Y0 = np.concatenate([T0, C0, E0, M0, pH0])

def simulate(params, t_span=(-10, 60), t_eval=None, dim=None, Nx=Nx, dx=dx, r=r, D_C_spatial=D_C_spatial):
    """Run simulation with given parameters."""
    if dim is None:
        dim = params.dim
    if t_eval is None:
        t_eval = np.linspace(t_span[0], t_span[1], 200)
    
    # Initialize RNG for this simulation
    initialize_rng(params.random_seed)
    
    sol = solve_ivp(
        lambda t, y: rhs(t, y, params, dim, Nx, dx, r, D_C_spatial), 
        t_span, Y0, t_eval=t_eval, 
        method='LSODA', rtol=1e-5, atol=1e-8
    )
    return sol

def objective(dose, params):
    """Optimization objective: maximize tumor reduction with entropy penalty."""
    params.dose = dose
    sol = simulate(params)
    if not sol.success:
        return 1000
    final_T = sol.y[:N, -1]
    ddx = dx if params.dim == '1D' else dx**2
    
    # FIXED: Proper parentheses for mass calculation
    final_mass = np.sum(final_T) * ddx
    init_mass = np.sum(T0) * ddx
    reduction = (1 - final_mass / init_mass) * 100
    
    # Entropy regularization (normalized)
    entropy = np.sum(final_T * np.log(np.maximum(final_T, 1e-12))) * ddx
    return -reduction + 0.1 * abs(entropy)

def dataset_test(params, n_patients=20):
    """Test on virtual patient cohort with parameter variability."""
    reductions = []
    for i in range(n_patients):
        p = GBMParameters()  # Create new instance
        p.random_seed = 42 + i  # Different seed per patient
        p.r_T = np.random.uniform(0.007, 0.017)
        p.D_T = np.random.uniform(0.0006, 0.0016)
        
        try:
            sol = simulate(p)
            if sol.success:
                final_T = sol.y[:N, -1]
                ddx = dx if p.dim == '1D' else dx**2
                
                # FIXED: Proper parentheses for mass calculation
                final_mass = np.sum(final_T) * ddx
                init_mass = np.sum(T0) * ddx
                reduction = (1 - final_mass / init_mass) * 100
                reductions.append(reduction)
            else:
                print(f"Patient {i+1} simulation failed: {sol.message}")
        except Exception as e:
            print(f"Patient {i+1} error: {e}")
    
    if reductions:
        mean, std = np.mean(reductions), np.std(reductions)
        print(f"Cohort (n={len(reductions)}): {mean:.1f}% ± {std:.1f}% tumor reduction")
        return mean, std, reductions
    else:
        print("All simulations failed")
        return None, None, []

# Example Run & Test
if __name__ == "__main__":
    print("Running GBM CAR-T Model")
    print("=" * 50)
    
    # Test 1D simulation
    print("\n1D Simulation Test:")
    params_1d = GBMParameters()
    params_1d.dim = '1D'
    sol = simulate(params_1d)
    
    if sol.success:
        final_T = sol.y[:N, -1]
        ddx = dx
        final_mass = np.sum(final_T) * ddx
        init_mass = np.sum(T0) * ddx
        reduction = (1 - final_mass / init_mass) * 100
        print(f"Tumor reduction: {reduction:.1f}%")
        
        # Dose optimization
        print("\nOptimizing dose...")
        res = minimize_scalar(lambda d: objective(d, params_1d), bounds=(0.1, 1.0), method='bounded')
        print(f"Optimal dose: {res.x:.2f}, Max reduction: {-res.fun:.1f}%")
    else:
        print(f"1D simulation failed: {sol.message}")
    
    # Test 2D simulation
    print("\n2D Simulation Test:")
    params_2d = GBMParameters()
    params_2d.dim = '2D'
    
    # Need to redefine grid for 2D
    x = y = np.linspace(0, L, Nx)
    X, Y = np.meshgrid(x, y)
    r_2d = np.sqrt((X - L/2)**2 + (Y - L/2)**2).flatten()
    N_2d = Nx * Nx
    D_C_spatial_2d = params_2d.D_C_base * (1 - 0.5 * np.exp(- r_2d**2 / 2.0**2 ))
    
    T0_2d = np.exp(- r_2d**2 / 1.0**2 )
    T0_2d /= np.max(T0_2d)
    C0_2d = np.zeros(N_2d)
    E0_2d = 0.65 * np.ones(N_2d)
    M0_2d = 10.0 * np.ones(N_2d)
    pH0_2d = 6.5 * np.ones(N_2d)
    Y0_2d = np.concatenate([T0_2d, C0_2d, E0_2d, M0_2d, pH0_2d])
    
    # Override globals for 2D
    N = N_2d
    r = r_2d
    D_C_spatial = D_C_spatial_2d
    Y0 = Y0_2d
    T0 = T0_2d
    
    sol_2d = simulate(params_2d, dim='2D')
    
    if sol_2d.success:
        final_T_2d = sol_2d.y[:N_2d, -1]
        ddx_2d = dx**2
        final_mass = np.sum(final_T_2d) * ddx_2d
        init_mass = np.sum(T0_2d) * ddx_2d
        reduction = (1 - final_mass / init_mass) * 100
        print(f"Tumor reduction: {reduction:.1f}%")
        
        # QA Plot
        final_T_2d_grid = final_T_2d.reshape((Nx, Nx))
        plt.figure(figsize=(8, 6))
        plt.imshow(final_T_2d_grid, cmap='hot', extent=[0, L, 0, L], origin='lower')
        plt.colorbar(label='Tumor Density')
        plt.title('Day 60 Tumor Distribution (2D)')
        plt.xlabel('x (cm)')
        plt.ylabel('y (cm)')
        plt.savefig('gbm_2d_output.png', dpi=150, bbox_inches='tight')
        print("Saved: gbm_2d_output.png")
    else:
        print(f"2D simulation failed: {sol_2d.message}")
    
    # Patient cohort test
    print("\nVirtual Patient Cohort Test:")
    dataset_test(params_1d, n_patients=20)
