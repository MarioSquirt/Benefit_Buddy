# safe_props_texture.py
from kivy.uix.label import Label
from functools import wraps
from kivy.metrics import sp

_orig_texture_update = Label.texture_update

@wraps(_orig_texture_update)
def texture_update(self, *args, **kwargs):
    # Inspect types before render
    def _t(val):
        try:
            return type(val).__name__
        except Exception:
            return "unknown"

    try:
        # font_size
        if hasattr(self, "font_size") and isinstance(self.font_size, str):
            print(f"⚠️ Label {self} font_size string {self.font_size!r} (type={_t(self.font_size)}) text={self.text!r}")
            # Coerce common cases once
            fs = self.font_size.strip()
            if fs.endswith("sp"):
                try:
                    self.font_size = sp(int(fs[:-2]))
                except Exception:
                    self.font_size = sp(16)
            else:
                try:
                    self.font_size = sp(int(fs))
                except Exception:
                    self.font_size = sp(16)

        # text_size
        if hasattr(self, "text_size") and isinstance(self.text_size, str):
            print(f"⚠️ Label {self} text_size string {self.text_size!r} (type={_t(self.text_size)}) text={self.text!r}")
            self.text_size = (0, 0)

        # padding
        if hasattr(self, "padding") and isinstance(self.padding, str):
            print(f"⚠️ Label {self} padding string {self.padding!r} (type={_t(self.padding)})")
            self.padding = (0, 0)

        # line_height
        if hasattr(self, "line_height") and isinstance(self.line_height, str):
            print(f"⚠️ Label {self} line_height string {self.line_height!r} (type={_t(self.line_height)})")
            self.line_height = 1.0

    except Exception as e:
        print(f"⚠️ Error while checking properties: {e}")

    return _orig_texture_update(self, *args, **kwargs)

Label.texture_update = texture_update
