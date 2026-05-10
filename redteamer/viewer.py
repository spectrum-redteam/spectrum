import webview
import markdown2
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MD_PATH = BASE_DIR / "session.md"

def get_html():
    body = ""
    if MD_PATH.exists():
        md_text = MD_PATH.read_text(encoding="utf-8")
        body = markdown2.markdown(md_text, extras=["fenced-code-blocks", "tables", "break-on-newline"])
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ 
                font-family: -apple-system, system-ui, sans-serif; 
                background: #1e1e1e; 
                color: #d4d4d4; 
                padding: 40px; 
                line-height: 1.6; 
                font-size: 14px; 
                max-width: 900px; 
                margin: auto; 
            }}
            h2 {{ 
                color: #9cdcfe; 
                font-size: 14px; 
                text-transform: uppercase; 
                border-bottom: 1px solid #3c3c3c; 
                padding-bottom: 5px; 
                margin-top: 40px; 
                letter-spacing: 1px; 
                font-weight: 600; 
            }}
            pre {{ 
                background: #252526; 
                padding: 16px; 
                border-radius: 4px; 
                border: 1px solid #3c3c3c; 
                overflow-x: auto; 
                margin: 15px 0; 
            }}
            code {{ 
                font-family: 'Consolas', 'Courier New', monospace; 
                color: #ce9178; 
                font-size: 13px; 
            }}
            pre code.language-text {{ color: #b5cea8; white-space: pre-wrap; word-break: break-all; }}
            blockquote {{ 
                border-left: 4px solid #608b4e; 
                padding: 10px 15px; 
                color: #858585; 
                background: #1e1e1e; 
                font-style: italic; 
                margin: 15px 0; 
            }}
            hr {{ border: 0; border-top: 1px solid #3c3c3c; margin: 30px 0; }}
            ::-webkit-scrollbar {{ width: 8px; }}
            ::-webkit-scrollbar-thumb {{ background: #424242; border-radius: 4px; }}
        </style>
        <script>
            let autoScroll = true;
            window.onscroll = function() {{
                let threshold = 150;
                autoScroll = (window.innerHeight + window.scrollY) >= (document.body.offsetHeight - threshold);
            }};
            function scrollToBottom() {{
                if (autoScroll) window.scrollTo({{ top: document.body.scrollHeight, behavior: 'auto' }});
            }}
            const observer = new MutationObserver(scrollToBottom);
            window.onload = () => {{
                observer.observe(document.body, {{ childList: true, subtree: true }});
                scrollToBottom();
            }};
        </script>
    </head>
    <body>
        {body}
        <div id="bottom" style="height: 100px;"></div>
    </body>
    </html>
    """

def start_window():
    window = webview.create_window('Operations Log', html=get_html(), width=900, height=950)
    def refresh(window):
        while True:
            time.sleep(2)
            window.load_html(get_html())
    webview.start(refresh, window)

if __name__ == "__main__":
    start_window()