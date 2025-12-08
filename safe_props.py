# safe_props.py
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.uix.textinput import TextInput
from kivy.metrics import sp

# --- Label ---
_orig_label_init = Label.__init__
def _debug_label_init(self, **kwargs):
    if "font_size" in kwargs and isinstance(kwargs["font_size"], str):
        print(f"⚠️ Label font_size string detected: {kwargs['font_size']!r}")
        try:
            kwargs["font_size"] = sp(int(kwargs["font_size"].replace("sp", "")))
        except Exception:
            kwargs["font_size"] = sp(16)
    _orig_label_init(self, **kwargs)
Label.__init__ = _debug_label_init

# --- Spinner ---
_orig_spinner_init = Spinner.__init__
def _debug_spinner_init(self, **kwargs):
    if "font_size" in kwargs and isinstance(kwargs["font_size"], str):
        print(f"⚠️ Spinner font_size string detected: {kwargs['font_size']!r}")
        try:
            kwargs["font_size"] = sp(int(kwargs["font_size"].replace("sp", "")))
        except Exception:
            kwargs["font_size"] = sp(16)
    _orig_spinner_init(self, **kwargs)
Spinner.__init__ = _debug_spinner_init

# --- CheckBox ---
_orig_checkbox_init = CheckBox.__init__
def _debug_checkbox_init(self, **kwargs):
    # CheckBox doesn’t usually use font_size, but catch any numeric misuse
    for key in ("size_hint", "pos_hint"):
        if key in kwargs and isinstance(kwargs[key], str):
            print(f"⚠️ CheckBox {key} string detected: {kwargs[key]!r}")
            kwargs[key] = None  # safe fallback
    _orig_checkbox_init(self, **kwargs)
CheckBox.__init__ = _debug_checkbox_init

# --- TextInput ---
_orig_textinput_init = TextInput.__init__
def _debug_textinput_init(self, **kwargs):
    if "font_size" in kwargs and isinstance(kwargs["font_size"], str):
        print(f"⚠️ TextInput font_size string detected: {kwargs['font_size']!r}")
        try:
            kwargs["font_size"] = sp(int(kwargs["font_size"].replace("sp", "")))
        except Exception:
            kwargs["font_size"] = sp(16)
    _orig_textinput_init(self, **kwargs)
TextInput.__init__ = _debug_textinput_init
