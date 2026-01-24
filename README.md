# Spatial Fractional Reaction-Diffusion Model for Optimizing CAR-T Therapy in Glioblastoma

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.18361371-blue)](https://doi.org/10.5281/zenodo.18361371)

## Overview

This repository contains a comprehensive computational framework for modeling and optimizing CAR-T therapy in glioblastoma multiforme (GBM). The model integrates:

- **Fractional diffusion** (α = 1.8) to capture anomalous invasion patterns
- **Tumor microenvironment barriers**: Extracellular matrix (ECM), myeloid-derived suppressor cells (MDSCs), and acidic pH
- **Switchable CAR-T killing dynamics** (inspired by UCSF E-SYNC platform)
- **IL-21 proliferation enhancement** (based on MD Anderson trials)
- **Spatial dose optimization** with entropy regularization

## Key Features

- ✅ **Validated against clinical data**: BraTS dataset with R² > 0.75
- ✅ **Comprehensive sensitivity analysis**: Sobol indices for parameter importance
- ✅ **Statistical rigor**: Bootstrap CI, hypothesis testing, effect size calculation
- ✅ **Numerical validation**: Grid convergence study and mass conservation
- ✅ **Publication-ready figures**: 7 figures with professional formatting
- ✅ **Fast execution**: ~2 seconds per simulation on standard hardware

## Installation

### Requirements

- Python 3.8+
- NumPy ≥ 1.21.0
- SciPy ≥ 1.7.0
- Matplotlib ≥ 3.4.0

### Quick Install

```bash
git clone https://github.com/bleuradience/gbm-cart-spatial-model.git
cd gbm-cart-spatial-model
pip install -r requirements.txt
```

## Quick Start

### Run basic simulation

```python
python gbm_cart_model_fixed.py
```

### Run complete publication analysis suite

```bash
# Quick test (15 minutes)
python publication_suite.py --mode quick

# Full analysis for publication (2-4 hours)
python publication_suite.py --mode full
```

### Run individual analyses

```bash
python brats_validation.py        # Validate against clinical data
python sensitivity_analysis.py    # Parameter sensitivity
python statistical_analysis.py    # Virtual cohort statistics
python convergence_study.py       # Numerical convergence
```

## Repository Structure

```
.
├── gbm_cart_model_fixed.py          # Main model implementation
├── swanson_baseline.py              # Baseline Swanson model
├── sensitivity_analysis.py          # Sobol sensitivity analysis
├── brats_validation.py              # Clinical data validation
├── statistical_analysis.py          # Cohort statistics
├── convergence_study.py             # Numerical validation
├── publication_suite.py             # Master analysis pipeline
├── references.bib                   # Complete bibliography
├── requirements.txt                 # Python dependencies
├── README.md                        # This file
├── LICENSE                          # CC BY-NC-SA 4.0
├── CITATION.cff                     # Citation metadata
│
├── figures/                         # Generated figures
│   ├── fig1_model_schematic.png
│   ├── fig2_validation_comparison.png
│   ├── fig3_tornado_plot.png
│   ├── fig4_statistical_cohorts.png
│   ├── fig5_convergence_study.png
│   └── ...
│
└── results/                         # Numerical results (.npz)
    ├── validation_results.npz
    ├── sensitivity_results.npz
    ├── statistical_results.npz
    └── convergence_results.npz
```

## Model Description

### Governing Equations

The model consists of five coupled partial differential equations:

**Tumor cells (T)**:
```
∂T/∂t = D_T ∇^α T + r_T T(1-T) - k_CT C T (1-γT) η - h_T T
```

**CAR-T cells (C)**:
```
∂C/∂t = D_C(x) ∇^α C + r_C C T/(T+0.5) - h_C C + δ(t) I(x)
```

**Extracellular matrix (E)**:
```
∂E/∂t = D_E ∇² E + β_E - d_E E (1 + 0.1T)
```

**MDSCs (M)**:
```
∂M/∂t = D_M ∇² M + T - 0.1M - d_M M
```

**pH**:
```
∂pH/∂t = D_pH ∇² pH - 0.1T + b_pH (7.4 - pH)
```

Where:
- α = 1.8 (fractional diffusion exponent)
- η = efficacy penalty from TME barriers
- ∇^α = fractional Laplacian operator

### Parameters

All parameters derived from published literature:

| Parameter | Value | Source |
|-----------|-------|--------|
| D_T | 0.001 cm²/day | Swanson et al. 2008 |
| r_T | 0.012 day⁻¹ | Rockne et al. 2010 |
| k_CT | 1.5 | Tunable (E-SYNC) |
| r_C | 0.27 day⁻¹ | MD Anderson IL-21 |

See `references.bib` for complete citations.

## Validation Results

### Clinical Data Fit
- **Fractional model**: R² = 0.78 ± 0.12
- **Swanson baseline**: R² = 0.65 ± 0.15
- **Improvement**: +20% better fit

### Virtual Cohort (n=100)
- **CAR-T treatment**: 48.3% ± 12.7% tumor reduction
- **Control**: -5.2% ± 8.3% (tumor growth)
- **p-value**: < 0.001
- **Cohen's d**: 1.87 (large effect)

### Computational Performance
- **Simulation time**: 2.1 seconds (Nx=51, 1D)
- **Convergence**: Verified at Nx=51
- **Mass conservation**: < 0.05% error

## Key Findings

1. **Fractional diffusion improves model accuracy by 20%** over standard diffusion
2. **Tumor invasion rate (D_T) is most influential parameter** (ΔEffect ~22%)
3. **CAR-T therapy shows significant benefit**: p < 0.001, Cohen's d = 1.87
4. **TME barriers reduce efficacy by ~15%** without interventions
5. **Optimal CAR-T dose**: 0.45-0.55 (normalized units)

## Citation

If you use this code in your research, please cite:

```bibtex
@software{harrison2026gbm,
  author    = {Harrison, Cassandra D.},
  title     = {Spatial Fractional Reaction-Diffusion Model for 
               Optimizing CAR-T Therapy in Glioblastoma},
  year      = {2026},
  publisher = {Zenodo},
  version   = {1.0.0},
  doi       = {10.5281/zenodo.18361371},
  url       = {https://github.com/bleuradience/gbm-cart-spatial-model}
}
```

## License

**CC BY-NC-SA 4.0** (Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International)

- ✅ **Allowed:** Academic research, clinical research (non-commercial), education, personal use, non-profit use
- ❌ **Prohibited:** Commercial use, selling this software or derivatives, pharmaceutical/biotech company use without separate license
- 💼 **Commercial licensing available** - Contact for pharmaceutical partnerships, commercial integration, or consulting

This ensures the model remains freely available for research while protecting against unauthorized commercial exploitation.

See the [LICENSE](LICENSE) file for complete terms and commercial licensing contact information.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/YourFeature`)
3. Commit your changes (`git commit -m 'Add YourFeature'`)
4. Push to the branch (`git push origin feature/YourFeature`)
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## Acknowledgments

- **BraTS Challenge** for multi-institutional GBM imaging data
- **City of Hope** (Dr. Christine Brown) for IL13Rα2 CAR-T clinical trials
- **UPenn** (Dr. Donald O'Rourke) for EGFRvIII CAR-T trials  
- **UCSF** for E-SYNC switchable CAR-T platform
- **MD Anderson** for IL-21 enhancement work

## Contact

**Cassandra D. Harrison, MBA, MPH**  
Principal Consultant, BleuConsult/AvaBleu Design LLC  
bleuisresting@gmail.com

## References

See [`references.bib`](references.bib) for complete bibliography (30+ citations).

Key references:

- Swanson et al. (2008). *Cancer Research*, 68(6), 1725–1731.
- Brown et al. (2016). *New England Journal of Medicine*, 375(26), 2561–2563.
- O'Rourke et al. (2017). *Science Translational Medicine*, 9(399), eaaa0984.
- Quail & Joyce (2013). *Nature Medicine*, 19(11), 1423–1437.

---

**Status**: Ready for manuscript submission  
**Last Updated**: January 2026  
**Version**: 1.0.0
