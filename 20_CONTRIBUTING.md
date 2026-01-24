# Contributing to GBM CAR-T Spatial Model

Thank you for your interest in contributing to this project! This computational framework aims to optimize CAR-T therapy for glioblastoma patients, and community contributions are welcome.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your environment (Python version, OS, etc.)
- Code snippet if applicable

**Before submitting:** Search existing issues to avoid duplicates.

### Suggesting Enhancements

Enhancement suggestions are welcome! Please:
- Describe the feature clearly
- Explain the use case (clinical, research, educational)
- Provide examples if possible
- Tag as "enhancement"

### Code Contributions

#### Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR-USERNAME/gbm-cart-spatial-model.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Install dependencies: `pip install -r requirements.txt`
5. Make your changes
6. Test thoroughly
7. Submit a pull request

#### Code Standards

**Python Style:**
- Follow PEP 8
- Use type hints where appropriate
- Add docstrings for functions/classes
- Keep functions focused and modular

**Documentation:**
- Update README.md if adding features
- Add comments for complex logic
- Include references for biological/clinical parameters

**Testing:**
- Ensure existing tests pass
- Add tests for new features
- Verify numerical accuracy

#### Biological/Clinical Validation

Contributions involving parameter changes or model modifications should:
- Cite peer-reviewed literature
- Explain biological justification
- Validate against known behavior
- Document assumptions clearly

### Pull Request Process

1. **Update documentation** - README, docstrings, etc.
2. **Ensure tests pass** - Run existing validation suite
3. **Describe changes** - Clear PR description
4. **Link issues** - Reference related issues
5. **Be patient** - Review may take 1-2 weeks

### Areas Needing Contribution

**High Priority:**
- [ ] Real BraTS data validation (replace synthetic patients)
- [ ] 3D extension with anatomical geometry
- [ ] Patient-specific parameter estimation from MRI
- [ ] Web interface for clinical use
- [ ] Additional TME mechanisms (Tregs, PD-L1)

**Medium Priority:**
- [ ] Multi-phenotype CAR-T model
- [ ] Stochastic Gillespie implementation
- [ ] Metabolic coupling (glucose, lactate)
- [ ] Angiogenesis and necrosis
- [ ] GPU acceleration

**Documentation:**
- [ ] Tutorial notebooks (Jupyter)
- [ ] Video walkthrough
- [ ] Clinical use case examples
- [ ] Parameter sensitivity guide

### Clinical Collaborations

If you're a clinician interested in using this model:
- Email: [your contact email]
- We can discuss data sharing agreements
- Patient-specific simulations available
- Co-authorship on validation studies

### Code of Conduct

**Be Respectful:**
- Constructive feedback only
- No personal attacks
- Assume good intentions
- Focus on science, not politics

**Be Professional:**
- This work impacts patient care
- Accuracy matters more than speed
- Cite sources properly
- Acknowledge limitations

**Be Inclusive:**
- Welcome researchers at all levels
- Encourage questions
- Mentor newcomers
- Share knowledge freely

### Questions?

- Create a discussion thread
- Email: [contact email]
- Check existing issues/discussions

### Attribution

Contributors will be acknowledged in:
- README.md (Contributors section)
- Published papers (if substantial contribution)
- Release notes

Thank you for helping improve GBM CAR-T therapy!

---

**Note on AI Contributions:**
This project was developed with AI assistance (Claude, Anthropic). AI-assisted contributions are acceptable if:
- You understand the code/science
- You can defend the approach
- You disclose AI use in PR
- Human reviewer validates accuracy
