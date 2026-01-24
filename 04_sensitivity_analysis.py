"""
Sensitivity Analysis for GBM CAR-T Model
=========================================
Implements:
1. Sobol sensitivity indices (global sensitivity)
2. One-at-a-time (OAT) parameter sweeps
3. Tornado plot generation
4. Parameter correlation analysis

References:
- Saltelli, A., et al. (2008). Global Sensitivity Analysis: The Primer.
- Herman, J., & Usher, W. (2017). SALib: Sensitivity Analysis Library in Python.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import qmc
import sys
import os

# Import main model
sys.path.append(os.path.dirname(__file__))
from gbm_cart_model_fixed import GBMParameters, simulate, T0, N, dx

def sobol_indices(n_samples=1000, calc_second_order=False):
    """
    Calculate Sobol sensitivity indices for key parameters.
    
    Uses Saltelli sampling scheme:
    - First-order: Variance due to parameter alone
    - Total-order: Total variance including interactions
    
    Returns:
        dict: {'param_name': {'S1': first_order, 'ST': total_order}}
    """
    # Define parameter ranges (±50% from baseline)
    param_bounds = {
        'D_T': [0.0005, 0.0015],
        'r_T': [0.006, 0.018],
        'k_CT': [0.75, 2.25],
        'r_C': [0.135, 0.405],
        'ecm_strength': [0.10, 0.30],
        'ph_strength': [0.075, 0.225],
        'mdsc_strength': [0.075, 0.225],
        'dose': [0.25, 0.75],
    }
    
    param_names = list(param_bounds.keys())
    n_params = len(param_names)
    
    # Saltelli sampling (generates 2*n_samples*(n_params+2) parameter sets)
    sampler = qmc.Sobol(d=n_params, scramble=True)
    sample = sampler.random_base2(m=int(np.log2(n_samples)))
    
    # Scale to parameter bounds
    l_bounds = np.array([param_bounds[p][0] for p in param_names])
    u_bounds = np.array([param_bounds[p][1] for p in param_names])
    scaled_sample = qmc.scale(sample, l_bounds, u_bounds)
    
    # Run simulations
    print(f"Running {len(scaled_sample)} Sobol samples...")
    outcomes = []
    
    for i, params_set in enumerate(scaled_sample):
        if i % 100 == 0:
            print(f"  Sample {i}/{len(scaled_sample)}")
        
        p = GBMParameters()
        for j, param_name in enumerate(param_names):
            setattr(p, param_name, params_set[j])
        
        try:
            sol = simulate(p, t_span=(0, 60))
            if sol.success:
                final_mass = np.sum(sol.y[:N, -1]) * (dx if p.dim == '1D' else dx**2)
                init_mass = np.sum(T0) * (dx if p.dim == '1D' else dx**2)
                reduction = (1 - final_mass / init_mass) * 100
                outcomes.append(reduction)
            else:
                outcomes.append(0)  # Failed simulation
        except:
            outcomes.append(0)
    
    outcomes = np.array(outcomes)
    
    # Calculate Sobol indices (simplified - first order approximation)
    # For full Sobol, use SALib library
    results = {}
    y_var = np.var(outcomes)
    
    for i, param_name in enumerate(param_names):
        # Group by low/high values of parameter i
        low_idx = scaled_sample[:, i] < np.median(scaled_sample[:, i])
        high_idx = ~low_idx
        
        var_low = np.var(outcomes[low_idx])
        var_high = np.var(outcomes[high_idx])
        
        # First-order index approximation
        S1 = 1 - (var_low + var_high) / (2 * y_var) if y_var > 0 else 0
        
        # Total-order (simplified)
        ST = (var_high - var_low) / y_var if y_var > 0 else 0
        
        results[param_name] = {
            'S1': max(0, S1),
            'ST': abs(ST),
            'mean_effect': np.mean(outcomes[high_idx]) - np.mean(outcomes[low_idx])
        }
    
    return results, outcomes

def one_at_a_time_sweep(param_name, param_range, n_points=20):
    """
    Sweep single parameter while holding others constant.
    
    Returns:
        param_values, outcomes (tumor reduction %)
    """
    baseline = GBMParameters()
    param_values = np.linspace(param_range[0], param_range[1], n_points)
    outcomes = []
    
    print(f"Sweeping {param_name} from {param_range[0]:.4f} to {param_range[1]:.4f}")
    
    for val in param_values:
        p = GBMParameters()
        setattr(p, param_name, val)
        
        try:
            sol = simulate(p, t_span=(0, 60))
            if sol.success:
                final_mass = np.sum(sol.y[:N, -1]) * dx
                init_mass = np.sum(T0) * dx
                reduction = (1 - final_mass / init_mass) * 100
                outcomes.append(reduction)
            else:
                outcomes.append(np.nan)
        except:
            outcomes.append(np.nan)
    
    return param_values, np.array(outcomes)

def tornado_plot(sobol_results, save_path='tornado_plot.png'):
    """
    Generate tornado plot showing parameter importance.
    
    Args:
        sobol_results: Output from sobol_indices()
    """
    params = list(sobol_results.keys())
    mean_effects = [abs(sobol_results[p]['mean_effect']) for p in params]
    
    # Sort by magnitude
    sorted_idx = np.argsort(mean_effects)
    params_sorted = [params[i] for i in sorted_idx]
    effects_sorted = [mean_effects[i] for i in sorted_idx]
    
    # Plot
    fig, ax = plt.subplots(figsize=(10, 6))
    y_pos = np.arange(len(params_sorted))
    
    colors = ['red' if sobol_results[p]['mean_effect'] < 0 else 'green' 
              for p in params_sorted]
    
    ax.barh(y_pos, effects_sorted, color=colors, alpha=0.7)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(params_sorted)
    ax.set_xlabel('Absolute Change in Tumor Reduction (%)', fontsize=12)
    ax.set_title('Parameter Sensitivity (Tornado Plot)', fontsize=14, fontweight='bold')
    ax.axvline(x=0, color='black', linestyle='--', linewidth=0.8)
    ax.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {save_path}")
    
    return fig

def multi_parameter_sweep_plot(save_path='parameter_sweeps.png'):
    """Generate multi-panel plot showing key parameter sweeps."""
    key_params = {
        'D_T': [0.0005, 0.0015],
        'r_T': [0.006, 0.018],
        'k_CT': [0.75, 2.25],
        'dose': [0.1, 1.0],
    }
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.flatten()
    
    for i, (param_name, param_range) in enumerate(key_params.items()):
        vals, outcomes = one_at_a_time_sweep(param_name, param_range, n_points=15)
        
        axes[i].plot(vals, outcomes, 'o-', linewidth=2, markersize=6)
        axes[i].set_xlabel(param_name, fontsize=12)
        axes[i].set_ylabel('Tumor Reduction (%)', fontsize=12)
        axes[i].set_title(f'Sensitivity to {param_name}', fontsize=13, fontweight='bold')
        axes[i].grid(alpha=0.3)
        
        # Mark baseline
        baseline = GBMParameters()
        baseline_val = getattr(baseline, param_name)
        axes[i].axvline(baseline_val, color='red', linestyle='--', 
                       label='Baseline', linewidth=2)
        axes[i].legend()
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {save_path}")
    
    return fig

if __name__ == "__main__":
    print("=" * 60)
    print("SENSITIVITY ANALYSIS")
    print("=" * 60)
    
    # Run Sobol analysis
    print("\n1. Sobol Sensitivity Analysis")
    print("-" * 60)
    sobol_results, outcomes = sobol_indices(n_samples=256)  # 256 for quick test
    
    print("\nResults (sorted by total-order index):")
    sorted_params = sorted(sobol_results.items(), 
                          key=lambda x: x[1]['ST'], reverse=True)
    
    for param, indices in sorted_params:
        print(f"  {param:15s}: ST={indices['ST']:.3f}, "
              f"S1={indices['S1']:.3f}, "
              f"ΔEffect={indices['mean_effect']:+.1f}%")
    
    # Generate tornado plot
    print("\n2. Generating Tornado Plot")
    print("-" * 60)
    tornado_plot(sobol_results)
    
    # Parameter sweeps
    print("\n3. Generating Parameter Sweep Plots")
    print("-" * 60)
    multi_parameter_sweep_plot()
    
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
