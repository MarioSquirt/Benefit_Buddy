# safe_props.py
from kivy.uix.label import Label
from kivy.metrics import sp

# Keep original __init__ for Label
_orig_init = Label.__init__

def _debug_init(self, **kwargs):
    # Check risky properties at construction
    for key in ("font_size", "text_size", "line_height", "padding", "letter_spacing"):
        if key in kwargs and isinstance(kwargs[key], str):
            print(f"⚠️ Runtime warning: {key} received a string value {kwargs[key]!r}")
            # Default to safe fallback
            if key == "font_size":
                try:
                    kwargs[key] = sp(int(kwargs[key].replace("sp", "")))
                except Exception:
                    kwargs[key] = sp(16)
            elif key in ("text_size", "padding"):
                kwargs[key] = (0, 0)  # safe tuple fallback
            elif key == "line_height":
                kwargs[key] = 1.0
            elif key == "letter_spacing":
                kwargs[key] = 0.0

    _orig_init(self, **kwargs)

# Monkey‑patch Label globally
Label.__init__ = _debug_init
