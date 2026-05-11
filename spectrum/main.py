import sys
import time
import random
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from spectrum import redteamer
from spectrum import blueteamer
from spectrum import tools

console = Console()

# Fixed Spelling: SPECTRUM (Replaced the 4th letter 'R' with 'C')
SPECTRUM_ASCII = [
    "[bold #ff5555]███████╗██████╗ ███████╗██████╗ [/][bold #5555ff]████████╗██████╗ ██╗   ██╗███╗   ███╗[/]",
    "[bold #ff5555]██╔════╝██╔══██╗██╔════╝██╔════╝[/][bold #5555ff]╚══██╔══╝██╔══██╗██║   ██║████╗ ████║[/]",
    "[bold #ff5555]███████╗██████╔╝█████╗  ██║     [/][bold #5555ff]   ██║   ██████╔╝██║   ██║██╔████╔██║[/]",
    "[bold #ff5555]╚════██║██╔═══╝ ██╔══╝  ██║     [/][bold #5555ff]   ██║   ██╔══██╗██║   ██║██║╚██╔╝██║[/]",
    "[bold #ff5555]███████║██║     ███████╗╚██████╗[/][bold #5555ff]   ██║   ██║  ██║╚██████╔╝██║ ╚═╝ ██║[/]",
    "[bold #ff5555]╚══════╝╚═╝     ╚══════╝ ╚═════╝[/][bold #5555ff]   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝[/]"
]

QUOTES =[
    "Breaking things is the only way to truly understand them.",
    "Exploitation is an art form.",
    "Mapping the attack surface...",
    "There is no patch for human stupidity.",
    "Data wants to be free.",
    "We are the ghost in the machine.",
    "Zero trust architecture engaged.",
    "Shattering the perimeter.",
    "Quietly breaking in...",
    "Security is just an illusion.",
    "Compiling zero-days...",
    "Vigilance is our shield.",
    "Identifying structural weaknesses...",
    "Calculated intrusion sequence initiated.",
    "Initiating deep network traverse.",
    "Bypassing the mainframe...",
    "The quieter you become, the more you are able to hear.",
    "Let's find the edge cases.",
    "Software is a gas; it expands to fill its container.",
    "Code never lies; comments sometimes do."
]

def main():
    print(chr(27) + "[2J\033[H", end="")
    
    # Claude-style Welcome Box
    welcome_text = Text("* Welcome to Spectrum Best", style="bold #e6b47c")
    console.print(Panel(welcome_text, border_style="#e6b47c", expand=False))
    print("\n")
    
    # logo - Line by line for stability
    for line in SPECTRUM_ASCII:
        console.print(line)
        time.sleep(0.06)
        
    print("\n")
    # Universal [/] terminator to fix MarkupError
    console.print("🎉 [dim]Login successful.[/] Press [bold #58a6ff]Enter[/] to continue...", end="")
    input()
    
    print(chr(27) + "[2J\033[H", end="")
    console.print(Panel.fit("[bold white]SPECTRUM[/] [dim]Mode Selector[/]", border_style="#30363d"))
    
    console.print(f"\n[italic #58a6ff]\"{random.choice(QUOTES)}\"[/]\n")
    
    console.print("[bold white]Select Operational Module:[/]")
    console.print("  [bold #ff5555]1.[/] [white]Red Team (Offensive)[/]")
    console.print("  [bold #5555ff]2.[/][white] Blue Team (Defensive)[/]")
    console.print("  [bold white]3.[/][dim]Exit[/]\n")
    
    try:
        c = input("❯ ").strip()
        if c == '1': redteamer.main()
        elif c == '2': blueteamer.main()
        else: sys.exit(0)
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == "__main__":
    main()
