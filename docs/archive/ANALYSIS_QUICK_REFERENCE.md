# IGSOA Analysis Quick Reference

**One-page cheat sheet for common analysis tasks**

---

## 🚀 Quick Start (3 Steps)

```bash
# 1. Run simulation with state extraction
cat my_config.json | ./dase_cli.exe > output.json

# 2. Analyze (replace 1.0 with your R_c value)
python analyze_igsoa_state.py output.json 1.0

# 3. Check results
cd igsoa_analysis/
ls  # See analysis_report_R1.0.txt and plots
```

---

## 📋 Common Commands

```bash
# Basic analysis
python analyze_igsoa_state.py data.json 2.0

# High-resolution PDF
python analyze_igsoa_state.py data.json 2.0 --plot-format pdf --dpi 600

# Verbose output
python analyze_igsoa_state.py data.json 1.0 --verbose

# Custom directory
python analyze_igsoa_state.py data.json 1.0 --output-dir my_results

# Report only (fast)
python analyze_igsoa_state.py data.json 1.0 --no-plots

# With timestamp
python analyze_igsoa_state.py data.json 1.0 --timestamp
```

---

## 📁 Required JSON Format

Your simulation **must** include `get_state` command:

```json
{"command":"create_engine","params":{"engine_type":"igsoa_complex","num_nodes":4096}}
{"command":"set_igsoa_state","params":{"engine_id":"engine_001","profile_type":"gaussian","params":{"amplitude":1.5,"center_node":2048,"width":256,"baseline_phi":0.0}}}
{"command":"run_mission","params":{"engine_id":"engine_001","num_steps":500,"iterations_per_node":30}}
{"command":"get_state","params":{"engine_id":"engine_001"}}
{"command":"destroy_engine","params":{"engine_id":"engine_001"}}
```

**Critical line:** `{"command":"get_state","params":{"engine_id":"engine_001"}}`

---

## 📊 Output Files

| File | Description |
|------|-------------|
| `analysis_report_R*.txt` | Full statistical report |
| `power_spectra_R*.png` | FFT frequency analysis |
| `spatial_correlation_R*.png` | Correlation function plot |
| `state_profiles_R*.png` | Real-space Ψ and Φ profiles |

---

## 🔍 Reading the Report

### Key Metrics

```
|Ψ|² mean: 1.000000           ← Should be ~1 if normalized
Φ mean: -60.840009            ← Average field value
Correlation length (ξ): 12    ← Info spreading distance
Ratio ξ/R_c: 1.200            ← Should be ~1.0 (validation)
```

### Validation Checks

```
✓ = Passed  ✗ = Failed  ? = Not measured

✓ Spectral cutoff validates R_c parameter
✓ Correlation length validates R_c parameter
✓ State approximately normalized (⟨|Ψ|²⟩ ~ 1)
```

---

## 🎨 Plot Interpretation

### Power Spectrum (Top)
- **X-axis:** Spatial frequency k
- **Y-axis:** Power (log scale)
- **Red line:** Expected cutoff at k = 1/R_c
- **Red X:** Dominant frequencies

✅ **Good:** Power drops off beyond k ~ 1/R_c
❌ **Bad:** No visible cutoff (R_c not working)

### Spatial Correlation
- **X-axis:** Distance Δx
- **Y-axis:** Correlation strength
- **Orange line:** e⁻¹ decay threshold
- **Green line:** Measured correlation length ξ

✅ **Good:** ξ ≈ R_c (green line near red lines)
❌ **Bad:** ξ >> R_c or ξ << R_c

### State Profiles
- **Top:** |Ψ|² (quantum probability density)
- **Middle:** arg(Ψ) (phase)
- **Bottom:** Φ (classical field)

**Evolution:** Peaked → Spreading → Flat (equilibrium)

---

## 🧪 Common Use Cases

### 1. Validate R_c Implementation

```bash
python analyze_igsoa_state.py output.json <R_c_value>

# Check report for:
# Ratio ξ/R_c: ~1.0 ✓
# Ratio k₀/(1/R_c): ~1.0 ✓
```

### 2. Track Wave Packet Spreading

```bash
# Run simulations at t = 100, 200, 500, 1000
for t in 100 200 500 1000; do
    # ... run simulation with num_steps=$t ...
    python analyze_igsoa_state.py output_t${t}.json 1.0 \
        --output-dir analysis_t${t}
done

# Compare state_profiles_R1.0.png across directories
```

### 3. Compare Different Initial States

```bash
# Gaussian
python analyze_igsoa_state.py gaussian_output.json 1.0 --output-dir gaussian

# Uniform
python analyze_igsoa_state.py uniform_output.json 1.0 --output-dir uniform

# Localized
python analyze_igsoa_state.py localized_output.json 1.0 --output-dir localized

# Compare reports
diff gaussian/analysis_report_R1.0.txt uniform/analysis_report_R1.0.txt
```

---

## ⚠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| "No valid get_state response" | Add `get_state` command to JSON |
| "Spectral decay: NOT MEASURED" | Normal for uniform states; increase N if needed |
| "No significant peaks found" | Normal for equilibrated systems |
| Font warnings | Ignore or set `text.usetex = False` in script |
| High memory usage | Use `--no-plots` flag |

---

## 🔧 Customization

### Change Plot Style

Edit `analyze_igsoa_state.py` lines 52-62:

```python
plt.rcParams['font.size'] = 14           # Larger text
plt.rcParams['figure.dpi'] = 100         # Screen viewing
plt.rcParams['lines.linewidth'] = 2.5    # Thicker lines
```

### Extract Data Programmatically

```python
from analyze_igsoa_state import IGSOAStateAnalyzer

analyzer = IGSOAStateAnalyzer('output.json', R_c=1.0)
analyzer.run_full_analysis()

# Access results
print(f"Correlation length: {analyzer.correlation_length}")
print(f"Mean |Ψ|²: {analyzer.F.mean()}")
print(f"Peak frequencies: {analyzer.peaks['frequencies']}")
```

---

## 📖 Full Documentation

See `docs/IGSOA_ANALYSIS_GUIDE.md` for:
- Detailed mathematical background
- Advanced batch processing
- Custom analysis examples
- Complete API reference

---

## 💡 Tips

1. **Always use the same R_c** in simulation config and analysis command
2. **Higher dpi = larger files** (300 is good, 600 for publications)
3. **Use `--timestamp`** when running many analyses to avoid overwriting
4. **Check validation summary** in report before trusting results
5. **Uniform final states** mean system reached equilibrium (not an error!)

---

**Need help?** Check `docs/IGSOA_ANALYSIS_GUIDE.md` or open an issue on GitHub.
