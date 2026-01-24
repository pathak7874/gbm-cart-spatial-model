---
name: Bug report
about: Report a bug or numerical issue
title: '[BUG] '
labels: bug
assignees: ''

---

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Run command '...'
2. With parameters '...'
3. See error

**Expected behavior**
What you expected to happen.

**Actual behavior**
What actually happened.

**Error message**
```
Paste full error traceback here
```

**Environment:**
 - OS: [e.g. Ubuntu 22.04, macOS 13, Windows 11]
 - Python version: [e.g. 3.10.8]
 - NumPy version: [e.g. 1.24.0]
 - SciPy version: [e.g. 1.10.0]

**Code snippet**
```python
# Minimal example to reproduce
from gbm_cart_model_fixed import GBMParameters, simulate
# ... your code
```

**Additional context**
- Are you using modified parameters?
- Does it work with default settings?
- Any custom modifications to the code?

**Numerical accuracy concern?**
If this is about numerical results:
- [ ] Mass conservation error > 0.1%
- [ ] Negative concentrations
- [ ] NaN/Inf values
- [ ] Solution divergence
- [ ] Grid refinement changes results >5%
