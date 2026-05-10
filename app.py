import streamlit as st
import os
import sys
import subprocess
import threading
import time
import re
from pathlib import Path

st.set_page_config(page_title="Spectrum", layout="wide")

BASE_DIR = Path(__file__).resolve().parent

def ansi_to_html(text):
    color_map = {
        '30': '#000000', '31': '#ff5555', '32': '#00ff41', '33': '#ffff55',
        '34': '#5555ff', '35': '#ff55ff', '36': '#55ffff', '37': '#ffffff',
        '90': '#888888', '91': '#ff8888', '92': '#88ff88', '93': '#ffff88',
        '94': '#8888ff', '95': '#ff88ff', '96': '#88ffff', '97': '#ffffff',
        '0': '', '1': 'font-weight:bold;', '2': 'opacity:0.6;', '3': 'font-style:italic;',
    }
    text = re.sub(r'\x1B\[\d*[HJK]', '', text)
    text = re.sub(r'\x1B\[\?25[hl]', '', text)
    text = re.sub(r'\x1B\[\d*;\d*H', '', text)
    
    result = []
    i = 0
    current_styles = []
    
    while i < len(text):
        if text[i] == '\x1B' and i+1 < len(text) and text[i+1] == '[':
            end = text.find('m', i)
            if end != -1:
                codes = text[i+2:end].split(';')
                for code in codes:
                    if code == '0':
                        current_styles.clear()
                    elif code == '1':
                        current_styles.append('font-weight:bold')
                    elif code == '2':
                        current_styles.append('opacity:0.6')
                    elif code == '3':
                        current_styles.append('font-style:italic')
                    elif code in color_map and code not in ['0','1','2','3']:
                        if code.startswith('3'):
                            current_styles = [s for s in current_styles if not s.startswith('color:')]
                            current_styles.append(f"color:{color_map[code]}")
                        elif code.startswith('4'):
                            current_styles = [s for s in current_styles if not s.startswith('background-color:')]
                            current_styles.append(f"background-color:{color_map[code]}")
                if current_styles:
                    result.append(f'<span style="{"; ".join(current_styles)}">')
                else:
                    result.append('</span>')
                i = end + 1
                continue
        
        if text[i] == '\n':
            result.append('<br>')
        elif text[i] == ' ':
            result.append('&nbsp;')
        elif text[i] == '<':
            result.append('&lt;')
        elif text[i] == '>':
            result.append('&gt;')
        elif text[i] == '&':
            result.append('&amp;')
        elif ord(text[i]) >= 32:
            result.append(text[i])
        i += 1
    
    open_spans = len([r for r in result if r.startswith('<span')]) - len([r for r in result if r == '</span>'])
    for _ in range(open_spans):
        result.append('</span>')
    return ''.join(result)

if "process" not in st.session_state:
    st.session_state.process = None
if "output" not in st.session_state:
    st.session_state.output = ""
if "started" not in st.session_state:
    st.session_state.started = False
if "lock" not in st.session_state:
    st.session_state.lock = threading.Lock()

def start():
    if st.session_state.process and st.session_state.process.poll() is None:
        st.session_state.process.terminate()
    with st.session_state.lock:
        st.session_state.output = ""
    env = os.environ.copy()
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
        while select.select([st.session_state.process.stdout], [], [], 0.05)[0]:
            line = st.session_state.process.stdout.readline()
            if line:
                with st.session_state.lock:
                    st.session_state.output += line

st.markdown("""
<style>
.stApp { background: #0a0a0a; }
input { background: #1a1a1a !important; color: #00ff41 !important; border: 1px solid #333 !important; font-family: Menlo, monospace !important; }
button { background: #1a1a1a !important; color: #00ff41 !important; border: 1px solid #333 !important; }
.terminal { background: #0a0a0a; padding: 15px; font-family: Menlo, Monaco, monospace; white-space: pre; border: 1px solid #333; min-height: 500px; max-height: 65vh; overflow-y: auto; font-size: 13px; line-height: 1.3; }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 style="color:#00ff41; font-family:Menlo,monospace;">Spectrum</h1>', unsafe_allow_html=True)

c1, c2 = st.columns([1,1])
with c1:
    if st.button("Start", use_container_width=True):
        start()
        st.rerun()
with c2:
    if st.button("Stop", use_container_width=True):
        if st.session_state.process:
            st.session_state.process.terminate()
            st.session_state.started = False

terminal = st.empty()
input_placeholder = st.empty()

if st.session_state.started:
    read_output()
    with st.session_state.lock:
        html_output = ansi_to_html(st.session_state.output[-10000:])
    terminal.markdown(f'<div class="terminal">{html_output}</div>', unsafe_allow_html=True)
    
    user_input = input_placeholder.text_input("", placeholder="Type here...", key="cmd", label_visibility="collapsed")
    if user_input:
        send(user_input)
        time.sleep(0.3)
        read_output()
        with st.session_state.lock:
            html_output = ansi_to_html(st.session_state.output[-10000:])
        terminal.markdown(f'<div class="terminal">{html_output}</div>', unsafe_allow_html=True)
        st.rerun()
else:
    terminal.markdown('<div class="terminal" style="color:#888;">Click Start to launch Spectrum</div>', unsafe_allow_html=True)
