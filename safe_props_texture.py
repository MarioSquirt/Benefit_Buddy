# safe_props_texture.py
from kivy.uix.label import Label
from functools import wraps
from kivy.metrics import sp
from kivy.properties import ObservableList
import inspect

# Some Kivy builds expose ObservableReferenceList via properties lists.
# We can’t import it directly everywhere, so handle generically.
def _as_tuple(value):
    # Normalize any Kivy list-like / sequences to a plain tuple
    try:
        if isinstance(value, (list, tuple, ObservableList)):
            return tuple(value)
        # Fallback: try iter(value) for other reactive lists (e.g., ObservableReferenceList)
        iter(value)  # raises TypeError if not iterable
        return tuple(value)
    except Exception:
        return None

def _to_int_safe(v, default=0):
    # Convert v to int if it’s numeric or numeric string; otherwise return default
    if v is None:
        return default
    try:
        if isinstance(v, (int, float)):
            return int(v)
        # Strings like "24", "24.0", "  24  " → 24
        s = str(v).strip()
        if s == "":
            return default
        return int(float(s))
    except Exception:
        return default

_orig_texture_update = Label.texture_update

@wraps(_orig_texture_update)
def texture_update(self, *args, **kwargs):
    """
    Wrapper around Label.texture_update that:
    - Unwraps any Kivy reactive list types into tuples
    - Ensures text_size and padding are integer tuples with safe defaults
    - Parses font_size strings (e.g., '20sp') and line_height reliably
    - Logs only when values are genuinely adjusted
    """

    def _t(val):
        try:
            return type(val).__name__
        except Exception:
            return "unknown"

    def _log_adjust(prop_name, value):
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
            _log_adjust("font_size", self.font_size)
            fs = str(self.font_size).strip()
            if fs.endswith("sp"):
                try:
                    self.font_size = sp(int(float(fs[:-2])))
                except Exception:
                    self.font_size = sp(16)
            else:
                try:
                    self.font_size = sp(int(float(fs)))
                except Exception:
                    self.font_size = sp(16)

        # --- TEXT SIZE ---
        raw_ts = self.text_size
        ts = _as_tuple(raw_ts)
        if ts is None or len(ts) != 2:
            _log_adjust("text_size", raw_ts)
            safe_w = _to_int_safe(getattr(self, "width", None), default=400)
            self.text_size = (safe_w, 0)
        else:
            w, h = ts
            safe_w = _to_int_safe(w, default=_to_int_safe(getattr(self, "width", None), default=400))
            safe_h = _to_int_safe(h, default=0)
            # If width ends up 0, use widget width or 400
            if safe_w == 0:
                safe_w = _to_int_safe(getattr(self, "width", None), default=400)
            self.text_size = (safe_w, safe_h)

        # --- PADDING ---
        raw_pad = self.padding
        pad = _as_tuple(raw_pad)
        if pad is None:
            _log_adjust("padding", raw_pad)
            self.padding = (10, 10)
        else:
            # Coerce each element safely; support 2 or 4 values
            coerced = tuple(_to_int_safe(v, default=0) for v in pad)
            if len(coerced) not in (2, 4):
                _log_adjust("padding", raw_pad)
                self.padding = (10, 10)
            else:
                if all(v == 0 for v in coerced):
                    _log_adjust("padding", raw_pad)
                    self.padding = (10, 10)
                else:
                    self.padding = coerced

        # --- LINE HEIGHT ---
        if not isinstance(self.line_height, (int, float)):
            _log_adjust("line_height", self.line_height)
            try:
                self.line_height = float(str(self.line_height).strip())
            except Exception:
                self.line_height = 1.0

    except Exception as e:
        print(f"⚠️ Error while coercing properties: {e}")

    return _orig_texture_update(self, *args, **kwargs)

Label.texture_update = texture_update
