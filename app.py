import streamlit as st
import os
import sys
import subprocess
import threading
import time
import queue
import re
from pathlib import Path

st.set_page_config(page_title="Spectrum", layout="wide")

BASE_DIR = Path(__file__).resolve().parent

def strip_ansi(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

if "process" not in st.session_state:
    st.session_state.process = None
if "output" not in st.session_state:
    st.session_state.output = ""
if "started" not in st.session_state:
    st.session_state.started = False

def start():
    if st.session_state.process and st.session_state.process.poll() is None:
        st.session_state.process.terminate()
    st.session_state.output = ""
    env = os.environ.copy()
    env["TERM"] = "dumb"
    env["NO_COLOR"] = "1"
    env["PYTHONUNBUFFERED"] = "1"
    st.session_state.process = subprocess.Popen(
        [sys.executable, str(BASE_DIR / "main.py")],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
        cwd=str(BASE_DIR)
    )
    st.session_state.started = True

def send(text):
    if st.session_state.process and st.session_state.process.poll() is None:
        st.session_state.process.stdin.write(text + "\n")
        st.session_state.process.stdin.flush()

def read_output():
    if st.session_state.process and st.session_state.process.poll() is None:
        import select
        if select.select([st.session_state.process.stdout], [], [], 0.1)[0]:
            line = st.session_state.process.stdout.readline()
            if line:
                st.session_state.output += strip_ansi(line)

st.markdown("""
<style>
.stApp { background: #0a0a0a; }
input { background: #1a1a1a !important; color: #00ff41 !important; border: 1px solid #333 !important; font-family: Menlo, monospace !important; }
button { background: #1a1a1a !important; color: #00ff41 !important; border: 1px solid #333 !important; }
.terminal { background: #0a0a0a; color: #00ff41; padding: 15px; font-family: Menlo, monospace; white-space: pre-wrap; border: 1px solid #333; min-height: 500px; max-height: 65vh; overflow-y: auto; font-size: 13px; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='color:#00ff41;font-family:Menlo,monospace;'>Spectrum</h1>", unsafe_allow_html=True)

c1, c2 = st.columns([1, 1])
with c1:
    if st.button("Start", use_container_width=True):
        start()
with c2:
    if st.button("Stop", use_container_width=True):
        if st.session_state.process:
            st.session_state.process.terminate()
            st.session_state.started = False

terminal = st.empty()
cmd = st.empty()

if st.session_state.started:
    read_output()
    terminal.markdown(f'<div class="terminal">{st.session_state.output[-8000:]}</div>', unsafe_allow_html=True)
    user_input = cmd.text_input("", placeholder="Type here...", key="input", label_visibility="collapsed")
    if user_input:
        send(user_input)
        time.sleep(0.5)
        read_output()
        terminal.markdown(f'<div class="terminal">{st.session_state.output[-8000:]}</div>', unsafe_allow_html=True)
        st.rerun()
    time.sleep(0.5)
    st.rerun()
else:
    terminal.markdown('<div class="terminal">Click Start to launch Spectrum</div>', unsafe_allow_html=True)
