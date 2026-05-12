import sys, os
import importlib.util

# Force-load the local providers module to avoid the installed spectrum package
_prov_path = os.path.join(os.path.dirname(__file__), "providers.py")
_spec_prov = importlib.util.spec_from_file_location("providers", _prov_path)
providers = importlib.util.module_from_spec(_spec_prov)
_spec_prov.loader.exec_module(providers)
generate = providers.generate  # convenience

import json
import re
import time
import subprocess
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from spectrum import tools

console = Console()
BASE_DIR = Path(__file__).resolve().parent
TUTORIALS_DIR = BASE_DIR / "tutorials"
ENV_PATH = BASE_DIR / ".env"
CONFIG_PATH = BASE_DIR / "config.json"
SESSION_MD = BASE_DIR / "session.md"
DUMP_PATH = BASE_DIR / "operation_state_recovery.json"
THOUGHTS_PATH = BASE_DIR / "thoughts.json"

RE_THINK = re.compile(r'\u4DC2(.*?)\u4DC2', re.DOTALL)
RE_SESSION_COOKIES = re.compile(r"SESSION_COOKIES: (.*?) -->")

RED_HACKER_ART = r"""[bold red]
                                               .-**-.                                               
                                            .-#@@@@@@#=.                                            
                                         .-#@@@@@@@@@@@@#-.                                         
                                       .+@@@@@@#****#@@@@@@+..                                      
                                     .#@@@@@#**********#@@@@@#.                                     
                                   .#@@@@@#***************@@@@@#.                                   
                                 .+@@@@@********************@@@@@+.                                 
                               .:%@@@@************************@@@@%:.                               
                              .-@@@@#**************************#@@@@=.                              
                             .=@@@@#*****************************@@@@=.                             
                            .=@@@@******#%@@@@@@@@@@@@@@@@%#******%@@@+.                            
                            -%@@@**#@@@@@@@@@@@@@@@@@@@@@@@@@@@@#**@@@@-                            
                           .#@@@@@@@@@@@@@@@@@@@%==%@@@@@@@@@@@@@@@@@@@#.                           
                           :%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%-                           
                           =@@@@@@%@@@@@%*****%@@@@@@%*****%@@@@@@@@@@@@+                           
                           *@@@@#*#@@@@@%*****%@@@@@@%*****%@@@@@#*#@@@@*                           
                          .*@@@#***%@@@@@@@@@@@@@@%@@@@@@@@@@@@@%***#@@@*.                          
                           *@@@#***#@@@@@@@@@@@@#=-#@@@@@@@@@@@@#***#@@@*                           
                           =%@@%****%@@@%-----::::::::-----#@@@%****%@@@=                           
                           .#@@@*****%@@@%-::::::::::::::-#@@@%*****@@@%:                           
                           .+@@@@*****#@@@@+::::::::::::+@@@@#*****%@@@+.                           
                            .*@@@@#*****@@@@@%::::::::%@@@@@#****#@@@@*.                            
                          .-#@@@@@@@@****#@@@@@@@@@@@@@@@@#****@@@@@@@@#-.                          
                       .-@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@=.                       
                     =@@@@@@@#*****#@@@@@@@@@@@@@@@@@@@@@@@@@@@@#****+#@@@@@@@=                     
                  .*@@@@@@**************+**##%@@@@@@@@%##**+**************@@@@@@*.                  
                .*@@@@@#*@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@##@@@@@*..               
              .-@@@@@***%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%***@@@@@=.              
             .%@@@@#****%@@@=::::::::::::::::::::::::::::::::::::::::::-@@@%****#@@@@%.             
            :%@@@%******%@@@=:::::::::::::::-+@@@@@@@@+-:::::::::::::::-@@@%******%@@@%:            
           :#@@@#*******%@@@=:::::::::::::+%@@@@@@@@@@@@@+-::::::::::::-@@@%*******#@@@#:           
          .*@@@#********%@@@=:::::::::::-%@@@@@%####%@@@@@%-:::::::::::-@@@%********#@@@*.          
         .-@@@%*********%@@@=::::::::::-@@@@%##########%@@@@-::::::::::-@@@%*********%@@@=.         
         .*@@@**********%@@@=::::::::::#@@@%############%@@@#::::::::::-@@@%**********@@@#:         
        .-@@@%**********%@@@=::::::::::@@@@%#%%%####%%%#%@@@@-:::::::::-@@@%**********#@@@-.        
        .=@@@#**********%@@@=::::::::::@@@@#%@@@%##%@@@%#@@@@-:::::::::-@@@%***********@@@+.        
        .*@@@*****#%#***%@@@=::::::::::%@@@%#%%%####%%%#%@@@%::::::::::-@@@%***#%#*****@@@*.        
        .#@@@****#@@@@%*%@@@=::::::::::-@@@@%##########%@@@@=::::::::::-@@@%*%@@@@#****@@@%.        
        .%@@@*****#@@@@@@@@@=:::::::::::=%@@@@##%@@%##@@@@@=:::::::::::-@@@@@@@@@#*****@@@%.        
        .%@@%*******#@@@@@@@=::::::::::::-#@@@#%@@@@%#@@@%-::::::::::::-@@@@@@@#*******%@@%.        
        .#@@@**********@@@@@=:::::::::::::*@@@@@@@@@@@@@@*:::::::::::::-@@@@@#*********@@@%.        
        .+@@@#**********%@@@=::::::::::::::=@@@@@@@@@@@@+::::::::::::::-@@@%***********@@@+.        
        .:%@@@**********%@@@=::::::::::::::::::------::::::::::::::::::-@@@%**********@@@%:.        
         .-@@@@*********%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%*********@@@@=.         
          .=@@@@%*******%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%*******%@@@@=.          
            :#@@@@%#****%@@@=::::::::::::::::::::::::::::::::::::::::::-@@@%*****%@@@@%:            
              -%@@@@@@@%@@@@*++++++++++++++++++++++++++++++++++++++++++*@@@@%@@@@@@@%-              
                .+%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%+..               
                   ..-+######################################################+-:.[/bold red]"""

