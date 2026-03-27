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
from kivy.metrics import sp
from kivy.properties import ObservableList
from kivy.utils import get_color_from_hex
Window.clearcolor = get_color_from_hex("#005EA5")

# === DEBUG: Inspect packaged filesystem on device ===
# Android-safe root path
try:
    from android.storage import app_storage_path
    app_root = app_storage_path()
except ImportError:
    # Desktop fallback
    app_root = os.path.dirname(os.path.abspath(__file__))

Logger.info(f"BenefitBuddy: APK root = {app_root}")

# Safely list root contents
try:
    Logger.info(f"BenefitBuddy: APK root contents = {os.listdir(app_root)}")
except Exception as e:
    Logger.error(f"BenefitBuddy: Could not list APK root: {e}")

# Check app_data
app_data_path = os.path.join(app_root, "app_data")
Logger.info(f"BenefitBuddy: app_data exists = {os.path.exists(app_data_path)}")
if os.path.exists(app_data_path):
    try:
        Logger.info(f"BenefitBuddy: app_data contents = {os.listdir(app_data_path)}")
    except Exception as e:
        Logger.error(f"BenefitBuddy: Could not list app_data: {e}")

# Check postcodes folder
postcodes_path = os.path.join(app_data_path, "postcodes")
Logger.info(f"BenefitBuddy: postcodes exists = {os.path.exists(postcodes_path)}")
if os.path.exists(postcodes_path):
    try:
        Logger.info(f"BenefitBuddy: postcodes contents = {os.listdir(postcodes_path)}")
    except Exception as e:
        Logger.error(f"BenefitBuddy: Could not list postcodes: {e}")

# Register resource paths
resource_add_path(app_data_path)
resource_add_path(postcodes_path)
Logger.info(f"BenefitBuddy: Added resource path → {app_data_path}")
Logger.info(f"BenefitBuddy: Added resource path → {postcodes_path}")

# ===============================================================
# 🛡️ SafeLabel wrapper
# ===============================================================
class SafeLabel(Label):
    def __init__(self, **kwargs):
        # --- FONT SIZE ---
        fs = kwargs.get("font_size", 16)
        if isinstance(fs, str):
            try:
                fs = fs.strip().replace("sp", "")
                kwargs["font_size"] = sp(int(fs))
            except Exception:
                kwargs["font_size"] = sp(16)
        elif isinstance(fs, (int, float)):
            kwargs["font_size"] = sp(fs)
        else:
            kwargs["font_size"] = sp(16)

        # --- TEXT SIZE ---
        ts = kwargs.get("text_size", None)
        if isinstance(ts, str):
            kwargs["text_size"] = (Window.width - 60, None)
        elif isinstance(ts, ObservableList):
            ts = tuple(ts)
            if ts in [(None, None), (0, 0)]:
                kwargs["text_size"] = (Window.width - 60, None)
            else:
                kwargs["text_size"] = ts
        elif isinstance(ts, (list, tuple)):
            ts = tuple(ts)
            if ts in [(None, None), (0, 0)]:
                kwargs["text_size"] = (Window.width - 60, None)
            else:
                kwargs["text_size"] = ts
        else:
            kwargs["text_size"] = (Window.width - 60, None)

        # --- PADDING ---
        pad = kwargs.get("padding", None)
        if isinstance(pad, str) or pad in [(0, 0), (0, 0, 0, 0), None]:
            kwargs["padding"] = (10, 10)
        elif isinstance(pad, ObservableList):
            pad = tuple(pad)
            if all(v == 0 for v in pad):
                kwargs["padding"] = (10, 10)
            else:
                kwargs["padding"] = pad
        elif isinstance(pad, (list, tuple)):
            kwargs["padding"] = tuple(pad)
        else:
            kwargs["padding"] = (10, 10)

        super().__init__(**kwargs)

        # 🔑 Bind text_size dynamically to widget width and window resize
        self.bind(width=self._update_text_size)
        Window.bind(size=lambda *_: self._update_text_size())

    def _update_text_size(self, *args):
        # Always keep text_size tied to current width
        self.text_size = (self.width - 20, None)

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
    benefit_calculator.BenefitBuddy().run()   # ✅ run your main App class


