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
# 🔧 Cross-Platform Asset Setup
# ===============================================================

IS_ANDROID = kivy_platform == "android"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Register folders so Kivy can find assets on all OS
for folder in ["data", "images", "font", "assets"]:
    full_path = os.path.join(BASE_DIR, folder)
    if os.path.exists(full_path):
        resource_add_path(full_path)
        Logger.info(f"BenefitBuddy: Added resource path → {full_path}")


def get_asset_path(filename: str) -> str:
    """Return an absolute path for assets, working cross-platform."""
    if not filename:
        return ""

    filename = filename.replace("\\", "/")
    found = resource_find(filename)
    if found:
        return found

    local_path = os.path.join(BASE_DIR, filename)
    if os.path.exists(local_path):
        return local_path

    Logger.warning(f"BenefitBuddy: Missing asset → {filename}")
    return filename


# ===============================================================
# ✅ Import the main app logic
# ===============================================================
try:
    import benefit_calculator
except ImportError:
    Logger.error("BenefitBuddy: benefit_calculator.py not found!")
    print("❌ Error: benefit_calculator.py not found!")
    sys.exit(1)


# ===============================================================
# 🌟 Splash Screen
# ===============================================================
class SplashScreen(App):
    """Animated GOV-themed splash screen before launching main app."""

    def build(self):
        Window.clearcolor = (29 / 255, 112 / 255, 184 / 255, 1)
        layout = BoxLayout(orientation="vertical", spacing=15, padding=60)

        # Logo
        logo_path = get_asset_path("images/logo.png")
        if os.path.exists(logo_path):
            logo = Image(source=logo_path, size_hint=(1, 0.5))
            layout.add_widget(logo)
        else:
            Logger.warning("BenefitBuddy: logo.png missing.")

        # App name
        self.label = Label(
            text="Benefit Buddy",
            font_size="32sp",
            bold=True,
            color=(1, 1, 1, 1),
            size_hint=(1, 0.2),
        )
        layout.add_widget(self.label)

        # Subtext
        self.sub = Label(
            text="Checking benefit entitlements...",
            font_size="18sp",
            color=(1, 1, 1, 0.8),
            size_hint=(1, 0.15),
        )
        layout.add_widget(self.sub)

        # Pulsing GOV yellow dot
        self.dot = Label(
            text="●",
            font_size="36sp",
            color=(1, 221 / 255, 0, 0.0),
            size_hint=(1, 0.15),
        )
        layout.add_widget(self.dot)

        # Animations
        anim1 = Animation(color=(1, 221 / 255, 0, 1), duration=0.6)
        anim1.repeat = True   # ✅ property, not method
        anim1.start(self.dot)

        anim2 = Animation(color=(1, 1, 1, 0.7), duration=1.2)
        anim2.repeat = True   # ✅ property, not method
        anim2.start(self.label)

        # Continue to main app after delay
        Clock.schedule_once(self.start_main_app, 3)
        return layout

    def start_main_app(self, *args):
        Logger.info("BenefitBuddy: Splash complete → launching BenefitBuddy app.")
        self.stop()
        benefit_calculator.BenefitBuddy().run()

# ===============================================================
# 🏁 Entry Point
# ===============================================================
if __name__ == "__main__":
    Logger.info("BenefitBuddy: Starting application.")
    BenefitBuddyApp().run()   # ✅ run your main App class, not a bare function
