import safe_props  # enables runtime safety nets globally
import safe_props_texture  # enables runtime logging for Label.texture_update

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
# 🏁 Entry Point
# ===============================================================
if __name__ == "__main__":
    Logger.info("BenefitBuddy: Starting application.")
    benefit_calculator.BenefitBuddy().run()   # ✅ run your main App class, not a bare function