def load_config():
    if not CONFIG_PATH.exists():
        default_config = {
            "provider": "huggingface",
            "api_key": "",
            "expert_models": [
                "deepseek-ai/DeepSeek-V3",
                "Qwen/Qwen3-Coder-480B-A35B-Instruct",
                "zai-org/GLM-5.1",
                "deepseek-ai/DeepSeek-V4-Pro",
                "deepseek-ai/DeepSeek-V4-Flash",
                "gemini-2.5-pro",
                "gemini-2.5-flash"
            ],
            "final_model_id": "deepseek-ai/DeepSeek-V4-Flash",
            "sentinel_model_id": "Qwen/Qwen2.5-3B-Instruct",
            "max_tokens_per_request": 8000,
            "temperature": 0.4,
            "use_database_framework": False,
            "use_local_bin_folder": False,
            "amd_config": {"endpoint": "https://api.amd.com/v1"},
            "gemini_model": "gemini-2.5-flash"
        }
        with open(CONFIG_PATH, "w") as f:
            json.dump(default_config, f, indent=4)
    config = json.loads(CONFIG_PATH.read_text())
    if "gemini_model" not in config:
        config["gemini_model"] = "gemini-2.5-flash"
    if "expert_models" not in config:
        config["expert_models"] = []
    if "api_key" not in config:
        config["api_key"] = ""
    return config

def load_env():
    if not ENV_PATH.exists():
        console.print("[bold yellow][!] .env file missing.[/bold yellow]")
        console.print("[bold white]Select AI Provider:[/bold white]")
        console.print("  [bold #ff5555]1.[/] [white]Hugging Face[/]")
        console.print("  [bold #5555ff]2.[/] [white]AMD Cloud[/]")
        console.print("  [bold #e6b47c]3.[/] [white]Gemini[/]")
        choice = input("Choice [1/2/3]: ").strip()
        
        if choice == "2":
            config = load_config()
            config["provider"] = "amd"
            with open(CONFIG_PATH, "w") as f:
                json.dump(config, f, indent=4)
            key = input("Enter AMD_API_KEY: ").strip()
            ENV_PATH.write_text(f"AMD_API_KEY={key}\n")
            os.environ["AMD_API_KEY"] = key
        elif choice == "3":
            config = load_config()
            config["provider"] = "gemini"
            with open(CONFIG_PATH, "w") as f:
                json.dump(config, f, indent=4)
            key = input("Enter GEMINI_API_KEY: ").strip()
            ENV_PATH.write_text(f"GEMINI_API_KEY={key}\n")
            os.environ["GEMINI_API_KEY"] = key
        else:
            token = input("Enter HF_TOKEN: ").strip()
            ENV_PATH.write_text(f"HF_TOKEN={token}\n")
            os.environ["HF_TOKEN"] = token
    else:
        for line in ENV_PATH.read_text().splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()
    
    config = load_config()
    provider = config.get("provider", "huggingface")
    if provider == "amd" and not os.environ.get("AMD_API_KEY"):
        console.print("[bold yellow]AMD provider selected but no API key found.[/bold yellow]")
        key = input("Enter AMD_API_KEY: ").strip()
        if key:
            os.environ["AMD_API_KEY"] = key
            with open(ENV_PATH, "a") as f:
                f.write(f"AMD_API_KEY={key}\n")
    elif provider == "gemini" and not os.environ.get("GEMINI_API_KEY"):
        console.print("[bold yellow]Gemini provider selected but no API key found.[/bold yellow]")
        key = input("Enter GEMINI_API_KEY: ").strip()
        if key:
            os.environ["GEMINI_API_KEY"] = key
            with open(ENV_PATH, "a") as f:
                f.write(f"GEMINI_API_KEY={key}\n")

