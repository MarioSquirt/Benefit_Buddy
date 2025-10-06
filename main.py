import os
import sys
import subprocess
import platform

def open_benefit_calculator():
    # Handle both normal runs and packaged (PyInstaller/Buildozer) runs
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    script_path = os.path.join(base_path, 'benefit_calculator.py')

    if not os.path.isfile(script_path):
        print("Error: benefit_calculator.py not found.")
        return

    try:
        system = platform.system()

        if system == "Windows":
            # Open in a new Command Prompt window
            subprocess.Popen(["start", "python", script_path], shell=True)

        elif system in ["Linux", "Darwin"]:  # Darwin = macOS
            # Try to open in a new terminal window
            terminals = [
                "x-terminal-emulator",
                "gnome-terminal",
                "konsole",
                "lxterminal",
                "xfce4-terminal",
                "xterm",
                "termux-open"  # For Termux / Android environments
            ]

            for term in terminals:
                if subprocess.call(["which", term], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
                    subprocess.Popen([term, "-e", f"python3 {script_path}"])
                    break
            else:
                # Fallback: just run it in the current process
                subprocess.Popen(["python3", script_path])

        else:
            # Unknown OS – fallback
            subprocess.Popen([sys.executable, script_path])

    except Exception as e:
        print(f"An error occurred while launching the calculator: {e}")

if __name__ == "__main__":
    open_benefit_calculator()
