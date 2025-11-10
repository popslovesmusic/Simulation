# IGSOA State Analysis Documentation

**Complete documentation suite for analyzing IGSOA simulation data**

---

## 📚 Documentation Index

| Document | Purpose | When to Use |
|----------|---------|-------------|
| **[Quick Reference](ANALYSIS_QUICK_REFERENCE.md)** | One-page cheat sheet | Starting out, need quick commands |
| **[Full Guide](IGSOA_ANALYSIS_GUIDE.md)** | Complete documentation | Learning features, troubleshooting |
| **[Workflow Diagram](ANALYSIS_WORKFLOW.md)** | Visual guide | Understanding the pipeline |
| **This README** | Overview & getting started | First time here |

---

## 🎯 What Does the Analysis Do?

The IGSOA state analysis tool (`analyze_igsoa_state.py`) processes simulation outputs and provides:

### Physical Insights
- **Spatial correlations** - How information spreads through the network
- **Spectral content** - Frequency decomposition via FFT
- **R_c validation** - Verifies causal structure implementation
- **Equilibration tracking** - Measures approach to steady state
- **Φ-Ψ coupling** - Quantum-classical field interactions

### Outputs
- **Text reports** with statistical summaries and validation checks
- **Publication-quality plots** in PNG, PDF, or SVG format
- **Automated diagnostics** to catch numerical issues

---

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Install required packages
pip install numpy scipy matplotlib
```

### 2. Run Your First Analysis

```bash
# Navigate to CLI directory
cd dase_cli

# Create a simple test simulation
cat > test_simulation.json << 'EOF'
{"command":"create_engine","params":{"engine_type":"igsoa_complex","num_nodes":4096}}
{"command":"set_igsoa_state","params":{"engine_id":"engine_001","profile_type":"gaussian","params":{"amplitude":1.5,"center_node":2048,"width":256,"baseline_phi":0.0}}}
{"command":"run_mission","params":{"engine_id":"engine_001","num_steps":500,"iterations_per_node":30}}
{"command":"get_state","params":{"engine_id":"engine_001"}}
{"command":"destroy_engine","params":{"engine_id":"engine_001"}}
EOF

# Run simulation
cat test_simulation.json | ./dase_cli.exe > test_output.json

# Analyze results (assuming R_c = 1.0)
python ../analyze_igsoa_state.py test_output.json 1.0

# Check results
cd igsoa_analysis/
ls
```

You should see:
- `analysis_report_R1.0.txt` - Read this first!
- `power_spectra_R1.0.png` - Frequency analysis
- `spatial_correlation_R1.0.png` - Correlation function
- `state_profiles_R1.0.png` - Real-space visualization

### 3. Interpret Results

Open `analysis_report_R1.0.txt` and look for:

```
======================================================================
PHYSICS VALIDATION SUMMARY
======================================================================
✓ Spectral cutoff validates R_c parameter
✓ Correlation length validates R_c parameter
✓ State approximately normalized (⟨|Ψ|²⟩ ~ 1)
```

**All ✓ marks?** Your simulation is working correctly!

---

## 📖 Learning Path

### Beginner (30 minutes)
1. Read **[Quick Reference](ANALYSIS_QUICK_REFERENCE.md)** (5 min)
2. Run the Quick Start above (10 min)
3. Review the generated plots and report (15 min)

### Intermediate (2 hours)
1. Read **[Full Guide](IGSOA_ANALYSIS_GUIDE.md)** sections 1-6 (1 hour)
2. Try **Examples 1-3** from the Guide (1 hour)
3. Experiment with different R_c values

### Advanced (1 day)
1. Complete **[Full Guide](IGSOA_ANALYSIS_GUIDE.md)** (2 hours)
2. Study **[Workflow Diagram](ANALYSIS_WORKFLOW.md)** (30 min)
3. Implement custom analysis (Example 5 from Guide) (3 hours)
4. Run batch parameter scans (2 hours)

---

## 🔍 Common Questions

### Q: What is R_c and why does it matter?

**A:** R_c (causal radius) controls how far information can propagate in the IGSOA network. The analysis validates that:
- Spatial correlation length ξ ≈ R_c
- Power spectrum cuts off at k ~ 1/R_c

This confirms the physics is implemented correctly.

### Q: My state is completely uniform - is that wrong?

**A:** No! A uniform state means your system has **equilibrated** (reached steady state). This is expected for:
- Long simulation times (num_steps >> 100)
- Strong dissipation (large γ)
- Small initial perturbations

To see dynamics, try:
- Shorter runs (num_steps = 50-200)
- Larger initial amplitudes
- Smaller γ parameter

### Q: What if I get "Spectral decay length: NOT MEASURED"?

**A:** This is normal for very uniform states (insufficient high-frequency content). It's not an error. To get measurements:
- Increase num_nodes (more k-space resolution)
- Use more structured initial states
- Use smaller R_c (broader k-space coverage)

### Q: How do I know if my results are trustworthy?

**A:** Check the "PHYSICS VALIDATION SUMMARY" in the report:
- **3 ✓ marks** → Results are excellent
- **2 ✓ marks + 1 ?** → Results are good (one metric unmeasurable)
- **Any ✗ marks** → Investigate the issue before trusting data

---

## 🛠️ Command Quick Reference

```bash
# Standard analysis
python analyze_igsoa_state.py output.json <R_c>

# High-res PDF for papers
python analyze_igsoa_state.py output.json <R_c> --plot-format pdf --dpi 600

# Fast report only (no plots)
python analyze_igsoa_state.py output.json <R_c> --no-plots

