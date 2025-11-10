SATP\_v2 (BLEND\_MODE) — Canonical Mission (NDJSON)

Notes:  
• This is exactly what you pipe to the CLI (one JSON per line).  
• The “header” block with the function is for humans; engine ignores it. We still include it at top for provenance.  
• The actual blend is effected by per-cycle mode:"blend" with concrete blend\_weight values sampled from the function.

Save as missions/SATP\_v2\_blend.ndjson:

{"\_note":"SATP v2 canonical (BLEND\_MODE). Function for u(τ) below is documentation only; concrete weights are baked per-cycle.","blend\_weight\_function":{"type":"linear","start":0.30,"end":0.60,"cycles":10}}  
{"command":"create\_engine","params":{"engine\_type":"igsoa\_complex","num\_nodes":4096,"R\_c":1.0}}

{"command":"set\_igsoa\_state","params":{"engine\_id":"engine\_001","profile\_type":"gaussian","mode":"overwrite","params":{"amplitude":100.0,"center\_node":2048,"width":256,"baseline\_phi":0.0}}}  
{"command":"run\_mission","params":{"engine\_id":"engine\_001","num\_steps":50,"iterations\_per\_node":30}}  
{"command":"get\_state","params":{"engine\_id":"engine\_001","output\_file":"analysis/satp\_translation\_results/cycle1.json"}}

{"command":"set\_igsoa\_state","params":{"engine\_id":"engine\_001","profile\_type":"gaussian","mode":"add","params":{"amplitude":+100.0,"center\_node":2148,"width":256}}}  
{"command":"set\_igsoa\_state","params":{"engine\_id":"engine\_001","profile\_type":"gaussian","mode":"add","params":{"amplitude":-100.0,"center\_node":2048,"width":256}}}  
{"command":"set\_igsoa\_state","params":{"engine\_id":"engine\_001","profile\_type":"gaussian","mode":"blend","params":{"amplitude":100.0,"center\_node":2148,"width":256,"baseline\_phi":0.0,"blend\_weight":0.330}}}  
{"command":"run\_mission","params":{"engine\_id":"engine\_001","num\_steps":50,"iterations\_per\_node":30}}  
{"command":"get\_state","params":{"engine\_id":"engine\_001","output\_file":"analysis/satp\_translation\_results/cycle2.json"}}

{"command":"set\_igsoa\_state","params":{"engine\_id":"engine\_001","profile\_type":"gaussian","mode":"add","params":{"amplitude":+100.0,"center\_node":2248,"width":256}}}  
{"command":"set\_igsoa\_state","params":{"engine\_id":"engine\_001","profile\_type":"gaussian","mode":"add","params":{"amplitude":-100.0,"center\_node":2148,"width":256}}}  
{"command":"set\_igsoa\_state","params":{"engine\_id":"engine\_001","profile\_type":"gaussian","mode":"blend","params":{"amplitude":100.0,"center\_node":2248,"width":256,"baseline\_phi":0.0,"blend\_weight":0.360}}}  
{"command":"run\_mission","params":{"engine\_id":"engine\_001","num\_steps":50,"iterations\_per\_node":30}}  
{"command":"get\_state","params":{"engine\_id":"engine\_001","output\_file":"analysis/satp\_translation\_results/cycle3.json"}}

{"command":"set\_igsoa\_state","params":{"engine\_id":"engine\_001","profile\_type":"gaussian","mode":"add","params":{"amplitude":+100.0,"center\_node":2348,"width":256}}}  
{"command":"set\_igsoa\_state","params":{"engine\_id":"engine\_001","profile\_type":"gaussian","mode":"add","params":{"amplitude":-100.0,"center\_node":2248,"width":256}}}  
{"command":"set\_igsoa\_state","params":{"engine\_id":"engine\_001","profile\_type":"gaussian","mode":"blend","params":{"amplitude":100.0,"center\_node":2348,"width":256,"baseline\_phi":0.0,"blend\_weight":0.390}}}  
{"command":"run\_mission","params":{"engine\_id":"engine\_001","num\_steps":50,"iterations\_per\_node":30}}  
{"command":"get\_state","params":{"engine\_id":"engine\_001","output\_file":"analysis/satp\_translation\_results/cycle4.json"}}

{"command":"set\_igsoa\_state","params":{"engine\_id":"engine\_001","profile\_type":"gaussian","mode":"add","params":{"amplitude":+100.0,"center\_node":2448,"width":256}}}  
{"command":"set\_igsoa\_state","params":{"engine\_id":"engine\_001","profile\_type":"gaussian","mode":"add","params":{"amplitude":-100.0,"center\_node":2348,"width":256}}}  
{"command":"set\_igsoa\_state","params":{"engine\_id":"engine\_001","profile\_type":"gaussian","mode":"blend","params":{"amplitude":100.0,"center\_node":2448,"width":256,"baseline\_phi":0.0,"blend\_weight":0.420}}}  
{"command":"run\_mission","params":{"engine\_id":"engine\_001","num\_steps":50,"iterations\_per\_node":30}}  
{"command":"get\_state","params":{"engine\_id":"engine\_001","output\_file":"analysis/satp\_translation\_results/cycle5.json"}}

