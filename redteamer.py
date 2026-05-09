import os
import sys
import json
import re
import time
import subprocess
import random
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

import tools

console = Console()
BASE_DIR = Path(__file__).resolve().parent
TUTORIALS_DIR = BASE_DIR / "tutorials"
ENV_PATH = BASE_DIR / ".env"
CONFIG_PATH = BASE_DIR / "config.json"
SESSION_MD = BASE_DIR / "session.md"
DUMP_PATH = BASE_DIR / "operation_state_recovery.json"
THOUGHTS_PATH = BASE_DIR / "thoughts.json"

RE_THINK = re.compile(r'䷂(.*?)䷂', re.DOTALL)
RE_SESSION_COOKIES = re.compile(r"SESSION_COOKIES: (.*?) -->")

COGNITION_VERBS =[
    "Cogitating adversarial vectors...",
    "Synthesizing heuristic bypasses...",
    "Orchestrating intrusion logic...",
    "Evaluating topological weaknesses...",
    "Extrapolating systemic vulnerabilities...",
    "Formulating execution matrix...",
    "Parsing protocol anomalies..."
]

# SOLID VIVID RED HACKER ART
RED_HACKER_ART = r"""
[bold #ff0000]                                               .-**-.                                               [/]
[bold #ff0000]                                            .-#@@@@@@#=.                                            [/]
[bold #ff0000]                                         .-#@@@@@@@@@@@@#-.                                         [/]
[bold #ff0000]                                       .+@@@@@@#****#@@@@@@+..                                      [/]
[bold #ff0000]                                     .#@@@@@#**********#@@@@@#.                                     [/]
[bold #ff0000]                                   .#@@@@@#***************@@@@@#.                                   [/]
[bold #ff0000]                                 .+@@@@@********************@@@@@+.                                 [/]
[bold #ff0000]                               .:%@@@@************************@@@@%:.                               [/]
[bold #ff0000]                              .-@@@@#**************************#@@@@=.                              [/]
[bold #ff0000]                             .=@@@@#*****************************@@@@=.                             [/]
[bold #ff0000]                            .=@@@@******#%@@@@@@@@@@@@@@@@%#******%@@@+.                            [/]
[bold #ff0000]                            -%@@@**#@@@@@@@@@@@@@@@@@@@@@@@@@@@@#**@@@@-                            [/]
[bold #ff0000]                           .#@@@@@@@@@@@@@@@@@@@%==%@@@@@@@@@@@@@@@@@@@#.                           [/]
[bold #ff0000]                           :%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%-                           [/]
[bold #ff0000]                           =@@@@@@%@@@@@%*****%@@@@@@%*****%@@@@@@@@@@@@+                           [/]
[bold #ff0000]                           *@@@@#*#@@@@@%*****%@@@@@@%*****%@@@@@#*#@@@@*                           [/]
[bold #ff0000]                          .*@@@#***%@@@@@@@@@@@@@@%@@@@@@@@@@@@@%***#@@@*.                          [/]
[bold #ff0000]                           *@@@#***#@@@@@@@@@@@@#=-#@@@@@@@@@@@@#***#@@@*                           [/]
[bold #ff0000]                           =%@@%****%@@@%-----::::::::-----#@@@%****%@@@=                           [/]
[bold #ff0000]                           .#@@@*****%@@@%-::::::::::::::-#@@@%*****@@@%:                           [/]
[bold #ff0000]                           .+@@@@*****#@@@@+::::::::::::+@@@@#*****%@@@+.                           [/]
[bold #ff0000]                            .*@@@@#*****@@@@@%::::::::%@@@@@#****#@@@@*.                            [/]
[bold #ff0000]                          .-#@@@@@@@@****#@@@@@@@@@@@@@@@@#****@@@@@@@@#-.                          [/]
[bold #ff0000]                       .-@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@=.                       [/]
[bold #ff0000]                     =@@@@@@@#*****#@@@@@@@@@@@@@@@@@@@@@@@@@@@@#****+#@@@@@@@=                     [/]
[bold #ff0000]                  .*@@@@@@**************+**##%@@@@@@@@%##**+**************@@@@@@*.                  [/]
[bold #ff0000]                .*@@@@@#*@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@##@@@@@*..               [/]
[bold #ff0000]              .-@@@@@***%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%***@@@@@=.              [/]
"""

def load_config():
    if not CONFIG_PATH.exists():
        json.dump({"final_model_id": "deepseek-ai/DeepSeek-V4-Flash", "max_tokens_per_request": 8000, "temperature": 0.2}, open(CONFIG_PATH, "w"), indent=4)
    return json.load(open(CONFIG_PATH, "r"))

