#!/usr/bin/env python3
# pyref.py - an annotated Python script that demonstrates many language features
#
# Linux-only (Ubuntu Server) variant. This revision prints a short, clear
# preamble before each demonstrated command/code block as requested:
#   This is the [command|code] used to [...]
#       [actual command/code]
#
# When a command does not produce output (e.g., setting a variable), the
# script prints a short result message and waits for a single keypress:
#   Press any key to continue
#
# Where a next command is unrelated to the previous, the screen is cleared
# before displaying the next demonstration block.
#
"""
Multi-line comment / module docstring:
This script is intended as a reference/tutorial showing many Python features
including: shebang, variable assignment, comments, immediate keypress handling
(so Y/N and menu selections do not require Enter), file I/O, subprocess usage,
data types, scope, functions, conditional branches, imports, marker files, and
text parsing/manipulation examples.

Notes:
- This version is tailored for Linux (POSIX) systems only. It uses termios/tty
  for single-key input without Enter and does not include Windows branches.
- Designed to be run on Ubuntu Server or similar Linux distributions.
"""
# ---------------------------------------------------------------------------

import os
import sys
import subprocess
import time
import json
from pathlib import Path

# Optional third-party lib used only for import-demo
try:
    import requests  # optional; only used for demonstration of imports
    HAS_REQUESTS = True
except Exception:
    HAS_REQUESTS = False

# File paths we will use
TMP_FILE = Path("/tmp/pyref_example.txt")
MARKER_FILE = Path("/tmp/pyref_marker")

# ---------------------- low-level terminal helpers -------------------------

def get_single_key():
    """
    Read a single keypress from stdin and return a tuple (char, ordinal).
    POSIX-only implementation using termios + tty. Does NOT require Enter.
    """
    import tty
    import termios

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if not ch:
            return "", 0
        if ord(ch) == 3:  # Ctrl-C -> KeyboardInterrupt
            raise KeyboardInterrupt
        return ch, ord(ch)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def press_any_key(message="Press any key to continue..."):
    """
    Wait for a single key press (no Enter). Used after commands that produce
    no stdout to let the user see a result before proceeding.
    """
    print(message, end="", flush=True)
    try:
        get_single_key()
    except KeyboardInterrupt:
        print()
        raise
    print()


def clear_screen():
    """Clear the terminal screen (POSIX)."""
    os.system("clear")

# ---------------------- demo display helper -------------------------------

def display_demo(kind, purpose, code_text, will_output=True, clear_before=False):
    """
    Display the preamble required by the user before executing demo code.

    - kind: "command" or "code" (string)
    - purpose: short phrase describing what the command/code does
    - code_text: the exact command or code snippet (string) to show indented
    - will_output: if False, the code is assumed to produce no visible output;
        display_demo will show a short 'result' message and wait for a keypress
        after executing the code.
    - clear_before: if True, clear the screen before displaying the preamble.
    """
    if clear_before:
        clear_screen()
    print(f"This is the {kind} used to {purpose}")
    for line in code_text.splitlines():
        print("    " + line)
    sys.stdout.flush()
    # If the code itself will not produce output, we'll call press_any_key later
    # from the caller after showing result. This helper only prints the preamble.


# ---------------------- example/demo functions ----------------------------

# 2) Example variable assignment (module-level)
example_var = "Hello, pyref!"


def write_initial_file():
    """
    Create /tmp/pyref_example.txt with several sample lines.
    """
    lines = [
        "Line 1: Header - pyref example file\n",
        "Line 2: This is the second line (we'll prepend numbers here later)\n",
        "Line 3: Menu item A - apples\n",
        "Line 4: Menu item B - bananas\n",
        "Line 5: Menu item C - cherries\n",
    ]
    TMP_FILE.write_text("".join(lines), encoding="utf-8")
    # The function prints informational output so callers can treat this as producing output.
    print(f"Wrote initial file to {TMP_FILE}")


