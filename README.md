### <span style="font-family: 'Glacial Indifference', sans-serif; font-size: 100px;"><span style="color:red">Spec</span><span style="color:blue">trum</span></span>
![Spectrum Picture](spectrumpicture.png)
<p align="center">
  <a href="https://github.com/spectrum-redteam/spectrum/commits/main">
    <img alt="GitHub Last Commit" src="https://img.shields.io/github/last-commit/spectrum-redteam/spectrum?style=for-the-badge&logo=git&labelColor=000000&color=6A35FF" />
  </a>
  <a href="https://github.com/spectrum-redteam/spectrum-project">
    <img alt="GitHub Repo Size" src="https://img.shields.io/github/repo-size/spectrum-redteam/spectrum?style=for-the-badge&logo=database&labelColor=000000&color=yellow" />
  </a>
  <a href="https://github.com/spectrum-redteam/spectrum/blob/main/LICENSE">
    <img alt="GitHub License" src="https://img.shields.io/github/license/spectrum-redteam/spectrum-project?style=for-the-badge&logo=codeigniter&labelColor=000000&color=FFCC19" />
  </a>
  <a href="https://pypi.org/project/spectrum-security/">
    <img alt="PyPI Version" src="https://img.shields.io/pypi/v/spectrum-security?style=for-the-badge&logo=pypi&labelColor=000000&color=00CCFF" />
  </a>
  <a href="https://pypi.org/project/spectrum-security/">
    <img alt="PyPI Downloads" src="https://img.shields.io/pypi/dm/spectrum-security?style=for-the-badge&logo=pypi&labelColor=000000&color=00FF88" />
  </a>
</p>

Spectrum is an agentic cybersecurity platform created by **Roland Poon** and **William Jiang**. It runs a fully autonomous Red Team agent that attacks and a Blue Team agent that defends — simultaneously — powered by large language models. Every action is inspected in real time by **LobsterTrap**, Spectrum's built-in guardrail engine.

Spectrum supports **Google Gemini**, **HuggingFace Inference API**, and **AMD Cloud** as LLM providers. It is built with Python and runs on most systems including macOS, Windows, and Debian or Ubuntu distributions including Kali Linux. The tool is lightweight and can be configured to use a local SQLite database and local cybersecurity tools such as Tshark, Wireshark, and John the Ripper. Wordlists are included.

