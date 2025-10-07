import os
import sys
import subprocess
import platform
from kivy.logger import Logger


def open_benefit_calculator():
    """
    Launch the Benefit Buddy calculator.
    - On Android: runs the Kivy app directly.
    - On desktop: opens benefit_calculator.py in a new terminal window.
    """

    # Detect Android
    is_android = hasattr(sys, 'getandroidapilevel')

    if is_android:
        Logger.info("BenefitBuddy: Detected Android environment. Launching app directly.")
        try:
            import benefit_calculator
            benefit_calculator.BenefitBuddy().run()
        except ImportError:
            Logger.error("BenefitBuddy: 'benefit_calculator' module not found in package.")
        except Exception as e:
            Logger.exception(f"BenefitBuddy: Error running calculator on Android — {e}")
        return

    # Desktop / non-Android environments
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    script_path = os.path.join(base_path, 'benefit_calculator.py')

    if not os.path.isfile(script_path):
        Logger.error("BenefitBuddy: benefit_calculator.py not found.")
        print("Error: benefit_calculator.py not found.")
        return

    try:
        system = platform.system()
        Logger.info(f"BenefitBuddy: Launching calculator on {system}")

        if system == "Windows":
            subprocess.Popen(["start", "python", script_path], shell=True)

        elif system in ["Linux", "Darwin"]:  # Linux or macOS
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
            # Fallback for unknown systems
            subprocess.Popen([sys.executable, script_path])

    except Exception as e:
        Logger.exception(f"BenefitBuddy: Failed to launch calculator — {e}")
        print(f"An error occurred while launching the calculator: {e}")


if __name__ == "__main__":
    Logger.info("BenefitBuddy: Starting main launcher.")
    open_benefit_calculator()
