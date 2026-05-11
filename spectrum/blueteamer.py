import os
import sys
import json
import re
import time
import subprocess
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from spectrum import tools
from spectrum import redteamer

console = Console()

# THE EXACT ASCII ART PROVIDED
BLUE_HACKER_ART = r"""[bold blue]
                                              .-+##+:.                                              
                                           .=%@@@@@@@@%=.                                           
                                         .:%@@@@@@@@@@@@%:.                                         
                                        .+@@@@@@@@@@@@@@@@*.                                        
                                       .*@@@@@@@@@@@@@@@@@@*.                                       
                                      .%@@@@@@@%%%%%%@@@@@@@%.                                      
                                     .#@@@@@@@@@%%%%@@@@@@@@@#.                                     
                                     -@@@#::=%%%%@@%%%%=::%@@@=                                     
                                    .@*-#@@@@@@@@@@@@@@@@@@#-*@.                                    
                                   .*-@@@@*.    +:      .*@@@@-#.                                   
                                    -@@@@@#-    +: .+   .=#@@@@:                                    
                                    +@@@@@@%.   =***+   =@@@@@@=                                    
                                    .*@@@@@@:  =*****. .+@@@@@*.                                    
                                      :%@@@@#:. ..:.  .-@@@@%.                                      
                                    .#@%*--#@@@###*##%@@%--*@@*.                                    
                                  .#@@@@@@@@@#=------=#@@@@@@@@@*.                                  
                                .*@@@@@@@@@%#****++****#%@@@@@@@@@+.                                
                                =@@*=@@@@@@@@@@@@@@@@@@@@@@@@@@-#@@=                                
                               .@@@#=@@@@@@@@@@@@@@@@@@@@@@@@@@-#@@%                                
                               =@@@%-@@@@@@@@@@@@@@@@@@@@@@@@@@:@@@@-                               
                              .@@@@@-@@@@@@@@@@@%--@@@@@@@@@@@@:@@@@@.                              
                              =@@@%+.@@@@@@@@@@-#@@*=@@@@@@@@@@.+%@@@:                              
                             .*@@@@@-#@@@@@@@@@@-*#=@@@@@@@@@@#-@@@@@*.                             
                             .#@@@@@++@@@@@@@@@@@%%@@@@@@@@@@@+*@@@@@#.                             
                             .*@@@@@%-@@@@@@@@@@@@@@@@@@@@@@@@=%@@@@@*.                             
                              .+@@@@@-@@@@@@@@@@@@@@@@@@@@@@@@=@@@@@=.                              
                                .:+#@.++++++++++++++++++++++++:@#+:.                                
                                    ..-**********************-..                                    
[/bold blue]"""

DEFENSE_PROMPT = """
# ROLE: INCIDENT VERIFIER & CLASSIFIER
You are a security analyst. Your job is to determine whether a suspicious request actually succeeded.

# WHAT YOU RECEIVE
You will receive a log snippet showing a suspicious request. The log format is:
TIMESTAMP - METHOD PATH from IP - Params: {...} - Form: {...}

# VERIFICATION RULES

## Normal requests (NOT attacks) - respond "NORMAL"
- Standard login: Form: {'username': 'john', 'password': 'password123'}
- Regular browsing: GET /, GET /dashboard, GET /users with no special characters
- Clean form submissions without SQL/command/template syntax

## Successful attack (NEEDS PATCH) - respond "PATCH: <type>"
- SQL injection payload in Form or Params that contains: ' --, '--, admin'--, ' OR ', UNION SELECT, 1=1
- Command injection in Params that contains: ;id, && ls, | cat, ;wget, `id`, $(whoami)
- File inclusion in Params that contains: file://, /etc/passwd, /etc/shadow, /proc/self/environ
- Template injection in Form that contains: {{, }}, {% , %}, {{config}}, {{self}}, {{''.__class__}}
- XSS in Form that contains: <script, onerror=, javascript:, <img src=x

# RESPONSE FORMAT
Respond with EXACTLY ONE LINE:
- "NORMAL" - no action needed
- "PATCH: sqli" - SQL injection attack
- "PATCH: cmdi" - command injection attack
- "PATCH: ssrf" - SSRF/LFI attack
- "PATCH: ssti" - template injection attack
- "PATCH: xss" - XSS attack
"""

