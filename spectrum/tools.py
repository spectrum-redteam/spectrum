import os
import json
import subprocess
import requests
import urllib3
import shlex
import sqlite3
from pathlib import Path

# Disable insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "kb.sqlite3"
global_session = requests.Session()

def truncate(text, limit=8000):
    if len(text) > limit:
        return text[:limit] + "\n\n[SYSTEM NOTICE: OUTPUT TRUNCATED]"
    return text

def search_kb(keyword):
    if not DB_PATH.exists():
        return "Error: kb.sqlite3 missing. Run bake_kb_to_sqlite.py first."
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        query = f"%{keyword}%"
        c.execute("SELECT path, content FROM kb_files WHERE content LIKE ? OR path LIKE ? LIMIT 3", (query, query))
        rows = c.fetchall()
        conn.close()
        if not rows:
            return f"Knowledge Base: No matching entries found for '{keyword}'."
        res = ""
        for path, content in rows:
            res += f"--- Source: {path} ---\n{content[:2000]}\n\n"
        return truncate(res)
    except Exception as e:
        return f"KB Error: {str(e)}"

def execute_terminal(cmd, timeout=30):
    """Raw shell execution gateway with PID Self-Preservation and timeout."""
    try:
        if not cmd: return "Error: No command provided."
        
        # Self-Kill Protection
        my_pid = str(os.getpid())
        cmd_tokens = cmd.replace(";", " ").replace("&&", " ").replace("|", " ").split()
        if "kill" in cmd_tokens and my_pid in cmd_tokens:
            return f"SYSTEM OVERRIDE: Refusing to execute command. {my_pid} is the AI Agent's own Process ID. You must find the target application's PID."

        process = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout, cwd=str(BASE_DIR))
        out = ""
        if process.stdout: out += f"[STDOUT]\n{process.stdout}\n"
        if process.stderr: out += f"[STDERR]\n{process.stderr}\n"
        return truncate(out if out else "Executed (No Output).")
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds (no output was received)."
    except Exception as e:
        return f"Execution Fault: {str(e)}"

def http_request(method, url, headers=None, body=""):
    """Advanced Browser Mimicry Engine for macOS Chrome emulation."""
    try:
        req_headers = headers if headers else {}
        default_headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"macOS"',
            "Upgrade-Insecure-Requests": "1"
        }
        for k, v in default_headers.items():
            if k not in req_headers:
                req_headers[k] = v

        resp = global_session.request(
            method=method.upper(), url=url, headers=req_headers, data=body, timeout=20, verify=False, allow_redirects=True
        )
        out =[f"Status: {resp.status_code}", f"Headers: {dict(resp.headers)}", f"Cookies: {dict(global_session.cookies)}", f"Body:\n{resp.text}"]
        return truncate("\n".join(out))
    except Exception as e: return f"HTTP Error: {str(e)}"