# Verbose progress
python analyze_igsoa_state.py output.json <R_c> --verbose

# Custom output directory
python analyze_igsoa_state.py output.json <R_c> --output-dir my_results
```

**Replace `<R_c>`** with the causal radius value used in your simulation (e.g., 1.0, 2.5, 10.0).

---

## 📊 Understanding the Plots

### Power Spectrum
![Power Spectrum Example](https://via.placeholder.com/400x300/4A90E2/FFFFFF?text=Power+Spectrum)

**What to look for:**
- Peak at k=0 (DC component - mean state)
- Decay beyond k ~ 1/R_c (red dashed line)
- Red X marks show dominant frequencies

**Good sign:** Clear cutoff visible near red line
**Warning sign:** No visible structure or cutoff

### Spatial Correlation
![Correlation Example](https://via.placeholder.com/400x300/7CB342/FFFFFF?text=Spatial+Correlation)

**What to look for:**
- Peak at Δx=0 (self-correlation)
- Decay to e⁻¹ ≈ 0.368 (orange line)
- Green line (measured ξ) near red lines (±R_c)

**Good sign:** Green and red lines overlap
**Warning sign:** Green line far from red lines

### State Profiles
![State Profiles Example](https://via.placeholder.com/400x300/E57373/FFFFFF?text=State+Profiles)

**What to look for:**
- Top: |Ψ|² shows quantum probability
- Middle: Phase shows coherence
- Bottom: Φ shows classical field

**Evolution:** Peaked → Spreading → Flat

---

## 🔧 Customization

### Change Plot Settings

Edit `analyze_igsoa_state.py` lines 52-62:

```python
plt.rcParams['font.size'] = 11          # Text size
plt.rcParams['figure.dpi'] = 100        # Screen resolution
plt.rcParams['lines.linewidth'] = 1.5   # Line thickness
```

### Use as Python Library

```python
from analyze_igsoa_state import IGSOAStateAnalyzer

# Load and analyze
analyzer = IGSOAStateAnalyzer('output.json', R_c=1.0, verbose=True)
analyzer.run_full_analysis(output_dir='my_analysis')

# Access results programmatically
print(f"Correlation length: {analyzer.correlation_length}")
print(f"Mean |Ψ|²: {np.mean(analyzer.F):.6f}")
print(f"Φ range: [{np.min(analyzer.phi):.3f}, {np.max(analyzer.phi):.3f}]")

# Get peak frequencies
if analyzer.peaks:
    print(f"Top peak at k = {analyzer.peaks['frequencies'][0]:.4f}")
```

---

## 📁 Example Data

Sample outputs are available in `examples/`:

```
examples/
├── gaussian_spread/
│   ├── output.json              ← Gaussian initial state
│   └── analysis/                ← Pre-run analysis
│
├── uniform_state/
│   ├── output.json              ← Uniform initial state
│   └── analysis/
│
└── localized_pulse/
    ├── output.json              ← Localized initial state
    └── analysis/
```

Try analyzing these:
```bash
python analyze_igsoa_state.py examples/gaussian_spread/output.json 1.0
```

---

## 🐛 Troubleshooting

| Error | Fix |
|-------|-----|
| `No valid get_state response found` | Add `get_state` command to your JSON config |
| `FileNotFoundError` | Check paths are correct, use absolute paths if needed |
| Font warnings | Ignore (plots still work) or set `text.usetex = False` |
| High memory usage | Use `--no-plots` or reduce num_nodes |

For detailed troubleshooting, see **[Full Guide](IGSOA_ANALYSIS_GUIDE.md)** Section 8.

---

## 🎓 Advanced Topics

### Batch Processing
Process multiple simulations automatically - see Guide Section 7.1

### Time Evolution Studies
Track spreading dynamics - see Guide Section 7.2 and Example 3

### R_c Validation Studies
Systematic validation - see Guide Example 2

### Custom Metrics
Implement your own analysis - see Guide Section 7.3 and Example 5

---

## 📞 Getting Help

1. **Check the docs first:**
   - Quick answer? → [Quick Reference](ANALYSIS_QUICK_REFERENCE.md)
   - Detailed info? → [Full Guide](IGSOA_ANALYSIS_GUIDE.md)
   - Understanding workflow? → [Workflow Diagram](ANALYSIS_WORKFLOW.md)

2. **Common issues:**
   - See Troubleshooting section above
   - Check Guide Section 8

3. **Still stuck?**
   - Check example data matches your format
   - Run with `--verbose` flag for detailed output
   - Open an issue on GitHub with error message

---

## 📜 License & Citation

If you use this analysis tool in published work, please cite:

```
IGSOA State Analysis Tool
Part of the IGSOA Simulation Suite
https://github.com/your-repo/igsoa-sim
```

---

## 🗺️ What's Next?

After mastering the analysis:

1. **Explore different initial states**
   - Gaussian, uniform, localized
   - Vary amplitude and width parameters

2. **Parameter scans**
   - Systematic R_c studies
   - Time evolution tracking
   - Coupling strength effects

3. **Custom analysis**
   - Implement new metrics
   - Compare with analytical theory
   - Develop new visualization techniques

4. **Share your findings!**
   - Publication-quality plots ready
   - Automated report generation
   - Reproducible analysis pipeline

---

**Happy analyzing!** 🎉

Start with the **[Quick Reference](ANALYSIS_QUICK_REFERENCE.md)** for immediate use, or dive into the **[Full Guide](IGSOA_ANALYSIS_GUIDE.md)** for comprehensive documentation.
