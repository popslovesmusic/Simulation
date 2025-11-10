# **SATP v2 (BLEND\_MODE) Reproducibility Standard — 1-page**

**Objective.** Reproduce drift-free SATP translation in 1D IGSOA with quantified exotic cost, using conformal field shaping in **BLEND\_MODE** with a **time-varying blend\_weight u(τ)**.

**Engine.** `igsoa_complex`, ring lattice, `N=4096`, causal radius `R_c=1.0`.

**Field.** Scale field Φ (phi). Initial seed: baseline 0 plus one Gaussian bubble.

**Control law.** Each translation cycle:

* Translate by \+100 sites via **difference-of-Gaussians (DoG)**:

  * add \+A at new center; add −A at previous center (A \= 100, width \= 256).

* Immediately **blend** toward the new target profile with weight `blend_weight = u(τ)` (0\<u≤1).

* Run engine for 50 steps @ 30 iterations per node (adiabatic settle).

**u(τ) spec.** Use a *parametric* schedule (“linear” from 0.30 → 0.60 across the 10 cycles). Labs may choose a different monotone ramp but must report it.

**Success criteria.**

* Translation: total measured shift \= **900 ± 1 site**; drift (measured−ideal) **≤ 0.5 site**.

* Causality/stability: no blow-ups; bubble walls remain localized.

* Exotic cost: integrated ∑|∇Φ|² reported; expect **O(10⁻³)** for this setup (blend will typically be ≥ additive case). Exact value is dataset-specific; labs must publish the number and the profile plot.

**Outputs.** Save logs/plots to `analysis/`, then archive with:

`python tools/archive_run.py satp_translation_run_v2_blend`

