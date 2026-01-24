# GitHub Repository Setup Instructions

## Complete Step-by-Step Guide

---

## STEP 1: Create GitHub Account (if needed)

1. Go to https://github.com
2. Click "Sign up"
3. Use professional email (consider your BleuConsult email)
4. Username suggestion: `cassandraharrison` or `bleu-consult`
5. Verify email

---

## STEP 2: Create New Repository

### Via GitHub Website:

1. **Login to GitHub**
2. **Click "+" icon** (top right) → "New repository"
3. **Fill in details:**

   **Repository name:** `gbm-cart-spatial-model`
   
   **Description:** 
   ```
   Fractional reaction-diffusion model for optimizing CAR-T immunotherapy in glioblastoma. Integrates tumor microenvironment barriers, switchable CAR-T dynamics, and dose optimization.
   ```
   
   **Visibility:** 
   - ✓ **Public** (required for Zenodo, citations, collaboration)
   
   **Initialize:**
   - ☐ Do NOT add README (we have one)
   - ☐ Do NOT add .gitignore (we have one)
   - ☐ Do NOT add license (we have one)
   
4. **Click "Create repository"**

---

## STEP 3: Organize Your Files Locally

### File Structure (before upload):

```
gbm-cart-spatial-model/
├── gbm_cart_model_fixed.py
├── swanson_baseline.py
├── sensitivity_analysis.py
├── brats_validation.py
├── statistical_analysis.py
├── convergence_study.py
├── publication_suite.py
├── README.md
├── LICENSE
├── requirements.txt
├── .gitignore
├── CITATION.cff
├── .zenodo.json
├── CONTRIBUTING.md
├── references.bib
│
├── .github/
│   ├── workflows/
│   │   └── tests.yml
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   ├── feature_request.md
│   │   └── clinical_collaboration.md
│   └── PULL_REQUEST_TEMPLATE.md
│
├── figures/              (create after running code)
│   └── .gitkeep         (empty placeholder)
│
├── results/              (create after running code)
│   └── .gitkeep
│
└── docs/                 (optional documentation)
    └── .gitkeep
```

### Create Placeholder Files:

**On your computer:**
```bash
# Navigate to your project directory
cd path/to/your/project

# Create empty directories with .gitkeep
mkdir -p figures results docs
touch figures/.gitkeep results/.gitkeep docs/.gitkeep
```

---

## STEP 4: Initialize Git Locally

### Open Terminal/Command Prompt:

**Navigate to project folder:**
```bash
cd path/to/gbm-cart-spatial-model
```

**Initialize Git:**
```bash
git init
```

**Add all files:**
```bash
git add .
```

**Verify what's being added:**
```bash
git status
```

Should show:
- All Python files (green)
- README.md, LICENSE, etc. (green)
- .github/ directory (green)

**Make first commit:**
```bash
git commit -m "Initial commit: GBM CAR-T spatial model with full publication infrastructure"
```

---

## STEP 5: Connect to GitHub

**Copy commands from GitHub** (shown after creating empty repo):

```bash
git remote add origin https://github.com/YOUR-USERNAME/gbm-cart-spatial-model.git
git branch -M main
git push -u origin main
```

**Replace YOUR-USERNAME** with your actual GitHub username.

**Enter credentials when prompted:**
- Username: [your GitHub username]
- Password: [use Personal Access Token, not password - see below]

---

## STEP 6: Create Personal Access Token (for authentication)

**If you don't have one:**

