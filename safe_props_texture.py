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
    - Normalizes ObservableList/ObservableReferenceList into tuples
    - Ensures text_size and padding are always integer tuples
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
        if isinstance(ts, (ObservableList, list, tuple)):
            ts = tuple(ts)
        else:
            ts = (self.width if hasattr(self, "width") else 400, 0)

        if len(ts) != 2:
            _log_issue("text_size", self.text_size)
            ts = (self.width if hasattr(self, "width") else 400, 0)

        w, h = ts
        # Replace None with safe defaults and cast to int
        w = int(w) if w not in (None, 0) else int(self.width if hasattr(self, "width") else 400)
        h = int(h) if h is not None else 0
        self.text_size = (w, h)

        # --- PADDING ---
        pad = self.padding
        if isinstance(pad, (ObservableList, list, tuple)):
            pad = tuple(int(v) if v is not None else 0 for v in pad)
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
