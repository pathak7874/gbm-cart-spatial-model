"""
Convergence Study
=================
Grid refinement analysis to validate numerical solution quality.
Tests spatial resolution (Nx) and time resolution (dt via rtol/atol).

Verifies:
1. Solution convergence with grid refinement
2. Mass conservation
3. Stability of fractional operators
4. Appropriate resolution for production runs

Reference:
LeVeque, R. J. (2007). Finite Difference Methods for Ordinary 
and Partial Differential Equations. SIAM.
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import os
from time import time

sys.path.append(os.path.dirname(__file__))
from gbm_cart_model_fixed import GBMParameters, simulate

def convergence_test_spatial(nx_values=[25, 51, 101, 201], t_end=60):
    """
    Test convergence with spatial grid refinement.
    
    Args:
        nx_values: list of grid sizes to test
        t_end: final simulation time
    
    Returns:
        dict: results for each Nx
    """
    results = {}
    
    print("Spatial Convergence Test")
    print("=" * 70)
    
    for Nx in nx_values:
        print(f"\nTesting Nx = {Nx}...")
        
        L = 10.0
        dx = L / (Nx - 1)
        x = np.linspace(0, L, Nx)
        r = np.abs(x - L/2)
        N = Nx
        
        # Initial condition
        T0 = np.exp(- r**2 / 1.0**2)
        T0 /= np.max(T0)
        C0 = np.zeros(N)
        E0 = 0.65 * np.ones(N)
        M0 = 10.0 * np.ones(N)
        pH0 = 6.5 * np.ones(N)
        Y0 = np.concatenate([T0, C0, E0, M0, pH0])
        
        # Spatial-dependent diffusion
        D_C_spatial = 0.0001 * (1 - 0.5 * np.exp(- r**2 / 2.0**2))
        
        # Run simulation
        params = GBMParameters()
        params.dim = '1D'
        
        start_time = time()
        
        # Need to pass correct arguments to simulate
        from scipy.integrate import solve_ivp
        from gbm_cart_model_fixed import rhs
        
        sol = solve_ivp(
            lambda t, y: rhs(t, y, params, '1D', Nx, dx, r, D_C_spatial),
            (0, t_end), Y0, t_eval=np.linspace(0, t_end, 200),
            method='LSODA', rtol=1e-5, atol=1e-8
        )
        
        runtime = time() - start_time
        
        if sol.success:
            final_T = sol.y[:N, -1]
            
            # Calculate metrics
            final_mass = np.sum(final_T) * dx
            init_mass = np.sum(T0) * dx
            reduction = (1 - final_mass / init_mass) * 100
            
            # Mass conservation check (sum of all species)
            init_total_mass = np.sum(Y0) * dx
            final_total_mass = np.sum(sol.y[:, -1]) * dx
            conservation_error = abs(final_total_mass - init_total_mass) / init_total_mass * 100
            
            # Peak tumor density
            peak_density = np.max(final_T)
            
            # Center of mass
            com = np.sum(x * final_T) / np.sum(final_T) if np.sum(final_T) > 0 else L/2
            
            print(f"  Success: reduction={reduction:.2f}%, "
                  f"runtime={runtime:.2f}s, "
                  f"conservation_error={conservation_error:.3f}%")
            
            results[Nx] = {
                'success': True,
                'Nx': Nx,
                'dx': dx,
                'reduction': reduction,
                'final_mass': final_mass,
                'peak_density': peak_density,
                'center_of_mass': com,
                'conservation_error': conservation_error,
                'runtime': runtime,
                'nfev': sol.nfev,
                'solution': sol.y[:N, :]
            }
        else:
            print(f"  FAILED: {sol.message}")
            results[Nx] = {
                'success': False,
                'Nx': Nx,
                'dx': dx,
                'message': sol.message
            }
    
    return results

def convergence_test_temporal(rtol_values=[1e-3, 1e-4, 1e-5, 1e-6], Nx=51):
    """
    Test convergence with temporal resolution (ODE tolerances).
    
    Args:
        rtol_values: list of relative tolerances
        Nx: fixed spatial resolution
    
    Returns:
        dict: results for each rtol
    """
    results = {}
    
    print("\nTemporal Convergence Test")
    print("=" * 70)
    
    L = 10.0
    dx = L / (Nx - 1)
    x = np.linspace(0, L, Nx)
    r = np.abs(x - L/2)
    N = Nx
    
    T0 = np.exp(- r**2 / 1.0**2)
    T0 /= np.max(T0)
    C0 = np.zeros(N)
    E0 = 0.65 * np.ones(N)
    M0 = 10.0 * np.ones(N)
    pH0 = 6.5 * np.ones(N)
    Y0 = np.concatenate([T0, C0, E0, M0, pH0])
    
    D_C_spatial = 0.0001 * (1 - 0.5 * np.exp(- r**2 / 2.0**2))
    
    params = GBMParameters()
    
    for rtol in rtol_values:
        print(f"\nTesting rtol = {rtol:.0e}...")
        
        from scipy.integrate import solve_ivp
        from gbm_cart_model_fixed import rhs
        
        start_time = time()
        
        sol = solve_ivp(
            lambda t, y: rhs(t, y, params, '1D', Nx, dx, r, D_C_spatial),
            (0, 60), Y0, t_eval=np.linspace(0, 60, 200),
            method='LSODA', rtol=rtol, atol=rtol*1e-2
        )
        
        runtime = time() - start_time
        
        if sol.success:
            final_T = sol.y[:N, -1]
            final_mass = np.sum(final_T) * dx
            init_mass = np.sum(T0) * dx
            reduction = (1 - final_mass / init_mass) * 100
            
            print(f"  Success: reduction={reduction:.2f}%, "
                  f"nfev={sol.nfev}, runtime={runtime:.2f}s")
            
            results[rtol] = {
                'success': True,
                'rtol': rtol,
                'reduction': reduction,
                'runtime': runtime,
                'nfev': sol.nfev
            }
        else:
            print(f"  FAILED: {sol.message}")
            results[rtol] = {'success': False, 'rtol': rtol}
    
    return results

def plot_convergence_results(spatial_results, temporal_results, 
                            save_path='convergence_study.png'):
    """Generate convergence plots."""
    
    fig = plt.figure(figsize=(14, 10))
    
    # Extract successful results
    nx_vals = [k for k, v in spatial_results.items() if v['success']]
    nx_vals.sort()
    
    # 1. Solution profiles at different resolutions
    ax1 = plt.subplot(2, 3, 1)
    
    for Nx in nx_vals:
        L = 10.0
        x = np.linspace(0, L, Nx)
        final_profile = spatial_results[Nx]['solution'][:, -1]
        ax1.plot(x, final_profile, label=f'Nx={Nx}', linewidth=2)
    
    ax1.set_xlabel('Position (cm)', fontsize=11)
    ax1.set_ylabel('Tumor Density', fontsize=11)
    ax1.set_title('Spatial Convergence: Final Profiles', fontsize=12, fontweight='bold')
    ax1.legend()
    ax1.grid(alpha=0.3)
    
    # 2. Tumor reduction vs grid size
    ax2 = plt.subplot(2, 3, 2)
    
    reductions = [spatial_results[Nx]['reduction'] for Nx in nx_vals]
    ax2.plot(nx_vals, reductions, 'o-', linewidth=2, markersize=8)
    
    ax2.set_xlabel('Grid Points (Nx)', fontsize=11)
    ax2.set_ylabel('Tumor Reduction (%)', fontsize=11)
    ax2.set_title('Reduction vs Resolution', fontsize=12, fontweight='bold')
    ax2.grid(alpha=0.3)
    
    # Add convergence threshold line
    if len(reductions) >= 2:
        converged_value = reductions[-1]
        ax2.axhline(converged_value, color='red', linestyle='--', 
                   label=f'Converged: {converged_value:.2f}%')
        ax2.legend()
    
    # 3. Runtime vs grid size
    ax3 = plt.subplot(2, 3, 3)
    
    runtimes = [spatial_results[Nx]['runtime'] for Nx in nx_vals]
    ax3.plot(nx_vals, runtimes, 's-', linewidth=2, markersize=8, color='purple')
    
    ax3.set_xlabel('Grid Points (Nx)', fontsize=11)
    ax3.set_ylabel('Runtime (seconds)', fontsize=11)
    ax3.set_title('Computational Cost', fontsize=12, fontweight='bold')
    ax3.set_yscale('log')
    ax3.grid(alpha=0.3)
    
    # 4. Conservation error
    ax4 = plt.subplot(2, 3, 4)
    
    conservation_errors = [spatial_results[Nx]['conservation_error'] for Nx in nx_vals]
    ax4.semilogy(nx_vals, conservation_errors, '^-', linewidth=2, markersize=8, color='orange')
    
    ax4.set_xlabel('Grid Points (Nx)', fontsize=11)
    ax4.set_ylabel('Mass Conservation Error (%)', fontsize=11)
    ax4.set_title('Conservation Error vs Resolution', fontsize=12, fontweight='bold')
    ax4.axhline(0.1, color='red', linestyle='--', label='0.1% threshold')
    ax4.legend()
    ax4.grid(alpha=0.3)
    
    # 5. Temporal convergence
    ax5 = plt.subplot(2, 3, 5)
    
    rtol_vals = [k for k, v in temporal_results.items() if v['success']]
    rtol_vals.sort(reverse=True)
    
    temp_reductions = [temporal_results[r]['reduction'] for r in rtol_vals]
    ax5.semilogx(rtol_vals, temp_reductions, 'o-', linewidth=2, markersize=8, color='green')
    
    ax5.set_xlabel('Relative Tolerance (rtol)', fontsize=11)
    ax5.set_ylabel('Tumor Reduction (%)', fontsize=11)
    ax5.set_title('Temporal Convergence', fontsize=12, fontweight='bold')
    ax5.invert_xaxis()
    ax5.grid(alpha=0.3)
    
    # 6. Efficiency (nfev vs rtol)
    ax6 = plt.subplot(2, 3, 6)
    
    nfevs = [temporal_results[r]['nfev'] for r in rtol_vals]
    runtimes_temp = [temporal_results[r]['runtime'] for r in rtol_vals]
    
    ax6_twin = ax6.twinx()
    
    l1 = ax6.semilogx(rtol_vals, nfevs, 's-', linewidth=2, markersize=8, 
                     color='blue', label='Function evaluations')
    l2 = ax6_twin.semilogx(rtol_vals, runtimes_temp, '^-', linewidth=2, 
                          markersize=8, color='red', label='Runtime')
    
    ax6.set_xlabel('Relative Tolerance (rtol)', fontsize=11)
    ax6.set_ylabel('Function Evaluations', fontsize=11, color='blue')
    ax6_twin.set_ylabel('Runtime (s)', fontsize=11, color='red')
    ax6.set_title('Computational Efficiency', fontsize=12, fontweight='bold')
    ax6.invert_xaxis()
    ax6.grid(alpha=0.3)
    
    # Combined legend
    lns = l1 + l2
    labs = [l.get_label() for l in lns]
    ax6.legend(lns, labs, loc='upper left')
    
    plt.suptitle('Convergence Study: Spatial & Temporal Resolution',
                fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"\nSaved: {save_path}")
    
    return fig

if __name__ == "__main__":
    print("=" * 70)
    print("CONVERGENCE STUDY")
    print("=" * 70)
    
    # Spatial convergence
    spatial_results = convergence_test_spatial(nx_values=[25, 51, 101])
    
    # Temporal convergence
    temporal_results = convergence_test_temporal(rtol_values=[1e-3, 1e-4, 1e-5, 1e-6])
    
    # Summary
    print("\n" + "=" * 70)
    print("CONVERGENCE SUMMARY")
    print("=" * 70)
    
    print("\nSpatial Convergence:")
    nx_vals = sorted([k for k, v in spatial_results.items() if v['success']])
    for Nx in nx_vals:
        print(f"  Nx={Nx:3d}: reduction={spatial_results[Nx]['reduction']:.3f}%, "
              f"error={spatial_results[Nx]['conservation_error']:.4f}%")
    
    # Check convergence (change < 1% between finest grids)
    if len(nx_vals) >= 2:
        diff = abs(spatial_results[nx_vals[-1]]['reduction'] - 
                  spatial_results[nx_vals[-2]]['reduction'])
        print(f"\nConvergence check: {diff:.3f}% change from Nx={nx_vals[-2]} to Nx={nx_vals[-1]}")
        if diff < 1.0:
            print("✓ CONVERGED (< 1% change)")
            print(f"Recommended production resolution: Nx={nx_vals[-2]}")
        else:
            print("✗ NOT CONVERGED - need finer grid")
    
    print("\nTemporal Convergence:")
    rtol_vals = sorted([k for k, v in temporal_results.items() if v['success']], 
                      reverse=True)
    for rtol in rtol_vals:
        print(f"  rtol={rtol:.0e}: reduction={temporal_results[rtol]['reduction']:.3f}%, "
              f"nfev={temporal_results[rtol]['nfev']}")
    
    # Plot results
    print("\nGenerating convergence plots...")
    plot_convergence_results(spatial_results, temporal_results)
    
    print("\n" + "=" * 70)
    print("CONVERGENCE STUDY COMPLETE")
    print("=" * 70)
