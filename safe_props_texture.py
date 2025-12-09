# safe_props_texture.py
from kivy.uix.label import Label
from functools import wraps
from kivy.metrics import sp
from kivy.properties import ObservableList
import inspect

_orig_texture_update = Label.texture_update

@wraps(_orig_texture_update)
def texture_update(self, *args, **kwargs):
    """
    Wrapper around Label.texture_update that:
    - Normalizes ObservableList and list values into safe tuples
    - Ensures text_size and padding are always valid integers
    - Coerces invalid values into sane defaults
    - Logs only when values are genuinely invalid
    """

    def _t(val):
        try:
            return type(val).__name__
        except Exception:
            return "unknown"

    def _log_issue(prop_name, value):
        frame = inspect.currentframe().f_back
        info = inspect.getframeinfo(frame)
        print(
            f"⚠️ {self.__class__.__name__} text={getattr(self, 'text', None)!r} "
            f"{prop_name} adjusted from {value!r} (type={_t(value)}) "
            f"at {info.filename}:{info.lineno}"
        )

    try:
        # --- FONT SIZE ---
        if not isinstance(self.font_size, (int, float)):
            _log_issue("font_size", self.font_size)
            fs = str(self.font_size).strip()
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

        # --- TEXT SIZE ---
        ts = self.text_size
        if isinstance(ts, ObservableList):
            ts = tuple(ts)
        if not isinstance(ts, tuple) or len(ts) != 2:
            _log_issue("text_size", self.text_size)
            self.text_size = (self.width if hasattr(self, "width") else 400, 0)
        else:
            w, h = ts
            if w in (None, 0):
                w = self.width if hasattr(self, "width") else 400
            if h is None:
                h = 0
            self.text_size = (int(w), int(h))

        # --- PADDING ---
        pad = self.padding
        if isinstance(pad, ObservableList):
            pad = tuple(pad)
        if isinstance(pad, (list, tuple)):
            pad = tuple(int(v) for v in pad)
            if all(v == 0 for v in pad):
                _log_issue("padding", self.padding)
                self.padding = (10, 10)
            else:
                self.padding = pad
        else:
            _log_issue("padding", self.padding)
            self.padding = (10, 10)

        # --- LINE HEIGHT ---
        if not isinstance(self.line_height, (int, float)):
            _log_issue("line_height", self.line_height)
            try:
                self.line_height = float(self.line_height)
            except Exception:
                self.line_height = 1.0

    except Exception as e:
        print(f"⚠️ Error while coercing properties: {e}")

    return _orig_texture_update(self, *args, **kwargs)

Label.texture_update = texture_update
