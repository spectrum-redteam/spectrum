import os
import sys
import json
import re
import time
import random
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

import tools
import redteamer

console = Console()

# SOLID VIVID BLUE HACKER ART
BLUE_HACKER_ART = r"""
[bold #0055ff]                                              .-+##+:.                                              [/]
[bold #0055ff]                                           .=%@@@@@@@@%=.                                           [/]
[bold #0055ff]                                         .:%@@@@@@@@@@@@%:.                                         [/]
[bold #0055ff]                                        .+@@@@@@@@@@@@@@@@*.                                        [/]
[bold #0055ff]                                       .*@@@@@@@@@@@@@@@@@@*.                                       [/]
[bold #0055ff]                                      .%@@@@@@@%%%%%%@@@@@@@%.                                      [/]
[bold #0055ff]                                     .#@@@@@@@@@%%%%@@@@@@@@@#.                                     [/]
[bold #0055ff]                                     -@@@#::=%%%%@@%%%%=::%@@@=                                     [/]
[bold #0055ff]                                    .@*-#@@@@@@@@@@@@@@@@@@#-*@.                                    [/]
[bold #0055ff]                                   .*-@@@@*.    +:      .*@@@@-#.                                   [/]
[bold #0055ff]                                    -@@@#-[/] [bold #0055ff]   +: .+   .=[/][bold #0055ff]#@@@@:                                    [/]
[bold #0055ff]                                    +@@@@@@%.   =***+   =@@@@@@=                                    [/]
[bold #0055ff]                                    .*@@@@@@:  =*****. .+@@@@@*.                                    [/]
[bold #0055ff]                                      :%@@@@#:. ..:.  .-@@@@%.                                      [/]
[bold #0055ff]                                    .#@%*--#@@@###*##%@@%--*@@*.                                    [/]
[bold #0055ff]                                  .#@@@@@@@@@#=------=#@@@@@@@@@*.                                  [/]
[bold #0055ff]                                .*@@@@@@@@@%#****++****#%@@@@@@@@@+.                                [/]
[bold #0055ff]                                =@@*=@@@@@@@@@@@@@@@@@@@@@@@@@@-#@@=                                [/]
[bold #0055ff]                               .@@@#=@@@@@@@@@@@@@@@@@@@@@@@@@@-#@@%                                [/]
[bold #0055ff]                               =@@@%-@@@@@@@@@@@@@@@@@@@@@@@@@@:@@@@-                               [/]
[bold #0055ff]                              .@@@@@-@@@@@@@@@@@%--@@@@@@@@@@@@:@@@@@.                              [/]
[bold #0055ff]                              =@@@%+.@@@@@@@@@@-#@@*=@@@@@@@@@@.+%@@@:                              [/]
[bold #0055ff]                             .*@@@@@-#@@@@@@@@@@-*#=@@@@@@@@@@#-@@@@@*.                             [/]
[bold #0055ff]                             .#@@@@@++@@@@@@@@@@@%%@@@@@@@@@@@+*@@@@@#.                             [/]
[bold #0055ff]                             .*@@@@@%-@@@@@@@@@@@@@@@@@@@@@@@@=%@@@@@*.                             [/]
[bold #0055ff]                              .+@@@@@-@@@@@@@@@@@@@@@@@@@@@@@@=@@@@@=.                              [/]
[bold #0055ff]                                .:+#@.++++++++++++++++++++++++:@#+:.                                [/]
[bold #0055ff]                                    ..-**********************-..                                    [/]
"""

def run_blue_team(config, target_url):
    messages =[{"role": "system", "content": "Defensive monitor."}, {"role": "user", "content": f"BEGIN: {target_url}"}]
    
    # Print Hacker Art once at top
    console.print(BLUE_HACKER_ART)
    
    turn = 1
    while True:
        try:
            console.print(f"\n[bold white]┌── Defense Cycle {turn}[/]")
            with console.status("[bold blue]Monitoring...", spinner="dots"):
                resp = redteamer.ai_call(messages, config)
            messages.append({"role": "assistant", "content": resp})
            tool = redteamer.robust_extract_tool(resp)
            if tool:
                res = str(tools.route_tool(tool.get("tool"), tool.get("args"), config))
                messages.append({"role": "user", "content": f"Result: {res}"})
            turn += 1
            time.sleep(10)
        except KeyboardInterrupt:
            if input("Resume? (y/N): ").lower() != 'y': break

def main():
    redteamer.load_env(); config = redteamer.load_config()
    url = input("Target / URL to defend ❯ ").strip() or "http://127.0.0.1:5000"
    run_blue_team(config, url)

if __name__ == "__main__":
    main()