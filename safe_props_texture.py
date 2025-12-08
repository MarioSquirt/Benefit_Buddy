# safe_props_texture.py
from kivy.uix.label import Label
from functools import wraps

# Keep original method
_orig_texture_update = Label.texture_update

# Important: the wrapper must be named 'texture_update'
@wraps(_orig_texture_update)
def texture_update(self, *args, **kwargs):
    # Pre-flight checks — log risky string values
    try:
        if isinstance(self.font_size, str):
            print(f"⚠️ Crash risk: Label {self} font_size is string {self.font_size!r}")
        if isinstance(self.text_size, str):
            print(f"⚠️ Crash risk: Label {self} text_size is string {self.text_size!r}")
        if isinstance(self.line_height, str):
            print(f"⚠️ Crash risk: Label {self} line_height is string {self.line_height!r}")
        if isinstance(self.padding, str):
            print(f"⚠️ Crash risk: Label {self} padding is string {self.padding!r}")
        if isinstance(self.letter_spacing, str):
            print(f"⚠️ Crash risk: Label {self} letter_spacing is string {self.letter_spacing!r}")
    except Exception as e:
        print(f"⚠️ Error while checking Label properties: {e}")

    # Delegate to original
    return _orig_texture_update(self, *args, **kwargs)

# Monkey-patch with a wrapper whose __name__ is 'texture_update'
Label.texture_update = texture_update