![macOS](https://img.shields.io/badge/Platform-macOS-black)
![Windows](https://img.shields.io/badge/Platform-Windows-blue?logo=microsoft)
![Ubuntu](https://img.shields.io/badge/Ubuntu-E95420?style=for-the-badge&logo=Ubuntu&logoColor=white)
![Linux](https://shields.io/badge/Platform-Linux-blue?logo=linux)
![Debian](https://img.shields.io/badge/debian-red?style=for-the-badge&logo=debian&logoColor=orange&color=darkred)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

---

## Quickstart

Spectrum requires Python 3.10 or higher.

**Linux — Ubuntu / Debian**
```bash
curl -fsSL https://spectrum-redteamer.github.io/spectrum-apt/install.sh
```

**AUR (Arch Linux)**
```bash
yay -S spectrum
```

**PyPI**
```bash
pip install spectrum-security
# or
pip3 install spectrum-security
```

**UV**
```bash
uvx spectrum-security
```

**macOS Homebrew**
```bash
brew install spectrum-security
```

**Portable Release**
```bash
./spectrum-darwin-arm64.tar.gz
```

**Windows Scoop**
```powershell
scoop bucket add spectrum-redteam https://github.com/spectrum-redteam/scoop-spectrum
scoop install spectrum
```

**Chocolatey**
```powershell
choco install spectrum-security
# Not yet ready for use
```

---

## Installation from Source

```bash
git clone https://github.com/spectrum-redteam/spectrum.git
cd spectrum
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows
pip install -r requirements.txt
```

On macOS with Homebrew Python you may need:
```bash
pip install --break-system-packages -r requirements.txt
```

---

## Configuration

Most configuration can be done in `config.json`. For example, to use Gemini 2.5 Flash:

```json
{
    "provider": "gemini",
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
    "gemini_model": "gemini-2.5-flash",
    "max_tokens_per_request": 8000,
    "temperature": 0.4,
    "use_database_framework": false,
    "use_local_bin_folder": false,
    "amd_config": {
        "endpoint": "https://api.amd.com/v1"
    }
}
```

### API Keys

On first run, Spectrum prompts for your provider API key. You can also set it manually:

```bash
# Google Gemini
echo "GEMINI_API_KEY=your_key_here" > .env

# HuggingFace
echo "HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx" > .env

# AMD Cloud
echo "AMD_API_KEY=your_key_here" > .env
```

You can always download or write your own skills and import them into the `tutorials/` folder — the AI will follow them as operational directives.

---

## Running Spectrum

**Start the vulnerable lab target (optional but recommended):**
```bash
python3 lab.py
```
This starts the intentionally vulnerable Flask app at `http://127.0.0.1:4999`.

**Launch Spectrum:**
```bash
python3 main.py
```

You will see the Spectrum banner. Press **Enter** to continue.

```
Select Operational Module:
  1. Red Team (Offensive)
  2. Blue Team (Defensive)
  3. Exit
```

**Red Team Mode** — Enter a target and objective. The agent plans and executes attacks autonomously using tools like nmap, John the Ripper, and curl.

**Blue Team Mode** — Enter the URL to defend. Sentinel monitors logs every 2 seconds. When an attack is detected, the main model classifies it, patches the vulnerable code, and restarts the server automatically.

During any session, press `Ctrl+C` then:
- `s` — steer the agent
- `p` — pause and save
- `Enter` — resume

---

## Features

- **Red Team Agent** — Automated pentesting with Thought-Action-Observation loops. Scans targets, identifies vulnerabilities, writes custom exploits, and pivots through systems.
- **Blue Team Agent** — Real-time log monitoring with autonomous patching. Uses a two-model pipeline: a lightweight Sentinel model watches logs continuously, and when an attack is detected, the main model classifies the threat and rewrites the vulnerable source code live. Mean patch time under 5 seconds.
- **LobsterTrap Guardrail Engine** — Every prompt generated by either agent is inspected before execution. Enforces 18 configurable rules covering data exfiltration, prompt injection, sensitive path access, and credential harvesting. Each decision — DENY, REVIEW, or ALLOW — is logged with a risk score. Live dashboard at `localhost:8080`.
- **Audit Trail** — Full structured logging of every agent action with timestamp, agent ID, action type, risk score, and outcome. Exportable as JSON, Markdown, or PDF.
- **Drift Analyser** — File integrity monitoring that detects hallucination, scope creep, and goal drift automatically. Compares tracked files against a SHA-256 baseline. Changed files are classified as expected, flagged, or auto-reverted.
- **Attack Dashboard** — Real-time visual interface (`spectrum_dashboard.html`) showing the full attack timeline, network map, risk scores per vector, LobsterTrap intercept feed, Blue Team patch log, and compliance control status.
- **Compliance Reporting** — SOC 2 Type II and HIPAA Security Rule (45 CFR §164.312) controls mapped and tracked live. Scores update as vulnerabilities are discovered and patched.
- **Demo Site** — Public-facing hacking challenge (`demo_site.html` + `demo_server.py`). Users attack SpecBot, a deliberately vulnerable AI chatbot. Every attack is scored by LobsterTrap in real time and ranked on a live leaderboard.
- **Multimodal Injection Detection** — Image-based prompt injection detection. Analyses uploaded images for embedded adversarial instructions before they reach the language model.
- **Knowledge Base (RAG)** — SQLite database (`kb.sqlite3`) of verified exploits and payloads for retrieval-augmented generation. Enable with `"use_database_framework": true` in `config.json`.
- **Purple Teaming** — Dual-team architecture creates a continuous feedback loop where every intrusion permanently hardens the system.
- **Emergency Save** — On server error or API quota exhaustion (402), the agent saves full session state to `operation_state_recovery.json` and resumes automatically on restart.
- **Custom Skills** — Drop `.md` or `.txt` playbooks into `tutorials/`. Both agents load them at startup as operational directives.
- **Thinking Delimiter** — The agent uses a custom token delimiter (`䷂`) to separate internal reasoning from external output, letting the AI think through strategy without cluttering the operator log.

---

## File Architecture

```
spectrum/
├── main.py                        # Entry point, mode selector
├── redteamer.py                   # Offensive agent logic
├── blueteamer.py                  # Defensive agent (Sentinel + patcher)
├── tools.py                       # Tool implementations (shell, HTTP, file I/O, patch engine)
├── providers.py                   # Unified LLM provider (Gemini / HuggingFace / AMD)
├── audit.py                       # Audit trail and access control
├── lab.py                         # Intentionally vulnerable Flask app (test target)
├── config.json                    # Model IDs and provider settings
├── requirements.txt               # Python dependencies
├── demo_server.py                 # Demo site backend (chatbot + scoring + leaderboard)
├── demo_site.html                 # Public hacking challenge site
├── spectrum_dashboard.html        # Real-time attack dashboard
├── viewer.py                      # Renderer for a better UI
├── __init__.py
├── tutorials/                     # Custom skill playbooks
├── modules/
│   ├── hash_util.py
│   └── port_scanner.py
├── wordlists/
│   └── common.txt
├── blocked_ips.txt                # IPs blocked during Blue Team sessions
├── attacks.log                    # Record of detected attacks
├── server.log                     # Flask output (created at runtime)
├── audit_log.json                 # Full structured audit trail
├── session.md                     # Live session log
├── thoughts.json                  # Agent reasoning trail
└── operation_state_recovery.json  # Emergency save state
```

---

## How It Works

### Provider Abstraction

```python
def ai_call(messages, config):
    provider = config.get("provider", "huggingface")
    if provider == "gemini":
        return gemini_ai_call(messages, config)
    elif provider == "amd":
        return amd_ai_call(messages, config)
    else:
        return huggingface_ai_call(messages, config)
```

### Blue Team — Sentinel

The Sentinel model watches the server log every 2 seconds. It is intentionally lightweight (Qwen 2.5 3B) so even thousands of requests cost pennies.

```python
def sentinel_check(log_snippet, config):
    """Ask the Sentinel model to check the log - supports both HF and AMD."""
    if not log_snippet or log_snippet.strip() == "":
        return "CLEAN"

    has_any_traffic = any(word in log_snippet for word in ["GET ", "POST ", "PUT ", "DELETE ", "Form:", "Params:"])
    if not has_any_traffic:
        return "CLEAN"

    messages = [
        {"role": "system", "content": SENTINEL_PROMPT},
        {"role": "user", "content": f"Check this log:\n\n{log_snippet}\n\nRespond CLEAN or ATTACK: <type>."}
    ]
```

When Sentinel fires, the main model verifies and patches:

```python
def verify_attack(log_snippet, suspicion, config):
    """Ask the main model to verify if the attack succeeded and patch the code."""
    user_msg = f"Verify this suspicious request:\n\n{log_snippet}\n\nInitial suspicion: {suspicion}\n\nDid this attack succeed? Respond NORMAL or PATCH: <type>."

    verify_msgs = [
        {"role": "system", "content": DEFENSE_PROMPT},
        {"role": "user", "content": user_msg}
    ]

    resp = redteamer.ai_call(verify_msgs, config)
    if "Error: 402" in resp:
        return "ERROR"
    return resp.strip()
```

### Red Team — Emergency Save

```python
BASE_DIR      = Path(__file__).resolve().parent
TUTORIALS_DIR = BASE_DIR / "tutorials"
SESSION_MD    = BASE_DIR / "session.md"
DUMP_PATH     = BASE_DIR / "operation_state_recovery.json"
THOUGHTS_PATH = BASE_DIR / "thoughts.json"
```

### Custom Skills

```python
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
```

---

## Troubleshooting

**Python version error** — Verify with `python3 --version`. Spectrum requires 3.10 or higher.

**Binary not found after install** — Add Python to PATH:
```bash
export PATH="$HOME/Library/Python/3.11/bin:$PATH"
```

**externally-managed-environment error on macOS** — Use a virtual environment or pass `--break-system-packages`:
```bash
python3 -m venv venv && source venv/bin/activate
```

**ModuleNotFoundError** — Run `pip install -r requirements.txt` again.

**API Quota Exhausted (402)** — The agent saves state automatically to `operation_state_recovery.json`. Wait a few minutes or switch models in `config.json`, then restart to resume.

**Blue Team Sentinel not detecting attacks** — Ensure `lab.py` is running and `server.log` is being written. Blue Team starts the server automatically for `lab.py`.

**LobsterTrap dashboard not loading** — Ensure `demo_server.py` is running:
```bash
python3 demo_server.py
```
Dashboard is at `http://localhost:5050`.

**Cached version issues** — Purge and reinstall:
```bash
pip cache purge
pip install spectrum-security --upgrade --no-cache-dir --force-reinstall
```

**Windows Scoop** — Ensure the bucket was added before installing:
```powershell
scoop bucket add spectrum-redteam https://github.com/spectrum-redteam/scoop-spectrum
```

**Terminal output broken** — Run `main.py` in a standard terminal. Rich formatting requires a proper TTY.

---

For questions or contributions, open an issue on the [GitHub repository](https://github.com/spectrum-redteam/spectrum).