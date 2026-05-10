# Spectrum – Red/Blue Team

A dual‑mode autonomous security platform.  
Run as **Red Team** to attack a target, or as **Blue Team** to monitor, detect intrusions and hot‑patch vulnerabilities.  
Powered by Hugging Face (or AMD Cloud) models.

---

## Prerequisites

- Python 3.10 or newer
- pip
- A Hugging Face account ([huggingface.co](https://huggingface.co)) and an API token
- Git (optional – you can also download the ZIP)

---

## Clone the project

~~~bash
git clone https://github.com/spectrum-redteamer/spectrum.git
cd spectrum
~~~

If you downloaded a ZIP, extract it and open a terminal inside the extracted folder.

---

## Install dependencies

Create and activate a virtual environment (recommended):

~~~bash
python3 -m venv venv
source venv/bin/activate       # macOS / Linux
venv\Scripts\activate          # Windows
~~~

Install the required packages:

~~~bash
pip install -r requirements.txt
~~~

On macOS with Homebrew Python you may need:

~~~bash
pip install --break-system-packages -r requirements.txt
~~~

---

## Configuration

### API Provider & Token

On the first run, Spectrum asks which provider you want to use:

1. **Hugging Face** – you will be prompted for your `HF_TOKEN`.
2. **AMD Cloud** – you will be prompted for your `AMD_API_KEY`.

The token is saved in a `.env` file.  
You can also create that file manually:

~~~bash
echo "HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx" > .env
~~~

(Replace `hf_xxxxxxxxxxxxxxxxxxxx` with your actual token.)

### Model selection (`config.json`)

The default models work out of the box.  
You can change `final_model_id` (the main agent) and `sentinel_model_id` (the lightweight Blue Team watcher) inside `config.json`.

Example excerpt:

~~~json
{
    "final_model_id": "deepseek-ai/DeepSeek-V4-Flash",
    "sentinel_model_id": "Qwen/Qwen2.5-3B-Instruct"
}
~~~

---

## Run a vulnerable target (optional)

The project includes a deliberately vulnerable Flask application (`lab.py`).  
Start it in a separate terminal to give the agents something to attack/defend:

~~~bash
python3 lab.py
~~~

It listens on `http://127.0.0.1:4999` (or the port printed in the terminal).

---

## Launch Spectrum

~~~bash
python3 main.py
~~~

You will see the Spectrum banner. Press **Enter** to continue.

### Choose your mode

~~~text
Select Operational Module:
  1. Red Team (Offensive)
  2. Blue Team (Defensive)
  3. Exit
~~~

---

### Red Team Mode

1. Enter a target / objective, for example:  
   `Find the hidden flag on http://127.0.0.1:4999`
2. The agent will plan, execute terminal commands, write scripts, and attempt to breach the target.
3. **Ctrl+C** to pause, then:
   - `s` – steer the agent (give an instruction)
   - `p` – pause and save the session
   - `Enter` – resume

---

### Blue Team Mode

1. Enter the URL to defend, for example:  
   `http://127.0.0.1:4999`
2. The Blue Team will:
   - Kill the existing server (if any) and restart it with logging enabled.
   - Start a Sentinel (small AI model) that watches the log file every few seconds.
   - When an attack is detected:
     - Record the attacker IP (in `blocked_ips.txt`).
     - Ask the main model to classify the attack.
     - Automatically patch the vulnerable code (SQLi, command injection, SSTI, etc.).
     - Restart the server with a fresh log.
3. **Ctrl+C** to pause, same steering options as Red Team.

---

## File structure (key files)

~~~
spectrum/
├── main.py               # Entry point, mode selector
├── redteamer.py          # Offensive agent logic
├── blueteamer.py         # Defensive agent (Sentinel + patcher)
├── tools.py              # Tool implementations (shell, HTTP, file I/O, patch engine)
├── lab.py                # Vulnerable SAAS lab (for testing)
├── config.json           # Model IDs and provider settings
├── requirements.txt      # Python dependencies
├── tutorials/            # Optional playbooks loaded by agents
│   ├── BLUE_DEFENSE_PLAYBOOK.md
│   └── VULNERABLE_APP_SOURCE.txt
├── blocked_ips.txt       # IPs blocked during Blue Team sessions
├── attacks.log           # Record of detected attacks
├── server.log            # Flask output (created at runtime)
├── session.md            # Live session log (viewed by viewer.py)
└── thoughts.json         # Agent reasoning trail
~~~

---

## Troubleshooting

- **ModuleNotFoundError** → run `pip install -r requirements.txt` again.
- **API Quota Exhausted** → wait a few minutes or switch to another model in `config.json`.
- **Blue Team doesn't detect attacks** → ensure the target was started with logging (the Blue Team does this automatically for `lab.py`).
- **Terminal output looks broken** → run `main.py` in a standard terminal; Rich formatting works best there.



For questions or contributions, open an issue on the project's GitHub page.
