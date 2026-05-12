#!/usr/bin/env python3
"""
Spectrum Settings TUI (curses)
===============================
Arrow keys navigate, Enter edits, 'q' saves, Esc cancels.
"""
import curses
import json
import os
from collections import OrderedDict

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

FIELDS = OrderedDict([
    ("provider", ("choice", ["huggingface", "gemini", "amd"])),
    ("api_key", ("string",)),
    ("gemini_model", ("choice", ["gemini-2.5-pro", "gemini-2.5-flash"])),
    ("temperature", ("float", (0.0, 2.0))),
    ("max_tokens_per_request", ("int", (1, 128000))),
    ("final_model_id", ("string",)),
    ("sentinel_model_id", ("string",)),
])

def load_config():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Config not found at {CONFIG_PATH}")
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)

def run(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(0)
    stdscr.keypad(1)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)   # highlight
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK) # title
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)  # edit mode

    config = load_config()
    keys = list(FIELDS.keys())
    row = 0
    status = ""

    def draw():
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        y = 1
        title = " Spectrum Settings "
        start_x = max(0, (w // 2) - (len(title) // 2))
        stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
        stdscr.addstr(y, start_x, title)
        stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)
        y += 2
        stdscr.addstr(y, 2, "↑↓ move  Enter edit  q save  Esc cancel", curses.A_DIM)
        y += 1
        stdscr.addstr(y, 2, "─" * (w - 4))
        y += 1

        for idx, key in enumerate(keys):
            if y >= h - 2:
                break
            val = config.get(key, "")
            display = val
            if key == "api_key" and val:
                display = "*" * min(len(val), 16) + (val[-4:] if len(val) > 4 else "")
            if isinstance(display, float):
                display = f"{display:.2f}"
            line = f"  {key}: {display}"

            if idx == row:
                stdscr.attron(curses.color_pair(1) | curses.A_REVERSE)
                stdscr.addstr(y, 2, line.ljust(w - 4))
                stdscr.attroff(curses.color_pair(1) | curses.A_REVERSE)
            else:
                stdscr.addstr(y, 2, line.ljust(w - 4))
            y += 1

        if status:
            stdscr.addstr(h - 2, 2, status[:w - 4], curses.A_BOLD)
        stdscr.refresh()

    while True:
        draw()
        key = stdscr.getch()

        if key == curses.KEY_UP and row > 0:
            row -= 1
        elif key == curses.KEY_DOWN and row < len(keys) - 1:
            row += 1
        elif key == ord("q") or key == ord("Q"):
            save_config(config)
            status = "Saved."
            draw()
            curses.napms(1000)
            break
        elif key == 27:  # Esc
            status = "Exit without saving."
            draw()
            curses.napms(1000)
            break
        elif key == 10:  # Enter
            sel_key = keys[row]
            field_def = FIELDS[sel_key]
            if field_def[0] == "choice":
                choices = field_def[1]
                ci = 0
                if config.get(sel_key) in choices:
                    ci = choices.index(config[sel_key])
                while True:
                    stdscr.clear()
                    h2, w2 = stdscr.getmaxyx()
                    y2 = 3
                    stdscr.addstr(y2, 5, f"Choose {sel_key}:")
                    y2 += 2
                    for i, c in enumerate(choices):
                        if i == ci:
                            stdscr.attron(curses.color_pair(1) | curses.A_REVERSE)
                            stdscr.addstr(y2, 7, f"> {c}")
                            stdscr.attroff(curses.color_pair(1) | curses.A_REVERSE)
                        else:
                            stdscr.addstr(y2, 7, f"  {c}")
                        y2 += 1
                    stdscr.refresh()
                    k = stdscr.getch()
                    if k == curses.KEY_UP and ci > 0:
                        ci -= 1
                    elif k == curses.KEY_DOWN and ci < len(choices) - 1:
                        ci += 1
                    elif k == 10:
                        config[sel_key] = choices[ci]
                        break
                    elif k == 27:
                        break
            else:
                # Text input
                stdscr.clear()
                h2, w2 = stdscr.getmaxyx()
                stdscr.addstr(3, 3, f"New value for {sel_key}:")
                stdscr.addstr(4, 3, "(press Enter to confirm)")
                curses.echo()
                curses.curs_set(1)
                stdscr.move(4, 3 + 30)  # approximate
                input_bytes = stdscr.getstr(4, 3 + 30, 256)
                curses.noecho()
                curses.curs_set(0)
                try:
                    new_val = input_bytes.decode("utf-8").strip()
                    if field_def[0] == "float":
                        lo, hi = field_def[1]
                        val = max(lo, min(hi, float(new_val)))
                        config[sel_key] = val
                    elif field_def[0] == "int":
                        lo, hi = field_def[1]
                        val = max(lo, min(hi, int(new_val)))
                        config[sel_key] = val
                    else:
                        config[sel_key] = new_val
                except (ValueError, KeyError):
                    pass  # keep old value

def main():
    curses.wrapper(run)

if __name__ == "__main__":
    main()