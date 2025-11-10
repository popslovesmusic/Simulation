# **SATP v2 Validation Protocol (external labs)**

**Prereqs.**

* DASE CLI available; run missions by piping NDJSON.

* Analysis scripts available: `analyze_translation_log.py`, `analyze_exotic_cost.py`.

**Run.**

`cd <repo-root>`  
`type missions/SATP_v2_blend.ndjson | igsoa-sim/dase_cli/dase_cli.exe > analysis/raw_translation_log_v2_blend.txt`

**Verify translation.**

`cd igsoa-sim/dase_cli`  
`python analyze_translation_log.py ../../analysis/raw_translation_log_v2_blend.txt`

Expected:

* Total shift 900 sites.

* Drift ≤ 0.5 site.

* Plot saved to `analysis/satp_translation_track.png`.

**Verify exotic cost.**

`python analyze_exotic_cost.py ../../analysis/raw_translation_log_v2_blend.txt`

Expected:

* Integrated exotic cost on the order of **10⁻³** (exact value depends on platform).

* Localized wall peaks in `analysis/satp_exotic_cost_profile.png`.

**Archive the run.**

`cd ../..`  
`python tools/archive_run.py satp_translation_run_v2_blend`

**Report.** Publish:

* NDJSON you used (verbatim),

* drift numbers,

* exotic cost number,

* the two plots.