def ask_yes_no(question="Do you want to continue? (y/n) "):
    """
    Ask a yes/no question, immediate keypress (no Enter). Returns True/False.
    Esc (27) is treated as 'no'.
    """
    sys.stdout.write(question)
    sys.stdout.flush()
    while True:
        ch, code = get_single_key()
        # echo the pressed key
        sys.stdout.write(ch + "\n")
        sys.stdout.flush()
        if ch.lower() == "y":
            return True
        if ch.lower() == "n":
            return False
        if code == 27:
            return False
        # otherwise prompt again
        sys.stdout.write("Please press 'y' or 'n': ")
        sys.stdout.flush()


def ask_for_text(prompt="Enter some text (press Enter when done): "):
    """
    Prompt the user to type a full line of text (requires Enter) and return it.
    """
    return input(prompt)


def append_text_to_file(text):
    """
    Append a line of text to TMP_FILE.
    """
    with TMP_FILE.open("a", encoding="utf-8") as f:
        f.write(text + "\n")
    print(f"Appended your text to {TMP_FILE}")


def prepend_number_to_second_line():
    """
    Prompt user for an integer and prepend it to the second line of TMP_FILE.
    If the file has fewer than two lines, create the second line.
    """
    while True:
        num_str = input("Enter an integer to prepend to line 2 (blank to skip): ").strip()
        if num_str == "":
            print("No number entered; skipping.")
            return
        try:
            int(num_str)
            break
        except ValueError:
            print("Please enter a valid integer (e.g. 5 or -2).")

    text = TMP_FILE.read_text(encoding="utf-8")
    lines = text.splitlines()
    while len(lines) < 2:
        lines.append("")
    lines[1] = f"{num_str} {lines[1]}"
    TMP_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Prepended number to the second line of {TMP_FILE}.")


def menu_from_file():
    """
    Create a menu from TMP_FILE lines. The user chooses by pressing a single-digit
    key (no Enter). Esc cancels.
    """
    content = TMP_FILE.read_text(encoding="utf-8")
    lines = [ln for ln in content.splitlines() if ln.strip()]
    if not lines:
        print("No menu items found in the file.")
        return None

    max_choices = min(9, len(lines))
    print("Menu (press the number key to choose; Esc to cancel):")
    for i in range(max_choices):
        print(f" {i+1}) {lines[i]}")

    while True:
        ch, code = get_single_key()
        if code == 27:
            print("\nMenu cancelled.")
            return None
        if ch.isdigit():
            n = int(ch)
            if 1 <= n <= max_choices:
                choice = lines[n - 1]
                print(f"\nYou selected: {choice}")
                return choice
        print("\nPress a valid number key or Esc: ", end="", flush=True)


def run_bash_command(cmd="echo hello from bash"):
    """
    Execute a shell command and stream its output to the terminal.
    """
    print(f"Executing shell command (streamed): {cmd}")
    subprocess.run(cmd, shell=True, check=False)


def capture_bash_output(cmd="ls -l /tmp"):
    """
    Capture stdout of a shell command and return it as a string.
    """
    try:
        output_bytes = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        output = output_bytes.decode("utf-8", errors="replace")
        print(f"Captured output of command: {cmd!r}")
        return output
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit {e.returncode}. Output:\n{e.output.decode('utf-8', errors='replace')}")
        return ""


def demonstrate_data_types():
    """
    Show common Python data types and their types using type().
    """
    an_int = 42
    a_float = 3.14159
    a_str = "sample"
    a_bool = True
    a_list = [1, 2, 3]
    a_tuple = ("a", "b")
    a_dict = {"key": "value"}
    a_none = None

    variables = {
        "an_int": an_int,
        "a_float": a_float,
        "a_str": a_str,
        "a_bool": a_bool,
        "a_list": a_list,
        "a_tuple": a_tuple,
        "a_dict": a_dict,
        "a_none": a_none,
    }
    print("\nData types and their values:")
    for name, val in variables.items():
        print(f" {name}: value={val!r}, type={type(val).__name__}")


GLOBAL_VAR = "I am global"


def demonstrate_scope():
    """
    Demonstrates local vs global scope and modifying a module-level var.
    """
    local_var = "I am local"

    def inner_without_global():
        GLOBAL_VAR = "modified in inner_without_global (local)"
        return GLOBAL_VAR

    def inner_with_global():
        global GLOBAL_VAR
        GLOBAL_VAR = "modified in inner_with_global (global)"
        return GLOBAL_VAR

    print("\nScope demonstration:")
    print(" Before calls, GLOBAL_VAR =", GLOBAL_VAR)
    print(" inner_without_global returns:", inner_without_global())
    print(" After inner_without_global, GLOBAL_VAR still =", GLOBAL_VAR)
    print(" inner_with_global returns:", inner_with_global())
    print(" After inner_with_global, GLOBAL_VAR now =", GLOBAL_VAR)
    print(" local_var remains accessible inside demonstrate_scope:", local_var)


