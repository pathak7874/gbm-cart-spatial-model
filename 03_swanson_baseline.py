"""
Baseline Swanson Model for GBM Growth
=====================================
Standard Fisher-Kolmogorov reaction-diffusion model without:
- Fractional diffusion (uses classical α=2)
- TME barriers (no ECM, MDSC, pH)
- CAR-T interventions (tumor only)

Reference:
Swanson, K. R., Rostomily, R. C., & Alvord, E. C. (2008). 
A mathematical modelling tool for predicting survival in patients 
with glioblastoma multiforme. Cancer Research, 68(6), 1725–1731.
"""

import numpy as np
from scipy.integrate import solve_ivp

class SwansonParameters:
    """Classical Swanson GBM parameters from literature."""
    D_T = 0.0013  # cm²/day (Swanson 2008 median)
    r_T = 0.012   # day⁻¹ (net proliferation)
    dim = '1D'

def swanson_rhs(t, T, params, dx, dim='1D', Nx=51):
    """Classical Fisher-KPP equation: dT/dt = D∇²T + rT(1-T)"""
    T = np.maximum(T, 0)  # Prevent negatives
    
    # Standard Laplacian (α=2)
    if dim == '1D':
        lap = np.zeros_like(T)
        lap[1:-1] = (T[2:] - 2*T[1:-1] + T[:-2]) / dx**2
        lap[0] = lap[1]
        lap[-1] = lap[-2]
    elif dim == '2D':
        T_2d = T.reshape((Nx, Nx))
        lap = np.zeros_like(T_2d)
        lap[1:-1,1:-1] = (T_2d[2:,1:-1] + T_2d[:-2,1:-1] + 
                          T_2d[1:-1,2:] + T_2d[1:-1,:-2] - 
                          4*T_2d[1:-1,1:-1]) / dx**2
        lap[0,:] = lap[1,:]
        lap[-1,:] = lap[-2,:]
        lap[:,0] = lap[:,1]
        lap[:,-1] = lap[:,-2]
        lap = lap.flatten()
    
    # Reaction: logistic growth
    reaction = params.r_T * T * (1 - T)
    
    # Diffusion
    diffusion = params.D_T * lap
    
    dT = diffusion + reaction
    dT = np.maximum(dT, -T)  # Prevent excessive decay
    
    return dT

def simulate_swanson(params, T0, t_span=(0, 60), t_eval=None, dx=0.2, dim='1D', Nx=51):
    """Simulate Swanson model."""
    if t_eval is None:
        t_eval = np.linspace(t_span[0], t_span[1], 200)
    
    sol = solve_ivp(
        lambda t, y: swanson_rhs(t, y, params, dx, dim, Nx),
        t_span, T0, t_eval=t_eval,
        method='LSODA', rtol=1e-5, atol=1e-8
    )
    return sol

if __name__ == "__main__":
    # Quick test
    L = 10.0
    Nx = 51
    dx = L / (Nx - 1)
    x = np.linspace(0, L, Nx)
    r = np.abs(x - L/2)
    
    T0 = np.exp(- r**2 / 1.0**2)
    T0 /= np.max(T0)
    
    params = SwansonParameters()
    sol = simulate_swanson(params, T0, t_span=(0, 60), dx=dx)
    
    if sol.success:
        final_mass = np.sum(sol.y[:, -1]) * dx
        init_mass = np.sum(T0) * dx
        growth = (final_mass / init_mass - 1) * 100
        print(f"Swanson baseline: {growth:+.1f}% mass change at day 60")
    else:
        print(f"Failed: {sol.message}")
