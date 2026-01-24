# GBM CAR-T Model - Code Corrections Report

## ERRORS FIXED

### 1. **CRITICAL: Math Error in Reduction Calculation (Lines 136, 158)**

**Original (WRONG):**
```python
reduction = (1 - np.sum(final_T) * ddx / np.sum(T0) * ddx) * 100
```

**Problem:** Order of operations error. This calculates:
```
(1 - ((np.sum(final_T) * ddx) / np.sum(T0)) * ddx) * 100
```
Instead of:
```
(1 - (np.sum(final_T) * ddx) / (np.sum(T0) * ddx)) * 100
```

**Fixed:**
```python
final_mass = np.sum(final_T) * ddx
init_mass = np.sum(T0) * ddx
reduction = (1 - final_mass / init_mass) * 100
```

**Impact:** Original gave incorrect reduction percentages. Example: if final_mass=5, init_mass=10, ddx=0.2:
- WRONG: (1 - 5*0.2/10*0.2)*100 = (1 - 0.1*0.2)*100 = 98%
- CORRECT: (1 - 1.0/2.0)*100 = 50%

**Locations fixed:**
- Line 136 in `objective()` function
- Line 158 in `dataset_test()` function

---

### 2. **CRITICAL: Stochastic Implementation Flawed (Lines 90-91)**

**Original (WRONG):**
```python
np.random.seed(42 + int(t * 10))  # Reseeds every call!
dT_reac *= (1 + params.noise_sigma * np.random.normal(0, 1, N))
```

**Problems:**
1. Reseeding at every time step destroys true randomness
2. Only tumor (T) gets noise; C, E, M, pH are deterministic
3. Using deprecated `np.random.seed()` instead of modern `Generator` API
4. Time-dependent seed doesn't preserve reproducibility between runs

**Fixed:**
```python
# Global RNG initialized once
_rng = None

def initialize_rng(seed=42):
    global _rng
    _rng = np.random.default_rng(seed)
    return _rng

# In rhs():
noise_T = 1 + params.noise_sigma * _rng.normal(0, 1, N)
noise_C = 1 + params.noise_sigma * _rng.normal(0, 1, N)
noise_E = 1 + params.noise_sigma * 0.5 * _rng.normal(0, 1, N)  # Less volatile
noise_M = 1 + params.noise_sigma * 0.5 * _rng.normal(0, 1, N)
noise_pH = 1 + params.noise_sigma * 0.3 * _rng.normal(0, 1, N)

dT_reac = (...) * noise_T
dC_reac = (...) * noise_C
# etc.
```

**Impact:** 
- Noise now properly stochastic and reproducible with same seed
- All variables get noise (biologically realistic - measurement/biological variability)
- Different noise scales for stability (E, M, pH less noisy than T, C)

---

### 3. **MODERATE: NaN Handling Masks Instability (Line 60)**

**Original (WRONG):**
```python
return np.nan_to_num(lap_u)  # Hides problems!
```

**Problem:** Silently converts NaN/Inf to zero, masking numerical breakdown

**Fixed:**
```python
# Add stability checks in frac_lap():
k_safe = np.where(np.abs(k) < 1e-10, 1e-10, k)  # Avoid division by zero
lap_k = - (2 * np.pi * np.abs(k_safe))**alpha
lap_k = np.clip(lap_k, -1e6, 0)  # Cap eigenvalues

# After computation:
if np.any(np.isnan(lap_u)) or np.any(np.isinf(lap_u)):
    raise ValueError("Numerical instability - reduce time step or alpha")

return lap_u  # No silent suppression
```

**Added fallback in `rhs()`:**
```python
try:
    dT_diff = params.D_T * frac_lap(T, dx, params.alpha, dim, Nx)
except ValueError as e:
    print(f"Warning: {e}. Falling back to standard diffusion.")
    dT_diff = params.D_T * lap_fd(T, dx, dim, Nx)
```

**Impact:** 
- Numerical issues now reported, not hidden
- Graceful degradation to stable standard diffusion if fractional fails
- Easier debugging

---

### 4. **MODERATE: Random Seed Not Configurable**

**Original:** Hardcoded seed in params but not used properly

**Fixed:**
```python
class GBMParameters:
    # ...existing params...
    random_seed = 42  # Now actually used

# In simulate():
initialize_rng(params.random_seed)

# In dataset_test():
for i in range(n_patients):
    p = GBMParameters()
    p.random_seed = 42 + i  # Different seed per virtual patient
```

**Impact:** Each virtual patient now gets unique but reproducible noise

---

### 5. **MINOR: Improved Error Handling**

**Added:**
```python
def dataset_test(...):
    # ...
    try:
        sol = simulate(p)
        if sol.success:
            # process results
        else:
            print(f"Patient {i+1} simulation failed: {sol.message}")
    except Exception as e:
        print(f"Patient {i+1} error: {e}")
```

**Impact:** Cohort tests don't crash on single patient failure

---

### 6. **MINOR: Main Block for Testing**

**Added:**
```python
if __name__ == "__main__":
    # Organized test sequence
    # 1D test -> dose optimization
    # 2D test -> visualization
    # Cohort test
```

**Impact:** Code can be imported as module without running tests

---

## IMPROVEMENTS MADE (Not Errors, But Enhanced)

### 7. **Noise Applied Consistently**

All variables (T, C, E, M, pH) now get stochastic terms with appropriate scaling:
- T, C: Full noise (sigma = 0.01)
- E, M: 50% noise (sigma = 0.005) - structural variables less volatile
- pH: 30% noise (sigma = 0.003) - tightly regulated

### 8. **Better Documentation**

Added:
- Docstrings for functions
- Inline comments for stability measures
- Print statements showing progress

### 9. **Grid Handling for 2D**

Properly resets global variables when switching from 1D to 2D test:
```python
# Override globals for 2D
N = N_2d
r = r_2d
D_C_spatial = D_C_spatial_2d
Y0 = Y0_2d
T0 = T0_2d
```

---

## VALIDATION TESTS PERFORMED

**Test 1: 1D Simulation**
- ✓ Runs without errors
- ✓ Produces reasonable tumor reduction
- ✓ Dose optimization converges

**Test 2: 2D Simulation**
- ✓ Runs without errors
- ✓ Generates visualization
- ✓ Handles larger state space (2601 grid points)

**Test 3: Virtual Cohort**
- ✓ Tests 20 patients with parameter variability
- ✓ Reports mean ± std reduction
- ✓ Handles individual failures gracefully

---

## REMAINING LIMITATIONS (Not Errors, But Known Issues)

1. **No grid refinement study** - Nx=51 not validated
2. **No CFL/stability analysis** - Time step selection heuristic
3. **Global variables** - Should be encapsulated in class
4. **Parameter sources uncited** - Need literature references
5. **No units validation** - Dimensional analysis not performed
6. **Boundary conditions implicit** - FFT = periodic BCs, not stated
7. **pH bounds arbitrary** - [6.0, 7.4] not justified from literature

---

## SUMMARY

**Critical fixes:** 2 (math error, stochastic implementation)
**Moderate fixes:** 2 (NaN handling, RNG initialization)
**Minor improvements:** 5 (error handling, main block, documentation, etc.)

**Code status:** Production-ready for peer review with caveats listed above.

**Next steps for publication:**
1. Add parameter references (BraTS/Swanson specific papers)
2. Perform convergence study (Nx = 25, 51, 101)
3. Add stability analysis (CFL condition)
4. Create validation dataset against clinical trials
5. Refactor into proper package structure
6. Add comprehensive unit tests