def add(a, b):
    """Return the sum of a and b."""
    return a + b


def greet(name="World"):
    """Return a greeting for the given name."""
    return f"Hello, {name}!"


def demonstrate_functions():
    print("\nFunctions demonstration:")
    print(" add(2,3) =>", add(2, 3))
    print(" greet('Alice') =>", greet("Alice"))


def conditional_example(value):
    """
    Demonstrates if / elif / else with a numeric value.
    """
    if value < 0:
        print("Value is negative.")
    elif value == 0:
        print("Value is zero.")
    else:
        print("Value is positive.")


def demonstrate_imports():
    """
    Show how to detect/use optional third-party 'requests' library.
    """
    print("\nImports demonstration:")
    if HAS_REQUESTS:
        print("The 'requests' library is installed. Example: you could use requests.get(url).")
    else:
        print("The 'requests' library is NOT installed. Install with: pip install requests")
        print("Standard library alternative: urllib.request")


def marker_file_demo():
    """
    Demonstrate creating/detecting a marker file to branch logic.
    """
    if MARKER_FILE.exists():
        print(f"Marker file {MARKER_FILE} exists. Taking branch A.")
        captured = capture_bash_output("date")
        print("Date output captured (example):", captured.strip())
    else:
        print(f"Marker file {MARKER_FILE} does not exist. Creating it now and taking branch B.")
        MARKER_FILE.write_text("marker\n", encoding="utf-8")
        print(f"Created marker file {MARKER_FILE}")


def text_parsing_demo():
    """
    Perform text search, replace, movement and suffix operations on TMP_FILE.
    """
    print("\nText parsing and manipulation demo:")
    text = TMP_FILE.read_text(encoding="utf-8")
    print("File contents (before):")
    print("-" * 40)
    print(text.rstrip())
    print("-" * 40)

    if "apples" in text:
        print("Found substring 'apples' in file.")
    else:
        print("Did not find substring 'apples' in file.")

    if "bananas" in text:
        text = text.replace("bananas", "blueberries", 1)
        print("Replaced first occurrence of 'bananas' with 'blueberries'.")

    lines = text.splitlines()
    if lines and "Header" in lines[0]:
        lines[0] = "Header: " + lines[0].replace("Header", "").strip()
        print("Moved 'Header' to start of first line.")

    if len(lines) >= 2:
        if not lines[1].endswith(" -- END"):
            lines[1] = lines[1].rstrip() + " -- END"
            print("Appended marker to end of second line.")

    TMP_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("File contents (after):")
    print("-" * 40)
    print(TMP_FILE.read_text(encoding="utf-8").rstrip())
    print("-" * 40)


# ----------------------------- main flow ----------------------------------