def update_markdown_view(history):
    md_content = ""
    for msg in history:
        role = msg["role"].upper()
        if role == "USER": role = "SYSTEM"
        elif role == "ASSISTANT": role = "AGENT"
        content = msg["content"]
        if "Result:" in content and role == "SYSTEM":
            parts = content.split("Result:", 1)
            md_content += f"## {role}\n{parts[0].strip()}\n\n```text\n{parts[1].strip()}\n```\n\n"
        else:
            md_content += f"## {role}\n{content}\n\n"
    SESSION_MD.write_text(md_content, encoding="utf-8")

def update_action_trail(turn, thought_text):
    trail = []
    if THOUGHTS_PATH.exists():
        try: trail = json.loads(THOUGHTS_PATH.read_text(encoding="utf-8"))
        except: pass
    trail.append({"turn": turn, "plan_and_reasoning": thought_text.strip()})
    THOUGHTS_PATH.write_text(json.dumps(trail, indent=4), encoding="utf-8")

def get_action_trail_context():
    if not THOUGHTS_PATH.exists(): return "No previous actions recorded."
    try:
        trail = json.loads(THOUGHTS_PATH.read_text(encoding="utf-8"))
        return json.dumps(trail[-5:], indent=2)
    except: return "Trail corrupted."

def get_tutorial_knowledge():
    knowledge = "\n# ABSOLUTE SYSTEM DIRECTIVES (MUST BE FOLLOWED STRICTLY):\n"
    if TUTORIALS_DIR.exists():
        for file in TUTORIALS_DIR.glob("*.md"):
            try: knowledge += f"## Directive Set: {file.name}\n{file.read_text(encoding='utf-8', errors='ignore')}\n\n"
            except: pass
        for file in TUTORIALS_DIR.glob("*.txt"):
            try: knowledge += f"## Reference: {file.name}\n{file.read_text(encoding='utf-8', errors='ignore')}\n\n"
            except: pass
    return knowledge

def robust_extract_tool(text):
    match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
    if not match: match = re.search(r'(\{[\s\S]*"tool"[\s\S]*\})', text)
    if match:
        try: 
            raw_json = match.group(1) if "```" in text else match.group(0)
            raw_json = re.sub(r',\s*\}', '}', raw_json)
            data = json.loads(raw_json)
            if "parameters" in data and "args" not in data: data["args"] = data.pop("parameters")
            return data
        except: return None
    return None

def save_session_state(messages):
    state = {"cookies": dict(tools.global_session.cookies), "messages": messages}
    DUMP_PATH.write_text(json.dumps(state, indent=4), encoding="utf-8")
    console.print(f"[bold green]Session state safely persisted to {DUMP_PATH.name}[/bold green]")

def restore_session():
    if not DUMP_PATH.exists(): return None
    console.print(f"\n[bold yellow][!] Suspended Operation State detected at: {DUMP_PATH.name}[/bold yellow]")
    if input("Resume operation? (y/N): ").lower() != 'y': return None
    try:
        state = json.loads(DUMP_PATH.read_text(encoding="utf-8"))
        tools.global_session.cookies.update(state.get("cookies", {}))
        os.remove(DUMP_PATH)
        return state.get("messages", [])
    except Exception as e:
        console.print(f"[bold red]Failed to restore state: {e}[/bold red]")
        return None

def ai_call(messages, config):
    for attempt in range(3):
        try:
            with console.status("[bold cyan]Agent Cognition...", spinner="line"):
                resp = generate(messages, config)
            if resp.startswith("Error: 402"):
                console.print("[bold red]API Quota Exhausted. Executing Emergency Save...[/bold red]")
                save_session_state(messages)
                return "Error: 402"
            return resp
        except Exception as e:
            console.print(f"[yellow]AI call attempt {attempt+1} failed: {e}[/yellow]")
            time.sleep(5 * (2 ** attempt))
    return "Error: API Timeout."

