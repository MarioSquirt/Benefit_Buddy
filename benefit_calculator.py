#BenefitCalculator.py


# import necessary libraries

# --- Kivy core ---
from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.core.window import Window
Window.softinput_mode = "below_target"
from kivy.core.image import Image as CoreImage
from kivy.metrics import sp
from kivy.utils import get_color_from_hex
from kivy.resources import resource_add_path, resource_find
from kivy.properties import ObservableList, StringProperty

# --- Kivy UI widgets/layouts ---
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.widget import Widget
from kivy.uix.checkbox import CheckBox
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup  # type: ignore
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem, TabbedPanelHeader
from kivy.uix.scrollview import ScrollView
from kivy.uix.behaviors import ButtonBehavior

# --- Kivy graphics/animation ---
from kivy.graphics import Color, Ellipse, Line, RoundedRectangle, Rectangle
from kivy.animation import Animation

# --- Project-specific ---
from main import SafeLabel

# --- Standard library ---
import os
import sys
import csv
import tracemalloc
from datetime import datetime



UC_RATES = {
    "year": "2025/26",

    "standard_allowance": {
        "single_u25": 316.98,
        "single_25plus": 400.14,
        "couple_u25": 497.55,
        "couple_25plus": 628.10,
        "minimum_amount": 0.01,
    },

    "child_element": {
        # First child born before 6 April 2017
        "first_child_pre2017": 339.00,
        # First child born on/after 6 April 2017, and subsequent children where allowed
        "child": 292.81,
    },

    "disabled_child": {
        "lower": 158.76,
        "higher": 495.87,
    },

    "lcw_lcwra": {
        "lcw": 158.76,
        "lcwra": 423.27,
    },

    "carer_element": 201.68,

    "childcare": {
        "reimbursement_rate": 0.85,
        "cap_one_child": 1031.88,
        "cap_two_plus": 1768.94,
    },

    "non_dependant": {
        "housing_cost_contribution": 93.02,
    },

    "work_allowance": {
        # Higher = no housing element, with children or LCW/LCWRA
        "higher": 684.00,
        # Lower = with housing element, with children or LCW/LCWRA
        "lower": 411.00,
    },

    "taper_rate": 0.55,

    "capital": {
        "lower_limit": 6000.00,
        "upper_limit": 16000.00,
        "tariff_per_250": 4.35,
    },

    # You can expand these if you later model daily sanction maths explicitly
    "sanctions": {
        "daily_100": {
            "single_u25": 10.40,
            "single_25plus": 13.10,
            "joint_u25": 8.10,
            "joint_25plus": 10.30,
        },
        "daily_40": {
            "single_u25": 4.10,
            "single_25plus": 5.20,
            "joint_u25": 3.20,
            "joint_25plus": 4.10,
        },
    },

    "deduction_caps": {
        "third_party_5pct": {
            "single_u25": 15.85,
            "single_25plus": 20.01,
            "joint_u25": 24.88,
            "joint_25plus": 31.41,
        },
        "rent_min_10pct": {
            "single_u25": 31.70,
            "single_25plus": 40.01,
            "joint_u25": 49.76,
            "joint_25plus": 62.81,
        },
        "rent_max_15pct": {
            "single_u25": 47.55,
            "single_25plus": 60.02,
            "joint_u25": 74.63,
            "joint_25plus": 94.22,
        },
        "overall_max_15pct": {
            "single_u25": 47.55,
            "single_25plus": 60.02,
            "joint_u25": 74.63,
            "joint_25plus": 94.22,
        },
    },

    "child_maintenance_deduction": 36.40,

    "transitional_sdp": {
        "lcwra_included": 143.37,
        "lcwra_not_included": 340.50,
        "joint_higher": 483.88,
        "extra_edp_single": 91.15,
        "extra_edp_couple": 130.22,
        "extra_dp_single": 186.64,
        "extra_dp_couple": 266.94,
        "extra_disabled_children": 192.07,
    },
}



def with_diagnostics(widget_names=None):
    """
    Decorator that injects automatic diagnostics into any Screen.
    widget_names: list of attribute names to check when the screen is opened.
    """
    widget_names = widget_names or []

    def decorator(cls):
        original_on_pre_enter = getattr(cls, "on_pre_enter", None)

        def new_on_pre_enter(self, *args, **kwargs):
            # Run original on_pre_enter if it exists
            if original_on_pre_enter:
                original_on_pre_enter(self, *args, **kwargs)

            print(f"\n=== Diagnostics for {cls.__name__} ===")

            for name in widget_names:
                widget = getattr(self, name, None)
                if widget is None:
                    print(f"  ✖ {name}: NOT FOUND")
                else:
                    print(f"  ✔ {name}: OK")

            print(f"=== End Diagnostics for {cls.__name__} ===\n")

        setattr(cls, "on_pre_enter", new_on_pre_enter)
        return cls

    return decorator


ICON_PATHS = {
    "Introduction": "images/icons/Introduction-icon/Introduction-32px.png",
    "Claimant Details": "images/icons/ClaimantDetails-icon/ClaimantDetails-32px.png",
    "Finances": "images/icons/Finances-icon/Finances-32px.png",
    "Housing": "images/icons/Housing-icon/Housing-32px.png",
    "Children": "images/icons/Children-icon/Children-32px.png",
    "Additional Elements": "images/icons/AdditionalElements-icon/AdditionalElements-32px.png",
    "Sanctions": "images/icons/Sanctions-icon/Sanctions-32px.png",
    "Advanced Payments": "images/icons/AdvancedPayment-icon/AdvancedPayment-32px.png",
    "Summary": "images/icons/Summary-icon/Summary-32px.png",
}


# --- Register base paths for resources ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Add folders to Kivy's resource search paths
for folder in ["images", "font", ".venv"]:
    full_path = os.path.join(BASE_DIR, folder)
    if os.path.exists(full_path):
        resource_add_path(full_path)


# Define GOV.UK colour scheme
GOVUK_BLUE = "#005EA5"
WHITE = "#FFFFFF"
YELLOW = "#FFDD00"

# Convert hex color to RGBA
color = get_color_from_hex("#005EA5")  # GOVUK_BLUE

# Set the background color of the app to GOVUK_BLUE
Window.clearcolor = get_color_from_hex("#005EA5")  # GOVUK_BLUE

layout = BoxLayout(orientation="vertical", spacing=10, padding=20, size_hint=(1,1))
if hasattr(Window, "maximize"):
    Window.maximize()

# Bind the window size to adjust the layout dynamically
def adjust_layout(instance, value):
    for widget in instance.children:
        if isinstance(widget, BoxLayout) and widget.size_hint == (1, 1):
            widget.size = (Window.width, Window.height)

Window.bind(size=adjust_layout)

# Helper function to create a label that wraps text within the window width
def wrapped_SafeLabel(text, font_size, height):
    label = SafeLabel(
        text=text,
        font_size=font_size,
        halign="center",
        valign="middle",
        color=get_color_from_hex(WHITE),
        size_hint_y=None,
        height=height
    )
    # Bind the label's width to the window width minus padding
    def update_text_size(instance, value):
        instance.text_size = (Window.width - 60, None)
    label.bind(width=update_text_size)
    update_text_size(label, None)
    return label

def build_header(layout, title_text):
    top_layout = BoxLayout(orientation="horizontal", size_hint_y=None, height=60)
    title = SafeLabel(
        text=title_text,
        font_size=50,
        bold=True,
        font_name="freedom",
        color=get_color_from_hex("#FFDD00"),  # GOV.UK yellow
        halign="center",
        valign="middle"
    )
    title.bind(size=lambda inst, val: setattr(inst, 'text_size', (val, None)))
    top_layout.add_widget(title)
    layout.add_widget(top_layout)

def build_footer(layout):
    bottom_layout = BoxLayout(orientation="horizontal", size_hint_y=None, height=25)
    footer_label = SafeLabel(
        text="Benefit Buddy © 2025   Version 1.0   All Rights Reserved",
        font_size=12,
        halign="center",
        color=get_color_from_hex("#FFDD00")  # GOV.UK yellow
    )
    bottom_layout.add_widget(footer_label)
    layout.add_widget(bottom_layout)

tracemalloc.start()  # Start tracing memory allocations

# Define the main application class
class BenefitBuddy(App):
    def build(self):
        sm = ScreenManager()

        sm.add_widget(InstantScreen(name="instant"))
        sm.add_widget(DisclaimerScreen(name="disclaimer"))
        sm.add_widget(SettingsScreen(name="settings"))
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(CreateAccountPage(name="create_account"))
        sm.add_widget(LoginPage(name="log_in"))
        sm.add_widget(MainScreenGuestAccess(name="main_guest_access"))
        sm.add_widget(MainScreenFullAccess(name="main_full_access"))
        sm.add_widget(Calculator(name="calculator"))
        sm.add_widget(CalculationBreakdownScreen(name="breakdown"))

        sm.current = "instant"
        return sm


    def on_start(self):
        # Switch away from InstantScreen
        Clock.schedule_once(self.go_to_disclaimer, 0)
    
        # Run diagnostics after everything exists
        Clock.schedule_once(self.run_startup_diagnostics, 0.1)

    
    def go_to_disclaimer(self, dt):
        self.root.current = "disclaimer"
    
    def run_startup_diagnostics(self, dt):
        print("\n=== Benefit Buddy Startup Diagnostics ===")
    
        self.check_assets()
        self.check_safe_props()
        self.check_window_size()
        self.check_memory()
    
        print("\n=== Startup Diagnostics Complete ===\n")

    def check_assets(self):
        print("\n[1] Asset Verification")
        required_assets = {
            "Logo": "images/logo.png",
            "BRMA CSV": "data/pcode_brma_lookup.csv",
            "Roboto Font": "font/roboto.ttf",
            "Chevron Down Icon": "images/icons/ChevronDown-icon/ChevronDown-32px.png",
            "Chevron Up Icon": "images/icons/ChevronUp-icon/ChevronUp-32px.png",
        }
        for label, asset in required_assets.items():
            path = resource_find(asset)
            print(f"  {'✔' if path else '✖'} {label}: {asset}")

    def check_safe_props(self):
        print("\n[2] Safe Props Texture Patch Check")
        from kivy.uix.label import Label
        patched = Label.texture_update.__name__ != "_texture_update"
        print("  ✔ safe_props_texture.py ACTIVE" if patched else "  ✖ NOT ACTIVE")
    
    def check_window_size(self):
        print("\n[3] Window Size Check")
        w, h = Window.width, Window.height
        print(f"  ✔ Window size OK ({w}x{h})" if w >= 600 else "  ✖ Window too small")
    
    def check_memory(self):
        print("\n[4] Memory Check")
        current, peak = tracemalloc.get_traced_memory()
        print(f"  ✔ Memory usage: {current/1024:.1f} KB (peak {peak/1024:.1f} KB)")



# Create a custom TextInput class to handle multiple inputs and keyboard events
class CustomTextInput(TextInput):
    layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

    def create_inputs(self): # Create multiple TextInput fields
        self.inputs = [TextInput(multiline=False) for _ in range(3)]
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        for i, input_box in enumerate(self.inputs):
            input_box.bind(on_text_validate=self.move_to_next)  # Bind Enter key
            layout.add_widget(input_box)
        return layout

    def move_to_next(self, instance): # Move focus to the next TextInput
        # Find the index of the current TextInput
        current_index = self.inputs.index(instance)
        # Focus the next TextInput if it exists
        if current_index + 1 < len(self.inputs):
            self.inputs[current_index + 1].focus = True
            
    def keyboard_on_key_down(self, window, keycode, text, modifiers): # Handle keyboard events
        # Check if Tab or Enter key is pressed
        if keycode[1] == 'tab':  # Check if Tab key is pressed
            self.focus_next()  # Move focus to the next TextInput
            return True
        elif keycode[1] == 'enter':  # Check if Enter key is pressed
            self.focus_next()  # Move focus to the next TextInput
            return True
        return super().keyboard_on_key_down(window, keycode, text, modifiers)

    def focus_next(self): # Move focus to the next TextInput
        # Find the next widget to focus
        focusable_widgets = self.parent.children[::-1]  # Reverse order
        current_index = focusable_widgets.index(self)
        if current_index + 1 < len(focusable_widgets):
            focusable_widgets[current_index + 1].focus = True

# Create a custom TextInput for date of birth input
class DOBInput(CustomTextInput):
    def insert_text(self, substring, from_undo=False):
        # Allow only digits and slashes
        allowed_chars = "0123456789"
        substring = ''.join(c for c in substring if c in allowed_chars)

        # Enforce the format DD/MM/YYYY
        text = self.text
        if len(text) == 2 or len(text) == 5:
            substring = '/' + substring

        # Limit the length to 10 characters (DD/MM/YYYY)
        if len(text) + len(substring) > 10:
            substring = substring[:10 - len(text)]

        super().insert_text(substring, from_undo=from_undo)

# Create a custom button with rounded corners
class RoundedButton(Button):
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
        if not ts or ts in [(None, None), (0, 0)] or isinstance(ts, ObservableList):
            kwargs["text_size"] = (Window.width - 60, None)

        # --- PADDING ---
        pad = kwargs.get("padding", None)
        if not pad or pad in [(0, 0), (0, 0, 0, 0)] or isinstance(pad, ObservableList):
            kwargs["padding"] = (10, 10)

        super().__init__(**kwargs)

        # --- Rounded rectangle background ---
        with self.canvas.before:
            self.color_instruction = Color(rgba=get_color_from_hex("#FFDD00"))  # GOVUK_YELLOW
            self.rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[20]
            )

        # Bind position and size to update the rectangle dynamically
        self.bind(pos=self.update_rect, size=self.update_rect)

        # 🔑 Bind text_size dynamically to widget width and window resize
        self.bind(width=self._update_text_size)
        Window.bind(size=lambda *_: self._update_text_size())

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def _update_text_size(self, *args):
        # Always keep text_size tied to current width
        self.text_size = (self.width - 20, None)



# ---------------------------------------------------------
# ROW USED INSIDE DROPDOWN
# ---------------------------------------------------------
class IconRow(ButtonBehavior, BoxLayout):
    def __init__(self, text, icon_path=None, **kwargs):
        super().__init__(
            orientation="horizontal",
            spacing=10,
            padding=(15, 10),
            size_hint_y=None,
            height=50,
            **kwargs
        )

        # Background
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.bg = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self._update_bg, size=self._update_bg)

        # Optional icon
        if icon_path:
            self.add_widget(Image(
                source=icon_path,
                size_hint=(None, None),
                size=(28, 28),
                allow_stretch=True,
                keep_ratio=True
            ))

        # Text label
        self.label = Label(
            text=text,
            color=get_color_from_hex("#005EA5"),
            font_size=18,
            halign="left",
            valign="middle"
        )
        self.add_widget(self.label)

    def _update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size


# ---------------------------------------------------------
# BASE GOV.UK SPINNER (styling only)
# ---------------------------------------------------------
class GovUkSpinner(Spinner):
    def __init__(self, **kwargs):
        super().__init__(
            size_hint=(None, None),
            size=(250, 50),
            background_normal="",
            background_color=get_color_from_hex("#FFDD00"),
            color=get_color_from_hex("#005EA5"),
            disabled_color=get_color_from_hex("#005EA5"),
            background_disabled_normal="",
            font_size=20,
            font_name="roboto",
            halign="center",
            valign="middle",
            text_size=(250, None),
            pos_hint={"center_x": 0.5},
            **kwargs
        )


# ---------------------------------------------------------
# FINAL GOV.UK ICON SPINNER (FULLY SAFE & FEATURED)
# ---------------------------------------------------------
class GovUkIconSpinner(GovUkSpinner):
    def __init__(self, icon_map=None, **kwargs):
        self.icon_map = icon_map or {}
        super().__init__(**kwargs)

        # -----------------------------------------------------
        # Clear default spinner children (just visual content)
        # -----------------------------------------------------
        self.clear_widgets()

        # -----------------------------------------------------
        # Build custom button layout
        # -----------------------------------------------------
        self.button_box = BoxLayout(
            orientation="horizontal",
            spacing=10,
            padding=(15, 10),
            size_hint=(1, 1)
        )

        # Spinner label
        self.label = Label(
            text=self.text or "Select",
            color=get_color_from_hex("#005EA5"),
            font_size=20,
            halign="left",
            valign="middle"
        )

        # Chevron icon (down arrow by default)
        self.chevron = Image(
            source="images/icons/ChevronDown-icon/ChevronDown-32px.png",
            size_hint=(None, None),
            size=(24, 24),
            allow_stretch=True,
            keep_ratio=True
        )

        self.button_box.add_widget(self.label)
        self.button_box.add_widget(self.chevron)
        self.add_widget(self.button_box)

        # Keep label synced with spinner text
        self.bind(text=lambda instance, value: setattr(self.label, "text", value))

        # -----------------------------------------------------
        # Simple active state (pressed)
        # -----------------------------------------------------
        self.normal_bg = get_color_from_hex("#FFDD00")
        self.active_bg = get_color_from_hex("#CCB000")

        def on_press(*_):
            self.background_color = self.active_bg

        def on_release(*_):
            self.background_color = self.normal_bg

        self.bind(on_press=on_press, on_release=on_release)

        # Ensure we start with normal background
        self.background_color = self.normal_bg

    # ---------------------------------------------------------
    # Build dropdown manually (Android-safe)
    # ---------------------------------------------------------
    def _build_dropdown(self):
        dropdown = DropDown()

        # Dropdown background
        with dropdown.canvas.before:
            Color(1, 1, 1, 1)
            dropdown.bg = Rectangle(pos=dropdown.pos, size=dropdown.size)

        dropdown.bind(pos=lambda *_: setattr(dropdown.bg, "pos", dropdown.pos))
        dropdown.bind(size=lambda *_: setattr(dropdown.bg, "size", dropdown.size))

        # Update spinner text when selecting
        dropdown.bind(on_select=lambda instance, value: setattr(self, "text", value))

        # Add rows
        for value in self.values:
            icon_path = self.icon_map.get(value)
            row = IconRow(text=value, icon_path=icon_path)
            row.bind(on_release=lambda row_instance: dropdown.select(row_instance.label.text))
            dropdown.add_widget(row)

        # When dropdown is dismissed, reset chevron + background
        dropdown.bind(on_dismiss=lambda *_: self._on_dropdown_dismiss())

        self._dropdown = dropdown

    # ---------------------------------------------------------
    # Open dropdown safely and swap chevron icon
    # ---------------------------------------------------------
    def open_dropdown(self, *args):
        # Ensure dropdown exists
        if not getattr(self, "_dropdown", None):
            self._build_dropdown()

        # Swap chevron to "up"
        if self.chevron:
            self.chevron.source = "images/icons/ChevronUp-icon/ChevronUp-32px.png"

        return super().open_dropdown(*args)

    # ---------------------------------------------------------
    # Handle dropdown dismiss: reset chevron + background
    # ---------------------------------------------------------
    def _on_dropdown_dismiss(self, *args):
        if self.chevron:
            self.chevron.source = "images/icons/ChevronDown-icon/ChevronDown-32px.png"
        self.background_color = self.normal_bg



