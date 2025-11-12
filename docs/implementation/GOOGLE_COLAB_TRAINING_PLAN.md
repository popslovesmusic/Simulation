# Google Colab Surrogate Training Plan

**Date:** 2025-11-11
**Status:** 📋 **PLANNED** (Implementation deferred)
**Priority:** P2 (After Phase 1 validation)

---

## Problem Statement

**Hardware Limitation:** Local system has Tesla K80 GPU (CUDA compute capability 3.7) which is **not supported** by PyTorch 2.9.0+. Only CPU-only PyTorch is currently installed, resulting in:

- **10-100x slower training** compared to GPU
- Training 25 epochs on 10K samples: ~30-60 minutes (CPU) vs ~3-5 minutes (GPU)
- Inference latency: ~10-50ms (CPU) vs ~1-5ms (GPU)

**Solution:** Use Google Colab's free GPU resources for surrogate model training.

---

## Colab Advantages

✅ **Free Tesla T4 GPU** (15GB VRAM, compute capability 7.5)
✅ **12-hour runtime** (sufficient for most training tasks)
✅ **No local setup** required (browser-based)
✅ **Google Drive integration** (persistent model storage)
✅ **Jupyter notebook** familiar interface
✅ **Pre-installed PyTorch** with CUDA support

---

## Workflow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LOCAL MACHINE                            │
│  1. Run simulations via Command Center                     │
│  2. Generate waveform datasets (CSV)                        │
│  3. Export to Colab-friendly format (ZIP)                   │
└────────────────────┬────────────────────────────────────────┘
                     │ Upload dataset.zip
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                   GOOGLE COLAB (T4 GPU)                     │
│  4. Mount Google Drive                                      │
│  5. Upload dataset or clone repo                            │
│  6. Train FeedForwardSurrogate on GPU                       │
│  7. Save trained model to Drive (.pt file)                  │
└────────────────────┬────────────────────────────────────────┘
                     │ Download model.pt
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                    LOCAL MACHINE                            │
│  8. Load trained model into SurrogateAdapter                │
│  9. Register for production missions                        │
│ 10. Enjoy 10-100x inference speedup!                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Tasks

### Task 1: Create Colab Notebook Template
**File:** `notebooks/colab_surrogate_training.ipynb`

**Cells:**
1. **Setup** - Mount Drive, install dependencies
2. **GPU Check** - Verify T4/V100 available
3. **Load Dataset** - Upload or clone from repo
4. **Train Model** - FeedForwardSurrogate training loop
5. **Visualize** - Plot loss curves
6. **Save Model** - Persist to Drive
7. **Download** - Export for local use

**Estimated Time:** 1 hour

---

### Task 2: Dataset Export Utility
**File:** `tools/export_for_colab.py`

**Purpose:** Package mission results into Colab-friendly format

**Features:**
- Extract waveform CSVs from results directory
- Create manifest.json with metadata
- ZIP archive for easy upload
- Validate dataset integrity

**Usage:**
```bash
python tools/export_for_colab.py results/mission_001 colab_dataset.zip
```

**Estimated Time:** 30 minutes

---

### Task 3: Training Configuration Template
**File:** `configs/surrogate_training_config.json`

**Contents:**
```json
{
  "input_dim": 128,
  "output_dim": 64,
  "hidden_layers": [512, 512],
  "learning_rate": 1e-3,
  "batch_size": 256,
  "epochs": 100,
  "device": "cuda",
  "seed": 42
}
```

**Estimated Time:** 15 minutes

---

### Task 4: Documentation
**File:** `docs/guides/SURROGATE_TRAINING_GUIDE.md`

**Topics:**
- Setting up Google Colab account
- Uploading datasets
- Running training notebook
- Downloading trained models
- Registering models in production
- Troubleshooting common issues

**Estimated Time:** 45 minutes

---

## Colab Notebook Structure (Detailed)

### Cell 1: Environment Setup
```python
# Mount Google Drive for persistent storage
from google.colab import drive
drive.mount('/content/drive')

# Clone repo or upload files
!git clone https://github.com/yourusername/igsoa-sim.git
%cd igsoa-sim

# Install dependencies
!pip install numpy torch matplotlib
```

### Cell 2: GPU Verification
```python
import torch
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")

# Expected output: "Tesla T4" or "Tesla V100"
assert torch.cuda.is_available(), "⚠️ GPU not available! Check Runtime > Change runtime type > Hardware accelerator > GPU"
```

### Cell 3: Load Dataset
```python
from pathlib import Path
import json
import numpy as np

# Option 1: From uploaded ZIP
!unzip /content/drive/MyDrive/igsoa_datasets/colab_dataset.zip -d datasets/

# Option 2: From repo
dataset_path = Path("analysis/datasets/example_waveforms")
manifest = json.loads((dataset_path / "manifest.json").read_text())
print(f"Loaded {manifest['sample_count']} samples")

# Load features and targets (implement based on your dataset format)
features = torch.randn(1000, 128)  # TODO: Load real data
targets = torch.randn(1000, 64)    # TODO: Load real data
```