BASE_PROMPT = """
# ROLE: PRIMARY OFFENSIVE SECURITY AGENT
You are an advanced, fully autonomous offensive security agent. 

# OPERATIONAL FRAMEWORK
1. **Continuous Planning:** Maintain a strict plan of attack. Review previous actions.
2. **Scripting Bias:** For complex data extraction or multi-stage payloads, ALWAYS write a Python/Bash script via `write_file` and execute it.
3. **Stealth/Logic:** Treat generic errors (like HTTP 500) as potential WAF logic. Exploit the input vectors.

# RULES OF ENGAGEMENT
1. Provide a concise, professional Operator Log in plain text before using a tool.
2. End with exactly ONE JSON block: {"tool": "execute_terminal", "args": {"cmd": "string"}}
"""

def run_red_team(config, objective):
    restored = restore_session()
    if restored:
        messages = restored
        console.print("[bold green]Operation Resumed.[/bold green]")
    else:
        if THOUGHTS_PATH.exists(): os.remove(THOUGHTS_PATH)
        system_prompt = BASE_PROMPT + f"\n\n# RECENT ACTION TRAIL & PLAN:\n{get_action_trail_context()}\n" + get_tutorial_knowledge()
        messages =[{"role": "system", "content": system_prompt}, {"role": "user", "content": f"OBJECTIVE: {objective}"}]
        
    SESSION_MD.write_text("", encoding="utf-8")
    subprocess.Popen(["python3", str(BASE_DIR / "viewer.py")], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

    console.print(RED_HACKER_ART)

    turn = (len(messages) // 2) + 1
    while turn < 100:
        try:
            if not restored:
                messages[0]["content"] = BASE_PROMPT + f"\n\n# RECENT ACTION TRAIL & PLAN:\n{get_action_trail_context()}\n" + get_tutorial_knowledge()

            console.print(f"\n[bold white]\u250c\u2500\u2500 Cycle {turn}[/bold white]")
            resp = ai_call(messages, config)
            if resp.startswith("Error: 402"):
                break
            messages.append({"role": "assistant", "content": resp})
            update_markdown_view(messages)
            
            think = RE_THINK.search(resp)
            if think: 
                thought_content = think.group(1).strip()
                update_action_trail(turn, thought_content)
                console.print(Panel(thought_content, title="Execution Plan", border_style="cyan", style="dim"))
            
            plain = re.sub(r'```(?:json)?.*?```', '', RE_THINK.sub('', resp), flags=re.DOTALL).strip()
            if plain: console.print(Panel(plain, title="Operator Log", border_style="blue"))

            tool = robust_extract_tool(resp)
            if tool:
                t_name, t_args = tool.get('tool', 'Unknown'), tool.get('args', {})
                raw_cmd = t_args.get('cmd') or t_args.get('command') or t_args.get('url') or str(t_args)
                
                console.print(Panel(f"[bold cyan]\u279c[/bold cyan] {raw_cmd}", title=f"TERMINAL EXECUTE ({t_name})", border_style="bright_cyan"))
                
                res = str(tools.route_tool(t_name, t_args, config))
                console.print(Panel(res[:3000], title="Standard Output", border_style="green"))
                
                messages.append({"role": "user", "content": f"Result: {res}"})
                update_markdown_view(messages)
                if t_name == "claim_flag": break
            else:
                messages.append({"role": "user", "content": "SYSTEM: No valid JSON tool block detected."})
            
            turn += 1
            restored = False
            
        except KeyboardInterrupt:
            console.print("\n[bold red][!] OPERATION SUSPENDED[/bold red]")
            choice = input("Options: [s]teer agent, [r]eport generation, [p]ause & save session, [Enter] to resume.\n> ").lower()
            if choice == 's': 
                messages.append({"role": "user", "content": f"OPERATOR OVERRIDE: {input('Instruction: ')}"})
            elif choice == 'r': 
                messages.append({"role": "user", "content": "OPERATOR OVERRIDE: Cease exploitation. Generate final report."})
            elif choice == 'p':
                save_session_state(messages)
                sys.exit(0)
            continue

def main():
    load_env()
    config = load_config()
    obj = input("Target / Objective \u276f ").strip()
    if obj: run_red_team(config, obj)

if __name__ == "__main__":
    main()