def load_env():
    if not ENV_PATH.exists():
        token = input("Enter HF_TOKEN: ").strip()
        ENV_PATH.write_text(f"HF_TOKEN={token}\n")
    for line in ENV_PATH.read_text().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip()

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
    trail =[]
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

def restore_session():
    if not DUMP_PATH.exists(): return None
    console.print(f"\n[bold yellow]Suspended Operation State detected.[/]")
    if input("Resume session? (y/N): ").lower() != 'y': return None
    try:
        state = json.loads(DUMP_PATH.read_text(encoding="utf-8"))
        tools.global_session.cookies.update(state.get("cookies", {}))
        os.remove(DUMP_PATH)
        return state.get("messages",[])
    except: return None

def ai_call(messages, config):
    from huggingface_hub import InferenceClient
    token = os.environ.get("HF_TOKEN")
    model = config.get("final_model_id")
    spinner_msg = f"[bold #ff5555]{random.choice(COGNITION_VERBS)}[/]"
    for attempt in range(3):
        try:
            client = InferenceClient(model=model, token=token)
            with console.status(spinner_msg, spinner="dots"):
                response = client.chat_completion(messages=messages, max_tokens=config["max_tokens_per_request"], temperature=0.2)
            msg = response.choices[0].message
            out = f"䷂\n{msg.reasoning}\n䷂\n" if hasattr(msg, 'reasoning') and msg.reasoning else ""
            return out + (msg.content or "")
        except Exception as e:
            if "402" in str(e).lower():
                save_session_state(messages)
                return "Error: 402"
            time.sleep(5 * (2 ** attempt))
    return "Error: API Timeout."

BASE_PROMPT = """
# ROLE: PRIMARY OFFENSIVE SECURITY AGENT
Review previous actions in thoughts.json. ALWAYS write scripts for complex exploits.
"""

def run_red_team(config, objective):
    restored = restore_session()
    if restored: messages = restored
    else:
        if THOUGHTS_PATH.exists(): os.remove(THOUGHTS_PATH)
        system_prompt = f"ROLE: RED TEAM AGENT. MISSION: {objective}.\n" + get_tutorial_knowledge()
        messages =[{"role": "system", "content": system_prompt}, {"role": "user", "content": "BEGIN."}]
    
    subprocess.Popen(["python3", str(BASE_DIR / "viewer.py")], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

    # Print Hacker Art once at top
    console.print(RED_HACKER_ART)

    turn = (len(messages) // 2) + 1
    while turn < 100:
        try:
            if not restored:
                messages[0]["content"] = f"ROLE: RED TEAM AGENT. MISSION: {objective}.\n" + f"\n\n# RECENT ACTION TRAIL & PLAN:\n{get_action_trail_context()}\n" + get_tutorial_knowledge()

            console.print(f"\n[bold white]┌── Cycle {turn}[/]")
            resp = ai_call(messages, config)
            if "Error: 402" in resp: break
            messages.append({"role": "assistant", "content": resp})
            update_markdown_view(messages)
            
            think = RE_THINK.search(resp)
            if think: 
                update_action_trail(turn, think.group(1).strip())
                console.print(Panel(think.group(1).strip(), title="Cognition", border_style="#ff5555", style="dim"))
            
            plain = re.sub(r'```(?:json)?.*?```', '', RE_THINK.sub('', resp), flags=re.DOTALL).strip()
            if plain: console.print(Panel(plain, title="Agent", border_style="red"))

            tool = robust_extract_tool(resp)
            if tool:
                res = str(tools.route_tool(tool.get('tool', 'Unknown'), tool.get('args', {}), config))
                console.print(Panel(res[:1000], title="Result", border_style="green"))
                messages.append({"role": "user", "content": f"Result: {res}"})
                update_markdown_view(messages)
                if tool.get('tool') == "claim_flag": break
            turn += 1
            restored = False
        except KeyboardInterrupt:
            choice = input("Options: [s]teer, [r]eport, [p]ause, [Enter] resume: ").lower()
            if choice == 's': messages.append({"role": "user", "content": f"SYSTEM: {input('Prompt: ')}"})
            elif choice == 'p': save_session_state(messages); sys.exit(0)
            continue

def main():
    load_env(); config = load_config()
    obj = input("Target / Objective ❯ ").strip()
    if obj: run_red_team(config, obj)

if __name__ == "__main__":
    main()