### Cell 4: Initialize Model
```python
import sys
sys.path.append('.')

from igsoa_analysis.surrogates.pytorch_surrogate import FeedForwardSurrogate

config = {
    "input_dim": 128,
    "output_dim": 64,
    "hidden_layers": [512, 512],  # Larger network on T4
    "learning_rate": 1e-3,
    "batch_size": 256,  # T4 has 16GB - can go large
    "epochs": 100,
    "device": "cuda",  # ← GPU acceleration
    "seed": 42
}

torch.manual_seed(config["seed"])
np.random.seed(config["seed"])

surrogate = FeedForwardSurrogate.from_config(config)
print(surrogate)
```

### Cell 5: Train Model
```python
import time
start_time = time.time()

loss_history = surrogate.train_on_arrays(features, targets)

elapsed = time.time() - start_time
print(f"\n✓ Training complete in {elapsed/60:.1f} minutes")
print(f"Final loss: {loss_history[-1]:.6f}")
```

### Cell 6: Visualize Results
```python
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 5))
plt.plot(loss_history)
plt.xlabel("Epoch")
plt.ylabel("Loss (MSE)")
plt.title("Surrogate Training Loss")
plt.grid(True, alpha=0.3)
plt.show()

# Evaluate on test set
with torch.no_grad():
    predictions = surrogate(features[:16])
    mse = torch.mean((predictions - targets[:16]) ** 2).item()
    print(f"Test MSE: {mse:.6f}")
```

### Cell 7: Save Model
```python
# Save to Google Drive (persists after session ends)
model_path = "/content/drive/MyDrive/igsoa_models/waveform_surrogate_v1.pt"
Path(model_path).parent.mkdir(parents=True, exist_ok=True)
surrogate.save(model_path)

print(f"✓ Model saved to: {model_path}")
print(f"File size: {Path(model_path).stat().st_size / 1024 / 1024:.1f} MB")
```

### Cell 8: Download for Local Use
```python
from google.colab import files

# Option 1: Direct download
files.download(model_path)

# Option 2: Already saved to Drive - access from local machine
print(f"✓ Model available in Google Drive: {model_path}")
print("Access from local machine via Google Drive sync")
```

---

## K80 OpenCL Investigation Results

**Attempted Solutions:**
1. ❌ **CUDA PyTorch** - K80 (compute 3.7) not supported by PyTorch 2.5+
2. ❌ **PlaidML** - Deprecated, unmaintained since 2020
3. ❌ **ONNX Runtime OpenCL** - Limited op support, immature
4. ❌ **ArrayFire** - C++ only, no Python surrogate integration

**Conclusion:** PyTorch dropped OpenCL support in 2018. Google Colab is the most practical solution.

---

## Local CPU-Only Fallback

If Colab is unavailable, the current CPU-only setup works:

```python
config = {
    "device": "cpu",  # ← Already configured
    "batch_size": 32,  # Smaller batch for CPU
    "epochs": 25,  # Reduce epochs
}
```

**Expected Performance:**
- Training: 30-60 minutes for 10K samples
- Inference: 10-50ms per prediction
- Still functional, just slower

---

## Production Deployment (Post-Training)

Once trained on Colab:

```python
# backend/engine/runtime.py or mission startup
from backend.engine import SurrogateAdapter
from igsoa_analysis.surrogates.pytorch_surrogate import FeedForwardSurrogate

# Load trained model
surrogate = FeedForwardSurrogate.load("models/waveform_surrogate_v1.pt")

# Register with adapter
adapter = SurrogateAdapter()
adapter.register("run_mission", surrogate)

# Use in runtime
runtime = MissionRuntime(surrogate_adapter=adapter)
runtime.execute(mission_commands)  # Automatically uses surrogate if available
```

---

## Cost Analysis

| Option | GPU | Cost | Training Time | Setup Time |
|--------|-----|------|---------------|------------|
| **Colab Free** | T4 | $0 | ~5 min | 10 min |
| Colab Pro | V100 | $10/mo | ~3 min | 5 min |
| AWS p2.xlarge | K80 | $0.90/hr | Not supported | N/A |
| AWS p3.2xlarge | V100 | $3.06/hr | ~3 min | 30 min |
| **Local CPU** | None | $0 | ~45 min | 0 min |

**Recommendation:** Start with Colab Free tier (T4 GPU).

---

## Next Steps (When Ready)

1. ✅ **Generate Dataset** - Run missions, collect waveforms
2. ✅ **Create Export Script** - Package dataset for Colab
3. ✅ **Create Colab Notebook** - Training pipeline template
4. ✅ **Train First Model** - Validate workflow end-to-end
5. ✅ **Test Locally** - Load `.pt` file, benchmark inference
6. ✅ **Production Deploy** - Register in SurrogateAdapter

---

## References

- **Code Review:** `docs/reviews/2025-03-bridge-backend-code-review.md`
- **Surrogate Infrastructure:** `backend/engine/surrogate_adapter.py`
- **PyTorch Model:** `igsoa_analysis/surrogates/pytorch_surrogate.py`
- **Phase 4 Review:** `docs/reviews/phase4_surrogate_performance_review.md`
- **Roadmap:** `docs/IGSOA_PROJECT_ROADMAP.md` (Phase 2)

---

**Status:** Ready to implement when Phase 1 validation data is available
**Priority:** P2 (Acceleration phase follows validation phase)
**Estimated Total Time:** 2.5 hours (all tasks)

---

*Created: 2025-11-11*
*Implementation: Deferred per user request*
