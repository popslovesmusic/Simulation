# **Appendix A: Critical Operational Findings**

This appendix details the mandatory requirements for command input and engine management identified during testing, which are crucial for stable CLI operation and state persistence.

## **1\. JSON Input Format Mandate**

While individual JSON objects must be single-line (not pretty-printed), multiple commands must be separated by a specific delimiter when piped to the executable.

| Requirement | Description | Consequence of Failure |
| :---- | :---- | :---- |
| **A. Single-Line Objects** | Each command must be a valid JSON object compressed onto a single, continuous line. | JSON parse error |
| **B. Newline Delimitation** | When streaming multiple commands (e.g., using type or cat), each JSON object **must** be followed by a newline character (\\n) to signal the end of the command to the parser. | JSON parse error (The parser reads the second { as an unexpected token.) |

**Correct Input Example (Commands separated by newlines):**

{"command":"create\_engine","params":{"engine\_type":"phase4b","num\_nodes":1024}}  
{"command":"run\_mission","params":{"engine\_id":"engine\_001","num\_steps":10}}  
{"command":"destroy\_engine","params":{"engine\_id":"engine\_001"}}

## **2\. Engine State and Session Persistence**

The DASE CLI architecture maintains engine state within the scope of a single operating system process (a single invocation of dase\_cli.exe).

### **A. The Single-Session Mandate**

To run any workflow that involves state (e.g., create followed by run, or run followed by get\_metrics), all commands **must** be fed to a single CLI process instance using the stream-piping method.

| Scenario | Command Method | Result |
| :---- | :---- | :---- |
| **GOOD (Piped)** | \`type commands.json | dase\_cli.exe\` |
| **BAD (Sequential)** | \`echo {create...} | dase\_cli.exefollowed byecho {run...} |

### **B. Engine ID Management**

The CLI utilizes an internal EngineManager to assign sequential IDs (engine\_001, engine\_002, etc.) to prevent conflicts.

1. **ID Assignment is Automatic:** The ID used in the command stream (engine\_id in run\_mission, get\_metrics, etc.) **must** match the ID that was **returned** by the preceding create\_engine command in that session.  
2. **ID Reset:** The sequence is reset (starting back at engine\_001) with every new invocation of dase\_cli.exe.

\* Always inspect the \`create\_engine\` output for the correct \`engine\_id\` to use in subsequent commands.  