SENTINEL_PROMPT = """
# ROLE: ATTACK DETECTOR
You examine server logs to find hacking attempts. The log format is:
TIMESTAMP - METHOD PATH from IP - Params: {...} - Form: {...}

# YOUR JOB
Look at the log and decide if it contains a hacking attempt.

# WHAT IS A HACK?
Any of these patterns in the Form or Params values:

SQL INJECTION:
- ' -- (single quote space dash dash)
- '-- (single quote dash dash)
- admin'--
- ' OR '1'='1
- ' OR 1=1
- UNION SELECT
- " OR "1"="1
- '; DROP TABLE

COMMAND INJECTION:
- ;id
- && ls
- | cat /etc/passwd
- ;wget
- `id`
- $(whoami)
- ;nc
- && curl

FILE INCLUSION:
- file:///etc/passwd
- file:///etc/shadow
- /proc/self/environ
- http://127.0.0.1
- http://localhost

TEMPLATE INJECTION:
- {{config}}
- {{self}}
- {{''.__class__}}
- {{ and }} together
- {% and %} together

XSS:
- <script>
- onerror=
- javascript:
- <img src=x

# WHAT IS NORMAL?
- Normal usernames and passwords: john, password123, alice, admin
- Browsing: GET /, GET /dashboard, GET /users, GET /profile/1
- Clean text in forms: "Hello world", "Test comment"
- Server startup messages: "Running on", "Debug mode", "Press CTRL+C"

# RESPONSE FORMAT
You MUST respond with EXACTLY ONE LINE:
- "CLEAN" if the log is completely normal
- "ATTACK: <type>" if you see a hack (e.g., "ATTACK: sqli", "ATTACK: cmdi", "ATTACK: ssrf", "ATTACK: ssti", "ATTACK: xss")

DO NOT EXPLAIN. Just one line.
"""
def sentinel_check(log_snippet, config):
    """Ask the Sentinel model to check the log - supports both HF and AMD."""
    from huggingface_hub import InferenceClient
    import requests as req

    if not log_snippet or log_snippet.strip() == "":
        return "CLEAN"

    has_any_traffic = any(word in log_snippet for word in ["GET ", "POST ", "PUT ", "DELETE ", "Form:", "Params:"])
    if not has_any_traffic:
        return "CLEAN"

    provider = config.get("provider", "huggingface")
    model = config.get("sentinel_model_id", "Qwen/Qwen2.5-3B-Instruct")

    messages = [
        {"role": "system", "content": SENTINEL_PROMPT},
        {"role": "user", "content": f"Check this log:\n\n{log_snippet}\n\nRespond CLEAN or ATTACK: <type>."}
    ]

    try:
        if provider == "amd":
            api_key = os.environ.get("AMD_API_KEY")
            endpoint = config.get("amd_config", {}).get("endpoint", "https://api.amd.com/v1")
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {"model": model, "messages": messages, "max_tokens": 20, "temperature": 0.01}
            response = req.post(f"{endpoint}/chat/completions", headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"].strip()
            else:
                console.print(f"[yellow]AMD Sentinel error: {response.status_code}[/yellow]")
                return "CLEAN"
        else:
            token = os.environ.get("HF_TOKEN")
            client = InferenceClient(model=model, token=token)
            response = client.chat_completion(messages=messages, max_tokens=20, temperature=0.01)
            return response.choices[0].message.content.strip()
    except Exception as e:
        console.print(f"[yellow]Sentinel error: {e}[/yellow]")
        return "CLEAN"

def verify_attack(log_snippet, suspicion, config):
    """Ask DeepSeek to verify if the attack succeeded and classify it."""
    system_prompt = DEFENSE_PROMPT
    user_msg = f"Verify this suspicious request:\n\n{log_snippet}\n\nInitial suspicion: {suspicion}\n\nDid this attack succeed? Respond NORMAL or PATCH: <type>."
    
    verify_msgs = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_msg}
    ]
    
    resp = redteamer.ai_call(verify_msgs, config)
    if "Error: 402" in resp:
        return "ERROR"
    return resp.strip()

