## **SATP v2 – BLEND\_MODE Operational Usage Notes**

### **1\) Mission File Location**

All SATP mission NDJSON files now live in:

`/missions/`

### **2\) Execution Syntax (unchanged)**

Run NDJSON via pipe:

`type missions/SATP_v2_blend.ndjson | igsoa-sim/dase_cli/dase_cli.exe > analysis/raw_translation_log_v2_blend.txt`

### **3\) Field Shaping Mode Change**

SATP v2 uses **BLEND\_MODE** as the canonical shaping mode.

This means every translation cycle uses 3 set\_igsoa\_state writes:

`1) gaussian add (+A new center)`  
`2) gaussian add (-A previous center)`  
`3) gaussian blend (center=new, blend_weight = u(τ))`

### **4\) blend\_weight**

`blend_weight` is now required when `mode:"blend"` is used.  
 SATP v2 uses a **dynamic schedule** (parametric) — not fixed constant.

### **5\) Results Location**

All runtime outputs, logs, and plots go to:

`/analysis/`

### **6\) Permanent Run Freezing / Archival**

After verification → freeze runs like so:

`python tools/archive_run.py <run_tag>`

This creates timestamped archive folders under:

`/archive/`

This prevents overwrites \+ enables reproducibility indexing.

