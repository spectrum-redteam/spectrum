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
            return "Knowledge Base: No matching entries found."
        res = ""
        for path, content in rows:
            res += f"--- Source: {path} ---\n{content[:2000]}\n\n"
        return truncate(res)
    except Exception as e:
        return f"KB Error: {str(e)}"

def execute_terminal(cmd):
    """Raw shell execution gateway for macOS."""
    try:
        if not cmd: return "Error: No command provided."
        process = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=600, cwd=str(BASE_DIR))
        out = ""
        if process.stdout: out += f"[STDOUT]\n{process.stdout}\n"
        if process.stderr: out += f"[STDERR]\n{process.stderr}\n"
        return truncate(out if out else "Executed (No Output).")
    except subprocess.TimeoutExpired:
        return "Error: Command timed out (10 min limit)."
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

def route_tool(tool_name, args, config):
    if args is None: args = {}
    routes = {
        "execute_terminal": lambda a: execute_terminal(a.get("cmd") or a.get("command")),
        "search_kb": lambda a: search_kb(a.get("keyword")),
        "http_request": lambda a: http_request(a.get("method", "GET"), a.get("url"), a.get("headers"), a.get("body")),
        "read_file": lambda a: truncate(Path(BASE_DIR / a.get("file_path")).read_text(encoding='utf-8', errors='ignore')),
        "write_file": lambda a: str(Path(BASE_DIR / a.get("file_path")).write_text(a.get("content", ""), encoding="utf-8")) and f"File written: {a.get('file_path')}",
        "claim_flag": lambda a: f"OBJECTIVE MET: {a.get('flag')}"
    }
    if tool_name in routes:
        try: return routes[tool_name](args)
        except Exception as e: return f"Routing Error: {str(e)}"
    return f"Invalid Tool: {tool_name}"