{"command":"set\_igsoa\_state","params":{"engine\_id":"engine\_001","profile\_type":"gaussian","mode":"add","params":{"amplitude":+100.0,"center\_node":2548,"width":256}}}  
{"command":"set\_igsoa\_state","params":{"engine\_id":"engine\_001","profile\_type":"gaussian","mode":"add","params":{"amplitude":-100.0,"center\_node":2448,"width":256}}}  
{"command":"set\_igsoa\_state","params":{"engine\_id":"engine\_001","profile\_type":"gaussian","mode":"blend","params":{"amplitude":100.0,"center\_node":2548,"width":256,"baseline\_phi":0.0,"blend\_weight":0.450}}}  
{"command":"run\_mission","params":{"engine\_id":"engine\_001","num\_steps":50,"iterations\_per\_node":30}}  
{"command":"get\_state","params":{"engine\_id":"engine\_001","output\_file":"analysis/satp\_translation\_results/cycle6.json"}}

{"command":"set\_igsoa\_state","params":{"engine\_id":"engine\_001","profile\_type":"gaussian","mode":"add","params":{"amplitude":+100.0,"center\_node":2648,"width":256}}}  
{"command":"set\_igsoa\_state","params":{"engine\_id":"engine\_001","profile\_type":"gaussian","mode":"add","params":{"amplitude":-100.0,"center\_node":2548,"width":256}}}  
{"command":"set\_igsoa\_state","params":{"engine\_id":"engine\_001","profile\_type":"gaussian","mode":"blend","params":{"amplitude":100.0,"center\_node":2648,"width":256,"baseline\_phi":0.0,"blend\_weight":0.480}}}  
{"command":"run\_mission","params":{"engine\_id":"engine\_001","num\_steps":50,"iterations\_per\_node":30}}  
{"command":"get\_state","params":{"engine\_id":"engine\_001","output\_file":"analysis/satp\_translation\_results/cycle7.json"}}

{"command":"set\_igsoa\_state","params":{"engine\_id":"engine\_001","profile\_type":"gaussian","mode":"add","params":{"amplitude":+100.0,"center\_node":2748,"width":256}}}  
{"command":"set\_igsoa\_state","params":{"engine\_id":"engine\_001","profile\_type":"gaussian","mode":"add","params":{"amplitude":-100.0,"center\_node":2648,"width":256}}}  
{"command":"set\_igsoa\_state","params":{"engine\_id":"engine\_001","profile\_type":"gaussian","mode":"blend","params":{"amplitude":100.0,"center\_node":2748,"width":256,"baseline\_phi":0.0,"blend\_weight":0.510}}}  
{"command":"run\_mission","params":{"engine\_id":"engine\_001","num\_steps":50,"iterations\_per\_node":30}}  
{"command":"get\_state","params":{"engine\_id":"engine\_001","output\_file":"analysis/satp\_translation\_results/cycle8.json"}}

{"command":"set\_igsoa\_state","params":{"engine\_id":"engine\_001","profile\_type":"gaussian","mode":"add","params":{"amplitude":+100.0,"center\_node":2848,"width":256}}}  
{"command":"set\_igsoa\_state","params":{"engine\_id":"engine\_001","profile\_type":"gaussian","mode":"add","params":{"amplitude":-100.0,"center\_node":2748,"width":256}}}  
{"command":"set\_igsoa\_state","params":{"engine\_id":"engine\_001","profile\_type":"gaussian","mode":"blend","params":{"amplitude":100.0,"center\_node":2848,"width":256,"baseline\_phi":0.0,"blend\_weight":0.540}}}  
{"command":"run\_mission","params":{"engine\_id":"engine\_001","num\_steps":50,"iterations\_per\_node":30}}  
{"command":"get\_state","params":{"engine\_id":"engine\_001","output\_file":"analysis/satp\_translation\_results/cycle9.json"}}

{"command":"set\_igsoa\_state","params":{"engine\_id":"engine\_001","profile\_type":"gaussian","mode":"add","params":{"amplitude":+100.0,"center\_node":2948,"width":256}}}  
{"command":"set\_igsoa\_state","params":{"engine\_id":"engine\_001","profile\_type":"gaussian","mode":"add","params":{"amplitude":-100.0,"center\_node":2848,"width":256}}}  
{"command":"set\_igsoa\_state","params":{"engine\_id":"engine\_001","profile\_type":"gaussian","mode":"blend","params":{"amplitude":100.0,"center\_node":2948,"width":256,"baseline\_phi":0.0,"blend\_weight":0.570}}}  
{"command":"run\_mission","params":{"engine\_id":"engine\_001","num\_steps":50,"iterations\_per\_node":30}}  
{"command":"get\_state","params":{"engine\_id":"engine\_001","output\_file":"analysis/satp\_translation\_results/cycle10.json"}}

{"command":"destroy\_engine","params":{"engine\_id":"engine\_001"}}

(Weights 0.33…0.57 implement a linear ramp 0.30→0.60; you can tweak granularly if you prefer exact tenth-step values like 0.30, 0.33, …, 0.60.)