# Create a loading animation using a sequence of PNG images
class PNGSequenceAnimationWidget(Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        base_path = os.path.dirname(os.path.abspath(__file__))
        images_path = os.path.join(base_path, "images", "loading")
        resource_add_path(images_path)

        self.frames = []
        for f in sorted(os.listdir(images_path)):
            if f.endswith(".png"):
                found_path = resource_find(f)
                if found_path:
                    self.frames.append(found_path)

        self.current_frame = 0
        Clock.schedule_interval(self.update_frame, 1 / 30.0)

    def update_frame(self, dt):
        if not self.frames:
            return
        self.source = self.frames[self.current_frame]
        self.current_frame = (self.current_frame + 1) % len(self.frames)


class PulsingGlow(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            self.color = Color(1, 1, 1, 0.3)
            self.ellipse = Ellipse(size=self.size, pos=self.pos)

        self.bind(size=self.update_graphics, pos=self.update_graphics)

        # Pulse animation
        anim = Animation(a=0.6, duration=0.8) + Animation(a=0.3, duration=0.8)
        anim.repeat = True
        anim.start(self.color)

    def update_graphics(self, *args):
        self.ellipse.size = self.size
        self.ellipse.pos = self.pos


@with_diagnostics([])
class InstantScreen(Screen):
    pass
        
# Define the Settings Screen
@with_diagnostics([])
class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = BoxLayout(orientation="vertical", spacing=30, padding=20)

        # Header
        header_anchor = AnchorLayout(anchor_x="center", anchor_y="top", size_hint_y=None, height=80)
        build_header(header_anchor, "Benefit Buddy")
        layout.add_widget(header_anchor)

        # Info label
        info_anchor = AnchorLayout(anchor_x="center", anchor_y="center")
        info_label = SafeLabel(
            text="Settings are currently in development.\n\nPlease check back later.",
            font_size=16, halign="center", valign="middle", color=get_color_from_hex(WHITE)
        )
        info_label.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
        info_anchor.add_widget(info_label)
        layout.add_widget(info_anchor)

        # Spacer above buttons
        layout.add_widget(Widget(size_hint_y=0.05))

        # Shared button style for consistency
        button_style = {
            "size_hint": (None, None),
            "size": (250, 60),
            "background_color": (0, 0, 0, 0),
            "background_normal": "",
            "pos_hint": {"center_x": 0.5}
        }

        # Grouped buttons in a vertical box
        buttons_box = BoxLayout(orientation="vertical", spacing=20, size_hint=(1, None))
        for text, handler in [
            ("Back to Main Menu", self.go_to_main),
        ]:
            btn = RoundedButton(
                text=text,
                **button_style,
                font_size=20,
                font_name="roboto",
                color=get_color_from_hex("#005EA5"),
                halign="center", valign="middle",
                text_size=(250, None),
                on_press=handler
            )
            buttons_box.add_widget(btn)

        layout.add_widget(buttons_box)

        # Spacer below buttons
        layout.add_widget(Widget(size_hint_y=0.05))

        # Footer
        footer_anchor = AnchorLayout(anchor_x="center", anchor_y="bottom", size_hint_y=None, height=60)
        build_footer(footer_anchor)
        layout.add_widget(footer_anchor)

        self.add_widget(layout)

    def go_to_main(self, instance):
        self.manager.current = "main"

# Disclaimer Screen
@with_diagnostics([])
class DisclaimerScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Main layout
        layout = BoxLayout(orientation="vertical", spacing=20, padding=20)

        # Disclaimer text
        disclaimer_text = SafeLabel(
            text=(
                "Disclaimer: This app is currently still in development and may not be fully accurate.\n\n"
                "It is for informational purposes only and does not constitute financial advice.\n\n\n"
                "Guest access has limited functionality and will not save your data."
            ),
            font_size=18,
            halign="center",
            valign="middle",
            color=get_color_from_hex("#FFFFFF")
        )
        disclaimer_text.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
        layout.add_widget(disclaimer_text)

        # -----------------------------
        # GOV.UK STYLE LOADING BAR
        # -----------------------------
        self.loading_label = SafeLabel(
            text="Loading data…",
            font_size=16,
            halign="center",
            valign="middle",
            color=get_color_from_hex("#FFDD00"),
            size_hint=(1, None),
            height=40
        )
        layout.add_widget(self.loading_label)

        # Background bar (black)
        self.loading_bar_bg = BoxLayout(
            size_hint=(1, None),
            height=20,
            padding=0,
            spacing=0
        )

        # Foreground bar (GOV.UK yellow)
        self.loading_bar_fg = BoxLayout(
            size_hint=(0, 1),  # width grows
            background_color=get_color_from_hex("#FFDD00")
        )

        self.loading_bar_bg.add_widget(self.loading_bar_fg)
        layout.add_widget(self.loading_bar_bg)

        # Continue button (disabled until CSV is loaded)
        self.continue_button = RoundedButton(
            text="Continue",
            size_hint=(None, None),
            size=(250, 60),
            disabled=True,
            background_color=(0, 0, 0, 0),
            background_normal="",
            color=get_color_from_hex("#005EA5"),
            font_size=20,
            on_press=lambda x: setattr(self.manager, "current", "main")
        )
        layout.add_widget(self.continue_button)

        # Footer
        build_footer(layout)

        self.add_widget(layout)

        # Internal progress tracker
        self._progress = 0.0

    # ---------------------------------------------------------
    # When disclaimer screen becomes visible
    # ---------------------------------------------------------
    def on_enter(self):
        # Start fake progress animation
        Clock.schedule_interval(self._animate_progress, 0.05)

        # Delay CSV loading slightly so Calculator screen exists
        Clock.schedule_once(self.start_csv_load, 1.0)

    # ---------------------------------------------------------
    # Animate GOV.UK loading bar (fake progress)
    # ---------------------------------------------------------
    def _animate_progress(self, dt):
        if self._progress < 0.9:
            self._progress += 0.01
            self.loading_bar_fg.size_hint_x = self._progress

    # ---------------------------------------------------------
    # Start CSV loading in a background thread
    # ---------------------------------------------------------
    def start_csv_load(self, dt):
        import threading
        threading.Thread(target=self._load_csv_thread).start()

    # ---------------------------------------------------------
    # Background thread: load BRMA cache safely
    # ---------------------------------------------------------
    def _load_csv_thread(self):
        app = App.get_running_app()

        # Wait until Calculator screen is fully created
        calculator = None
        while calculator is None:
            try:
                calculator = app.root.get_screen("calculator")
            except:
                calculator = None

        # Load CSV cache (heavy work)
        calculator.load_brma_cache()

        # Notify UI thread when done
        Clock.schedule_once(self._loading_complete, 0)

    # ---------------------------------------------------------
    # Update UI when loading is complete
    # ---------------------------------------------------------
    def _loading_complete(self, dt):
        # Finish bar animation
        self._progress = 1.0
        self.loading_bar_fg.size_hint_x = 1.0

        self.loading_label.text = "Ready"
        self.continue_button.disabled = False

# Define the main screen for the app
@with_diagnostics([])
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Root layout fills the whole screen
        layout = BoxLayout(orientation="vertical", spacing=30, padding=20)

        # Header pinned to top
        header_anchor = AnchorLayout(anchor_x="center", anchor_y="top", size_hint_y=None, height=80)
        build_header(header_anchor, "Benefit Buddy")
        layout.add_widget(header_anchor)

        # Logo centered and resized
        logo_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=250)
        logo = Image(
            source="images/logo.png",
            size_hint=(None, None),
            size=(250, 250),   # balanced size for tablets
            allow_stretch=True,
            keep_ratio=True
        )
        logo_anchor.add_widget(logo)
        layout.add_widget(logo_anchor)

        # Spacer above buttons
        layout.add_widget(Widget(size_hint_y=0.05))

        # Shared button style for consistency
        button_style = {
            "size_hint": (None, None),
            "size": (250, 60),
            "background_color": (0, 0, 0, 0),
            "background_normal": "",
            "pos_hint": {"center_x": 0.5}
        }

        # Grouped buttons in a vertical box
        buttons_box = BoxLayout(orientation="vertical", spacing=20, size_hint=(1, None))
        for text, handler in [
            ("Create Account", self.go_to_create_account),
            ("Login", self.go_to_login),
            ("Guest Access", self.go_to_guest_access),
            ("Settings", self.go_to_settings),
            ("Exit", self.exit_app),
        ]:
            btn = RoundedButton(
                text=text,
                **button_style,
                font_size=20,
                font_name="roboto",
                color=get_color_from_hex("#005EA5"),
                halign="center", valign="middle",
                text_size=(250, None),
                on_press=handler
            )
            buttons_box.add_widget(btn)

        layout.add_widget(buttons_box)

        # Spacer below buttons
        layout.add_widget(Widget(size_hint_y=0.05))

        # Footer pinned to bottom
        footer_anchor = AnchorLayout(anchor_x="center", anchor_y="bottom", size_hint_y=None, height=60)
        build_footer(footer_anchor)
        layout.add_widget(footer_anchor)

        self.add_widget(layout)

    # Navigation methods
    def go_to_create_account(self, instance):
        self.manager.current = "create_account"

    def go_to_login(self, instance):
        self.manager.current = "log_in"

    def go_to_guest_access(self, instance):
        self.manager.current = "main_guest_access"

    def go_to_settings(self, instance):
        self.manager.current = "settings"

    def exit_app(self, instance):
        App.get_running_app().stop()

# Define the Main Screen for Full Access
@with_diagnostics([])
class MainScreenFullAccess(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Main vertical layout
        layout = BoxLayout(orientation="vertical", spacing=30, padding=20)

        # Header pinned to top
        header_anchor = AnchorLayout(anchor_x="center", anchor_y="top", size_hint_y=None, height=80)
        build_header(header_anchor, "Benefit Buddy")
        layout.add_widget(header_anchor)

        # Shared button style for consistency (only button-level props)
        button_style = {
            "size_hint": (None, None),
            "size": (250, 60),
            "background_normal": "",
            "background_color": (0, 0, 0, 0),  # transparent background
            "pos_hint": {"center_x": 0.5}
        }

        # Spacer above buttons
        layout.add_widget(Widget(size_hint_y=0.05))

        # Grouped buttons in a vertical box
        buttons_box = BoxLayout(orientation="vertical", spacing=20, size_hint=(1, None))

        for text, handler in [
            ("Predict Next Payment", lambda x: print("Prediction feature not yet implemented")),
            ("View Previous Payments", lambda x: print("Payments feature not yet implemented")),
            ("Update Details", lambda x: print("Update details feature not yet implemented")),
            ("Log Out", self.log_out),
        ]:
            btn = RoundedButton(
                text=text,
                **button_style,
                font_size=20,
                font_name="roboto",
                color=get_color_from_hex("#005EA5"),  # GOV.UK blue text
                halign="center", valign="middle",
                text_size=(250, None),
                on_press=handler
            )
            buttons_box.add_widget(btn)

        layout.add_widget(buttons_box)

        # Spacer below buttons
        layout.add_widget(Widget(size_hint_y=0.05))

        # Footer pinned to bottom
        footer_anchor = AnchorLayout(anchor_x="center", anchor_y="bottom", size_hint_y=None, height=60)
        build_footer(footer_anchor)
        layout.add_widget(footer_anchor)

        self.add_widget(layout)

        # Initialize attributes to avoid AttributeError
        self.dob_input = TextInput(hint_text="DD/MM/YYYY")
        self.partner_dob_input = TextInput(hint_text="DD/MM/YYYY")
        self.relationship_input = TextInput(hint_text="single/couple")
        self.children_dob_inputs = []
        self.is_carer = False
        self.lcw = False
        self.receives_housing_support = False

    # ------------------------
    # Popup helpers
    # ------------------------
    def create_popup(self, title, message):
        lbl = SafeLabel(
            text=message,
            halign="center",
            color=get_color_from_hex("#005EA5"),  # GOV.UK blue text
            font_size=18,
            font_name="roboto"
        )
        lbl.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
        return Popup(
            title=title,
            content=lbl,
            size_hint=(0.8, 0.4),
            title_color=get_color_from_hex("#005EA5"),  # styled popup title
            separator_color=get_color_from_hex("#FFDD00")  # GOV.UK yellow separator
        )

    # ------------------------
    # Predict Payment Flow
    # ------------------------
    def predict_payment(self, instance):
        content = BoxLayout(orientation="vertical", spacing=20, padding=20)

        self.income_input = TextInput(
            hint_text="Enter your income for this assessment period",
            font_size=18,
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex("#005EA5"),
            font_name="roboto"
        )

        submit_button = RoundedButton(
            text="Submit",
            size_hint=(None, None), size=(250, 50),
            background_normal="",
            background_color=get_color_from_hex("#FFDD00"),
            font_size=20,
            font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            pos_hint={"center_x": 0.5},
            halign="center", valign="middle",
            text_size=(250, None),
            on_press=lambda _: self.show_prediction_popup(self.income_input.text)
        )

        content.add_widget(SafeLabel(
            text="Enter your income:",
            font_size=20,
            halign="center",
            color=get_color_from_hex("#005EA5"),
            font_name="roboto"
        ))
        content.add_widget(self.income_input)
        content.add_widget(submit_button)

        popup = Popup(
            title="Payment Prediction",
            content=content,
            size_hint=(0.8, 0.5),
            title_color=get_color_from_hex("#005EA5"),
            separator_color=get_color_from_hex("#FFDD00")
        )
        popup.open()

    def show_prediction_popup(self, income):
        income = income.strip() if income else ""
        try:
            value = float(income)
            predicted_payment = self.payment_prediction(value)
            message = f"Your next payment is predicted to be: £{predicted_payment:.2f}"
        except (ValueError, TypeError):
            message = "Invalid income entered. Please enter a numeric value."

        result_label = SafeLabel(
            text=message,
            font_size=20,
            halign="center",
            color=get_color_from_hex("#005EA5"),
            font_name="roboto"
        )
        result_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (val[0], None)))

        result_popup = Popup(
            title="Prediction Result",
            content=result_label,
            size_hint=(0.8, 0.4),
            title_color=get_color_from_hex("#005EA5"),
            separator_color=get_color_from_hex("#FFDD00")
        )
        result_popup.open()

    def payment_prediction(self, income):
        self.income_input.text = str(income)
        return self.calculate_entitlement()

    def calculate_entitlement(self):
        try:
            dob_date = datetime.strptime(self.dob_input.text, "%d-%m-%Y")
            partner_dob_date = datetime.strptime(self.partner_dob_input.text, "%d-%m-%Y")
        except ValueError:
            self.create_popup("Invalid Date", "Please enter DOBs in DD/MM/YYYY format").open()
            return

        current_date = datetime.now()
        age = current_date.year - dob_date.year - ((current_date.month, current_date.day) < (dob_date.month, dob_date.day))
        partner_age = current_date.year - partner_dob_date.year - ((current_date.month, current_date.day) < (partner_dob_date.month, partner_dob_date.day))

        relationship_status = self.relationship_input.text.lower()

        if relationship_status == "single":
            standard_allowance = 316.98 if age < 25 else 400.14
        elif relationship_status == "couple":
            standard_allowance = 497.55 if age < 25 and partner_age < 25 else 628.10
        else:
            self.create_popup("Invalid Relationship Status", "Please select single or couple").open()
            return

        child_element = 0
        children_dobs = []
        for dob_input in self.children_dob_inputs:
            try:
                dob = datetime.strptime(dob_input.text, "%d-%m-%Y")
                children_dobs.append(dob)
            except ValueError:
                self.create_popup("Invalid Date", "Children DOBs must be DD/MM/YYYY").open()
                return

        for i, dob in enumerate(children_dobs):
            if i == 0:
                child_element += 339 if dob < datetime(2017, 4, 6) else 292.81
            else:
                child_element += 292.81

        carer_element = 201.68 if self.is_carer else 0
        disability_element = 0
        childcare_element = 0
        housing_element = 0

        try:
            income = float(self.income_input.text)
        except ValueError:
            self.create_popup("Invalid Income", "Please enter a numeric income").open()
            return

        children = len(children_dobs)
        work_allowance = 411 if (children > 0 or self.lcw) and self.receives_housing_support else (684 if (children > 0 or self.lcw) else 0)

        total_allowance = standard_allowance + child_element + carer_element + disability_element + childcare_element + housing_element
        total_deductions = max(0, income - work_allowance) * 0.55
        entitlement = max(0, total_allowance - total_deductions)

        return entitlement

    def log_out(self, instance):
        self.manager.current = "main"
        