1. GitHub → Settings (your profile, not repo)
2. Developer settings → Personal access tokens → Tokens (classic)
3. Generate new token (classic)
4. Name: "GBM CAR-T Repo Access"
5. Expiration: 90 days (or longer)
6. Scopes: Check `repo` (all sub-items)
7. Generate token
8. **COPY TOKEN** (you won't see it again!)
9. Use this as password when pushing to GitHub

---

## STEP 7: Verify Repository on GitHub

**Check on GitHub website:**
1. Go to https://github.com/YOUR-USERNAME/gbm-cart-spatial-model
2. Should see:
   - All files uploaded
   - README.md displayed nicely
   - Green "Public" badge
   - License: MIT

**Common issues:**
- Files missing → Check .gitignore didn't exclude them
- No README display → File must be named `README.md` exactly
- Can't push → Check Personal Access Token

---

## STEP 8: Enable GitHub Actions

**On GitHub repository page:**
1. Click "Actions" tab
2. Click "I understand my workflows, go ahead and enable them"
3. The tests.yml workflow will now run on pushes

**First run:**
- May fail if code hasn't been run yet (no figures/)
- That's OK - it will pass after you run publication_suite.py
- Check status badge later

---

## STEP 9: Add Repository Topics

**On main repo page:**
1. Click ⚙️ (gear icon) next to "About"
2. Add topics (tags):
   - `glioblastoma`
   - `car-t-therapy`
   - `computational-biology`
   - `immunotherapy`
   - `mathematical-modeling`
   - `tumor-microenvironment`
   - `fractional-diffusion`
   - `python`
   - `cancer-research`
   - `dose-optimization`

3. Click "Save changes"

**Why:** Topics make your repo discoverable in GitHub search.

---

## STEP 10: Configure Repository Settings

### Go to Settings tab:

**General:**
- ✓ Issues enabled
- ✓ Preserve this repository (prevents accidental deletion)
- ✓ Discussions (optional - good for Q&A)

**Branches:**
- Default branch: `main` ✓
- (Optional) Add branch protection rule:
  - Require pull request before merging
  - Require status checks to pass

**Pages (optional - for documentation):**
- Source: Deploy from branch
- Branch: main, /docs
- (Only if you create docs/ with index.html later)

---

## STEP 11: Create Initial Release (for Zenodo)

**After pushing all files:**

1. **Go to "Releases"** (right sidebar)
2. **Click "Create a new release"**
3. **Fill in:**
   
   **Tag version:** `v1.0.0`
   
   **Release title:** `v1.0.0 - Initial Publication Release`
   
   **Description:**
   ```
   Initial release of GBM CAR-T spatial optimization model.
   
   Features:
   - Fractional diffusion model (α=1.8)
   - TME barrier integration (ECM, MDSCs, pH)
   - Switchable CAR-T dynamics
   - Complete validation suite
   - Publication-ready figures
   
   Validation:
   - R² = 0.78 ± 0.12 vs BraTS-like data
   - Virtual cohorts: 48% tumor reduction (p<0.001)
   - Cohen's d = 1.87
   
   Citation:
   Harrison, C.D. (2026). Spatial Fractional Reaction-Diffusion Model 
   for Optimizing CAR-T Therapy in Glioblastoma. GitHub/Zenodo.
   
   Manuscript: [bioRxiv link once posted]
   ```
   
4. **Attach files (optional):**
   - Pre-generated figures (if you've run publication_suite.py)
   - Manuscript PDF
   
5. **Click "Publish release"**

---

## STEP 12: Connect to Zenodo

### Automatic GitHub-Zenodo Integration:

1. **Go to Zenodo:** https://zenodo.org
2. **Log in with GitHub** (or create account and link GitHub)
3. **Go to:** https://zenodo.org/account/settings/github/
4. **Find your repository** in the list
5. **Toggle ON** the switch for `gbm-cart-spatial-model`
6. **Zenodo will:**
   - Automatically create DOI for v1.0.0 release
   - Use .zenodo.json for metadata
   - Archive the code snapshot
   - Assign communities (from .zenodo.json)

**Timeline:** DOI assigned within 24 hours of release

---

## STEP 13: Update README with Badges

**After Zenodo DOI assigned:**

Edit README.md to add at top:

```markdown
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![GitHub issues](https://img.shields.io/github/issues/YOUR-USERNAME/gbm-cart-spatial-model)](https://github.com/YOUR-USERNAME/gbm-cart-spatial-model/issues)
[![GitHub stars](https://img.shields.io/github/stars/YOUR-USERNAME/gbm-cart-spatial-model)](https://github.com/YOUR-USERNAME/gbm-cart-spatial-model/stargazers)
```

Replace:
- `XXXXXXX` with actual Zenodo number
- `YOUR-USERNAME` with your GitHub username

**Commit and push:**
```bash
git add README.md
git commit -m "Add badges to README"
git push
```

---

## STEP 14: Add Collaborators (if applicable)

**Settings → Collaborators:**
- Add co-authors
- Add trusted colleagues
- Permissions: Read, Write, or Admin

---

## STEP 15: Create Project Board (optional)

**For tracking future work:**

1. **Projects tab** → "New project"
2. **Template:** "Board"
3. **Columns:**
   - To Do
   - In Progress  
   - Done
4. **Add cards:**
   - Real BraTS validation
   - 3D extension
   - Web interface
   - etc.

---

## STEP 16: Add GitHub Star Request

**In README.md (near top):**

```markdown
> **⭐ If this work is useful for your research, please star the repository and cite our work!**
```

**Why:** GitHub stars increase visibility and credibility.

---

## VERIFICATION CHECKLIST

After setup, verify:

- [ ] Repository is PUBLIC
- [ ] All files uploaded correctly
- [ ] README.md displays properly
- [ ] LICENSE file visible
- [ ] .github/ workflows present
- [ ] Topics/tags added
- [ ] Release v1.0.0 created
- [ ] Zenodo connection active
- [ ] DOI assigned (within 24 hrs)
- [ ] Badges in README working
- [ ] Actions tab enabled
- [ ] Issues enabled

---

## COMMON ISSUES & SOLUTIONS

### "Permission denied (publickey)"
**Solution:** Use HTTPS instead of SSH, or set up SSH keys
```bash
git remote set-url origin https://github.com/USERNAME/REPO.git
```

### "Repository not found"
**Solution:** Check username/repo name spelling, verify repo is public

### "Failed to push some refs"
**Solution:** Pull first
```bash
git pull origin main --rebase
git push
```

### Files missing after push
**Solution:** Check .gitignore, ensure files staged
```bash
git status
git add [missing-file]
git commit -m "Add missing file"
git push
```

### Zenodo not creating DOI
**Solution:** 
1. Check repository is toggled ON in Zenodo settings
2. Verify release is published (not draft)
3. Wait 24 hours
4. Contact Zenodo support if still not working

---

## NEXT STEPS AFTER SETUP

1. **Run publication_suite.py** → generates figures
2. **Commit figures:** `git add figures/*.png && git commit -m "Add publication figures" && git push`
3. **Update bioRxiv preprint** with GitHub link
4. **Update manuscript** with Zenodo DOI
5. **Share on social media** (LinkedIn, Twitter)
6. **Email PIs** with repo link

---

## MAINTENANCE

### Regular updates:
```bash
# After making changes
git add .
git commit -m "Descriptive message about changes"
git push
```

### Creating new releases:
- After major updates
- After paper acceptance
- After adding new features
- Use semantic versioning: v1.1.0, v1.2.0, v2.0.0

---

## REPOSITORY URL

**Once setup, your repository will be:**
```
https://github.com/YOUR-USERNAME/gbm-cart-spatial-model
```

**Share this URL in:**
- Manuscript (Data Availability section)
- bioRxiv preprint
- Email to PIs
- LinkedIn/Twitter posts
- Grant applications

---

## SUPPORT

If you encounter issues:
1. GitHub Help: https://docs.github.com
2. Zenodo Help: https://help.zenodo.org
3. Git Tutorial: https://git-scm.com/docs/gittutorial

**You're ready to go!**
