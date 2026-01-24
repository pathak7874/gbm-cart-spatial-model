"""
Publication Suite - Complete Analysis Pipeline
================================================
Runs all validation, sensitivity, convergence, and statistical analyses.
Generates publication-ready figures for manuscript submission.

Usage:
    python publication_suite.py --full     # Run all analyses (2-4 hours)
    python publication_suite.py --quick    # Quick test (15 minutes)
    python publication_suite.py --figures  # Generate figures only (from cached results)

Outputs:
    figures/
        fig1_model_schematic.png
        fig2_validation_comparison.png
        fig3_sensitivity_analysis.png
        fig4_statistical_cohorts.png
        fig5_convergence_study.png
        figS1_parameter_sweeps.png
        figS2_2d_spatial_distribution.png

    results/
        validation_results.npz
        sensitivity_results.npz
        statistical_results.npz
        convergence_results.npz
"""

import numpy as np
import matplotlib.pyplot as plt
import os
import sys
from datetime import datetime
import argparse

# Import analysis modules
sys.path.append(os.path.dirname(__file__))
from brats_validation import load_brats_cohort, validate_cohort, plot_validation_results
from sensitivity_analysis import sobol_indices, tornado_plot, multi_parameter_sweep_plot
from statistical_analysis import virtual_cohort_analysis, compare_cohorts, plot_cohort_comparison
from convergence_study import convergence_test_spatial, convergence_test_temporal, plot_convergence_results

def setup_directories():
    """Create output directories."""
    os.makedirs('figures', exist_ok=True)
    os.makedirs('results', exist_ok=True)
    print("Output directories created: figures/, results/")

