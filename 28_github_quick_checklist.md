# GitHub Setup Quick Checklist

## Monday Morning (30-45 minutes)

### Prerequisites
- [ ] GitHub account created
- [ ] Git installed on your computer (download from https://git-scm.com)
- [ ] All project files in one folder

### Step 1: Create Repository (5 min)
- [ ] Go to https://github.com
- [ ] Click "+" → "New repository"
- [ ] Name: `gbm-cart-spatial-model`
- [ ] Public repository
- [ ] Do NOT initialize with README/license/.gitignore
- [ ] Click "Create repository"

### Step 2: Upload Files (10 min)
```bash
cd /path/to/your/project/folder
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR-USERNAME/gbm-cart-spatial-model.git
git branch -M main
git push -u origin main
```

### Step 3: Personal Access Token (5 min)
- [ ] GitHub → Settings → Developer settings → Personal access tokens
- [ ] Generate new token (classic)
- [ ] Select "repo" scope
- [ ] Copy token (save somewhere safe!)
- [ ] Use as password when pushing

### Step 4: Configure Repository (5 min)
- [ ] Add topics: glioblastoma, car-t-therapy, computational-biology, etc.
- [ ] Enable Issues (Settings → General)
- [ ] Enable Discussions (optional)

### Step 5: Create Release (10 min)
- [ ] Click "Releases" → "Create a new release"
- [ ] Tag: `v1.0.0`
- [ ] Title: `v1.0.0 - Initial Publication Release`
- [ ] Description: See GITHUB_SETUP_INSTRUCTIONS.md
- [ ] Publish release

### Step 6: Connect Zenodo (5 min)
- [ ] Go to https://zenodo.org
- [ ] Log in with GitHub
- [ ] Enable repository at https://zenodo.org/account/settings/github/
- [ ] Wait 24 hours for DOI

### Step 7: Add Badges (5 min)
- [ ] Edit README.md
- [ ] Add Zenodo DOI badge (after DOI assigned)
- [ ] Commit and push changes

---

## Verification (5 min)

Visit your repo: `https://github.com/YOUR-USERNAME/gbm-cart-spatial-model`

Check:
- [ ] All files visible
- [ ] README displays nicely
- [ ] Green "Public" badge
- [ ] Topics/tags showing
- [ ] Release v1.0.0 exists
- [ ] License: MIT

---

## What You'll Have

**GitHub URL:**
`https://github.com/YOUR-USERNAME/gbm-cart-spatial-model`

**Zenodo DOI (within 24 hours):**
`https://doi.org/10.5281/zenodo.XXXXXXX`

**Use these in:**
- ✓ bioRxiv preprint
- ✓ Manuscript Data Availability
- ✓ PI outreach emails
- ✓ LinkedIn/Twitter posts

---

## Need Help?

**Common errors:**
1. "Permission denied" → Use Personal Access Token as password
2. "Repository not found" → Check spelling of username/repo name
3. Files missing → Check .gitignore didn't exclude them

**Detailed guide:** See GITHUB_SETUP_INSTRUCTIONS.md

**Still stuck?** GitHub help: https://docs.github.com

---

## After Setup

**Immediately:**
- [ ] Share GitHub link on LinkedIn
- [ ] Add to PI outreach emails (Friday)
- [ ] Include in bioRxiv submission (Wednesday)

**This week:**
- [ ] Run `python publication_suite.py --mode full`
- [ ] Commit and push generated figures
- [ ] Update README with DOI badge

**Done! You're live on GitHub.**