def main():
    # Intro: show code that prints example_var and its value (setting was done at import)
    display_demo("code", "show the example_var value", "print('example_var currently contains:', example_var)", clear_before=True)
    # Show the effect (this would not execute the shown code snippet literally; we show the result)
    print("Result: example_var =", example_var)
    press_any_key()

    # Create initial file
    display_demo("code", "create the initial example file at /tmp", "write_initial_file()", clear_before=True)
    # this function prints output when it runs, so mark will_output=True
    write_initial_file()

    # Ask if user wants to edit the file (immediate key)
    display_demo("command", "ask whether to edit the example file now (press y/n)", "ask_yes_no('Would you like to edit the example file now? (y/n) ')", clear_before=True)
    try:
        if ask_yes_no("Would you like to edit the example file now? (y/n) "):
            # Prompt for a text line to append
            display_demo("command", "prompt for a line of text to append to the file", "user_text = ask_for_text('Please type a line to append to the file: ')", clear_before=True, )
            user_text = ask_for_text("Please type a line to append to the file: ")
            # Show what was set (assignment produces no stdout), then append
            print(f"Result: user_text = {user_text!r}")
            press_any_key()
            display_demo("code", "append the user's text to the example file", "append_text_to_file(user_text)")
            append_text_to_file(user_text)

            # Prompt to prepend a number to the second line
            display_demo("command", "prompt for an integer and prepend it to line 2", "prepend_number_to_second_line()", clear_before=True)
            prepend_number_to_second_line()
        else:
            # No output other than the decision; show it and pause
            print("Result: user chose not to edit the example file.")
            press_any_key()
    except KeyboardInterrupt:
        print("\nInterrupted by user; continuing with defaults.")
        press_any_key()

    # Inform user that editing steps are complete (this is a message/pause)
    display_demo("code", "inform the user and wait for a keypress", "press_any_key('Informing you: editing steps are complete. Press any key to continue...')", clear_before=True)
    press_any_key("Informing you: editing steps are complete. Press any key to continue...")

    # Menu selection from file
    display_demo("command", "display a menu built from /tmp/pyref_example.txt and wait for single-key selection", "choice = menu_from_file()", clear_before=True)
    choice = menu_from_file()
    if choice is None:
        print("Result: No menu choice selected.")
    else:
        print(f"Result: You chose: {choice}")
    press_any_key()

    # Execute a bash command (streamed)
    shell_cmd = "echo 'This is a shell command running from Python'; ls -l /tmp | head -n 3"
    display_demo("command", "execute a shell command and stream its output", shell_cmd, clear_before=True)
    run_bash_command(shell_cmd)
    press_any_key()

    # Capture bash output into a variable
    capture_cmd = "ls -1 /tmp | head -n 10"
    display_demo("command", "capture the output of a shell command into a Python variable", f"ls_output = capture_bash_output({capture_cmd!r})", clear_before=True)
    ls_output = capture_bash_output(capture_cmd)
    # Show the captured variable content (it may be multi-line)
    print("Result: ls_output (first 200 chars):")
    print(ls_output[:200].rstrip())
    press_any_key()

    # Demonstrate data types
    display_demo("code", "run the data types demonstration", "demonstrate_data_types()", clear_before=True)
    demonstrate_data_types()
    press_any_key()

    # Demonstrate variable scope
    display_demo("code", "run the scope demonstration", "demonstrate_scope()", clear_before=True)
    demonstrate_scope()
    press_any_key()

    # Demonstrate functions
    display_demo("code", "run the functions demonstration", "demonstrate_functions()", clear_before=True)
    demonstrate_functions()
    press_any_key()

    # Conditional example
    display_demo("command", "prompt for an integer and run an if/elif/else demo", "v = int(input(...)); conditional_example(v)", clear_before=True)
    try:
        v = int(input("Enter an integer for the conditional demo (e.g. -1, 0, 5): "))
    except Exception:
        v = 0
    conditional_example(v)
    press_any_key()

    # Imports demonstration
    display_demo("code", "demonstrate imports (requests detection)", "demonstrate_imports()", clear_before=True)
    demonstrate_imports()
    press_any_key()

    # Marker file demo
    display_demo("code", "demonstrate marker file creation/detection", "marker_file_demo()", clear_before=True)
    marker_file_demo()
    press_any_key()

    # Text parsing/manipulation demo
    display_demo("code", "run text parsing and manipulation demo on the example file", "text_parsing_demo()", clear_before=True)
    text_parsing_demo()
    press_any_key()

    # Cleanup prompt and possible removal
    display_demo("command", "ask whether to clean up example files (press y/n)", "ask_yes_no()", clear_before=True)
    try:
        if ask_yes_no("Demo complete. Clean up example files? (y/n) "):
            # Files removal does not print a long result; show what we removed
            if TMP_FILE.exists():
                TMP_FILE.unlink()
            if MARKER_FILE.exists():
                MARKER_FILE.unlink()
            print("Result: Example files removed.")
            press_any_key()
        else:
            print(f"Result: Files left in place: {TMP_FILE}, {MARKER_FILE}")
            press_any_key()
    except KeyboardInterrupt:
        print("\nInterrupted during cleanup prompt; leaving files in place.")
        press_any_key()

    print("Exiting pyref.py. Goodbye.")


if __name__ == "__main__":
    main()