def run_full_analysis(mode='quick'):
    """
    Run complete analysis pipeline.
    
    Args:
        mode: 'quick' (n=20, Nx=[25,51]) or 'full' (n=100, Nx=[25,51,101,201])
    """
    
    print("=" * 80)
    print("PUBLICATION ANALYSIS SUITE")
    print(f"Mode: {mode.upper()}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    results = {}
    
    # ========================================
    # 1. BraTS Validation
    # ========================================
    print("\n" + "=" * 80)
    print("1. BraTS VALIDATION")
    print("=" * 80)
    
    n_patients = 10 if mode == 'quick' else 20
    patients = load_brats_cohort(n_patients=n_patients, pattern_mix=True)
    
    print("\nValidating Fractional Model...")
    fractional_results = validate_cohort(patients, model_type='fractional')
    
    print("\nValidating Swanson Baseline...")
    swanson_results = validate_cohort(patients, model_type='swanson')
    
    print("\nGenerating validation figure...")
    plot_validation_results(fractional_results, swanson_results,
                           save_path='figures/fig2_validation_comparison.png')
    
    results['validation'] = {
        'fractional': fractional_results,
        'swanson': swanson_results,
        'patients': patients
    }
    
    # Save results
    np.savez('results/validation_results.npz',
             fractional_r2=fractional_results['mean_r2'],
             swanson_r2=swanson_results['mean_r2'],
             improvement=(fractional_results['mean_r2'] - swanson_results['mean_r2']) / swanson_results['mean_r2'] * 100)
    
    # ========================================
    # 2. Sensitivity Analysis
    # ========================================
    print("\n" + "=" * 80)
    print("2. SENSITIVITY ANALYSIS")
    print("=" * 80)
    
    n_samples = 128 if mode == 'quick' else 512
    print(f"\nRunning Sobol analysis (n={n_samples} samples)...")
    sobol_results, sobol_outcomes = sobol_indices(n_samples=n_samples)
    
    print("\nGenerating sensitivity figures...")
    tornado_plot(sobol_results, save_path='figures/fig3_tornado_plot.png')
    multi_parameter_sweep_plot(save_path='figures/figS1_parameter_sweeps.png')
    
    results['sensitivity'] = {
        'sobol': sobol_results,
        'outcomes': sobol_outcomes
    }
    
    # Save results
    np.savez('results/sensitivity_results.npz',
             sobol_results=sobol_results,
             outcomes=sobol_outcomes)
    
    # ========================================
    # 3. Statistical Analysis (Virtual Cohorts)
    # ========================================
    print("\n" + "=" * 80)
    print("3. STATISTICAL ANALYSIS")
    print("=" * 80)
    
    n_cohort = 50 if mode == 'quick' else 100
    
    print(f"\nRunning CAR-T cohort (n={n_cohort})...")
    cart_results = virtual_cohort_analysis(n_patients=n_cohort, treatment='cart', seed=42)
    
    print(f"\nRunning control cohort (n={n_cohort})...")
    control_results = virtual_cohort_analysis(n_patients=n_cohort, treatment='control', seed=100)
    
    print("\nStatistical comparison...")
    comparison = compare_cohorts(cart_results, control_results)
    
    print("\nGenerating cohort comparison figure...")
    plot_cohort_comparison(cart_results, control_results,
                          save_path='figures/fig4_statistical_cohorts.png')
    
    results['statistical'] = {
        'cart': cart_results,
        'control': control_results,
        'comparison': comparison
    }
    
    # Save results
    np.savez('results/statistical_results.npz',
             cart_mean=cart_results['mean_reduction'],
             control_mean=control_results['mean_reduction'],
             p_value=comparison['reduction']['t_pvalue'],
             cohens_d=comparison['reduction']['cohens_d'])
    
    # ========================================
    # 4. Convergence Study
    # ========================================
    print("\n" + "=" * 80)
    print("4. CONVERGENCE STUDY")
    print("=" * 80)
    
    if mode == 'quick':
        nx_vals = [25, 51]
        rtol_vals = [1e-3, 1e-5]
    else:
        nx_vals = [25, 51, 101]
        rtol_vals = [1e-3, 1e-4, 1e-5, 1e-6]
    
    print(f"\nSpatial convergence (Nx={nx_vals})...")
    spatial_conv = convergence_test_spatial(nx_values=nx_vals, t_end=60)
    
    print(f"\nTemporal convergence (rtol={rtol_vals})...")
    temporal_conv = convergence_test_temporal(rtol_values=rtol_vals)
    
    print("\nGenerating convergence figure...")
    plot_convergence_results(spatial_conv, temporal_conv,
                            save_path='figures/fig5_convergence_study.png')
    
    results['convergence'] = {
        'spatial': spatial_conv,
        'temporal': temporal_conv
    }
    
    # Save results
    np.savez('results/convergence_results.npz',
             nx_values=nx_vals,
             spatial_results=spatial_conv)
    
    # ========================================
    # Summary Report
    # ========================================
    print("\n" + "=" * 80)
    print("ANALYSIS SUMMARY")
    print("=" * 80)
    
    print("\n1. Validation Results:")
    print(f"   Fractional model: R² = {fractional_results['mean_r2']:.3f} ± {fractional_results['std_r2']:.3f}")
    print(f"   Swanson baseline: R² = {swanson_results['mean_r2']:.3f} ± {swanson_results['std_r2']:.3f}")
    improvement = (fractional_results['mean_r2'] - swanson_results['mean_r2']) / swanson_results['mean_r2'] * 100
    print(f"   Improvement: {improvement:+.1f}%")
    
    print("\n2. Sensitivity Analysis:")
    sorted_params = sorted(sobol_results.items(), key=lambda x: abs(x[1]['mean_effect']), reverse=True)
    print("   Top 3 parameters by influence:")
    for i, (param, indices) in enumerate(sorted_params[:3]):
        print(f"     {i+1}. {param}: ΔEffect = {indices['mean_effect']:+.1f}%")
    
    print("\n3. Statistical Analysis:")
    print(f"   CAR-T: {cart_results['mean_reduction']:.1f}% ± {cart_results['std_reduction']:.1f}% reduction")
    print(f"   Control: {control_results['mean_reduction']:.1f}% ± {control_results['std_reduction']:.1f}% reduction")
    print(f"   p-value: {comparison['reduction']['t_pvalue']:.6f}")
    print(f"   Cohen's d: {comparison['reduction']['cohens_d']:.2f}")
    
    print("\n4. Convergence:")
    nx_list = sorted([k for k, v in spatial_conv.items() if v['success']])
    if len(nx_list) >= 2:
        conv_check = abs(spatial_conv[nx_list[-1]]['reduction'] - 
                        spatial_conv[nx_list[-2]]['reduction'])
        print(f"   Convergence: {conv_check:.3f}% change between finest grids")
        if conv_check < 1.0:
            print(f"   ✓ CONVERGED - Recommended Nx={nx_list[-2]}")
        else:
            print(f"   ✗ Not fully converged - consider Nx={nx_list[-1]*2}")
    
    print("\n" + "=" * 80)
    print("Figures saved to: figures/")
    print("Results saved to: results/")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    return results

def generate_model_schematic():
    """
    Generate Figure 1: Model schematic with equations.
    This is a placeholder - create actual schematic in external tool.
    """
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.text(0.5, 0.9, 'GBM CAR-T Spatial Model', 
           ha='center', fontsize=20, fontweight='bold')
    
    # Equations
    equations = [
        r'$\frac{\partial T}{\partial t} = D_T \nabla^\alpha T + r_T T(1-T) - k_{CT} C T (1-\gamma T) \eta - h_T T$',
        r'$\frac{\partial C}{\partial t} = D_C(x) \nabla^\alpha C + r_C C \frac{T}{T+0.5} - h_C C + \delta(t) I(x)$',
        r'$\frac{\partial E}{\partial t} = D_E \nabla^2 E + \beta_E - d_E E (1 + 0.1 T)$',
        r'$\frac{\partial M}{\partial t} = D_M \nabla^2 M + T - 0.1 M - d_M M$',
        r'$\frac{\partial pH}{\partial t} = D_{pH} \nabla^2 pH - 0.1 T + b_{pH} (7.4 - pH)$',
    ]
    
    y_pos = 0.7
    for eq in equations:
        ax.text(0.5, y_pos, eq, ha='center', fontsize=12, 
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        y_pos -= 0.12
    
    # Key features
    ax.text(0.1, 0.15, 'Key Features:\n• Fractional diffusion (α=1.8)\n• TME barriers (ECM, MDSC, pH)\n• Switchable CAR-T killing\n• Dose optimization',
           fontsize=11, verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))
    
    ax.axis('off')
    plt.tight_layout()
    plt.savefig('figures/fig1_model_schematic.png', dpi=300, bbox_inches='tight')
    print("Model schematic saved (placeholder - replace with actual diagram)")

def main():
    parser = argparse.ArgumentParser(description='Run publication analysis suite')
    parser.add_argument('--mode', choices=['quick', 'full', 'figures'], 
                       default='quick',
                       help='Analysis mode: quick (15 min), full (2-4 hrs), figures (regen only)')
    args = parser.parse_args()
    
    setup_directories()
    
    if args.mode == 'figures':
        print("Regenerating figures from saved results...")
        # Load and replot (implementation depends on saved data structure)
        print("NOT IMPLEMENTED - run --mode quick or --mode full first")
    else:
        generate_model_schematic()
        run_full_analysis(mode=args.mode)
    
    print("\n" + "=" * 80)
    print("PUBLICATION SUITE COMPLETE")
    print("Next steps:")
    print("  1. Review figures in figures/ directory")
    print("  2. Check results/*.npz for numerical data")
    print("  3. Replace fig1_model_schematic.png with proper diagram")
    print("  4. Use these figures in manuscript submission")
    print("=" * 80)

if __name__ == "__main__":
    main()
