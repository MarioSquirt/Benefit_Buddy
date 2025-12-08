# safe_props_texture.py
from kivy.uix.label import Label

# Keep original texture_update
_orig_texture_update = Label.texture_update

def _debug_texture_update(self, *args, **kwargs):
    try:
        # Check risky properties before calling the original method
        if isinstance(self.font_size, str):
            print(f"⚠️ Crash risk: Label {self} has font_size string {self.font_size!r}")
        if isinstance(self.text_size, str):
            print(f"⚠️ Crash risk: Label {self} has text_size string {self.text_size!r}")
        if isinstance(self.line_height, str):
            print(f"⚠️ Crash risk: Label {self} has line_height string {self.line_height!r}")
        if isinstance(self.padding, str):
            print(f"⚠️ Crash risk: Label {self} has padding string {self.padding!r}")
        if isinstance(self.letter_spacing, str):
            print(f"⚠️ Crash risk: Label {self} has letter_spacing string {self.letter_spacing!r}")
    except Exception as e:
        print(f"⚠️ Error while checking Label properties: {e}")

    # Call the original method
    return _orig_texture_update(self, *args, **kwargs)

# Monkey‑patch globally
Label.texture_update = _debug_texture_update
