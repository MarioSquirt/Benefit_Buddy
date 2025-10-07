import os
import sys
import platform
import subprocess
from kivy.logger import Logger
from kivy.app import App
from kivy.uix.label import Label

# ✅ Force import early so Buildozer includes the file
import benefit_calculator


class SplashScreen(App):
    """Simple splash screen shown while the main app loads"""
    def build(self):
        return Label(text="Loading Benefit Buddy…", font_size="22sp", halign="center")


def open_benefit_calculator():
    """Launch the Benefit Buddy calculator — works on Android and desktop."""

    # Detect Android
    is_android = hasattr(sys, 'getandroidapilevel')

    if is_android:
        Logger.info("BenefitBuddy: Detected Android environment. Launching app directly.")
        try:
            SplashScreen().run()  # Show loading screen
            benefit_calculator.BenefitBuddy().run()
        except Exception as e:
            Logger.exception(f"BenefitBuddy: Error running calculator on Android — {e}")
        return

    # For desktop or packaged apps
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
        Logger.exception(f"BenefitBuddy: Failed to launch calculator — {e}")
        print(f"An error occurred while launching the calculator: {e}")


if __name__ == "__main__":
    Logger.info("BenefitBuddy: Starting main launcher.")
    open_benefit_calculator()
