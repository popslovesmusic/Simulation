### **tools/generate\_blend\_schedule.py**

### 

### **Usage:**

Example schedule file:

`missions/SATP_v2_schedule.json`

`{`  
  `"blend_weight_function": {`  
    `"type": "linear",`  
    `"start": 0.30,`  
    `"end": 0.60,`  
    `"cycles": 10`  
  `}`  
`}`

run:

`python tools/generate_blend_schedule.py missions/SATP_v2_schedule.json`

output → exact `blend_weight` numbers printed, copy/paste into NDJSON cycles.

### **Why this matters engineering-wise**

This makes SATP v2 *parametrically reproducible* without hand tuning and prevents drift between labs / future runs / agents modifying values individually.

This becomes also the entry point to:

* auto-schedule optimizer (SATP v3)

* energy-cost minimization solver

* IGSOA RC-space parameter sweeps