def apply_patch(vulnerability, file_path="lab.py"):
    """Apply a pre-defined security patch to the target file."""
    full_path = BASE_DIR / file_path
    if not full_path.exists():
        return f"Error: {file_path} not found."
    
    code = full_path.read_text(encoding='utf-8', errors='ignore')
    patched = False
    
    vuln = vulnerability.lower()
    
    if vuln in ["sqli", "sql injection", "sql_injection"]:
        # Fix /login endpoint
        old_login = 'query = f"SELECT * FROM users WHERE username=\'{username}\' AND password=\'{password}\'"'
        new_login = 'query = "SELECT * FROM users WHERE username=? AND password=?"'
        if old_login in code:
            code = code.replace(old_login, new_login)
            # Also fix the execute line
            code = code.replace('cur = db.execute(query)', 'cur = db.execute(query, (username, password))')
            patched = True
        
        # Fix /users search endpoint
        old_users = 'query = f"SELECT id, username, email FROM users WHERE username LIKE \'%{search}%\'"'
        new_users = 'query = "SELECT id, username, email FROM users WHERE username LIKE ?"'
        if old_users in code:
            code = code.replace(old_users, new_users)
            code = code.replace('cur = db.execute(query)', 'cur = db.execute(query, (f\'%{search}%\',))')
            patched = True
    
    elif vuln in ["command injection", "command_injection", "cmdi"]:
        # Fix command injection in /ping_exec
        old_cmd = 'cmd = f"ping -c 2 {host}"'
        new_cmd = 'cmd = ["ping", "-c", "2", host]'
        if old_cmd in code:
            code = code.replace(old_cmd, new_cmd)
            code = code.replace(
                'output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=5)',
                'output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=5)'
            )
            patched = True
    
    elif vuln in ["ssrf", "lfi", "file inclusion"]:
        # Fix SSRF/LFI in /webhook_fetch
        old_lfi = '''if url.startswith("file://"):
        path = url[7:]
        with open(path, 'r') as f:
            return f"<pre>{f.read()}</pre>"'''
        new_lfi = '''if url.startswith("file://") or url.startswith("file:"):
        return "Error: File protocol not allowed for security reasons."
    if re.match(r'https?://(127\\.|10\\.|192\\.168\\.|172\\.(1[6-9]|2[0-9]|3[0-1])|0\\.0\\.0\\.0|localhost)', url):
        return "Error: Internal/private addresses are not allowed."'''
        if old_lfi in code:
            code = code.replace(old_lfi, new_lfi)
            patched = True
    
    elif vuln in ["ssti", "template injection"]:
        # Fix SSTI in /set_announcement
        old_ssti = 'template = "<h2>Announcement:</h2>" + msg\n    return render_template_string(template)'
        new_ssti = 'safe_msg = msg.replace(\'{{\', \'\').replace(\'}}\', \'\').replace(\'{%\', \'\').replace(\'%}\', \'\')\n    return f"<h2>Announcement:</h2>{safe_msg}"'
        if old_ssti in code:
            code = code.replace(old_ssti, new_ssti)
            patched = True
    
    elif vuln in ["idor", "xss", "stored xss", "idor_xss"]:
        # Fix IDOR in /profile
        old_profile = 'def profile(user_id):\n    cur = db.execute(f"SELECT * FROM users WHERE id={user_id}")'
        new_profile = 'def profile(user_id):\n    if \'user_id\' not in session or session[\'user_id\'] != user_id:\n        return "Access denied", 403\n    cur = db.execute("SELECT * FROM users WHERE id=?", (user_id,))'
        if old_profile in code:
            code = code.replace(old_profile, new_profile)
            patched = True
        
        # Fix Stored XSS in /comment
        old_xss = "db.execute(f\"INSERT INTO comments (user_id, text) VALUES ({user_id}, '{text}')\")"
        new_xss = 'import html as html_module\n    safe_text = html_module.escape(text)\n    db.execute("INSERT INTO comments (user_id, text) VALUES (?, ?)", (user_id, safe_text))'
        if old_xss in code:
            code = code.replace(old_xss, new_xss)
            patched = True
    
    else:
        return f"Unknown vulnerability type: {vulnerability}. Supported: sqli, cmdi, ssrf, ssti, xss, idor_xss"
    
    if patched:
        full_path.write_text(code, encoding='utf-8')
        return f"✅ Successfully patched {file_path} for {vulnerability}"
    else:
        return f"⚠️  Could not find vulnerable code for {vulnerability}. File may already be patched."

def route_tool(tool_name, args, config):
    if args is None: args = {}
    routes = {
        "execute_terminal": lambda a: execute_terminal(a.get("cmd") or a.get("command"), timeout=int(a.get("timeout", 30))),
        "search_kb": lambda a: search_kb(a.get("keyword")),
        "http_request": lambda a: http_request(a.get("method", "GET"), a.get("url"), a.get("headers"), a.get("body")),
        "read_file": lambda a: truncate(Path(BASE_DIR / a.get("file_path")).read_text(encoding='utf-8', errors='ignore')),
        "write_file": lambda a: str(Path(BASE_DIR / a.get("file_path")).write_text(a.get("content", ""), encoding="utf-8")) and f"File written: {a.get('file_path')}",
        "apply_patch": lambda a: apply_patch(a.get("vulnerability"), a.get("file_path", "lab.py")),
        "claim_flag": lambda a: f"OBJECTIVE MET: {a.get('flag')}"
    }
    if tool_name in routes:
        try: return routes[tool_name](args)
        except Exception as e: return f"Routing Error: {str(e)}"
    return f"Invalid Tool: {tool_name}"