# Define the Guest Access Screen (reusing HomePage for simplicity)
@with_diagnostics([])
class MainScreenGuestAccess(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = BoxLayout(orientation="vertical", spacing=30, padding=20)

        # Header
        header_anchor = AnchorLayout(anchor_x="center", anchor_y="top", size_hint_y=None, height=80)
        build_header(header_anchor, "Benefit Buddy")
        layout.add_widget(header_anchor)

        # Info label
        info_anchor = AnchorLayout(anchor_x="center", anchor_y="center")
        info_label = SafeLabel(
            text="Guest Access has limited functionality.\n\nFull Access Mode is in development.",
            font_size=16, halign="center", valign="middle", color=get_color_from_hex(WHITE)
        )
        info_label.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
        info_anchor.add_widget(info_label)
        layout.add_widget(info_anchor)

        # Spacer above buttons
        layout.add_widget(Widget(size_hint_y=0.05))

        # Shared button style for consistency
        button_style = {
            "size_hint": (None, None),
            "size": (250, 60),
            "background_color": (0, 0, 0, 0),
            "background_normal": "",
            "pos_hint": {"center_x": 0.5}
        }

        # Grouped buttons in a vertical box
        buttons_box = BoxLayout(orientation="vertical", spacing=20, size_hint=(1, None))
        for text, handler in [
            ("Calculate Universal Credit", self.go_to_calculator),
            ("Log Out", self.log_out),
        ]:
            btn = RoundedButton(
                text=text,
                **button_style,
                font_size=20,
                font_name="roboto",
                color=get_color_from_hex("#005EA5"),
                halign="center", valign="middle",
                text_size=(250, None),
                on_press=handler
            )
            buttons_box.add_widget(btn)

        layout.add_widget(buttons_box)

        # Spacer below buttons
        layout.add_widget(Widget(size_hint_y=0.05))

        # Footer
        footer_anchor = AnchorLayout(anchor_x="center", anchor_y="bottom", size_hint_y=None, height=60)
        build_footer(footer_anchor)
        layout.add_widget(footer_anchor)

        self.add_widget(layout)

    def go_to_calculator(self, instance):
        self.manager.current = "calculator"

    def log_out(self, instance):
        self.manager.current = "main"

# Define the Create Account Screen
@with_diagnostics([])
class CreateAccountPage(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = BoxLayout(orientation="vertical", spacing=30, padding=20)

        # Header
        header_anchor = AnchorLayout(anchor_x="center", anchor_y="top", size_hint_y=None, height=80)
        build_header(header_anchor, "Benefit Buddy")
        layout.add_widget(header_anchor)

        # Info label
        info_anchor = AnchorLayout(anchor_x="center", anchor_y="center")
        info_label = SafeLabel(
            text="This section is still in development.\n\nPlease check back later for updates.",
            font_size=16, halign="center", valign="middle", color=get_color_from_hex(WHITE)
        )
        info_label.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
        info_anchor.add_widget(info_label)
        layout.add_widget(info_anchor)

        # Spacer above buttons
        layout.add_widget(Widget(size_hint_y=0.05))

        # Shared button style for consistency
        button_style = {
            "size_hint": (None, None),
            "size": (250, 60),
            "background_color": (0, 0, 0, 0),
            "background_normal": "",
            "pos_hint": {"center_x": 0.5}
        }

        # Grouped buttons in a vertical box
        buttons_box = BoxLayout(orientation="vertical", spacing=20, size_hint=(1, None))
        for text, handler in [
            ("Back to Home", self.go_back),
        ]:
            btn = RoundedButton(
                text=text,
                **button_style,
                font_size=20,
                font_name="roboto",
                color=get_color_from_hex("#005EA5"),
                halign="center", valign="middle",
                text_size=(250, None),
                on_press=handler
            )
            buttons_box.add_widget(btn)

        layout.add_widget(buttons_box)

        # Spacer below buttons
        layout.add_widget(Widget(size_hint_y=0.05))

        # Footer
        footer_anchor = AnchorLayout(anchor_x="center", anchor_y="bottom", size_hint_y=None, height=60)
        build_footer(footer_anchor)
        layout.add_widget(footer_anchor)

        self.add_widget(layout)

    def go_back(self, instance):
        self.manager.current = "main"

# Define the Login Screen
@with_diagnostics([])
class LoginPage(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = BoxLayout(orientation="vertical", spacing=30, padding=20)

        # Header
        header_anchor = AnchorLayout(anchor_x="center", anchor_y="top", size_hint_y=None, height=80)
        build_header(header_anchor, "Benefit Buddy")
        layout.add_widget(header_anchor)

        # Info label
        info_anchor = AnchorLayout(anchor_x="center", anchor_y="center")
        info_label = SafeLabel(
            text="Login functionality is in development.\n\nFuture versions will allow full account access.",
            font_size=16,
            halign="center",
            valign="middle",
            color=get_color_from_hex(WHITE)
        )
        info_label.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
        info_anchor.add_widget(info_label)
        layout.add_widget(info_anchor)

        # Spacer
        layout.add_widget(Widget(size_hint_y=0.05))

        # Shared button style for consistency
        button_style = {
            "size_hint": (None, None),
            "size": (250, 60),
            "background_color": (0, 0, 0, 0),
            "background_normal": "",
            "pos_hint": {"center_x": 0.5}
        }

        # Buttons
        for text, handler in [
            ("Log In", self.log_in),
            ("Back to Home", self.go_back),
        ]:
            btn = RoundedButton(
                text=text,
                **button_style,
                font_size=20,
                font_name="roboto",
                color=get_color_from_hex("#005EA5"),
                halign="center", valign="middle",
                text_size=(250, None),
                on_press=handler
            )
            layout.add_widget(btn)

        # Footer
        footer_anchor = AnchorLayout(anchor_x="center", anchor_y="bottom", size_hint_y=None, height=60)
        build_footer(footer_anchor)
        layout.add_widget(footer_anchor)

        self.add_widget(layout)

    def log_in(self, instance):
        self.manager.current = "main_full_access"

    def go_back(self, instance):
        self.manager.current = "main"

# Define the Calculator Screen
@with_diagnostics([
    # Claimant
    "name_input",
    "dob_input",
    "partner_name_input",
    "partner_dob_input",
    "single_claimant_checkbox",
    "couple_claim_checkbox",

    # Finances
    "income_input",
    "savings_input",
    "debts_input",

    # Housing
    "housing_type_spinner",
    "tenancy_type_spinner",
    "rent_input",
    "mortgage_input",
    "shared_input",
    "non_dependants_input",
    "postcode_input",
    "location_spinner",
    "brma_spinner",

    # Children
    "children_dob_inputs",
    "children_layout",

    # Additional Elements
    "is_carer_input",
    "disability_input",
    "childcare_input",

    # Sanctions
    "sanction_type_input",
    "sanction_duration_input",

    # Advance Payments
    "advance_amount_input",
    "repayment_period_input",

    # Summary
    "summary_label"
])
class Calculator(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # =========================================================
        # USER DATA
        # =========================================================
        self.user_data = {
            "claimant_dob": "",
            "partner_dob": "",
            "relationship": "single",
            "income": 0.0,
            "savings": 0.0,
            "children": [],
            "disability": "",
            "had_lcw_before_uc": False,
            "carer": False,
            "childcare": 0.0,
            "housing_type": "",
            "tenancy_type": "",
            "location": "",
            "brma": "",
            "rent": 0.0,
            "mortgage": 0.0,
            "shared": 0.0,
            "non_dependants": 0,
            "service_charges": {},
            "care_leaver": False,
            "severe_disability": False,
            "mappa": False,
            "hostel_resident": False,
            "domestic_abuse_refuge": False,
            "ex_offender": False,
            "foster_carer": False,
            "prospective_adopter": False,
            "temporary_accommodation": False,
            "modern_slavery": False,
            "armed_forces_reservist": False,
            "sanction_type": "",
            "sanction_duration": 0,
            "hardship": False,
            "advance_amount": 0.0,
            "repayment_period": 0,
            "had_sdp": False,
            "extra_edp": False,
            "extra_dp": False,
            "extra_disabled_children": False,
        }

        self.current_subscreen = "Introduction"

        # =========================================================
        # LAZY‑LOADING + UI CACHING
        # =========================================================
        self._screen_cache = {}              # Cache for whole screens
        self._brma_dropdown_cache = {}       # Cache for BRMA dropdowns
        self._child_row_cache = []           # Cache for child rows
        self._summary_section_cache = {}     # Cache for collapsible summary sections

        # =========================================================
        # MAIN LAYOUT
        # =========================================================
        layout = BoxLayout(orientation="vertical", spacing=30, padding=20)

        # Header
        header_anchor = AnchorLayout(anchor_x="center", anchor_y="top", size_hint_y=None, height=80)
        build_header(header_anchor, "Benefit Buddy")
        layout.add_widget(header_anchor)

        layout.add_widget(Widget(size_hint_y=0.05))

        # Back button
        back_button = RoundedButton(
            text="Back to Guest Access",
            size_hint=(None, None),
            size=(250, 60),
            background_color=(0, 0, 0, 0),
            background_normal="",
            pos_hint={"center_x": 0.5},
            font_size=20,
            font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            on_press=lambda x: setattr(self.manager, 'current', "main_guest_access")
        )
        layout.add_widget(back_button)

        layout.add_widget(Widget(size_hint_y=0.05))

        # =========================================================
        # SCREEN SPINNER
        # =========================================================
        self.screens = [
            ("Introduction", self.create_intro_screen),
            ("Claimant Details", self.create_claimant_details_screen),
            ("Finances", self.create_finances_screen),
            ("Housing", self.create_housing_screen),
            ("Children", self.create_children_screen),
            ("Additional Elements", self.create_additional_elements_screen),
            ("Sanctions", self.create_sanction_screen),
            ("Advanced Payments", self.create_advance_payments_screen),
            ("Summary", self.create_calculate_screen)
        ]

        spinner_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=70)
        self.screen_spinner = GovUkIconSpinner(
            text="Introduction",
            icon_map=ICON_PATHS,
            values=[name for name, _ in self.screens],
        )
        spinner_anchor.add_widget(self.screen_spinner)
        layout.add_widget(spinner_anchor)

        # =========================================================
        # SCREEN CONTENT CONTAINER
        # =========================================================
        self.screen_content = BoxLayout(orientation="vertical", spacing=10, padding=10)

        # Lazy‑load the first screen
        intro_widget = self._get_or_build_screen("Introduction")
        self.screen_content.add_widget(intro_widget)

        layout.add_widget(self.screen_content)
        layout.add_widget(Widget(size_hint_y=0.05))

        # Footer
        footer_anchor = AnchorLayout(anchor_x="center", anchor_y="bottom", size_hint_y=None, height=60)
        build_footer(footer_anchor)
        layout.add_widget(footer_anchor)

        self.add_widget(layout)

        # Bind spinner AFTER layout is built
        self.screen_spinner.bind(text=self.on_screen_select)

    # =========================================================
    # LAZY‑LOADING SCREEN BUILDER
    # =========================================================
    def _get_or_build_screen(self, name):
        """Build a screen once, then reuse it forever."""
        if name not in self._screen_cache:
            for screen_name, builder in self.screens:
                if screen_name == name:
                    self._screen_cache[name] = builder()
                    break
        return self._screen_cache[name]

    # =========================================================
    # SCREEN SWITCH HANDLER
    # =========================================================
    def on_screen_select(self, _, text):
        clean_text = text.replace(" ▼", "")
        self.autosave_current_screen()
        self.current_subscreen = clean_text

        # Clear old content
        self.screen_content.clear_widgets()

        # Lazy‑load new content
        widget = self._get_or_build_screen(clean_text)
        self.screen_content.add_widget(widget)

        # Pre‑enter hooks
        if clean_text == "Introduction":
            self.on_pre_enter_intro()
        elif clean_text == "Claimant Details":
            self.on_pre_enter_claimant()
        elif clean_text == "Finances":
            self.on_pre_enter_finances()
        elif clean_text == "Housing":
            self.on_pre_enter_housing()
        elif clean_text == "Children":
            self.on_pre_enter_children()
        elif clean_text == "Additional Elements":
            self.on_pre_enter_additional()
        elif clean_text == "Sanctions":
            self.on_pre_enter_sanctions()
        elif clean_text == "Advanced Payments":
            self.on_pre_enter_advance()
        elif clean_text == "Summary":
            self.on_pre_enter_summary()

    # =========================================================
    # UI CACHING HELPERS
    # =========================================================
    def get_brma_dropdown(self, country):
        if country not in self._brma_dropdown_cache:
            dd = DropDown()
            for brma in sorted(self._brmas_by_country.get(country, [])):
                btn = RoundedButton(
                    text=brma,
                    size_hint_y=None,
                    height=44
                )
                dd.add_widget(btn)
            self._brma_dropdown_cache[country] = dd
        return self._brma_dropdown_cache[country]

    def get_child_row(self, index):
        if index >= len(self._child_row_cache):
            row = self.build_child_row(index)
            self._child_row_cache.append(row)
        return self._child_row_cache[index]

    def get_summary_section(self, title, lines):
        if title not in self._summary_section_cache:
            self._summary_section_cache[title] = self.CollapsibleSection(title, lines)
        return self._summary_section_cache[title]

    # =========================================================
    # COLLAPSIBLE SECTION CLASS
    # =========================================================
    class CollapsibleSection(BoxLayout):
        def __init__(self, title, content_lines, **kwargs):
            super().__init__(orientation="vertical", spacing=5, size_hint_y=None, **kwargs)
            self.is_open = False
            self.content_lines = content_lines

            self.header = RoundedButton(
                text=f"▶  {title}",
                size_hint=(1, None),
                height=50,
                font_size=18,
                background_color=(0, 0, 0, 0),
                color=get_color_from_hex("#FFDD00"),
                halign="left",
                valign="middle",
                text_size=(Window.width - 60, None)
            )
            self.header.bind(on_press=self.toggle)
            self.add_widget(self.header)

            self.content_box = BoxLayout(
                orientation="vertical",
                spacing=5,
                padding=(20, 0),
                size_hint_y=None,
                height=0,
                opacity=0
            )
            self.add_widget(self.content_box)

        def toggle(self, *args):
            self.is_open = not self.is_open

            if self.is_open:
                self.header.text = self.header.text.replace("▶", "▼")
                self.content_box.opacity = 1
                self.content_box.clear_widgets()

                for line in self.content_lines:
                    lbl = SafeLabel(
                        text=line,
                        font_size=16,
                        halign="left",
                        valign="middle",
                        color=get_color_from_hex("#FFFFFF"),
                        size_hint_y=None
                    )
                    lbl.bind(
                        width=lambda inst, val: setattr(inst, "text_size", (val, None)),
                        texture_size=lambda inst, val: setattr(inst, "height", val[1])
                    )
                    self.content_box.add_widget(lbl)

                total_height = sum(child.height for child in self.content_box.children)
                self.content_box.height = total_height

            else:
                self.header.text = self.header.text.replace("▼", "▶")
                self.content_box.opacity = 0
                self.content_box.height = 0
                self.content_box.clear_widgets()

    # =========================================================
    # BRMA CACHE LOADER (unchanged)
    # =========================================================
    def load_brma_cache(self):
        if hasattr(self, "_brma_cache_loaded"):
            return

        self._brma_cache_loaded = True
        self._brmas_by_country = {"England": set(), "Scotland": set(), "Wales": set()}
        self._postcode_to_brma = {}
        self._postcode_to_country = {}

        csv_path = resource_find("data/pcode_brma_lookup.csv")
        if not csv_path:
            print("BRMA CSV not found")
            return

        try:
            with open(csv_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    brma = row.get("brma_name", "").strip()
                    country_code = row.get("country", "").strip().upper()

                    if country_code == "E":
                        self._brmas_by_country["England"].add(brma)
                    elif country_code == "S":
                        self._brmas_by_country["Scotland"].add(brma)
                    elif country_code == "W":
                        self._brmas_by_country["Wales"].add(brma)

                    for key in ("PCD", "PCD2", "PCDS"):
                        p = row.get(key, "").strip().upper()
                        if p:
                            self._postcode_to_brma[p] = brma
                            self._postcode_to_country[p] = country_code

        except Exception as e:
            print("Error loading BRMA cache:", e)

    def go_to_breakdown(self, *args):
        breakdown = self.get_calculation_breakdown()
        screen = self.manager.get_screen("breakdown")
        screen.populate_breakdown(breakdown)
        self.manager.current = "breakdown"

    def get_calculation_breakdown(self):
        """
        Returns a dict of all calculation components.
        Must match the internal logic of calculate_entitlement().
        """
    
        data = self.user_data
    
        # Re-run the calculation but capture each component
        breakdown = {}
    
        # Standard allowance
        age = data.get("claimant_age")
        partner_age = data.get("partner_age")
        is_single = (data.get("relationship") == "single")
    
        if is_single:
            if age < 25:
                sa = UC_RATES["standard_allowance"]["single_u25"]
            else:
                sa = UC_RATES["standard_allowance"]["single_25plus"]
        else:
            if age < 25 and partner_age < 25:
                sa = UC_RATES["standard_allowance"]["couple_u25"]
            else:
                sa = UC_RATES["standard_allowance"]["couple_25plus"]
    
        breakdown["Standard Allowance"] = sa
    
        # Housing element
        housing = self.calculate_housing_element(data, UC_RATES)
        breakdown["Housing Element"] = housing
    
        # Child elements
        children = self.calculate_child_elements(data, UC_RATES)
        breakdown["Child Elements"] = children
    
        # Disability
        disability_element, has_lcw, has_lcwra, lcw_payable = \
            self.calculate_disability_elements(data, UC_RATES)
        breakdown["Disability Element"] = disability_element
    
        # Carer
        carer_element = UC_RATES["carer_element"] if (data.get("carer") and not has_lcwra) else 0.0
        breakdown["Carer Element"] = carer_element
    
        # Childcare
        childcare = float(data.get("childcare") or 0)
        breakdown["Childcare Costs"] = childcare
    
        # Transitional SDP
        transitional_sdp = self.calculate_transitional_sdp(
            data, UC_RATES, has_lcwra, is_single
        )
        breakdown["Transitional SDP"] = transitional_sdp
    
        # Capital deduction
        capital = float(data.get("savings") or 0)
        lower_cap = UC_RATES["capital"]["lower_limit"]
        upper_cap = UC_RATES["capital"]["upper_limit"]
        tariff_per_250 = UC_RATES["capital"]["tariff_per_250"]
    
        if capital >= upper_cap:
            capital_income = float("inf")
        elif capital < lower_cap:
            capital_income = 0.0
        else:
            blocks = ((capital - lower_cap) + 249) // 250
            capital_income = blocks * tariff_per_250
    
        breakdown["Capital Deduction"] = -capital_income
    
        # Earnings deduction
        earnings_deduction = self.calculate_earnings_deduction(
            data, UC_RATES, housing, has_lcw, has_lcwra, len(data.get("children", []))
        )
        breakdown["Earnings Deduction"] = -earnings_deduction
    
        # Sanctions
        sanction = self.calculate_sanction_reduction(
            data, UC_RATES, age, partner_age
        )
        breakdown["Sanctions"] = -sanction
    
        # Advance repayment
        advance = float(data.get("advance_amount") or 0)
        months = int(data.get("repayment_period") or 0)
        advance_deduction = advance / months if months > 0 else 0.0
        breakdown["Advance Repayment"] = -advance_deduction
    
        # Deduction caps
        deduction_caps_total = self.apply_deduction_caps(
            data, UC_RATES, sa
        )
        breakdown["Deduction Caps"] = -deduction_caps_total
    
        # Final entitlement
        total = sum(breakdown.values())
        breakdown["Final Entitlement"] = total
    
        return breakdown
    
    def is_sar_exempt(self, data):
        """
        Returns True if the claimant is exempt from the Shared Accommodation Rate.
        """
        return any([
            data.get("care_leaver"),
            data.get("severe_disability"),
            data.get("mappa"),
            data.get("hostel_resident"),
            data.get("domestic_abuse_refuge"),
            data.get("ex_offender"),
            data.get("foster_carer"),
            data.get("prospective_adopter"),
            data.get("temporary_accommodation"),
            data.get("modern_slavery"),
            data.get("armed_forces_reservist"),
        ])
    
    def calculate_earnings_deduction(self, data, UC_RATES, housing_element, has_lcw, has_lcwra, num_children):
        earnings = float(data.get("income") or 0)
        if earnings <= 0:
            return 0.0
    
        qualifies_for_WA = (
            num_children > 0 or
            has_lcw or
            has_lcwra
        )
    
        if not qualifies_for_WA:
            return earnings * UC_RATES["taper_rate"]
    
        work_allowance = (
            UC_RATES["work_allowance"]["lower"]
            if housing_element > 0
            else UC_RATES["work_allowance"]["higher"]
        )
    
        earnings_after_WA = max(0, earnings - work_allowance)
        return earnings_after_WA * UC_RATES["taper_rate"]

    def calculate_child_elements(self, data, UC_RATES):
        """
        Fully modular, DWP-accurate child element calculation:
        - Two-child limit
        - Exceptions (adoption, kinship care, multiple birth, NCC)
        - First child pre-2017 rule
        - Multiple birth addition
        - Disabled child additions (lower / higher)
        """
    
        # ---------------------------------------------------------
        # 1. Parse children safely
        # ---------------------------------------------------------
        children = self._parse_children(data.get("children", []))
        if not children:
            return 0.0
    
        # ---------------------------------------------------------
        # 2. Apply two-child limit with exceptions
        # ---------------------------------------------------------
        eligible = self._apply_two_child_limit(children)
    
        # ---------------------------------------------------------
        # 3. Calculate base child elements
        # ---------------------------------------------------------
        total = 0.0
    
        # First eligible child
        first_child = eligible[0]
        total += self._first_child_rate(first_child, UC_RATES)
    
        # Remaining eligible children
        for child in eligible[1:]:
            total += UC_RATES["child_element"]["child"]
    
        # ---------------------------------------------------------
        # 4. Add multiple birth additions
        # ---------------------------------------------------------
        total += self._multiple_birth_additions(children, UC_RATES)
    
        # ---------------------------------------------------------
        # 5. Add disabled child additions
        # ---------------------------------------------------------
        total += self._disabled_child_additions(children, UC_RATES)
    
        return total
    
    
    # ============================================================
    # MODULE 1 — PARSE CHILDREN
    # ============================================================
    def _parse_children(self, children):
        parsed = []
        for child in children:
            dob_str = child.get("dob", "")
            try:
                dob = datetime.strptime(dob_str, "%d/%m/%Y")
                parsed.append({
                    "dob": dob,
                    "raw": child
                })
            except:
                continue
    
        # Sort oldest → youngest
        parsed.sort(key=lambda c: c["dob"])
        return parsed
    
    
    # ============================================================
    # MODULE 2 — TWO-CHILD LIMIT
    # ============================================================
    def _is_exception(self, child_raw):
        return (
            child_raw.get("adopted") or
            child_raw.get("kinship_care") or
            child_raw.get("multiple_birth") or
            child_raw.get("non_consensual")
        )
    
    
    def _apply_two_child_limit(self, children):
        """
        children = list of {"dob": datetime, "raw": {...}}
        """
        eligible = []
    
        for i, child in enumerate(children):
            if i < 2:
                eligible.append(child)
            else:
                if self._is_exception(child["raw"]):
                    eligible.append(child)
    
        return eligible
    
    
    # ============================================================
    # MODULE 3 — FIRST CHILD RATE
    # ============================================================
    def _first_child_rate(self, child, UC_RATES):
        cutoff = datetime(2017, 4, 6)
        if child["dob"] < cutoff:
            return UC_RATES["child_element"]["first_child_pre2017"]
        return UC_RATES["child_element"]["child"]
    
    
    # ============================================================
    # MODULE 4 — MULTIPLE BIRTH ADDITIONS
    # ============================================================
    def _multiple_birth_additions(self, children, UC_RATES):
        """
        Correct DWP logic:
        - Group children by DOB
        - If two or more share the same DOB → multiple birth
        - First child in that birth gets NO addition
        - Additional children get the multiple birth addition
        """
    
        # Group by DOB
        from collections import defaultdict
        groups = defaultdict(list)
    
        for child in children:
            groups[child["dob"]].append(child)
    
        total = 0.0
    
        for dob, group in groups.items():
            if len(group) <= 1:
                continue  # not a multiple birth
    
            # First child in the group gets no addition
            extra_children = len(group) - 1
            total += extra_children * UC_RATES["child_element"]["multiple_birth"]
    
        return total
    
    
    # ============================================================
    # MODULE 5 — DISABLED CHILD ADDITIONS
    # ============================================================
    def _disabled_child_additions(self, children, UC_RATES):
        total = 0.0
    
        for child in children:
            raw = child["raw"]
    
            if raw.get("severely_disabled"):
                total += UC_RATES["child_element"]["disabled_child_higher"]
            elif raw.get("disabled"):
                total += UC_RATES["child_element"]["disabled_child_lower"]
    
        return total

    def calculate_disability_elements(self, data, UC_RATES):
        """
        Determines LCW / LCWRA element and applies rules:
        - LCWRA always payable unless claimant is a carer
        - LCW only payable if claimant had LCW before UC
        - LCW still gives Work Allowance even if not payable
        Returns:
            disability_element (float),
            has_lcw (bool),
            has_lcwra (bool),
            lcw_payable (bool)
        """

        data["severe_disability"] = False
        
        status = (data.get("disability") or "").upper().strip()
        is_carer = bool(data.get("carer"))
    
        has_lcw = (status == "LCW")
        has_lcwra = (status == "LCWRA")
    
        # LCWRA + Carer rule
        if has_lcwra and is_carer:
            # LCWRA removed entirely
            return 0.0, False, False, False
    
        # LCWRA always payable
        if has_lcwra:
            # LCWRA automatically counts as severe disability for SAR exemption
            data["severe_disability"] = has_lcwra
            return UC_RATES["lcw_lcwra"]["lcwra"], False, True, True
    
        # LCW logic
        if has_lcw:
            had_lcw_before = bool(data.get("had_lcw_before_uc"))
    
            if had_lcw_before:
                # LCW payable
                return UC_RATES["lcw_lcwra"]["lcw"], True, False, True
            else:
                # LCW NOT payable — but still gives Work Allowance
                return 0.0, True, False, False
        
        # No disability
        return 0.0, False, False, False

    def calculate_sanction_reduction(self, data, UC_RATES, age, partner_age):
        """
        Calculates sanction reduction using:
        - sanction_type: "low", "medium", "high"
        - sanction_duration: number of days
        - claimant type (single/couple)
        - age category
        - hardship rules (reduced sanction)
        """
    
        sanction_type = (data.get("sanction_type") or "").lower().strip()
        duration_str = data.get("sanction_duration")
    
        if not sanction_type or not duration_str:
            return 0.0
    
        try:
            days = int(duration_str)
        except:
            return 0.0
    
        # Determine claimant category
        is_single = (data.get("relationship") == "single")
    
        if is_single:
            category = "single_u25" if age < 25 else "single_25plus"
        else:
            if age < 25 and partner_age < 25:
                category = "joint_u25"
            else:
                category = "joint_25plus"
    
        # Determine daily rate based on sanction type
        if sanction_type == "high":
            daily_rate = UC_RATES["sanctions"]["daily_100"][category]
            base_rate_type = "100"
        elif sanction_type == "medium":
            daily_rate = UC_RATES["sanctions"]["daily_40"][category]
            base_rate_type = "40"
        elif sanction_type == "low":
            daily_rate = UC_RATES["sanctions"]["daily_40"][category]
            base_rate_type = "40"
        else:
            return 0.0
    
        # Hardship reduction
        hardship = bool(data.get("hardship"))
        if hardship:
            # Reduce sanction to 60% of normal
            daily_rate *= 0.6
    
        return daily_rate * days

    def apply_deduction_caps(self, data, UC_RATES, standard_allowance):
        """
        Applies UC deduction caps using only the caps defined in UC_RATES:
        - Third-party deductions (5%)
        - Rent/service charge deductions (10–15%)
        - Fraud/overpayment deductions (no individual cap, but included in overall 15%)
        - Overall maximum deduction cap (15%)
        - Child maintenance (fixed, outside cap)
        Returns total_deductions
        """
    
        # -----------------------------
        # 0. Work out claimant category
        # -----------------------------
        age = data.get("claimant_age")
        partner_age = data.get("partner_age")
        is_single = (data.get("relationship") == "single")

        if age is None:
            raise ValueError("Claimant age missing — DOB must be entered before calculation.")
        
        if data.get("relationship") == "couple" and partner_age is None:
            raise ValueError("Partner age missing — partner DOB must be entered before calculation.")
    
        if is_single:
            category = "single_u25" if age < 25 else "single_25plus"
        else:
            if age < 25 and partner_age < 25:
                category = "joint_u25"
            else:
                category = "joint_25plus"
    
        caps = UC_RATES["deduction_caps"]
    
        # -----------------------------
        # 1. Third-party deductions (5%)
        # -----------------------------
        third_party = float(data.get("third_party_deductions") or 0)
        third_party_cap = caps["third_party_5pct"][category]
        third_party = min(third_party, third_party_cap)
    
        # -----------------------------
        # 2. Rent/service charge deductions (10–15%)
        # -----------------------------
        rent_deduction = float(data.get("rent_arrears_deduction") or 0)
        min_rent = caps["rent_min_10pct"][category]
        max_rent = caps["rent_max_15pct"][category]
    
        # If there is any rent deduction, it must be between min and max
        if rent_deduction > 0:
            rent_deduction = max(min_rent, min(rent_deduction, max_rent))
        else:
            rent_deduction = 0.0
    
        # -----------------------------
        # 3. Fraud / overpayment deductions
        # -----------------------------
        fraud_deduction = float(data.get("fraud_deduction") or 0)
        overpayment = float(data.get("overpayment_deduction") or 0)
    
        # No individual caps defined in UC_RATES, they will be controlled by overall cap
        fraud_deduction = max(0.0, fraud_deduction)
        overpayment = max(0.0, overpayment)
    
        # -----------------------------
        # 4. Child maintenance (outside cap)
        # -----------------------------
        child_maintenance = float(data.get("child_maintenance") or 0)
        child_maintenance = min(child_maintenance, UC_RATES["child_maintenance_deduction"])
    
        # -----------------------------
        # 5. Apply overall 15% cap to capped deductions
        # -----------------------------
        overall_cap = caps["overall_max_15pct"][category]
    
        capped_deductions = third_party + rent_deduction + fraud_deduction + overpayment
        capped_deductions = min(capped_deductions, overall_cap)
    
        # Child maintenance is added AFTER the cap
        total_deductions = capped_deductions + child_maintenance
    
        return total_deductions

    def calculate_bedroom_entitlement(self, data):
        """
        Returns the number of bedrooms the household is entitled to.
        Based on standard UC bedroom rules.
        """
        children = data.get("children", [])
        num_children = len(children)
    
        # Adults
        is_single = (data.get("relationship") == "single")
        adults = 1 if is_single else 2
    
        bedrooms = 1  # for the claimant(s)
    
        # Children sharing rules:
        # - Two children under 10 share regardless of sex
        # - Two children under 16 of same sex share
        # - Otherwise each child gets their own room
    
        # Parse children ages
        child_ages = []
        for child in children:
            try:
                dob = datetime.strptime(child["dob"], "%d/%m/%Y")
                age = (datetime.now() - dob).days // 365
                child_ages.append((age, child.get("sex", "U")))
            except:
                continue
    
        # Sort by age
        child_ages.sort(key=lambda x: x[0])
    
        # Group children into rooms
        used = [False] * len(child_ages)
    
        for i in range(len(child_ages)):
            if used[i]:
                continue
    
            age_i, sex_i = child_ages[i]
    
            # Try to pair with another child
            paired = False
            for j in range(i + 1, len(child_ages)):
                if used[j]:
                    continue
    
                age_j, sex_j = child_ages[j]
    
                # Under 10 → always share
                if age_i < 10 and age_j < 10:
                    used[i] = used[j] = True
                    bedrooms += 1
                    paired = True
                    break
    
                # Same sex and both under 16 → share
                if sex_i == sex_j and age_i < 16 and age_j < 16:
                    used[i] = used[j] = True
                    bedrooms += 1
                    paired = True
                    break
    
            if not paired:
                used[i] = True
                bedrooms += 1
    
        return bedrooms 

    def lookup_lha_rate(self, brma, bedrooms, location):
        """
        Looks up the LHA rate for the given BRMA, bedroom entitlement, and location.
        CSV files:
            LHA-England.csv
            LHA-Scotland.csv
            LHA-Wales.csv
    
        Columns:
            BRMA, SAR, 1 Bed, 2 bed, 3 bed, 4 Bed
        """
    
        if not brma:
            return 0.0
    
        # Determine which file to load
        location = (location or "").strip().lower()
    
        if location == "england":
            filename = "LHA-England.csv"
        elif location == "scotland":
            filename = "LHA-Scotland.csv"
        elif location == "wales":
            filename = "LHA-Wales.csv"
        else:
            return 0.0
    
        csv_path = resource_find(filename)
        if not csv_path:
            return 0.0
    
        # Map bedroom entitlement to column name
        if bedrooms == "shared":
            col = "SAR"
        elif bedrooms == 1:
            col = "1 Bed"
        elif bedrooms == 2:
            col = "2 bed"
        elif bedrooms == 3:
            col = "3 bed"
        elif bedrooms >= 4:
            col = "4 Bed"
        else:
            return 0.0
    
        try:
            with open(csv_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("BRMA", "").strip().lower() == brma.lower():
                        weekly = float(row.get(col, 0) or 0)
                        # Convert weekly → monthly
                        return weekly * 52 / 12
        except Exception:
            pass
    
        return 0.0

    def calculate_non_dependant_deduction(self, data, UC_RATES):
        """
        Applies the standard non-dependant housing cost contribution.
        """
        nondeps = int(data.get("non_dependants", 0))
        if nondeps <= 0:
            return 0.0
    
        rate = UC_RATES["non_dependant"]["housing_cost_contribution"]
        return nondeps * rate

    def calculate_housing_element(self, data, UC_RATES):
        housing_type = (data.get("housing_type") or "").lower()
    
        # -----------------------------
        # Owner-occupier (mortgage)
        # -----------------------------
        if housing_type == "own":
            mortgage = float(data.get("mortgage") or 0)
            return mortgage
    
        # -----------------------------
        # Shared accommodation
        # -----------------------------
        if housing_type == "shared accommodation":
            shared = float(data.get("shared") or 0)
            return shared
    
        # -----------------------------
        # Renting (private or social)
        # -----------------------------
        rent = float(data.get("rent") or 0)
        brma = data.get("brma", "")
        location = data.get("location", "")
    
        # Non-dependant deductions
        nondep = self.calculate_non_dependant_deduction(data, UC_RATES)
    
        # SOCIAL RENT
        if location.lower() in ["england", "scotland", "wales"] and data.get("tenancy_type") == "social":
            eligible_services = self.calculate_eligible_service_charges(data)
            eligible_rent = float(data.get("rent") or 0)
        
            # Eligible rent = eligible rent + eligible service charges - non-dependant deductions
            eligible = max(0, eligible_rent + eligible_services - nondep)
            return eligible
    
        # PRIVATE RENT (LHA)
        bedrooms = self.calculate_bedroom_entitlement(data)
    
        # Shared accommodation rule
        if bedrooms == 1 and data.get("single_under_35"):
            bedrooms = "shared"
    
        # Lookup LHA rate
        lha_rate = self.lookup_lha_rate(brma, bedrooms, data.get("location"))
    
        eligible = min(rent, lha_rate)
        eligible -= nondep
        return max(0, eligible)

    def calculate_transitional_sdp(self, data, UC_RATES, has_lcwra, is_single):
        """
        Calculates Transitional SDP Element based on:
        - Whether claimant previously received SDP
        - Whether LCWRA is included in the award
        - Whether single or couple
        - Additional EDP/DP/disabled child amounts
        """
    
        if not data.get("had_sdp"):
            return 0.0
    
        rates = UC_RATES["transitional_sdp"]
    
        # Base SDP transitional protection
        if is_single:
            if has_lcwra:
                base = rates["lcwra_included"]
            else:
                base = rates["lcwra_not_included"]
        else:
            base = rates["joint_higher"]
    
        # Additional components
        extra = 0.0
    
        if data.get("extra_edp"):
            extra += rates["extra_edp_single"] if is_single else rates["extra_edp_couple"]
    
        if data.get("extra_dp"):
            extra += rates["extra_dp_single"] if is_single else rates["extra_dp_couple"]
    
        if data.get("extra_disabled_children"):
            extra += rates["extra_disabled_children"]
    
        return base + extra

    def calculate_eligible_service_charges(self, data):
        """
        Calculates eligible service charges for social rent.
        Expects data['service_charges'] to be a dict like:
            {
                "cleaning": 12.50,
                "lighting": 5.00,
                "grounds": 8.00,
                "heating": 20.00,
                "water": 15.00,
                ...
            }
        Only eligible charges are included.
        """
    
        eligible_keys = {
            "cleaning",
            "communal_cleaning",
            "lighting",
            "communal_lighting",
            "grounds",
            "grounds_maintenance",
            "lift_maintenance",
            "fire_safety",
            "door_entry",
            "shared_facilities",
            "communal_repairs",
            "estate_services",
        }
    
        charges = data.get("service_charges", {})
        if not isinstance(charges, dict):
            return 0.0
    
        total = 0.0
        for key, value in charges.items():
            if key.lower().strip() in eligible_keys:
                try:
                    total += float(value)
                except:
                    pass
    
        return total


    # -----------------------------

    def calculate_entitlement(self):
        """Full Universal Credit calculation using all modular helpers."""
    
        data = self.user_data

        if not data.get("relationship"):
            data["relationship"] = "single"

        if not data.get("tenancy_type"):
            data["tenancy_type"] = "private"

    
        # -----------------------------
        # Parse ages
        # -----------------------------
        def parse_age(dob_str):
            if not dob_str:
                return None
            try:
                dob = datetime.strptime(dob_str, "%d/%m/%Y")
                return (datetime.now() - dob).days // 365
            except:
                return None
        
        age = parse_age(data.get("claimant_dob"))
        partner_age = parse_age(data.get("partner_dob"))
        is_single = (data.get("relationship") == "single")
        
        # Strict validation
        if age is None:
            raise ValueError("Please enter a valid claimant date of birth (DD/MM/YYYY).")
        
        if not is_single and partner_age is None:
            raise ValueError("Please enter a valid partner date of birth (DD/MM/YYYY).")
        
        # Store ages for deduction caps
        data["claimant_age"] = age
        data["partner_age"] = partner_age if not is_single else None
    
        # -----------------------------
        # Children (full rules)
        # -----------------------------
        child_elements = self.calculate_child_elements(data, UC_RATES)
        children = data.get("children", [])
        num_children = len(children)

        # -----------------------------
        # Determine SAR rule (single under 35)
        # -----------------------------
        is_single = (data.get("relationship") == "single")
        num_children = len(data.get("children", []))
        age = data.get("claimant_age")
        tenancy_type = data.get("tenancy_type")
        
        data["single_under_35"] = (
            is_single and
            age is not None and age < 35 and
            num_children == 0 and
            tenancy_type == "private" and
            not self.is_sar_exempt(data)
        )
        
        # -----------------------------
        # Disability (LCW / LCWRA)
        # -----------------------------
        disability_element, has_lcw, has_lcwra, lcw_payable = \
            self.calculate_disability_elements(data, UC_RATES)
    
        # -----------------------------
        # Carer element (LCWRA conflict handled in helper)
        # -----------------------------
        is_carer = bool(data.get("carer"))
        carer_element = UC_RATES["carer_element"] if (is_carer and not has_lcwra) else 0.0
    
        # -----------------------------
        # Childcare
        # -----------------------------
        childcare_costs = float(data.get("childcare") or 0)
    
        # -----------------------------
        # Standard allowance
        # -----------------------------
        if is_single:
            if age is not None and age < 25:
                standard_allowance = UC_RATES["standard_allowance"]["single_u25"]
            else:
                standard_allowance = UC_RATES["standard_allowance"]["single_25plus"]
        else:
            if age is not None and partner_age is not None:
                if age < 25 and partner_age < 25:
                    standard_allowance = UC_RATES["standard_allowance"]["couple_u25"]
                else:
                    standard_allowance = UC_RATES["standard_allowance"]["couple_25plus"]
            else:
                standard_allowance = UC_RATES["standard_allowance"]["couple_25plus"]
    
        # -----------------------------
        # Housing element (full LHA + social rent)
        # -----------------------------
        housing_element = self.calculate_housing_element(data, UC_RATES)
    
        # -----------------------------
        # Transitional SDP
        # -----------------------------
        transitional_sdp = self.calculate_transitional_sdp(
            data,
            UC_RATES,
            has_lcwra,
            is_single
        )
    
        # -----------------------------
        # Capital deductions
        # -----------------------------
        capital = float(data.get("savings") or 0)
        lower_cap = UC_RATES["capital"]["lower_limit"]
        upper_cap = UC_RATES["capital"]["upper_limit"]
        tariff_per_250 = UC_RATES["capital"]["tariff_per_250"]
    
        if capital >= upper_cap:
            return 0.0
    
        if capital < lower_cap:
            capital_income = 0.0
        else:
            blocks = ((capital - lower_cap) + 249) // 250
            capital_income = blocks * tariff_per_250
    
        # -----------------------------
        # Earnings deduction (work allowance + taper)
        # -----------------------------
        earnings_deduction = self.calculate_earnings_deduction(
            data,
            UC_RATES,
            housing_element,
            has_lcw,
            has_lcwra,
            num_children
        )
    
        # -----------------------------
        # Sanctions (full rules + hardship)
        # -----------------------------
        sanction_reduction = self.calculate_sanction_reduction(
            data,
            UC_RATES,
            age,
            partner_age
        )
    
        # -----------------------------
        # Advance payments
        # -----------------------------
        advance = float(data.get("advance_amount") or 0)
        repayment_months = int(data.get("repayment_period") or 0)
        advance_deduction = advance / repayment_months if repayment_months > 0 else 0.0
    
        # -----------------------------
        # Total before capped deductions
        # -----------------------------
        total = (
            standard_allowance +
            housing_element +
            child_elements +
            childcare_costs +
            carer_element +
            disability_element +
            transitional_sdp
        )
    
        # Apply deductions
        total -= capital_income
        total -= earnings_deduction
        total -= sanction_reduction
        total -= advance_deduction
    
        # -----------------------------
        # Apply deduction caps
        # -----------------------------
        deduction_caps_total = self.apply_deduction_caps(
            data,
            UC_RATES,
            standard_allowance
        )
    
        total -= deduction_caps_total
    
        # -----------------------------
        # Final entitlement
        # -----------------------------
        return max(0.0, round(total, 2))



    def show_loading(self, message="Loading..."):
        # Prevent duplicate overlays
        if hasattr(self, "loading_overlay") and self.loading_overlay.parent:
            return
    
        # Fullscreen dimmed overlay
        overlay = AnchorLayout(size_hint=(1, 1), opacity=0)
    
        # Dim background
        with overlay.canvas.before:
            Color(0, 0, 0, 0.55)  # GOV.UK modal dim
            self._dim_rect = Rectangle(size=overlay.size, pos=overlay.pos)
        overlay.bind(size=lambda inst, val: setattr(self._dim_rect, "size", val))
        overlay.bind(pos=lambda inst, val: setattr(self._dim_rect, "pos", val))
    
        # Container for glow + animation + text
        box = BoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            size=(260, 260),
            spacing=10,
            padding=10
        )
    
        # Pulsing glow behind animation
        glow = PulsingGlow(size_hint=(None, None), size=(220, 220))
        box.add_widget(glow)
    
        # Animated PNG loader (your existing widget)
        loader = PNGSequenceAnimationWidget(
            size_hint=(None, None),
            size=(200, 200),
            allow_stretch=True,
            keep_ratio=True
        )
        box.add_widget(loader)
    
        # Optional loading text
        label = Label(
            text=message,
            font_size=20,
            font_name="roboto",
            color=get_color_from_hex("#FFFFFF"),
            halign="center",
            valign="middle",
            size_hint=(1, None),
            height=40
        )
    
        # Fade the text gently
        text_anim = Animation(color=(1, 1, 1, 0.4), duration=0.8) + Animation(color=(1, 1, 1, 1), duration=0.8)
        text_anim.repeat = True
        text_anim.start(label)
    
        box.add_widget(label)
    
        overlay.add_widget(box)
    
        # Store reference
        self.loading_overlay = overlay
        self.add_widget(overlay)
    
        # Fade in overlay
        Animation(opacity=1, duration=0.25).start(overlay)
    
        # Optional timeout fallback (10 seconds)
        self._loading_timeout = Clock.schedule_once(lambda dt: self.hide_loading(), 10)
    
    
    def hide_loading(self):
        if not hasattr(self, "loading_overlay") or not self.loading_overlay.parent:
            return
    
        # Cancel timeout if active
        if hasattr(self, "_loading_timeout"):
            self._loading_timeout.cancel()
    
        overlay = self.loading_overlay
    
        anim = Animation(opacity=0, duration=0.25)
        anim.bind(on_complete=lambda *args: self.remove_widget(overlay))
        anim.start(overlay)
    

    def autosave_current_screen(self):
        """Automatically save data for whichever screen the user is leaving."""
        screen = self.current_subscreen
    
        if screen == "Claimant Details":
            self.save_claimant_details()
        elif screen == "Finances":
            self.save_finances_details()
        elif screen == "Housing":
            self.save_housing_details()
        elif screen == "Children":
            self.save_children_details()
        elif screen == "Additional Elements":
            self.save_additional_elements()
        elif screen == "Sanctions":
            self.save_sanction_details()
        elif screen == "Advanced Payments":
            self.save_advance_payment_details()
        # Introduction and Summary screens don’t need saving




        
    def calculate(self, instance=None):
        """
        Wrapper that:
        - Saves all screen data
        - Runs the UC calculation
        - Shows result or error popup
        """
    
        # -----------------------------
        # 1. SAVE ALL SCREEN DATA
        # -----------------------------
        try:
            if hasattr(self, "save_claimant_details"):
                self.save_claimant_details()
    
            if hasattr(self, "save_finances_details"):
                self.save_finances_details()
    
            if hasattr(self, "save_housing_details"):
                self.save_housing_details()
    
            if hasattr(self, "save_children_details"):
                self.save_children_details()
    
            if hasattr(self, "save_additional_elements"):
                self.save_additional_elements()
    
            if hasattr(self, "save_sanction_details"):
                self.save_sanction_details()
    
            if hasattr(self, "save_advance_payment_details"):
                self.save_advance_payment_details()
    
        except Exception as e:
            Popup(
                title="Error Saving Data",
                content=SafeLabel(text=str(e)),
                size_hint=(0.8, 0.4)
            ).open()
            return
    
        # -----------------------------
        # 2. RUN THE CALCULATION
        # -----------------------------
        try:
            result = self.calculate_entitlement()
        except Exception as e:
            Popup(
                title="Calculation Error",
                content=SafeLabel(text=str(e)),
                size_hint=(0.8, 0.4)
            ).open()
            return
    
        # -----------------------------
        # 3. SHOW RESULT
        # -----------------------------
        result_text = f"Your predicted Universal Credit entitlement is:\n\n£{result:.2f}"
    
        self.summary_label.text = result_text
    
        Popup(
            title="Calculation Result",
            content=SafeLabel(
                text=result_text,
                halign="center",
                valign="middle"
            ),
            size_hint=(0.8, 0.4)
        ).open()
     
    def create_intro_screen(self):
        # Scrollable container
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
    
        # Vertical layout inside scroll
        layout = BoxLayout(
            orientation="vertical",
            spacing=20,
            padding=20,
            size_hint=(1, None)
        )
        layout.bind(minimum_height=layout.setter("height"))
    
        # Introductory text (GOV.UK style spacing)
        layout.add_widget(wrapped_SafeLabel("Welcome to the Benefit Buddy Calculator", 20, 32))
        layout.add_widget(wrapped_SafeLabel("This calculator will help you estimate your Universal Credit entitlement.", 16, 28))
        layout.add_widget(wrapped_SafeLabel("Please follow the steps to enter your details.", 16, 28))
        layout.add_widget(wrapped_SafeLabel("You can navigate through the screens using the dropdown menu above.", 16, 28))
    
        layout.add_widget(wrapped_SafeLabel("Before you start, please ensure you have the following information ready:", 16, 28))
        layout.add_widget(wrapped_SafeLabel("- Your personal details (name, date of birth, etc.)", 14, 24))
        layout.add_widget(wrapped_SafeLabel("- Your income and capital details", 14, 24))
        layout.add_widget(wrapped_SafeLabel("- Your housing situation (rent or own)", 14, 24))
        layout.add_widget(wrapped_SafeLabel("- Details of any children or dependents", 14, 24))
        layout.add_widget(wrapped_SafeLabel("- Any additional elements that may apply to you", 14, 24))
    
        scroll.add_widget(layout)
        return scroll

    def on_pre_enter_intro(self, *args):
        pass
        
    def on_couple_claim_checkbox_active(self, checkbox, value):
        # Enable/disable partner fields based on checkbox
        self.partner_name_input.disabled = not value
        self.partner_dob_input.disabled = not value


    def create_claimant_details_screen(self):
        # ---------------------------------------------------------
        # SCROLLABLE OUTER LAYOUT
        # ---------------------------------------------------------
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
    
        outer = AnchorLayout(anchor_x="center", anchor_y="center", size_hint=(1, None))
        scroll.add_widget(outer)
    
        layout = BoxLayout(
            orientation="vertical",
            spacing=20,
            padding=(20, 120, 20, 20),
            size_hint=(1, None)
        )
        layout.bind(minimum_height=layout.setter("height"))
        outer.add_widget(layout)
    
        # ---------------------------------------------------------
        # WIDGET STORAGE (for lazy-loading)
        # ---------------------------------------------------------
        self.claimant_widgets = {}
    
        # ---------------------------------------------------------
        # SECTION HEADER
        # ---------------------------------------------------------
        header_anchor = AnchorLayout(anchor_x="center", anchor_y="top", size_hint_y=None, height=60)
        header_label = SafeLabel(
            text="Select Claimant Type",
            font_size=20,
            halign="center",
            valign="middle",
            color=get_color_from_hex(WHITE)
        )
        header_label.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))
        header_anchor.add_widget(header_label)
        layout.add_widget(header_anchor)
    
        # ---------------------------------------------------------
        # CLAIMANT TYPE CHECKBOXES
        # ---------------------------------------------------------
        claimant_type_layout = BoxLayout(orientation="horizontal", spacing=20, size_hint_y=None)
        claimant_type_layout.bind(minimum_height=claimant_type_layout.setter("height"))
    
        self.claimant_widgets["single_checkbox"] = CheckBox(group="claimant_type")
        self.claimant_widgets["couple_checkbox"] = CheckBox(group="claimant_type")
    
        claimant_type_layout.add_widget(SafeLabel(text="Single", font_size=18, color=get_color_from_hex(WHITE)))
        claimant_type_layout.add_widget(self.claimant_widgets["single_checkbox"])
        claimant_type_layout.add_widget(SafeLabel(text="Couple", font_size=18, color=get_color_from_hex(WHITE)))
        claimant_type_layout.add_widget(self.claimant_widgets["couple_checkbox"])
    
        layout.add_widget(claimant_type_layout)
    
        # Bind once
        self.claimant_widgets["couple_checkbox"].bind(active=self.on_couple_claim_checkbox_active)
    
        # ---------------------------------------------------------
        # CLAIMANT DETAILS
        # ---------------------------------------------------------
        layout.add_widget(SafeLabel(text="Enter Claimant Details", font_size=20, color=get_color_from_hex(WHITE)))
    
        self.claimant_widgets["name"] = CustomTextInput(
            hint_text="Name",
            multiline=False,
            font_size=18,
            size_hint=(1, None),
            height=50,
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE)
        )
        layout.add_widget(self.claimant_widgets["name"])
    
        self.claimant_widgets["dob"] = DOBInput(
            hint_text="DD/MM/YYYY",
            multiline=False,
            font_size=18,
            size_hint=(1, None),
            height=50,
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE)
        )
        layout.add_widget(self.claimant_widgets["dob"])
    
        # ---------------------------------------------------------
        # PARTNER DETAILS
        # ---------------------------------------------------------
        layout.add_widget(SafeLabel(text="Enter Partner Details", font_size=20, color=get_color_from_hex(WHITE)))
    
        self.claimant_widgets["partner_name"] = CustomTextInput(
            hint_text="Partner Name",
            multiline=False,
            font_size=18,
            size_hint=(1, None),
            height=50,
            disabled=True,
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE)
        )
        layout.add_widget(self.claimant_widgets["partner_name"])
    
        self.claimant_widgets["partner_dob"] = DOBInput(
            hint_text="DD/MM/YYYY",
            multiline=False,
            font_size=18,
            size_hint=(1, None),
            height=50,
            disabled=True,
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE)
        )
        layout.add_widget(self.claimant_widgets["partner_dob"])
    
        return scroll
    
    # ---------------------------------------------------------
    # SAVE LOGIC
    # ---------------------------------------------------------
    def save_claimant_details(self):
        w = self.claimant_widgets
    
        if w["single_checkbox"].active:
            self.user_data["relationship"] = "single"
        elif w["couple_checkbox"].active:
            self.user_data["relationship"] = "couple"
    
        self.user_data["claimant_name"] = w["name"].text.strip()
        self.user_data["claimant_dob"] = w["dob"].text.strip()
    
        if w["couple_checkbox"].active:
            self.user_data["partner_name"] = w["partner_name"].text.strip()
            self.user_data["partner_dob"] = w["partner_dob"].text.strip()
        else:
            self.user_data["partner_name"] = ""
            self.user_data["partner_dob"] = ""
    
    # ---------------------------------------------------------
    # RESTORE LOGIC
    # ---------------------------------------------------------
    def on_pre_enter_claimant(self, *args):
        w = self.claimant_widgets
    
        # Restore relationship
        rel = self.user_data.get("relationship", "single")
        w["single_checkbox"].active = (rel == "single")
        w["couple_checkbox"].active = (rel == "couple")
    
        # Restore claimant fields
        w["name"].text = self.user_data.get("claimant_name", "")
        w["dob"].text = self.user_data.get("claimant_dob", "")
    
        # Restore partner fields
        w["partner_name"].text = self.user_data.get("partner_name", "")
        w["partner_dob"].text = self.user_data.get("partner_dob", "")
    
        is_couple = (rel == "couple")
        w["partner_name"].disabled = not is_couple
        w["partner_dob"].disabled = not is_couple


    def create_finances_screen(self):
        # ---------------------------------------------------------
        # SCROLLABLE OUTER LAYOUT
        # ---------------------------------------------------------
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
    
        outer = AnchorLayout(anchor_x="center", anchor_y="center", size_hint=(1, None))
        scroll.add_widget(outer)
    
        layout = BoxLayout(
            orientation="vertical",
            spacing=20,
            padding=(20, 120, 20, 20),
            size_hint=(1, None)
        )
        layout.bind(minimum_height=layout.setter("height"))
        outer.add_widget(layout)
    
        # ---------------------------------------------------------
        # WIDGET STORAGE (for lazy-loading)
        # ---------------------------------------------------------
        self.finances_widgets = {}
    
        # ---------------------------------------------------------
        # INSTRUCTION LABEL
        # ---------------------------------------------------------
        instruction = SafeLabel(
            text="Enter your financial details:",
            font_size=18,
            halign="center",
            valign="middle",
            color=get_color_from_hex("#005EA5")
        )
        instruction.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))
        layout.add_widget(instruction)
    
        # ---------------------------------------------------------
        # MONTHLY INCOME
        # ---------------------------------------------------------
        layout.add_widget(SafeLabel(
            text="Monthly income (£)",
            font_size=18,
            color=get_color_from_hex("#FFFFFF"),
            halign="left"
        ))
    
        self.finances_widgets["income"] = TextInput(
            hint_text="Enter monthly income (£)",
            multiline=False,
            font_size=18,
            size_hint=(1, None),
            height=50,
            input_filter="float",
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE)
        )
        layout.add_widget(self.finances_widgets["income"])
    
        # ---------------------------------------------------------
        # SAVINGS
        # ---------------------------------------------------------
        layout.add_widget(SafeLabel(
            text="Savings (£)",
            font_size=18,
            color=get_color_from_hex("#FFFFFF"),
            halign="left"
        ))
    
        self.finances_widgets["savings"] = TextInput(
            hint_text="Enter total savings (£)",
            multiline=False,
            font_size=18,
            size_hint=(1, None),
            height=50,
            input_filter="float",
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE)
        )
        layout.add_widget(self.finances_widgets["savings"])
    
        # ---------------------------------------------------------
        # DEBTS
        # ---------------------------------------------------------
        layout.add_widget(SafeLabel(
            text="Debts (£)",
            font_size=18,
            color=get_color_from_hex("#FFFFFF"),
            halign="left"
        ))
    
        self.finances_widgets["debts"] = TextInput(
            hint_text="Enter total debts (£)",
            multiline=False,
            font_size=18,
            size_hint=(1, None),
            height=50,
            input_filter="float",
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE)
        )
        layout.add_widget(self.finances_widgets["debts"])
    
        # Spacer
        layout.add_widget(Widget(size_hint_y=0.05))
    
        return scroll
    
    def save_finances_details(self):
        w = self.finances_widgets
    
        # Save raw values
        self.user_data["income_raw"] = w["income"].text.strip()
        self.user_data["savings_raw"] = w["savings"].text.strip()
        self.user_data["debts_raw"] = w["debts"].text.strip()
    
        # Parse floats safely
        try:
            self.user_data["income"] = float(w["income"].text or 0)
        except:
            self.user_data["income"] = 0.0
    
        try:
            self.user_data["savings"] = float(w["savings"].text or 0)
        except:
            self.user_data["savings"] = 0.0
    
        try:
            self.user_data["debts"] = float(w["debts"].text or 0)
        except:
            self.user_data["debts"] = 0.0
    
    def on_pre_enter_finances(self, *args):
        w = self.finances_widgets
    
        w["income"].text = str(self.user_data.get("income_raw", ""))
        w["savings"].text = str(self.user_data.get("savings_raw", ""))
        w["debts"].text = str(self.user_data.get("debts_raw", ""))

    
    def create_housing_screen(self):
        # ---------------------------------------------------------
        # SCROLLABLE OUTER LAYOUT
        # ---------------------------------------------------------
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
    
        outer = AnchorLayout(anchor_x="center", anchor_y="center", size_hint=(1, None))
        scroll.add_widget(outer)
    
        layout = BoxLayout(
            orientation="vertical",
            spacing=20,
            padding=(20, 120, 20, 20),
            size_hint=(1, None)
        )
        layout.bind(minimum_height=layout.setter("height"))
        outer.add_widget(layout)
    
        # ---------------------------------------------------------
        # WIDGET STORAGE (for lazy-loading)
        # ---------------------------------------------------------
        self.housing_widgets = {}
    
        # ---------------------------------------------------------
        # HOUSING TYPE SPINNER
        # ---------------------------------------------------------
        housing_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=70)
    
        self.housing_widgets["housing_type"] = GovUkIconSpinner(
            text="Housing Type",
            values=["Rent", "Own", "Shared Accommodation"],
            icon_map={}
        )
    
        housing_anchor.add_widget(self.housing_widgets["housing_type"])
        layout.add_widget(housing_anchor)
    
        Clock.schedule_once(lambda dt: setattr(self.housing_widgets["housing_type"], "text", "Housing Type"), 0)
    
        # ---------------------------------------------------------
        # TENANCY TYPE SPINNER
        # ---------------------------------------------------------
        self.housing_widgets["tenancy_type"] = Spinner(
            text="Select tenancy type",
            values=["private", "social"],
            size_hint=(1, None),
            height=50,
            background_color=get_color_from_hex(WHITE),
            color=get_color_from_hex(GOVUK_BLUE)
        )
        layout.add_widget(self.housing_widgets["tenancy_type"])
    
        # ---------------------------------------------------------
        # RENT / MORTGAGE / SHARED INPUTS
        # ---------------------------------------------------------
        def make_money_input(hint):
            return TextInput(
                hint_text=hint,
                multiline=False,
                font_size=18,
                size_hint=(1, None),
                height=50,
                background_color=get_color_from_hex("#FFFFFF"),
                foreground_color=get_color_from_hex("#005EA5")
            )
    
        self.housing_widgets["rent"] = make_money_input("Enter monthly rent amount (£)")
        self.housing_widgets["mortgage"] = make_money_input("Enter monthly mortgage amount (£)")
        self.housing_widgets["shared"] = make_money_input("Enter shared accommodation contribution (£)")
    
        for key in ("rent", "mortgage", "shared"):
            w = self.housing_widgets[key]
            layout.add_widget(w)
            w.opacity = 0
            w.disabled = True
            w.height = 0
    
        # ---------------------------------------------------------
        # SHOW/HIDE LOGIC FOR AMOUNT INPUTS
        # ---------------------------------------------------------
        def _show_amount_widget(value_text):
            # Hide all
            for key in ("rent", "mortgage", "shared"):
                w = self.housing_widgets[key]
                w.opacity = 0
                w.disabled = True
                w.height = 0
    
            text = (value_text or "").lower()
            if "rent" in text:
                target = self.housing_widgets["rent"]
            elif "own" in text:
                target = self.housing_widgets["mortgage"]
            elif "shared" in text:
                target = self.housing_widgets["shared"]
            else:
                return
    
            target.opacity = 1
            target.disabled = False
            target.height = 50
    
        self.housing_widgets["housing_type"].bind(text=lambda spinner, value: _show_amount_widget(value))
    
        # ---------------------------------------------------------
        # NON-DEPENDANTS
        # ---------------------------------------------------------
        self.housing_widgets["non_dependants"] = TextInput(
            hint_text="Number of non-dependants (e.g. adult children)",
            multiline=False,
            font_size=18,
            size_hint=(1, None),
            height=50,
            background_color=get_color_from_hex("#FFFFFF"),
            foreground_color=get_color_from_hex("#005EA5")
        )
        layout.add_widget(self.housing_widgets["non_dependants"])
    
        # ---------------------------------------------------------
        # POSTCODE INPUT
        # ---------------------------------------------------------
        self.housing_widgets["postcode"] = TextInput(
            hint_text="Enter postcode (e.g. SW1A 1AA)",
            multiline=False,
            font_size=18,
            size_hint=(1, None),
            height=50,
            background_color=get_color_from_hex("#FFFFFF"),
            foreground_color=get_color_from_hex("#005EA5")
        )
        layout.add_widget(self.housing_widgets["postcode"])
    
        # ---------------------------------------------------------
        # MANUAL LOCATION / BRMA OVERRIDE (COLLAPSIBLE)
        # ---------------------------------------------------------
        self.housing_widgets["manual_section_expanded"] = False
    
        manual_header = RoundedButton(
            text="Manual Location/BRMA selection ▸",
            size_hint=(1, None),
            height=50,
            background_normal="",
            background_color=(0, 0, 0, 0),
            font_size=18,
            font_name="roboto",
            color=get_color_from_hex("#FFFFFF"),
            halign="left",
            valign="middle"
        )
        manual_header.bind(
            size=lambda inst, val: setattr(inst, "text_size", (val[0] - 20, None))
        )
        layout.add_widget(manual_header)
    
        # Manual content box
        self.housing_widgets["manual_box"] = BoxLayout(
            orientation="vertical",
            spacing=10,
            size_hint=(1, None)
        )
        self.housing_widgets["manual_box"].bind(
            minimum_height=self.housing_widgets["manual_box"].setter("height")
        )
        layout.add_widget(self.housing_widgets["manual_box"])
    
        # Start collapsed
        self.housing_widgets["manual_box"].opacity = 0
        self.housing_widgets["manual_box"].disabled = True
        self.housing_widgets["manual_box"].height = 0
    
        # Toggle manual section
        def toggle_manual_section(instance):
            expanded = not self.housing_widgets["manual_section_expanded"]
            self.housing_widgets["manual_section_expanded"] = expanded
    
            if expanded:
                manual_header.text = "Manual Location/BRMA selection ▾"
                box = self.housing_widgets["manual_box"]
                box.opacity = 1
                box.disabled = False
            else:
                manual_header.text = "Manual Location/BRMA selection ▸"
                box = self.housing_widgets["manual_box"]
                box.opacity = 0
                box.disabled = True
                box.height = 0
    
        manual_header.bind(on_press=toggle_manual_section)
    
        # ---------------------------------------------------------
        # MANUAL OVERRIDE TOGGLE
        # ---------------------------------------------------------
        toggle_row = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=50)
    
        self.housing_widgets["manual_toggle"] = CheckBox(size_hint=(None, None), size=(40, 40))
        manual_label = SafeLabel(
            text="Enable manual Location/BRMA override",
            font_size=16,
            color=get_color_from_hex("#FFFFFF")
        )
        manual_label.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))
    
        toggle_row.add_widget(self.housing_widgets["manual_toggle"])
        toggle_row.add_widget(manual_label)
        self.housing_widgets["manual_box"].add_widget(toggle_row)
    
        # Enable/disable location + BRMA spinners
        def toggle_manual_mode(instance, value):
            self.housing_widgets["location"].disabled = not value
            self.housing_widgets["brma"].disabled = not value
    
        self.housing_widgets["manual_toggle"].bind(active=toggle_manual_mode)
    
        # ---------------------------------------------------------
        # LOCATION SPINNER
        # ---------------------------------------------------------
        location_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=70)
    
        self.housing_widgets["location"] = GovUkIconSpinner(
            text="Select Location",
            values=["England", "Scotland", "Wales"],
            icon_map={}
        )
        location_anchor.add_widget(self.housing_widgets["location"])
        self.housing_widgets["manual_box"].add_widget(location_anchor)
    
        self.housing_widgets["location"].disabled = True
    
        # ---------------------------------------------------------
        # BRMA SPINNER (cached values later)
        # ---------------------------------------------------------
        brma_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=70)
    
        self.housing_widgets["brma"] = GovUkIconSpinner(
            text="Select BRMA",
            values=["Select BRMA"],
            icon_map={}
        )
        brma_anchor.add_widget(self.housing_widgets["brma"])
        self.housing_widgets["manual_box"].add_widget(brma_anchor)
    
        self.housing_widgets["brma"].disabled = True
    
        Clock.schedule_once(lambda dt: setattr(self.housing_widgets["brma"], "text", "Select BRMA"), 0)
    
        # ---------------------------------------------------------
        # SERVICE CHARGES (COLLAPSIBLE)
        # ---------------------------------------------------------
        self.housing_widgets["service_section_expanded"] = False
    
        service_header = RoundedButton(
            text="Eligible Service Charges (Social Rent Only) ▸",
            size_hint=(1, None),
            height=50,
            background_normal="",
            background_color=(0, 0, 0, 0),
            font_size=18,
            font_name="roboto",
            color=get_color_from_hex("#FFFFFF"),
            halign="left",
            valign="middle"
        )
        service_header.bind(
            size=lambda inst, val: setattr(inst, "text_size", (val[0] - 20, None))
        )
        layout.add_widget(service_header)
    
        self.housing_widgets["service_box"] = BoxLayout(
            orientation="vertical",
            spacing=10,
            size_hint=(1, None)
        )
        self.housing_widgets["service_box"].bind(
            minimum_height=self.housing_widgets["service_box"].setter("height")
        )
        layout.add_widget(self.housing_widgets["service_box"])
    
        # Start collapsed
        box = self.housing_widgets["service_box"]
        box.opacity = 0
        box.disabled = True
        box.height = 0
    
        # Add service charge rows (cached)
        self.housing_widgets["service_fields"] = {}
    
        def add_service_charge_row(label_text, key):
            row = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=50)
    
            lbl = SafeLabel(
                text=label_text,
                font_size=16,
                color=get_color_from_hex("#FFFFFF"),
                halign="left"
            )
            lbl.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))
    
            ti = TextInput(
                hint_text="£0.00",
                multiline=False,
                font_size=18,
                size_hint=(1, None),
                height=50,
                background_color=get_color_from_hex("#FFFFFF"),
                foreground_color=get_color_from_hex("#005EA5")
            )
    
            self.housing_widgets["service_fields"][key] = ti
    
            row.add_widget(lbl)
            row.add_widget(ti)
            self.housing_widgets["service_box"].add_widget(row)
    
        # Add all service charge fields
        add_service_charge_row("Cleaning", "cleaning")
        add_service_charge_row("Communal Cleaning", "communal_cleaning")
        add_service_charge_row("Lighting", "lighting")
        add_service_charge_row("Communal Lighting", "communal_lighting")
        add_service_charge_row("Grounds Maintenance", "grounds")
        add_service_charge_row("Lift Maintenance", "lift")
        add_service_charge_row("Fire Safety", "fire_safety")
        add_service_charge_row("Door Entry System", "door_entry")
        add_service_charge_row("Shared Facilities", "shared_facilities")
        add_service_charge_row("Communal Repairs", "communal_repairs")
        add_service_charge_row("Estate Services", "estate_services")
    
        # Toggle service section
        def toggle_service_section(instance):
            if service_header.disabled:
                return
    
            expanded = not self.housing_widgets["service_section_expanded"]
            self.housing_widgets["service_section_expanded"] = expanded
    
            if expanded:
                service_header.text = "Eligible Service Charges (Social Rent Only) ▾"
                box.opacity = 1
                box.disabled = False
            else:
                service_header.text = "Eligible Service Charges (Social Rent Only) ▸"
                box.opacity = 0
                box.disabled = True
                box.height = 0
    
        service_header.bind(on_press=toggle_service_section)
    
        # Enable/disable service charges based on tenancy type
        def toggle_service_charges(spinner, value):
            social = (value.lower() == "social")
    
            service_header.disabled = not social
            service_header.opacity = 1 if social else 0.4
    
            for ti in self.housing_widgets["service_fields"].values():
                ti.disabled = not social
    
            if not social:
                self.housing_widgets["service_section_expanded"] = False
                service_header.text = "Eligible Service Charges (Social Rent Only) ▸"
                box.opacity = 0
                box.disabled = True
                box.height = 0
    
        self.housing_widgets["tenancy_type"].bind(text=toggle_service_charges)
    
        # ---------------------------------------------------------
        # FIND BRMA BUTTON
        # ---------------------------------------------------------
        find_brma_btn = RoundedButton(
            text="Find BRMA",
            size_hint=(None, None),
            size=(250, 60),
            background_normal="",
            background_color=(0, 0, 0, 0),
            font_size=20,
            font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            halign="center",
            valign="middle",
            text_size=(250, None),
            pos_hint={"center_x": 0.5}
        )
        layout.add_widget(find_brma_btn)
    
        def on_find_brma(instance):
            postcode = self.housing_widgets["postcode"].text.strip().upper()
    
            self.show_loading("Finding BRMA...")
    
            def do_lookup(dt):
                brma_name = self.lookup_brma(postcode)
    
                self.housing_widgets["brma"].values = [brma_name]
                self.housing_widgets["brma"].text = brma_name
                self.housing_widgets["brma"]._update_dropdown()
    
                location = self.lookup_location_for_postcode(postcode)
                if location:
                    self.housing_widgets["location"].text = location
    
                self.hide_loading()
    
            Clock.schedule_once(do_lookup, 0.1)
    
        find_brma_btn.bind(on_press=on_find_brma)
    
        # ---------------------------------------------------------
        # INITIAL STATE SYNC
        # ---------------------------------------------------------
        _show_amount_widget(self.housing_widgets["housing_type"].text)
    
        return scroll
    
    def lookup_brma(self, postcode):
        self.load_brma_cache()
        return self._postcode_to_brma.get(postcode, "BRMA not found")
    
    def lookup_location_for_postcode(self, postcode):
        self.load_brma_cache()
        code = self._postcode_to_country.get(postcode)
        return {"E": "England", "S": "Scotland", "W": "Wales"}.get(code)
    
    def save_housing_details(self):
        w = self.housing_widgets
    
        # Basic fields
        self.user_data["housing_type"] = w["housing_type"].text.strip().lower()
        self.user_data["tenancy_type"] = w["tenancy_type"].text.strip().lower()
    
        self.user_data["rent_raw"] = w["rent"].text.strip()
        self.user_data["mortgage_raw"] = w["mortgage"].text.strip()
        self.user_data["shared_raw"] = w["shared"].text.strip()
    
        self.user_data["non_dependants_raw"] = w["non_dependants"].text.strip()
        self.user_data["postcode"] = w["postcode"].text.strip()
    
        self.user_data["location"] = w["location"].text.strip()
        self.user_data["brma"] = w["brma"].text.strip()
    
        self.user_data["manual_location"] = w["manual_toggle"].active
    
        # SERVICE CHARGES
        charges = {}
    
        def parse_charge(widget):
            try:
                return float(widget.text or 0)
            except:
                return 0.0
    
        for key, widget in w["service_fields"].items():
            charges[key] = parse_charge(widget)
    
        self.user_data["service_charges"] = charges
    
        # Parsed numeric values
        try:
            self.user_data["non_dependants"] = int(w["non_dependants"].text or 0)
        except:
            self.user_data["non_dependants"] = 0
    
        try:
            self.user_data["rent"] = float(w["rent"].text or 0)
        except:
            self.user_data["rent"] = 0.0
    
        try:
            self.user_data["mortgage"] = float(w["mortgage"].text or 0)
        except:
            self.user_data["mortgage"] = 0.0
    
        try:
            self.user_data["shared"] = float(w["shared"].text or 0)
        except:
            self.user_data["shared"] = 0.0
    
    def on_pre_enter_housing(self, *args):
        w = self.housing_widgets
    
        # Restore basic fields
        w["housing_type"].text = self.user_data.get("housing_type", "Rent").capitalize()
        w["tenancy_type"].text = self.user_data.get("tenancy_type", "Select tenancy type")
    
        w["rent"].text = str(self.user_data.get("rent_raw", ""))
        w["mortgage"].text = str(self.user_data.get("mortgage_raw", ""))
        w["shared"].text = str(self.user_data.get("shared_raw", ""))
        w["non_dependants"].text = str(self.user_data.get("non_dependants_raw", ""))
        w["postcode"].text = self.user_data.get("postcode", "")
    
        # Manual override
        manual = self.user_data.get("manual_location", False)
        w["manual_toggle"].active = manual
        w["location"].disabled = not manual
        w["brma"].disabled = not manual
    
        w["location"].text = self.user_data.get("location", "Select Location")
        w["brma"].text = self.user_data.get("brma", "Select BRMA")
    
        # Show correct rent/mortgage/shared input
        text = w["housing_type"].text.lower()
    
        for key in ("rent", "mortgage", "shared"):
            field = w[key]
            field.opacity = 0
            field.disabled = True
            field.height = 0
    
        if "rent" in text:
            target = w["rent"]
        elif "own" in text:
            target = w["mortgage"]
        elif "shared" in text:
            target = w["shared"]
        else:
            target = None
    
        if target:
            target.opacity = 1
            target.disabled = False
            target.height = 50
    
        # Restore service charges
        charges = self.user_data.get("service_charges", {})
    
        for key, widget in w["service_fields"].items():
            widget.text = str(charges.get(key, ""))
    
        # Re-apply tenancy-dependent service charge enable/disable
        tenancy = w["tenancy_type"].text.strip().lower()
        social = (tenancy == "social")
    
        for widget in w["service_fields"].values():
            widget.disabled = not social
        

    def create_children_screen(self):
        # ---------------------------------------------------------
        # SCROLLABLE, CENTERED, UPWARD-BIASED OUTER LAYOUT
        # ---------------------------------------------------------
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
    
        outer = AnchorLayout(anchor_x="center", anchor_y="center", size_hint=(1, None))
        scroll.add_widget(outer)
    
        layout = BoxLayout(
            orientation="vertical",
            spacing=20,
            padding=(20, 120, 20, 20),  # upward bias
            size_hint=(1, None)
        )
        layout.bind(minimum_height=layout.setter("height"))
        outer.add_widget(layout)
    
        # Keep reference for dynamic insertion
        self.children_layout = layout
    
        # ---------------------------------------------------------
        # INSTRUCTION LABEL
        # ---------------------------------------------------------
        instruction = SafeLabel(
            text="Enter children details:",
            font_size=18,
            halign="center",
            valign="middle",
            color=get_color_from_hex("#005EA5")
        )
        instruction.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))
        layout.add_widget(instruction)
    
        # ---------------------------------------------------------
        # CHILDREN CONTAINER
        # ---------------------------------------------------------
        self.child_sections = []  # list of dicts: {header_btn, content_box, widgets...}
    
        saved_children = self.user_data.get("children", [])
    
        if not saved_children:
            self.add_child_section()
        else:
            for child in saved_children:
                self.add_child_section(prefill=child)
    
        # ---------------------------------------------------------
        # SPACER ABOVE BUTTONS
        # ---------------------------------------------------------
        layout.add_widget(Widget(size_hint_y=0.05))
    
        # ---------------------------------------------------------
        # ADD CHILD BUTTON
        # ---------------------------------------------------------
        add_btn = RoundedButton(
            text="Add Another Child",
            size_hint=(None, None),
            size=(250, 60),
            background_color=(0, 0, 0, 0),
            background_normal="",
            pos_hint={"center_x": 0.5},
            font_size=20,
            font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            halign="center",
            valign="middle",
            text_size=(250, None),
            on_press=self.add_child_section
        )
        layout.add_widget(add_btn)
    
        # ---------------------------------------------------------
        # SPACER BELOW BUTTONS
        # ---------------------------------------------------------
        layout.add_widget(Widget(size_hint_y=0.05))
    
        return scroll
    
    
    # ---------------------------------------------------------
    # ADD CHILD SECTION
    # ---------------------------------------------------------
    def add_child_section(self, instance=None, prefill=None):
        """
        Creates a collapsible child section with:
        - Name
        - DOB
        - Gender
        - Adoption / Kinship / Multiple birth flags
        - Remove button
        """
    
        # ---------------------------------------------------------
        # COLLAPSIBLE HEADER
        # ---------------------------------------------------------
        header_btn = RoundedButton(
            text="▸ New Child",
            size_hint=(1, None),
            height=50,
            background_color=(0, 0, 0, 0),
            background_normal="",
            color=get_color_from_hex(WHITE),
            font_size=18,
            halign="left",
            valign="middle"
        )
        header_btn.bind(
            width=lambda inst, val: setattr(inst, "text_size", (val, None))
        )
    
        # ---------------------------------------------------------
        # CONTENT BOX (starts collapsed)
        # ---------------------------------------------------------
        content_box = BoxLayout(
            orientation="vertical",
            spacing=10,
            padding=(10, 10),
            size_hint=(1, None),
            height=0,
            opacity=0
        )
    
        # ---------------------------------------------------------
        # CHILD NAME
        # ---------------------------------------------------------
        name_input = CustomTextInput(
            hint_text="Child Name",
            multiline=False,
            font_size=18,
            size_hint=(1, None),
            height=50,
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE),
            text=prefill.get("name", "") if prefill else ""
        )
        content_box.add_widget(name_input)
    
        # ---------------------------------------------------------
        # CHILD DOB
        # ---------------------------------------------------------
        dob_input = DOBInput(
            hint_text="Child Date of Birth (DD/MM/YYYY)",
            multiline=False,
            font_size=18,
            size_hint=(1, None),
            height=50,
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE),
            text=prefill.get("dob", "") if prefill else ""
        )
        content_box.add_widget(dob_input)
    
        # ---------------------------------------------------------
        # GENDER SPINNER
        # ---------------------------------------------------------
        gender_spinner = GovUkIconSpinner(
            text=prefill.get("gender", "Select gender") if prefill else "Select gender",
            values=["Male", "Female", "Prefer not to say"],
            icon_map={}
        )
        content_box.add_widget(gender_spinner)
    
        # ---------------------------------------------------------
        # FLAGS
        # ---------------------------------------------------------
        def make_flag(label, value=False):
            row = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=40)
            cb = CheckBox(active=value)
            lbl = SafeLabel(text=label, font_size=16, color=get_color_from_hex(WHITE))
            row.add_widget(cb)
            row.add_widget(lbl)
            return row, cb
    
        adopted_row, adopted_cb = make_flag("Adopted", prefill.get("adopted", False) if prefill else False)
        kinship_row, kinship_cb = make_flag("Kinship care", prefill.get("kinship_care", False) if prefill else False)
        multiple_row, multiple_cb = make_flag("Multiple birth", prefill.get("multiple_birth", False) if prefill else False)
    
        content_box.add_widget(adopted_row)
        content_box.add_widget(kinship_row)
        content_box.add_widget(multiple_row)
    
        # ---------------------------------------------------------
        # REMOVE CHILD BUTTON
        # ---------------------------------------------------------
        remove_btn = RoundedButton(
            text="Remove Child",
            size_hint=(None, None),
            size=(200, 50),
            background_color=(0, 0, 0, 0),
            background_normal="",
            color=get_color_from_hex("#D4351C"),  # GOV.UK red
            font_size=16,
            on_press=lambda inst: self.remove_child_section(section)
        )
        content_box.add_widget(remove_btn)
    
        # ---------------------------------------------------------
        # COLLAPSE/EXPAND LOGIC
        # ---------------------------------------------------------
        def toggle_section(instance):
            if content_box.height == 0:
                # Expand
                content_box.height = content_box.minimum_height
                content_box.opacity = 1
                header_btn.text = f"▾ {self.get_child_header_text(section)}"
            else:
                # Collapse
                content_box.height = 0
                content_box.opacity = 0
                header_btn.text = f"▸ {self.get_child_header_text(section)}"
    
        header_btn.bind(on_press=toggle_section)
    
        # ---------------------------------------------------------
        # STORE SECTION
        # ---------------------------------------------------------
        section = {
            "header": header_btn,
            "content": content_box,
            "name": name_input,
            "dob": dob_input,
            "gender": gender_spinner,
            "adopted": adopted_cb,
            "kinship": kinship_cb,
            "multiple": multiple_cb
        }
    
        self.child_sections.append(section)
    
        # ---------------------------------------------------------
        # INSERT INTO LAYOUT ABOVE BUTTONS
        # ---------------------------------------------------------
        insert_index = len(self.children_layout.children) - 2
        self.children_layout.add_widget(header_btn, index=insert_index)
        self.children_layout.add_widget(content_box, index=insert_index)
    
    
    # ---------------------------------------------------------
    # REMOVE CHILD SECTION
    # ---------------------------------------------------------
    def remove_child_section(self, section):
        if section in self.child_sections:
            self.child_sections.remove(section)
            self.children_layout.remove_widget(section["header"])
            self.children_layout.remove_widget(section["content"])
    
    
    # ---------------------------------------------------------
    # HEADER TEXT (Child 1 (Name))
    # ---------------------------------------------------------
    def get_child_header_text(self, section):
        index = self.child_sections.index(section) + 1
        name = section["name"].text.strip()
        return f"Child {index} ({name})" if name else f"Child {index}"
    
    
    # ---------------------------------------------------------
    # SAVE LOGIC
    # ---------------------------------------------------------
    def save_children_details(self):
        children = []
    
        for section in self.child_sections:
            name = section["name"].text.strip()
            dob = section["dob"].text.strip()
            gender = section["gender"].text.strip()
    
            if not dob:
                continue  # skip empty entries
    
            children.append({
                "name": name,
                "dob": dob,
                "gender": gender,
                "adopted": section["adopted"].active,
                "kinship_care": section["kinship"].active,
                "multiple_birth": section["multiple"].active
            })
    
        self.user_data["children"] = children
        self.user_data["children_dobs"] = [c["dob"] for c in children]
    
    
    # ---------------------------------------------------------
    # RESTORE LOGIC
    # ---------------------------------------------------------
    def on_pre_enter_children(self, *args):
        saved_children = self.user_data.get("children", [])
    
        # Clear existing
        for section in list(self.child_sections):
            self.remove_child_section(section)
    
        # Rebuild
        if not saved_children:
            self.add_child_section()
        else:
            for child in saved_children:
                self.add_child_section(prefill=child)

    
    def create_additional_elements_screen(self):
        # ---------------------------------------------------------
        # SCROLLABLE OUTER LAYOUT
        # ---------------------------------------------------------
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
    
        outer = AnchorLayout(anchor_x="center", anchor_y="center", size_hint=(1, None))
        scroll.add_widget(outer)
    
        layout = BoxLayout(
            orientation="vertical",
            spacing=20,
            padding=(20, 120, 20, 20),
            size_hint=(1, None)
        )
        layout.bind(minimum_height=layout.setter("height"))
        outer.add_widget(layout)
    
        # ---------------------------------------------------------
        # WIDGET STORAGE (for lazy-loading)
        # ---------------------------------------------------------
        self.additional_widgets = {}
        w = self.additional_widgets
        w["sar_fields"] = {}
    
        # ---------------------------------------------------------
        # INSTRUCTION
        # ---------------------------------------------------------
        instruction = SafeLabel(
            text="Enter additional elements:",
            font_size=18,
            halign="center",
            valign="middle",
            color=get_color_from_hex("#005EA5")
        )
        instruction.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))
        layout.add_widget(instruction)
    
        # ---------------------------------------------------------
        # CARER CHECKBOX
        # ---------------------------------------------------------
        carer_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=50, spacing=10)
        w["carer"] = CheckBox(size_hint=(None, None), size=(40, 40))
    
        carer_label = SafeLabel(
            text="Are you a carer?",
            font_size=18,
            color=get_color_from_hex("#FFFFFF"),
            halign="left"
        )
        carer_label.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))
    
        carer_row.add_widget(w["carer"])
        carer_row.add_widget(carer_label)
        layout.add_widget(carer_row)
    
        # ---------------------------------------------------------
        # DISABILITY: LCW / LCWRA (mutually exclusive)
        # ---------------------------------------------------------
        disability_title = SafeLabel(
            text="Disability status",
            font_size=18,
            color=get_color_from_hex("#FFFFFF"),
            halign="left"
        )
        disability_title.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))
        layout.add_widget(disability_title)
    
        # LCW
        lcw_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=50, spacing=10)
        w["lcw"] = CheckBox(size_hint=(None, None), size=(40, 40))
    
        lcw_label = SafeLabel(
            text="Limited Capability for Work (LCW)",
            font_size=16,
            color=get_color_from_hex("#FFFFFF"),
            halign="left"
        )
        lcw_label.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))
    
        lcw_row.add_widget(w["lcw"])
        lcw_row.add_widget(lcw_label)
        layout.add_widget(lcw_row)
    
        # LCWRA
        lcwra_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=50, spacing=10)
        w["lcwra"] = CheckBox(size_hint=(None, None), size=(40, 40))
    
        lcwra_label = SafeLabel(
            text="Limited Capability for Work and Related Activity (LCWRA)",
            font_size=16,
            color=get_color_from_hex("#FFFFFF"),
            halign="left"
        )
        lcwra_label.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))
    
        lcwra_row.add_widget(w["lcwra"])
        lcwra_row.add_widget(lcwra_label)
        layout.add_widget(lcwra_row)
    
        # Mutual exclusion
        def on_lcw_active(instance, value):
            if value:
                w["lcwra"].active = False
    
        def on_lcwra_active(instance, value):
            if value:
                w["lcw"].active = False
    
        w["lcw"].bind(active=on_lcw_active)
        w["lcwra"].bind(active=on_lcwra_active)
    
        # ---------------------------------------------------------
        # CHILDCARE INPUT
        # ---------------------------------------------------------
        w["childcare"] = TextInput(
            hint_text="Monthly childcare costs (£)",
            multiline=False,
            font_size=18,
            size_hint=(1, None),
            height=50,
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE)
        )
        layout.add_widget(w["childcare"])
    
        # ---------------------------------------------------------
        # SAR EXEMPTIONS (COLLAPSIBLE)
        # ---------------------------------------------------------
        w["sar_expanded"] = False
    
        sar_header = RoundedButton(
            text="Shared Accommodation Rate (SAR) Exemptions ▸",
            size_hint=(1, None),
            height=50,
            background_color=(0, 0, 0, 0),
            background_normal="",
            font_size=20,
            font_name="roboto",
            color=get_color_from_hex("#FFFFFF"),
            halign="left",
            valign="middle",
        )
        sar_header.bind(
            size=lambda inst, val: setattr(inst, "text_size", (val[0] - 20, None))
        )
        layout.add_widget(sar_header)
    
        w["sar_box"] = BoxLayout(
            orientation="vertical",
            spacing=10,
            size_hint=(1, None)
        )
        w["sar_box"].bind(minimum_height=w["sar_box"].setter("height"))
        layout.add_widget(w["sar_box"])
    
        # Start collapsed
        w["sar_box"].opacity = 0
        w["sar_box"].disabled = True
        w["sar_box"].height = 0
    
        # Helper to add SAR rows
        def add_sar_row(text, key):
            row = BoxLayout(orientation="horizontal", size_hint_y=None, height=40, spacing=10)
            cb = CheckBox(size_hint=(None, None), size=(40, 40))
            w["sar_fields"][key] = cb
    
            lbl = SafeLabel(
                text=text,
                font_size=16,
                color=get_color_from_hex("#FFFFFF"),
                halign="left"
            )
            lbl.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))
    
            row.add_widget(cb)
            row.add_widget(lbl)
            w["sar_box"].add_widget(row)
    
        # Add all SAR fields
        add_sar_row("Care leaver (under 25)", "care_leaver")
        add_sar_row("Severe disability (LCWRA)", "severe_disability")
        add_sar_row("MAPPA supervision", "mappa")
        add_sar_row("Hostel resident (3+ months)", "hostel_resident")
        add_sar_row("Domestic abuse refuge", "domestic_abuse")
        add_sar_row("Ex-offender under supervision", "ex_offender")
        add_sar_row("Foster carer", "foster_carer")
        add_sar_row("Prospective adopter", "prospective_adopter")
        add_sar_row("Temporary accommodation", "temporary_accommodation")
        add_sar_row("Victim of modern slavery", "modern_slavery")
        add_sar_row("Armed forces reservist returning to civilian life", "armed_forces")
    
        # Toggle SAR section
        def toggle_sar_section(instance):
            expanded = not w["sar_expanded"]
            w["sar_expanded"] = expanded
    
            if expanded:
                sar_header.text = "Shared Accommodation Rate (SAR) Exemptions ▾"
                w["sar_box"].opacity = 1
                w["sar_box"].disabled = False
            else:
                sar_header.text = "Shared Accommodation Rate (SAR) Exemptions ▸"
                w["sar_box"].opacity = 0
                w["sar_box"].disabled = True
                w["sar_box"].height = 0
    
        sar_header.bind(on_press=toggle_sar_section)
    
        # ---------------------------------------------------------
        # SPACERS / BUTTONS (structure preserved)
        # ---------------------------------------------------------
        layout.add_widget(Widget(size_hint_y=0.05))
    
        buttons_box = BoxLayout(orientation="vertical", spacing=20, size_hint=(1, None))
        layout.add_widget(buttons_box)
    
        layout.add_widget(Widget(size_hint_y=0.05))
    
        return scroll
    
    def save_additional_elements(self):
        w = self.additional_widgets
    
        # Carer
        self.user_data["carer"] = w["carer"].active
    
        # Disability: LCW / LCWRA
        lcw = w["lcw"].active
        lcwra = w["lcwra"].active
    
        self.user_data["disability_flag"] = lcw or lcwra
    
        if lcwra:
            self.user_data["disability"] = "LCWRA"
        elif lcw:
            self.user_data["disability"] = "LCW"
        else:
            self.user_data["disability"] = ""
    
        # Childcare
        self.user_data["childcare_raw"] = w["childcare"].text.strip()
        try:
            self.user_data["childcare"] = float(w["childcare"].text or 0)
        except:
            self.user_data["childcare"] = 0.0
    
        # SAR exemptions
        sar = w["sar_fields"]
        self.user_data["care_leaver"] = sar["care_leaver"].active
        self.user_data["severe_disability"] = sar["severe_disability"].active
        self.user_data["mappa"] = sar["mappa"].active
        self.user_data["hostel_resident"] = sar["hostel_resident"].active
        self.user_data["domestic_abuse_refuge"] = sar["domestic_abuse"].active
        self.user_data["ex_offender"] = sar["ex_offender"].active
        self.user_data["foster_carer"] = sar["foster_carer"].active
        self.user_data["prospective_adopter"] = sar["prospective_adopter"].active
        self.user_data["temporary_accommodation"] = sar["temporary_accommodation"].active
        self.user_data["modern_slavery"] = sar["modern_slavery"].active
        self.user_data["armed_forces_reservist"] = sar["armed_forces"].active
    
    def on_pre_enter_additional(self, *args):
        w = self.additional_widgets
    
        # Carer
        w["carer"].active = self.user_data.get("carer", False)
    
        # Disability
        disability_value = self.user_data.get("disability", "").upper()
        if disability_value == "LCWRA":
            w["lcwra"].active = True
            w["lcw"].active = False
        elif disability_value == "LCW":
            w["lcw"].active = True
            w["lcwra"].active = False
        else:
            w["lcw"].active = False
            w["lcwra"].active = False
    
        # Childcare
        w["childcare"].text = str(self.user_data.get("childcare_raw", ""))
    
        # SAR exemptions
        sar = w["sar_fields"]
        sar["care_leaver"].active = self.user_data.get("care_leaver", False)
        sar["severe_disability"].active = self.user_data.get("severe_disability", False)
        sar["mappa"].active = self.user_data.get("mappa", False)
        sar["hostel_resident"].active = self.user_data.get("hostel_resident", False)
        sar["domestic_abuse"].active = self.user_data.get("domestic_abuse_refuge", False)
        sar["ex_offender"].active = self.user_data.get("ex_offender", False)
        sar["foster_carer"].active = self.user_data.get("foster_carer", False)
        sar["prospective_adopter"].active = self.user_data.get("prospective_adopter", False)
        sar["temporary_accommodation"].active = self.user_data.get("temporary_accommodation", False)
        sar["modern_slavery"].active = self.user_data.get("modern_slavery", False)
        sar["armed_forces"].active = self.user_data.get("armed_forces_reservist", False)
    
        # Collapse SAR section on re-entry
        w["sar_expanded"] = False
        w["sar_box"].opacity = 0
        w["sar_box"].disabled = True
        w["sar_box"].height = 0


    def create_sanction_screen(self):
        # ---------------------------------------------------------
        # SCROLLABLE OUTER LAYOUT
        # ---------------------------------------------------------
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
    
        outer = AnchorLayout(anchor_x="center", anchor_y="center", size_hint=(1, None))
        scroll.add_widget(outer)
    
        layout = BoxLayout(
            orientation="vertical",
            spacing=20,
            padding=(20, 120, 20, 20),
            size_hint=(1, None)
        )
        layout.bind(minimum_height=layout.setter("height"))
        outer.add_widget(layout)
    
        # ---------------------------------------------------------
        # WIDGET STORAGE
        # ---------------------------------------------------------
        self.sanctions_widgets = {}
        w = self.sanctions_widgets
    
        # ---------------------------------------------------------
        # INSTRUCTION LABEL
        # ---------------------------------------------------------
        instruction = SafeLabel(
            text="Enter sanction details:",
            font_size=18,
            halign="center",
            valign="middle",
            color=get_color_from_hex("#005EA5")
        )
        instruction.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))
        layout.add_widget(instruction)
    
        # ---------------------------------------------------------
        # SANCTION TYPE
        # ---------------------------------------------------------
        sanction_type_label = SafeLabel(
            text="Sanction type",
            font_size=18,
            color=get_color_from_hex("#FFFFFF"),
            halign="left"
        )
        sanction_type_label.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))
        layout.add_widget(sanction_type_label)
    
        w["type"] = GovUkIconSpinner(
            text="Select sanction type",
            values=["lowest", "low", "medium", "high"],
            icon_map={}
        )
        layout.add_widget(w["type"])
    
        # ---------------------------------------------------------
        # SANCTION DURATION
        # ---------------------------------------------------------
        sanction_duration_label = SafeLabel(
            text="Sanction duration",
            font_size=18,
            color=get_color_from_hex("#FFFFFF"),
            halign="left"
        )
        sanction_duration_label.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))
        layout.add_widget(sanction_duration_label)
    
        w["duration"] = GovUkIconSpinner(
            text="Select duration",
            values=[
                "7 days",
                "14 days",
                "28 days",
                "91 days",
                "182 days"
            ],
            icon_map={}
        )
        layout.add_widget(w["duration"])
    
        # ---------------------------------------------------------
        # SPACERS / BUTTONS (structure preserved)
        # ---------------------------------------------------------
        layout.add_widget(Widget(size_hint_y=0.05))
    
        buttons_box = BoxLayout(orientation="vertical", spacing=20, size_hint=(1, None))
        layout.add_widget(buttons_box)
    
        layout.add_widget(Widget(size_hint_y=0.05))
    
        return scroll
    
    def save_sanction_details(self):
        w = self.sanctions_widgets
    
        # Save sanction type
        self.user_data["sanction_type"] = w["type"].text.strip().lower()
    
        # Save raw duration string
        self.user_data["sanction_duration_raw"] = w["duration"].text.strip()
    
        # Convert duration to integer days
        try:
            duration_str = w["duration"].text.split()[0]
            self.user_data["sanction_duration"] = int(duration_str)
        except:
            self.user_data["sanction_duration"] = 0
    
    def on_pre_enter_sanctions(self, *args):
        w = self.sanctions_widgets
    
        # Restore sanction type
        saved_type = self.user_data.get("sanction_type", "")
        if saved_type in ["lowest", "low", "medium", "high"]:
            w["type"].text = saved_type
        else:
            w["type"].text = "Select sanction type"
    
        # Restore sanction duration
        saved_duration = self.user_data.get("sanction_duration_raw", "")
        valid_durations = ["7 days", "14 days", "28 days", "91 days", "182 days"]
    
        if saved_duration in valid_durations:
            w["duration"].text = saved_duration
        else:
            w["duration"].text = "Select duration"


    def create_advance_payments_screen(self):
        # ---------------------------------------------------------
        # SCROLLABLE OUTER LAYOUT
        # ---------------------------------------------------------
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
    
        outer = AnchorLayout(anchor_x="center", anchor_y="center", size_hint=(1, None))
        scroll.add_widget(outer)
    
        layout = BoxLayout(
            orientation="vertical",
            spacing=20,
            padding=(20, 120, 20, 20),
            size_hint=(1, None)
        )
        layout.bind(minimum_height=layout.setter("height"))
        outer.add_widget(layout)
    
        # ---------------------------------------------------------
        # WIDGET STORAGE
        # ---------------------------------------------------------
        self.advance_widgets = {}
        w = self.advance_widgets
    
        # ---------------------------------------------------------
        # INSTRUCTION LABEL
        # ---------------------------------------------------------
        instruction = SafeLabel(
            text="Enter advance payment details:",
            font_size=18,
            halign="center",
            valign="middle",
            color=get_color_from_hex("#005EA5")
        )
        instruction.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))
        layout.add_widget(instruction)
    
        # ---------------------------------------------------------
        # ADVANCE AMOUNT
        # ---------------------------------------------------------
        amount_label = SafeLabel(
            text="Advance amount (£)",
            font_size=18,
            color=get_color_from_hex("#FFFFFF"),
            halign="left"
        )
        amount_label.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))
        layout.add_widget(amount_label)
    
        w["amount"] = TextInput(
            hint_text="Enter amount (£)",
            multiline=False,
            font_size=18,
            size_hint=(1, None),
            height=50,
            input_filter="float",
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE)
        )
        layout.add_widget(w["amount"])
    
        # ---------------------------------------------------------
        # REPAYMENT PERIOD
        # ---------------------------------------------------------
        repayment_label = SafeLabel(
            text="Repayment period",
            font_size=18,
            color=get_color_from_hex("#FFFFFF"),
            halign="left"
        )
        repayment_label.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))
        layout.add_widget(repayment_label)
    
        w["period"] = GovUkIconSpinner(
            text="Select repayment period",
            values=[
                "3 months",
                "6 months",
                "9 months",
                "12 months"
            ],
            icon_map={}
        )
        layout.add_widget(w["period"])
    
        # ---------------------------------------------------------
        # SPACERS / BUTTONS (structure preserved)
        # ---------------------------------------------------------
        layout.add_widget(Widget(size_hint_y=0.05))
    
        buttons_box = BoxLayout(orientation="vertical", spacing=20, size_hint=(1, None))
        layout.add_widget(buttons_box)
    
        layout.add_widget(Widget(size_hint_y=0.05))
    
        return scroll
    
    def save_advance_payment_details(self):
        w = self.advance_widgets
    
        # Save advance amount
        raw_amount = w["amount"].text.strip()
        self.user_data["advance_amount_raw"] = raw_amount
    
        try:
            self.user_data["advance_amount"] = float(raw_amount or 0)
        except:
            self.user_data["advance_amount"] = 0.0
    
        # Save repayment period
        self.user_data["repayment_period_raw"] = w["period"].text.strip()
    
        # Convert repayment period to integer months
        try:
            months_str = w["period"].text.split()[0]
            self.user_data["repayment_period"] = int(months_str)
        except:
            self.user_data["repayment_period"] = 0
    
    def on_pre_enter_advance(self, *args):
        w = self.advance_widgets
    
        # Restore advance amount
        w["amount"].text = str(self.user_data.get("advance_amount_raw", ""))
    
        # Restore repayment period
        saved_period = self.user_data.get("repayment_period_raw", "")
        valid_periods = ["3 months", "6 months", "9 months", "12 months"]
    
        if saved_period in valid_periods:
            w["period"].text = saved_period
        else:
            w["period"].text = "Select repayment period"

            
    def create_calculate_screen(self):
        # OUTER LAYOUT
        outer = BoxLayout(
            orientation="vertical",
            spacing=0,
            padding=0
        )
    
        # ============================
        # TOP: SCROLLABLE SUMMARY AREA
        # ============================
        self.calculate_scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            do_scroll_y=True
        )
    
        summary_layout = BoxLayout(
            orientation="vertical",
            spacing=30,
            padding=20,
            size_hint=(1, None)
        )
        summary_layout.bind(minimum_height=summary_layout.setter("height"))
    
        # -----------------------------------------
        # WIDGET STORAGE FOR SUMMARY SCREEN
        # -----------------------------------------
        self.summary_widgets = {}
        w = self.summary_widgets
    
        # Title
        summary_layout.add_widget(
            wrapped_SafeLabel(
                "Summary of your Universal Credit calculation:",
                18,
                30
            )
        )
    
        # Summary text placeholder
        w["label"] = SafeLabel(
            text="No calculation yet.",
            font_size=16,
            halign="left",
            valign="top",
            color=get_color_from_hex("#FFFFFF"),
            size_hint_y=None
        )
        w["label"].bind(
            width=lambda inst, val: setattr(inst, "text_size", (val, None)),
            texture_size=lambda inst, val: setattr(inst, "height", val[1])
        )
        summary_layout.add_widget(w["label"])
    
        self.calculate_scroll.add_widget(summary_layout)
        outer.add_widget(self.calculate_scroll)
    
        # ============================
        # BOTTOM: FIXED BUTTON BAR
        # ============================
        button_bar = BoxLayout(
            size_hint=(1, None),
            height=100,
            padding=20
        )
    
        run_btn = RoundedButton(
            text="Run Calculation",
            size_hint=(1, 1),
            background_color=(0, 0, 0, 0),
            background_normal="",
            font_size=20,
            font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            halign="center",
            valign="middle",
            text_size=(250, None),
            on_press=self.run_calculation
        )
        button_bar.add_widget(run_btn)
    
        breakdown_btn = RoundedButton(
            text="View Calculation Breakdown",
            size_hint=(1, 1),
            background_color=(0, 0, 0, 0),
            font_size=20,
            on_press=self.go_to_breakdown
        )
        button_bar.add_widget(breakdown_btn)
    
        outer.add_widget(button_bar)
    
        return outer
        
    def run_calculation(self, *args):
        try:
            if hasattr(self, "save_claimant_details"):
                self.save_claimant_details()
            if hasattr(self, "save_finances_details"):
                self.save_finances_details()
            if hasattr(self, "save_housing_details"):
                self.save_housing_details()
            if hasattr(self, "save_children_details"):
                self.save_children_details()
            if hasattr(self, "save_additional_elements"):
                self.save_additional_elements()
            if hasattr(self, "save_sanction_details"):
                self.save_sanction_details()
            if hasattr(self, "save_advance_payment_details"):
                self.save_advance_payment_details()
        except Exception as e:
            self.summary_widgets["label"].text = f"Error saving data: {str(e)}"
            return
    
        try:
            result = self.calculate_entitlement()
            result_text = f"Calculated Entitlement: £{result:.2f}"
            self.user_data["calculation_result"] = result_text
        except Exception as e:
            self.summary_widgets["label"].text = f"Error during calculation: {str(e)}"
            return
    
        try:
            self.on_pre_enter_summary()
        except Exception as e:
            self.summary_widgets["label"].text = f"Error updating summary: {str(e)}"
            return
    
        Clock.schedule_once(lambda dt: setattr(self.calculate_scroll, "scroll_y", 1.0), 0)
    
    def on_pre_enter_summary(self, *args):
        d = self.user_data
    
        summary_layout = self.calculate_scroll.children[0]
        summary_layout.clear_widgets()
    
        summary_layout.add_widget(
            wrapped_SafeLabel(
                "Summary of your Universal Credit calculation:",
                18,
                30
            )
        )
    
        def add_section(title, lines):
            section = CollapsibleSection(title, lines)
            summary_layout.add_widget(section)
    
        # Claimant
        add_section("Claimant Details", [
            f"Claimant DOB: {d.get('claimant_dob')}",
            f"Partner DOB: {d.get('partner_dob')}",
            f"Relationship: {d.get('relationship')}",
        ])
    
        # Finances
        add_section("Finances", [
            f"Income: £{d.get('income')}",
            f"Savings: £{d.get('savings')}",
            f"Debts: £{d.get('debts')}",
        ])
    
        # Housing
        add_section("Housing", [
            f"Housing Type: {d.get('housing_type')}",
            f"Tenancy Type: {d.get('tenancy_type')}",
            f"Rent: £{d.get('rent')}",
            f"Mortgage: £{d.get('mortgage')}",
            f"Shared Accommodation Charge: £{d.get('shared')}",
            f"Non-dependants: {d.get('non_dependants')}",
            f"Postcode: {d.get('postcode')}",
            f"Location: {d.get('location')}",
            f"BRMA: {d.get('brma')}",
            f"Manual BRMA Mode: {d.get('manual_location')}",
        ])
    
        # Service Charges
        charges = d.get("service_charges", {})
        if charges:
            add_section("Service Charges (Social Rent)", [
                f"{k.replace('_', ' ').title()}: £{v}" for k, v in charges.items()
            ])
    
        # Children
        child_lines = [f"Number of Children: {len(d.get('children', []))}"]
        for i, child in enumerate(d.get("children", []), start=1):
            child_lines.extend([
                f"Child {i}:",
                f"  DOB: {child.get('dob')}",
                f"  Sex: {child.get('gender')}",
                f"  Adopted: {child.get('adopted')}",
                f"  Kinship Care: {child.get('kinship_care')}",
                f"  Multiple Birth: {child.get('multiple_birth')}",
            ])
        add_section("Children", child_lines)
    
        # Additional Elements
        add_section("Additional Elements", [
            f"Carer: {d.get('carer')}",
            f"Disability: {d.get('disability')}",
            f"Childcare Costs: £{d.get('childcare')}",
        ])
    
        # SAR Exemptions
        add_section("SAR Exemptions", [
            f"Care Leaver: {d.get('care_leaver')}",
            f"Severe Disability: {d.get('severe_disability')}",
            f"MAPPA: {d.get('mappa')}",
            f"Hostel Resident: {d.get('hostel_resident')}",
            f"Domestic Abuse Refuge: {d.get('domestic_abuse_refuge')}",
            f"Ex-Offender: {d.get('ex_offender')}",
            f"Foster Carer: {d.get('foster_carer')}",
            f"Prospective Adopter: {d.get('prospective_adopter')}",
            f"Temporary Accommodation: {d.get('temporary_accommodation')}",
            f"Modern Slavery Victim: {d.get('modern_slavery')}",
            f"Armed Forces Reservist: {d.get('armed_forces_reservist')}",
        ])
    
        # Sanctions
        add_section("Sanctions", [
            f"Type: {d.get('sanction_type')}",
            f"Duration: {d.get('sanction_duration')} days",
        ])
    
        # Advance Payments
        add_section("Advance Payments", [
            f"Amount: £{d.get('advance_amount')}",
            f"Repayment Period: {d.get('repayment_period')} months",
        ])
    
        # Calculation Result
        if d.get("calculation_result"):
            add_section("Calculation Result", [
                d["calculation_result"]
            ])
    
        Clock.schedule_once(lambda dt: setattr(self.calculate_scroll, "scroll_y", 1.0), 0)


class CalculationBreakdownScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # -----------------------------------------
        # WIDGET STORAGE (lazy-loading compatible)
        # -----------------------------------------
        self.breakdown_widgets = {}
        w = self.breakdown_widgets

        outer = BoxLayout(orientation="vertical", spacing=20, padding=20)

        # Title
        title = wrapped_SafeLabel("Calculation Breakdown", 22, 40)
        outer.add_widget(title)

        # Scrollable table
        w["scroll"] = ScrollView(size_hint=(1, 1))

        w["table"] = BoxLayout(
            orientation="vertical",
            spacing=10,
            padding=10,
            size_hint=(1, None)
        )
        w["table"].bind(minimum_height=w["table"].setter("height"))

        w["scroll"].add_widget(w["table"])
        outer.add_widget(w["scroll"])

        # Back button
        back_btn = RoundedButton(
            text="Back to Summary",
            size_hint=(1, None),
            height=60,
            on_press=self.go_back
        )
        outer.add_widget(back_btn)

        self.add_widget(outer)

    def go_back(self, *args):
        self.manager.current = "summary"

    def populate_breakdown(self, breakdown_dict):
        """Fill the table with calculation components."""
        w = self.breakdown_widgets
        table = w["table"]

        table.clear_widgets()

        for label, amount in breakdown_dict.items():
            row = BoxLayout(orientation="horizontal", size_hint_y=None, height=40)

            lbl = SafeLabel(
                text=label,
                font_size=18,
                color=get_color_from_hex("#FFFFFF"),
                halign="left"
            )
            lbl.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))

            amt = SafeLabel(
                text=f"£{amount:.2f}",
                font_size=18,
                color=get_color_from_hex("#FFDD00"),
                halign="right"
            )
            amt.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))

            row.add_widget(lbl)
            row.add_widget(amt)
            table.add_widget(row)


# TO DO:

# check advance payments logic/summary
# check the sanctions logic/summary

# check for the need for non-dependent deductions
# check for the need for child maintenance deductions
 
# positioning and spread of widgets, etc.
# sort logic for payment prediction for the full access account

# create a settings screen to allow the user to change the app's:
#   theme,
#   font size,
#   language,
#   links to other applications,
#   links to help and support,
#   and other preferences


# add a feature to allow the user to reset all inputs and summaries
# add a feature to allow the user to save their inputs and summaries
# add a feature to allow the user to load their inputs and summaries

# add a save feature to save the user's data to a file
# add a load feature to load the user's data from a file





# Run the app
if __name__ == "__main__":
    BenefitBuddy().run()
























