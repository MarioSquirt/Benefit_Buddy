import os
import sys
import subprocess
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
# 🔧 Cross-Platform Asset Path Helper
# ===============================================================

IS_ANDROID = kivy_platform == "android"

def get_asset_path(path: str) -> str:
    """
    Return a safe path to an asset, handling Android redirection.
    Only normalizes known asset types: fonts, images, CSVs.
    """
    if not path:
        return path

    # Normalize separators
    path = path.replace("\\", "/")

    # On Android, try to redirect known paths
    if IS_ANDROID:
        # Remove known Windows prefixes
        for prefix in ["UC-Calc/", "BenefitBuddy/", "benefitbuddy/"]:
            if prefix in path:
                path = path.split(prefix, 1)[-1]
                break

        # Fonts
        if path.lower().endswith(".ttf") and not path.startswith("font/"):
            path = os.path.join("font", os.path.basename(path))

        # Images
        elif "images/" not in path and any(x in path.lower() for x in ["loading", "logo", "splash"]):
            path = os.path.join("images", os.path.basename(path))

        # Add fallback: resource_find first
        found = resource_find(path)
        if found:
            return found

        # Fallback: local relative path
        return os.path.join(os.getcwd(), path)

    # Desktop: just return original path
    return path

if IS_ANDROID:
    Logger.info("BenefitBuddy: Adding Android asset paths.")
    for folder in ["font", "images", "assets"]:
        resource_add_path(os.path.join(os.getcwd(), folder))

# ===============================================================
# ✅ Import main app logic
# ===============================================================
try:
    import benefit_calculator
except ImportError:
    Logger.error("BenefitBuddy: benefit_calculator.py not found!")
    print("Error: benefit_calculator.py not found!")
    sys.exit(1)

# ===============================================================
# 🔹 Splash Screen
# ===============================================================
class SplashScreen(App):
    """Animated GOV-themed splash screen before loading main app."""

    def build(self):
        Window.clearcolor = (29/255, 112/255, 184/255, 1)
        layout = BoxLayout(orientation='vertical', spacing=15, padding=60)

        # Logo
        logo_path = get_asset_path("images/logo.png")
        if os.path.exists(logo_path):
            logo = Image(source=logo_path, size_hint=(1, 0.5))
            layout.add_widget(logo)
        else:
            Logger.warning("BenefitBuddy: logo.png not found, skipping image.")

        # App name
        self.label = Label(
            text="Benefit Buddy",
            font_size="32sp",
            bold=True,
            color=(1, 1, 1, 1),
            size_hint=(1, 0.2)
        )
        layout.add_widget(self.label)

        # Subtext
        self.sub = Label(
            text="Checking benefit entitlements...",
            font_size="18sp",
            color=(1, 1, 1, 0.8),
            size_hint=(1, 0.15)
        )
        layout.add_widget(self.sub)

        # GOV yellow pulsing dot
        self.dot = Label(
            text="●",
            font_size="36sp",
            color=(1, 221/255, 0, 0.0),
            size_hint=(1, 0.15)
        )
        layout.add_widget(self.dot)

        # Animations
        anim = Animation(color=(1, 221/255, 0, 1), duration=0.6) + Animation(color=(1, 221/255, 0, 0.1), duration=0.6)
        anim.repeat_count = -1
        anim.start(self.dot)

        title_anim = Animation(color=(1, 1, 1, 0.7), duration=1.2) + Animation(color=(1, 1, 1, 1), duration=1.2)
        title_anim.repeat_count = -1
        title_anim.start(self.label)

        Clock.schedule_once(self.start_main_app, 3)
        return layout

    def start_main_app(self, *args):
        Logger.info("BenefitBuddy: Splash done, launching main app.")
        self.stop()
        # Directly run the main app logic
        benefit_calculator.BenefitBuddy().run()

# ===============================================================
# 🔹 Cross-Platform Launcher
# ===============================================================
def open_benefit_calculator():
    """Main entry point: splash then launch calculator."""

    if IS_ANDROID:
        Logger.info("BenefitBuddy: Launching on Android with splash.")
        SplashScreen().run()
        return

    # Desktop fallback
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    script_path = os.path.join(base_path, 'benefit_calculator.py')

    if not os.path.isfile(script_path):
        Logger.error("BenefitBuddy: benefit_calculator.py not found!")
        print("Error: benefit_calculator.py not found.")
        return

    try:
        system = sys.platform
        Logger.info(f"BenefitBuddy: Launching calculator on {system}")

        if system.startswith("win"):
            subprocess.Popen(f'start python "{script_path}"', shell=True)
        elif system in ["linux", "darwin"]:
            subprocess.Popen([sys.executable, script_path])
        else:
            subprocess.Popen([sys.executable, script_path])

    except Exception as e:
        Logger.exception(f"BenefitBuddy: Failed to launch calculator — {e}")
        print(f"An error occurred while launching the calculator: {e}")

# ===============================================================
# 🔹 Optional Test (for Android path redirection)
# ===============================================================
if IS_ANDROID:
    test_paths = [
        r"C:\Users\Kyle\UC-Calc\images\loading.png",
        r"C:\Users\Kyle\UC-Calc\font\roboto.ttf",
        r"C:\Users\Kyle\UC-Calc\pcode_brma_lookup.csv"
    ]
    for path in test_paths:
        fixed_path = get_asset_path(path)
        exists_after_patch = os.path.exists(fixed_path)
        Logger.info(f"BenefitBuddy TEST → {path}")
        Logger.info(f" ↳ redirected path: {fixed_path}")
        Logger.info(f" ↳ os.path.exists(): {exists_after_patch}")

# ===============================================================
# 🔹 Entry Point
# ===============================================================
if __name__ == "__main__":
    Logger.info("BenefitBuddy: Starting application.")
    open_benefit_calculator()
