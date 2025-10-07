import os
import sys
import subprocess
import platform

def open_benefit_calculator():
    # Detect Android environment
    is_android = hasattr(sys, 'getandroidapilevel')

    if is_android:
        # On Android, import and run directly (no subprocess)
        try:
            import benefit_calculator
            benefit_calculator.run_calculator()  # assuming you have a run_calculator() function
        except ImportError:
            print("Error: benefit_calculator module not found in package.")
        except Exception as e:
            print(f"An error occurred while running the calculator: {e}")
        return

    # Desktop or normal OS
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    script_path = os.path.join(base_path, 'benefit_calculator.py')

    if not os.path.isfile(script_path):
        print("Error: benefit_calculator.py not found.")
        return

    try:
        system = platform.system()

        if system == "Windows":
            subprocess.Popen(["start", "python", script_path], shell=True)

        elif system in ["Linux", "Darwin"]:
            terminals = [
                "x-terminal-emulator", "gnome-terminal", "konsole",
                "lxterminal", "xfce4-terminal", "xterm"
            ]
            for term in terminals:
                if subprocess.call(["which", term], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
                    subprocess.Popen([term, "-e", f"python3 {script_path}"])
                    break
            else:
                subprocess.Popen(["python3", script_path])

        else:
            subprocess.Popen([sys.executable, script_path])

    except Exception as e:
        print(f"An error occurred while launching the calculator: {e}")


if __name__ == "__main__":
    open_benefit_calculator()
