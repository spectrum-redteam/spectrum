import streamlit as st
import os
import sys
import subprocess
import threading
import time
import queue
import re
from pathlib import Path

st.set_page_config(page_title="Spectrum Proto", page_icon="🔴🔵", layout="wide")

BASE_DIR = Path(__file__).resolve().parent

# Remove ANSI escape codes for clean display
def strip_ansi(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

# Init session state
if "process" not in st.session_state:
    st.session_state.process = None
if "output" not in st.session_state:
    st.session_state.output = ""
if "started" not in st.session_state:
    st.session_state.started = False
if "output_queue" not in st.session_state:
    st.session_state.output_queue = queue.Queue()

def drain_output():
    while not st.session_state.output_queue.empty():
        try:
            line = st.session_state.output_queue.get_nowait()
            st.session_state.output += strip_ansi(line)
        except queue.Empty:
            break

def start_spectrum():
    if st.session_state.process and st.session_state.process.poll() is None:
        st.session_state.process.terminate()
    
    st.session_state.output = ""
    st.session_state.output_queue = queue.Queue()
    
    env = os.environ.copy()
    env["TERM"] = "dumb"
    env["FORCE_COLOR"] = "0"
    env["NO_COLOR"] = "1"
    
    st.session_state.process = subprocess.Popen(
        [sys.executable, str(BASE_DIR / "main.py")],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
        cwd=str(BASE_DIR)
    )
    
    def reader():
        for line in iter(st.session_state.process.stdout.readline, ''):
            if line:
                st.session_state.output_queue.put(line)
    
    threading.Thread(target=reader, daemon=True).start()
    time.sleep(2)
    st.session_state.process.stdin.write("\n")
    st.session_state.process.stdin.flush()
    time.sleep(2)
    drain_output()
    st.session_state.started = True

def send_input(text):
    if st.session_state.process and st.session_state.process.poll() is None:
        st.session_state.process.stdin.write(text + "\n")
        st.session_state.process.stdin.flush()
        time.sleep(0.5)
        drain_output()

# ---- UI ----
st.markdown("""
<style>
.stApp { background: #0a0a0a; }
.stTextInput > div > div > input { background: #1a1a1a; color: #00ff41; border: 1px solid #333; font-family: 'Menlo', monospace; }
.stButton > button { background: #1a1a1a; color: #00ff41; border: 1px solid #333; width: 100%; }
.stButton > button:hover { background: #222; border-color: #00ff41; }
.terminal { background: #0a0a0a; color: #00ff41; padding: 15px; font-family: 'Menlo', monospace; 
    white-space: pre-wrap; border: 1px solid #333; border-radius: 5px; min-height: 500px; max-height: 65vh; overflow-y: auto; font-size: 13px; line-height: 1.4; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='color:#ff5555;'>🔴<span style='color:#5555ff;'>🔵</span> Spectrum Proto</h1>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    if st.button("🚀 Start Spectrum", key="start"):
        start_spectrum()
with col2:
    if st.button("⏹️ Stop", key="stop"):
        if st.session_state.process:
            st.session_state.process.terminate()
            st.session_state.started = False

# Terminal output
drain_output()
terminal_placeholder = st.empty()
terminal_placeholder.markdown(
    f'<div class="terminal">{st.session_state.output[-8000:]}</div>',
    unsafe_allow_html=True
)

# Input
if st.session_state.started:
    cmd = st.chat_input("Type here... (1=Red, 2=Blue, s=steer, p=pause)")
    if cmd:
        send_input(cmd)
        drain_output()
        terminal_placeholder.markdown(
            f'<div class="terminal">{st.session_state.output[-8000:]}</div>',
            unsafe_allow_html=True
        )
        st.rerun()
else:
    st.info("Click **Start Spectrum** to begin")

# Auto-refresh
if st.session_state.started:
    drain_output()
    time.sleep(1)
    st.rerun()