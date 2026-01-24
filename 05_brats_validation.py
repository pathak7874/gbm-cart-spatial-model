"""
BraTS Data Validation Framework
================================
Load BraTS tumor segmentations, extract growth curves, 
and validate model against clinical data.

Data sources:
- BraTS 2024/2025: https://www.synapse.org/#!Synapse:syn53708249
- UPenn-GBM: https://www.cancerimagingarchive.net/collection/upenn-gbm/

References:
Baid, U., et al. (2021). The RSNA-ASNR-MICCAI BraTS 2021 Benchmark 
on Brain Tumor Segmentation. arXiv:2107.02314
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from scipy.stats import pearsonr
import sys
import os

sys.path.append(os.path.dirname(__file__))
from gbm_cart_model_fixed import GBMParameters, simulate, T0, N, dx
from swanson_baseline import SwansonParameters, simulate_swanson

class BraTSPatient:
    """Synthetic BraTS patient data for validation (proxy until real data loaded)."""
    
    def __init__(self, patient_id, growth_pattern='typical'):
        self.patient_id = patient_id
        self.timepoints = np.array([0, 30, 60, 90, 120])  # days
        
        # Synthetic growth curves based on literature
        # Swanson 2008: ~0.5-2mm/week radial expansion
        # Median OS ~15 months = ~450 days
        
        if growth_pattern == 'typical':
            # Slow-growing, standard response
            self.volumes = np.array([10.0, 15.2, 22.8, 33.5, 48.2])  # cm³
        elif growth_pattern == 'aggressive':
            # Fast-growing
            self.volumes = np.array([10.0, 18.5, 34.2, 62.8, 115.0])
        elif growth_pattern == 'responding':
            # Tumor responding to therapy
            self.volumes = np.array([10.0, 9.2, 7.5, 6.1, 5.0])
        else:
            # Random patient variability
            np.random.seed(patient_id)
            D_T = np.random.uniform(0.0008, 0.0015)
            r_T = np.random.uniform(0.008, 0.016)
            self.volumes = self._generate_synthetic_curve(D_T, r_T)
        
        # Convert to equivalent radius (assuming sphere)
        self.radii = (3 * self.volumes / (4 * np.pi))**(1/3)
        
        # Survival time (for later use)
        self.survival_days = np.random.uniform(300, 600)
    
    def _generate_synthetic_curve(self, D_T, r_T):
        """Generate synthetic growth curve using Swanson model."""
        params = SwansonParameters()
        params.D_T = D_T
        params.r_T = r_T
        
        # Run simulation
        L = 10.0
        Nx = 51
        dx_loc = L / (Nx - 1)
        x = np.linspace(0, L, Nx)
        r = np.abs(x - L/2)
        T0_loc = np.exp(- r**2 / 1.0**2)
        T0_loc /= np.max(T0_loc)
        
        volumes = []
        for t_end in self.timepoints:
            sol = simulate_swanson(params, T0_loc, t_span=(0, t_end), 
                                  t_eval=[t_end], dx=dx_loc)
            if sol.success:
                mass = np.sum(sol.y[:, -1]) * dx_loc
                # Convert mass to volume (arbitrary scaling)
                vol = 10.0 * mass  
                volumes.append(vol)
            else:
                volumes.append(np.nan)
        
        return np.array(volumes)

def load_brats_cohort(n_patients=10, pattern_mix=True):
    """
    Load BraTS patient cohort.
    
    TODO: Replace with actual BraTS data loading when available.
    Currently generates synthetic patients based on literature parameters.
    """
    patients = []
    
    if pattern_mix:
        patterns = ['typical'] * 6 + ['aggressive'] * 2 + ['responding'] * 2
    else:
        patterns = ['random'] * n_patients
    
    for i in range(n_patients):
        pattern = patterns[i] if i < len(patterns) else 'random'
        patients.append(BraTSPatient(patient_id=i, growth_pattern=pattern))
    
    return patients

def fit_model_to_patient(patient, model_type='fractional', verbose=False):
    """
    Fit model parameters (D_T, r_T) to patient growth curve.
    
    Args:
        patient: BraTSPatient instance
        model_type: 'fractional' or 'swanson'
    
    Returns:
        dict: {'D_T': fitted_D, 'r_T': fitted_r, 'r_squared': R²}
    """
    
    def objective(params_array):
        D_T, r_T = params_array
        
        if model_type == 'fractional':
            p = GBMParameters()
            p.D_T = D_T
            p.r_T = r_T
            sim_func = lambda t_end: simulate(p, t_span=(0, t_end), 
                                             t_eval=[t_end])
            dx_use = dx
        else:
            p = SwansonParameters()
            p.D_T = D_T
            p.r_T = r_T
            # Need to setup grid
            L = 10.0
            Nx = 51
            dx_use = L / (Nx - 1)
            x = np.linspace(0, L, Nx)
            r = np.abs(x - L/2)
            T0_loc = np.exp(- r**2 / 1.0**2)
            T0_loc /= np.max(T0_loc)
            sim_func = lambda t_end: simulate_swanson(p, T0_loc, t_span=(0, t_end),
                                                      t_eval=[t_end], dx=dx_use)
        
        predicted_volumes = []
        for t in patient.timepoints[1:]:  # Skip t=0
            try:
                sol = sim_func(t)
                if sol.success:
                    mass = np.sum(sol.y[:, -1]) * dx_use
                    vol = 10.0 * mass  # Scale to match data
                    predicted_volumes.append(vol)
                else:
                    return 1e6  # Penalty for failed simulation
            except:
                return 1e6
        
        predicted_volumes = np.array(predicted_volumes)
        observed_volumes = patient.volumes[1:]
        
        # Mean squared error
        mse = np.mean((predicted_volumes - observed_volumes)**2)
        return mse
    
    # Optimize
    initial_guess = [0.0013, 0.012]  # Swanson medians
    bounds = [(0.0005, 0.002), (0.005, 0.020)]
    
    result = minimize(objective, initial_guess, bounds=bounds, 
                     method='L-BFGS-B')
    
    if verbose:
        print(f"  Optimization: success={result.success}, nfev={result.nfev}")
    
    # Calculate R²
    D_T_fit, r_T_fit = result.x
    
    # Get predictions with fitted params
    if model_type == 'fractional':
        p = GBMParameters()
        p.D_T = D_T_fit
        p.r_T = r_T_fit
        sim_func = lambda t_end: simulate(p, t_span=(0, t_end), t_eval=[t_end])
        dx_use = dx
    else:
        p = SwansonParameters()
        p.D_T = D_T_fit
        p.r_T = r_T_fit
        L = 10.0
        Nx = 51
        dx_use = L / (Nx - 1)
        x = np.linspace(0, L, Nx)
        r = np.abs(x - L/2)
        T0_loc = np.exp(- r**2 / 1.0**2)
        T0_loc /= np.max(T0_loc)
        sim_func = lambda t_end: simulate_swanson(p, T0_loc, t_span=(0, t_end),
                                                  t_eval=[t_end], dx=dx_use)
    
    predicted_volumes = [patient.volumes[0]]  # Include t=0
    for t in patient.timepoints[1:]:
        sol = sim_func(t)
        if sol.success:
            mass = np.sum(sol.y[:, -1]) * dx_use
            predicted_volumes.append(10.0 * mass)
        else:
            predicted_volumes.append(np.nan)
    
    predicted_volumes = np.array(predicted_volumes)
    observed_volumes = patient.volumes
    
    # R² calculation
    ss_res = np.sum((observed_volumes - predicted_volumes)**2)
    ss_tot = np.sum((observed_volumes - np.mean(observed_volumes))**2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    
    # Pearson correlation
    corr, _ = pearsonr(observed_volumes, predicted_volumes)
    
    return {
        'D_T': D_T_fit,
        'r_T': r_T_fit,
        'r_squared': r_squared,
        'correlation': corr,
        'predicted_volumes': predicted_volumes,
        'mse': result.fun
    }

def validate_cohort(patients, model_type='fractional'):
    """
    Validate model against patient cohort.
    
    Returns:
        dict: Summary statistics and per-patient results
    """
    results = []
    
    print(f"\nValidating {model_type} model on {len(patients)} patients...")
    print("-" * 70)
    
    for i, patient in enumerate(patients):
        print(f"Patient {patient.patient_id}: ", end='')
        fit_result = fit_model_to_patient(patient, model_type=model_type)
        
        print(f"R²={fit_result['r_squared']:.3f}, "
              f"D_T={fit_result['D_T']:.6f}, "
              f"r_T={fit_result['r_T']:.4f}")
        
        results.append({
            'patient_id': patient.patient_id,
            **fit_result
        })
    
    # Summary statistics
    r_squared_values = [r['r_squared'] for r in results]
    mean_r2 = np.mean(r_squared_values)
    std_r2 = np.std(r_squared_values)
    median_r2 = np.median(r_squared_values)
    
    print("-" * 70)
    print(f"Summary: R² = {mean_r2:.3f} ± {std_r2:.3f} (median={median_r2:.3f})")
    print(f"         {np.sum(np.array(r_squared_values) > 0.7)} / {len(patients)} patients with R² > 0.7")
    
    return {
        'model_type': model_type,
        'n_patients': len(patients),
        'mean_r2': mean_r2,
        'std_r2': std_r2,
        'median_r2': median_r2,
        'per_patient': results
    }

def plot_validation_results(fractional_results, swanson_results, 
                           save_path='validation_comparison.png'):
    """Generate publication figure comparing model fits."""
    
    fig = plt.figure(figsize=(16, 10))
    
    # Get first 6 patients for plotting
    n_plot = min(6, len(fractional_results['per_patient']))
    
    for i in range(n_plot):
        ax = plt.subplot(2, 3, i+1)
        
        patient_id = fractional_results['per_patient'][i]['patient_id']
        
        # Load patient data
        patients = load_brats_cohort(n_patients=10)
        patient = patients[patient_id]
        
        # Plot observed data
        ax.plot(patient.timepoints, patient.volumes, 'ko', 
               markersize=8, label='Observed', zorder=3)
        
        # Plot fractional model fit
        frac_pred = fractional_results['per_patient'][i]['predicted_volumes']
        ax.plot(patient.timepoints, frac_pred, 'b-', linewidth=2, 
               label=f"Fractional (R²={fractional_results['per_patient'][i]['r_squared']:.2f})")
        
        # Plot Swanson model fit
        swan_pred = swanson_results['per_patient'][i]['predicted_volumes']
        ax.plot(patient.timepoints, swan_pred, 'r--', linewidth=2,
               label=f"Swanson (R²={swanson_results['per_patient'][i]['r_squared']:.2f})")
        
        ax.set_xlabel('Time (days)', fontsize=11)
        ax.set_ylabel('Tumor Volume (cm³)', fontsize=11)
        ax.set_title(f'Patient {patient_id}', fontsize=12, fontweight='bold')
        ax.legend(fontsize=9)
        ax.grid(alpha=0.3)
    
    plt.suptitle('Model Validation: Fractional vs Swanson', 
                fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"\nSaved: {save_path}")
    
    return fig

if __name__ == "__main__":
    print("=" * 70)
    print("BraTS VALIDATION FRAMEWORK")
    print("=" * 70)
    
    # Load synthetic cohort
    print("\nLoading patient cohort...")
    patients = load_brats_cohort(n_patients=10, pattern_mix=True)
    print(f"Loaded {len(patients)} patients")
    
    # Validate fractional model
    fractional_results = validate_cohort(patients, model_type='fractional')
    
    # Validate Swanson baseline
    swanson_results = validate_cohort(patients, model_type='swanson')
    
    # Compare
    print("\n" + "=" * 70)
    print("MODEL COMPARISON")
    print("=" * 70)
    print(f"Fractional model: R² = {fractional_results['mean_r2']:.3f} ± {fractional_results['std_r2']:.3f}")
    print(f"Swanson baseline: R² = {swanson_results['mean_r2']:.3f} ± {swanson_results['std_r2']:.3f}")
    
    improvement = (fractional_results['mean_r2'] - swanson_results['mean_r2']) / swanson_results['mean_r2'] * 100
    print(f"Improvement: {improvement:+.1f}%")
    
    # Generate comparison plot
    print("\nGenerating validation plots...")
    plot_validation_results(fractional_results, swanson_results)
    
    print("\n" + "=" * 70)
    print("VALIDATION COMPLETE")
    print("=" * 70)
    print("\nNOTE: Currently using synthetic data.")
    print("Replace BraTSPatient class with real data loader for production.")