def run_blue_team(config, target_url):
    port_match = re.search(r':(\d+)', target_url)
    port = port_match.group(1) if port_match else "5000"

    if redteamer.THOUGHTS_PATH.exists():
        os.remove(redteamer.THOUGHTS_PATH)

    console.print(BLUE_HACKER_ART)
    console.print("[bold green]🛡️  Blue Team Sentinel Initializing...[/bold green]")

    # ---- STEP 1: SETUP ----
    console.print("[bold cyan]Setting up monitoring environment...[/bold cyan]")
    
    pid_output = tools.execute_terminal(f"lsof -i :{port} -t")
    pids = [p for p in pid_output.splitlines() if p.strip().isdigit()]
    
    if pids:
        pid = pids[0]
        console.print(f"[dim]Killing existing process PID: {pid}[/dim]")
        tools.execute_terminal(f"kill -9 {pid}")
        time.sleep(1)
    
    tools.execute_terminal("rm -f server.log")
    tools.execute_terminal(f"nohup python3 lab.py > server.log 2>&1 &")
    time.sleep(2)
    
    pid_output = tools.execute_terminal(f"lsof -i :{port} -t")
    pids = [p for p in pid_output.splitlines() if p.strip().isdigit()]
    
    if not pids:
        console.print("[bold red]Failed to start server.[/bold red]")
        return
    
    pid = pids[0]
    console.print(f"[green]✅ Server running - PID: {pid} | Port: {port}[/green]")
    console.print(f"[green]📋 Logging to: server.log[/green]")

    messages = []
    redteamer.SESSION_MD.write_text("", encoding="utf-8")
    
    try:
        subprocess.Popen(["python3", str(redteamer.BASE_DIR / "viewer.py")],
                        stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    except:
        pass

    console.print("\n[bold blue]🔍 Sentinel active - watching every 2s...[/bold blue]")
    console.print("[dim]All traffic classified by AI. No regex.[/dim]\n")

    cycle = 0
    attack_cooldown = 0
    
    while True:
        try:
            cycle += 1
            
            # Cooldown after patching
            if attack_cooldown > 0:
                attack_cooldown -= 1
                console.print(f"[dim]⏱️  Cycle {cycle}: COOLDOWN ({attack_cooldown} remaining)[/dim]")
                time.sleep(2)
                continue

            # Read log
            log_output = tools.execute_terminal("tail -n 30 server.log")
            
            # Show log snapshot
            if log_output.strip():
                console.print(Panel(
                    Text(log_output, style="dim"),
                    title=f"📄 Log (Cycle {cycle})",
                    border_style="bright_black"
                ))
            else:
                console.print(f"[dim]📄 Log (Cycle {cycle}): EMPTY[/dim]")

            # Sentinel check - PURE AI, NO REGEX
            sentinel_result = sentinel_check(log_output, config)
            console.print(f"[dim]Sentinel AI: {sentinel_result}[/dim]")

            if sentinel_result == "CLEAN" or sentinel_result.startswith("CLEAN"):
                console.print(f"[dim]⏱️  Cycle {cycle}: CLEAN[/dim]")
                time.sleep(2)
                continue

            if sentinel_result.startswith("ATTACK:"):
                attack_type = sentinel_result.split(":", 1)[1].strip()
                console.print(Panel(f"🚨 {attack_type}", title="⚠️  ATTACK DETECTED", border_style="red"))
                
                # Extract IP from log
                ip_match = re.search(r'from (\S+)', log_output)
                attacker_ip = ip_match.group(1) if ip_match else "127.0.0.1"
                
                # Block IP
                console.print(f"[yellow]🚫 Blocking IP: {attacker_ip}[/yellow]")
                tools.execute_terminal(f"echo '{time.ctime()} | {attacker_ip} | {attack_type}' >> blocked_ips.txt")
                
                # Verify with DeepSeek
                console.print("[bold yellow]🔎 DeepSeek verifying attack...[/bold yellow]")
                verification = verify_attack(log_output, attack_type, config)
                console.print(f"[dim]DeepSeek: {verification}[/dim]")
                
                if verification.upper().startswith("PATCH:"):
                    vuln_type = verification.split(":", 1)[1].strip().lower()
                    
                    # Map to patch types
                    vuln_map = {
                        "sqli": "sqli",
                        "sql injection": "sqli",
                        "cmdi": "command_injection",
                        "command injection": "command_injection",
                        "ssrf": "ssrf",
                        "lfi": "ssrf",
                        "file inclusion": "ssrf",
                        "ssti": "ssti",
                        "template injection": "ssti",
                        "xss": "idor_xss",
                    }
                    patch_type = vuln_map.get(vuln_type, "unknown")
                    
                    console.print(f"[bold red]🛠️  Patching: {patch_type}[/bold red]")
                    res = tools.apply_patch(patch_type, "lab.py")
                    console.print(Panel(res, title="Patch Result", border_style="green"))
                    
                    # Restart with clean log
                    tools.execute_terminal(f"kill -9 {pid}")
                    time.sleep(1)
                    tools.execute_terminal("rm -f server.log")
                    tools.execute_terminal(f"nohup python3 lab.py > server.log 2>&1 &")
                    time.sleep(2)
                    
                    new_pid_output = tools.execute_terminal(f"lsof -i :{port} -t")
                    new_pids = [p for p in new_pid_output.splitlines() if p.strip().isdigit()]
                    if new_pids:
                        pid = new_pids[0]
                        console.print(f"[green]✅ New PID: {pid}[/green]")
                    
                    attack_cooldown = 8
                    console.print("[green]✅ Attack patched. Cooldown started.[/green]\n")
                else:
                    console.print(f"[dim]⏱️  Cycle {cycle}: {verification} - no patch needed[/dim]")
            
            time.sleep(2)

        except KeyboardInterrupt:
            console.print("\n[bold red][!] DEFENSE OPS SUSPENDED[/bold red]")
            choice = input("Options: [s]teer agent, [p]ause & save, [Enter] resume: ").lower()
            if choice == 's':
                messages.append({"role": "user", "content": f"OPERATOR OVERRIDE: {input('Instruction: ')}"})
            elif choice == 'p':
                redteamer.save_session_state(messages)
                sys.exit(0)
            continue

def main():
    redteamer.load_env()
    config = redteamer.load_config()
    url = input("Target / URL to defend ❯ ").strip() or "http://127.0.0.1:5000"
    run_blue_team(config, url)

if __name__ == "__main__":
    main()