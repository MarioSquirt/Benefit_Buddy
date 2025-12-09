# safe_props_texture.py
from kivy.uix.label import Label
from functools import wraps
from kivy.metrics import sp
import inspect

_orig_texture_update = Label.texture_update

@wraps(_orig_texture_update)
def texture_update(self, *args, **kwargs):
    """
    Wrapper around Label.texture_update that:
    - Detects string values in numeric properties
    - Coerces them into safe numeric defaults
    - Logs widget class, text, offending value, and source location for debugging
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
            f"{prop_name} string {value!r} (type={_t(value)}) "
            f"at {info.filename}:{info.lineno}"
        )

    try:
        # font_size
        if isinstance(self.font_size, str):
            _log_issue("font_size", self.font_size)
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
        if isinstance(self.text_size, str):
            _log_issue("text_size", self.text_size)
            try:
                parts = [int(p) for p in self.text_size.replace(',', ' ').split()]
                if len(parts) == 2:
                    self.text_size = tuple(parts)
                else:
                    self.text_size = (0, 0)
            except Exception:
                self.text_size = (0, 0)

        # padding
        if isinstance(self.padding, str):
            _log_issue("padding", self.padding)
            try:
                parts = [int(p) for p in self.padding.replace(',', ' ').split()]
                if len(parts) in (2, 4):
                    self.padding = tuple(parts)
                else:
                    self.padding = (0, 0)
            except Exception:
                self.padding = (0, 0)

        # line_height
        if isinstance(self.line_height, str):
            _log_issue("line_height", self.line_height)
            try:
                self.line_height = float(self.line_height)
            except Exception:
                self.line_height = 1.0

    except Exception as e:
        print(f"⚠️ Error while coercing properties: {e}")

    return _orig_texture_update(self, *args, **kwargs)

Label.texture_update = texture_update
