import os
import sys
import subprocess
import builtins
from kivy.logger import Logger
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.utils import platform as kivy_platform
from kivy.resources import resource_find, resource_add_path

# ===============================================================
# 🔧 Universal Path Redirection Patch (handles Windows → Android)
# ===============================================================

IS_ANDROID = kivy_platform == "android"

if IS_ANDROID:
    Logger.info("BenefitBuddy: Applying Android path redirection patch.")

    # Add known asset folders to Kivy search path
    for folder in ["font", "images", "assets"]:
        resource_add_path(os.path.join(os.getcwd(), folder))

    _orig_open = builtins.open
    _orig_exists = os.path.exists
    _orig_listdir = os.listdir

    def fix_path(path):
        """Redirect Windows paths to Android relative asset paths."""
        if not path:
            return path

        # Normalize path separators
        path = path.replace("\\", "/")

        # Remove known prefixes from Windows/PC paths
        for prefix in [
            "UC-Calc/",
            "BenefitBuddy/",
            "benefitbuddy/",
            "/data/user/0/mariosquirt.benefitbuddy.benefitbuddy/files/app/",
        ]:
            if prefix in path:
                path = path.split(prefix, 1)[-1]
                break

        # Handle fonts
        if path.lower().endswith(".ttf") and not path.startswith("font/"):
            path = "font/" + os.path.basename(path)

        # Handle images
        elif "images/" not in path and any(x in path.lower() for x in ["loading", "logo", "splash"]):
            path = "images/" + os.path.basename(path)

        # Check resource_find first
        found = resource_find(path)
        if found:
            return found

        # Fallback: local relative path
        return os.path.join(os.getcwd(), path)

    # Patch built-in open
    def open_patched(file, *args, **kwargs):
        new_file = fix_path(file)
        if new_file != file:
            Logger.info(f"BenefitBuddy: Redirecting file → {new_file}")
        return _orig_open(new_file, *args, **kwargs)

    builtins.open = open_patched

    # Patch os.path.exists
    os.path.exists = lambda path: _orig_exists(fix_path(path))

    # Patch os.listdir
    def listdir_patched(path):
        return _orig_listdir(fix_path(path))
    os.listdir = listdir_patched

    Logger.info("BenefitBuddy: Path redirection patch active.")

# ===============================================================
# ✅ Import main app logic
# ===============================================================
import benefit_calculator


class SplashScreen(App):
    """Animated GOV-themed splash screen before loading main app."""

    def build(self):
        Window.clearcolor = (29/255, 112/255, 184/255, 1)
        layout = BoxLayout(orientation='vertical', spacing=15, padding=60)

        # ✅ App logo (redirected automatically)
        logo_path = os.path.join("images", "logo.png")
        if os.path.exists(logo_path):
            logo = Image(source=logo_path, size_hint=(1, 0.5))
            layout.add_widget(logo)
        else:
            Logger.warning("BenefitBuddy: logo.png not found, skipping image.")

        # ✅ App name
        self.label = Label(
            text="Benefit Buddy",
            font_size="32sp",
            bold=True,
            color=(1, 1, 1, 1),
            size_hint=(1, 0.2)
        )
        layout.add_widget(self.label)

        # ✅ Animated subtext
        self.sub = Label(
            text="Checking benefit entitlements...",
            font_size="18sp",
            color=(1, 1, 1, 0.8),
            size_hint=(1, 0.15)
        )
        layout.add_widget(self.sub)

        # ✅ GOV yellow pulsing dot
        self.dot = Label(
            text="●",
            font_size="36sp",
            color=(1, 221/255, 0, 0.0),
            size_hint=(1, 0.15)
        )
        layout.add_widget(self.dot)

        anim = Animation(color=(1, 221/255, 0, 1), duration=0.6) + Animation(color=(1, 221/255, 0, 0.1), duration=0.6)
        anim.repeat = True
        anim.start(self.dot)

        title_anim = Animation(color=(1, 1, 1, 0.7), duration=1.2) + Animation(color=(1, 1, 1, 1), duration=1.2)
        title_anim.repeat = True
        title_anim.start(self.label)

        Clock.schedule_once(self.start_main_app, 3)
        return layout

    def start_main_app(self, *args):
        Logger.info("BenefitBuddy: Splash done, launching main app.")
        self.stop()
        benefit_calculator.BenefitBuddy().run()


def open_benefit_calculator():
    """Main entry point: splash then launch calculator."""
    is_android = hasattr(sys, 'getandroidapilevel')

    if is_android:
        Logger.info("BenefitBuddy: Launching on Android with GOV splash.")
        SplashScreen().run()
        return

    # Desktop fallback
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    script_path = os.path.join(base_path, 'benefit_calculator.py')

    if not os.path.isfile(script_path):
        Logger.error("BenefitBuddy: benefit_calculator.py not found.")
        print("Error: benefit_calculator.py not found.")
        return

    try:
        system = sys.platform
        Logger.info(f"BenefitBuddy: Launching calculator on {system}")

        if system.startswith("win"):
            subprocess.Popen(["start", "python", script_path], shell=True)
        elif system in ["linux", "darwin"]:
            subprocess.Popen(["python3", script_path])
        else:
            subprocess.Popen([sys.executable, script_path])
    except Exception as e:
        Logger.exception(f"BenefitBuddy: Failed to launch calculator — {e}")
        print(f"An error occurred while launching the calculator: {e}")


# ===============================================================
# 🔍 Quick Test: Verify path redirection works (for debugging)
# ===============================================================
if IS_ANDROID:
    test_paths = [
        r"C:\Users\Kyle\UC-Calc\images\loading.png",
        r"C:\Users\Kyle\UC-Calc\font\roboto.ttf",
        r"C:\Users\Kyle\UC-Calc\pcode_brma_lookup.csv"
    ]

    for path in test_paths:
        fixed_path = path.replace("\\", "/")
        from os.path import exists
        found = resource_find(fixed_path)
        exists_after_patch = exists(fixed_path)
        Logger.info(f"BenefitBuddy TEST → {path}")
        Logger.info(f" ↳ resource_find: {found}")
        Logger.info(f" ↳ os.path.exists(): {exists_after_patch}")


if __name__ == "__main__":
    Logger.info("BenefitBuddy: Starting with GOV splash.")
    open_benefit_calculator()
