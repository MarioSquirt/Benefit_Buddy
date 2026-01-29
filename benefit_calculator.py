#BenefitCalculator.py


# import necessary libraries

# --- Kivy core ---
from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.core.window import Window
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
from kivy.uix.spinner import Spinner, SpinnerOption
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
from math import sin, cos, radians
from datetime import datetime



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
Window.maximize()

# Bind the window size to adjust the layout dynamically
def adjust_layout(instance, value):
    for widget in instance.children:
        if isinstance(widget, BoxLayout):
            widget.size = (Window.width, Window.height) # Set the size to match the window size

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
        sm.add_widget(SplashScreen(name="splash"))
        sm.add_widget(DisclaimerScreen(name="disclaimer"))
        sm.add_widget(SettingsScreen(name="settings"))
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(CreateAccountPage(name="create_account"))
        sm.add_widget(LoginPage(name="log_in"))
        sm.add_widget(MainScreenGuestAccess(name="main_guest_access"))
        sm.add_widget(MainScreenFullAccess(name="main_full_access"))
        sm.add_widget(Calculator(name="calculator")) 
        # Add more screens as needed
        return sm

    def on_start(self):
        self.run_startup_diagnostics()

    def run_startup_diagnostics(self):
        print("=== Startup Diagnostics ===")

        # --- Asset check ---
        required_assets = [
            "images/logo.png",
            "data/pcode_brma_lookup.csv",
            "font/roboto.ttf"
        ]
        for asset in required_assets:
            path = resource_find(asset)
            if path and os.path.exists(path):
                print(f"[OK] Asset: {asset}")
            else:
                print(f"[MISSING] Asset: {asset}")

        # --- Widget check ---
        critical_widgets = [
            ("Claimant Name Input", getattr(self, "name_input", None)),
            ("Claimant DOB Input", getattr(self, "dob_input", None)),
            ("Partner Name Input", getattr(self, "partner_name_input", None)),
            ("Partner DOB Input", getattr(self, "partner_dob_input", None)),
            ("Income Input", getattr(self, "income_input", None)),
            ("Capital Input", getattr(self, "capital_input", None)),
            ("Housing Type Spinner", getattr(self, "housing_type_spinner", None)),
            ("Location Spinner", getattr(self, "location_spinner", None)),
            ("BRMA Spinner", getattr(self, "brma_spinner", None)),
            ("Sanction Level Spinner", getattr(self, "sanction_level_spinner", None)),
            ("Advance Payments Input", getattr(self, "advance_payments_input", None)),
        ]

        for label, widget in critical_widgets:
            if widget is None:
                print(f"[MISSING] Widget: {label}")
            else:
                try:
                    # Simple sanity check: can we access text/value?
                    if hasattr(widget, "text"):
                        _ = widget.text
                    print(f"[OK] Widget: {label}")
                except Exception as e:
                    print(f"[ERROR] Widget: {label} failed with {e}")

        print("===========================")



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
        allowed_chars = "0123456789/"
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

# Customizing Spinner to change dropdown background color
class CustomSpinnerOption(SpinnerOption):
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
        if isinstance(ts, (ObservableList, list, tuple)):
            ts = tuple(ts)
        else:
            ts = (Window.width - 60, 0)

        if len(ts) != 2:
            ts = (Window.width - 60, 0)

        w, h = ts
        w = int(w) if w not in (None, 0) else int(Window.width - 60)
        h = int(h) if h is not None else 0
        kwargs["text_size"] = (w, h)

        # --- PADDING ---
        pad = kwargs.get("padding", None)
        if isinstance(pad, (ObservableList, list, tuple)):
            pad = tuple(int(v) if v is not None else 0 for v in pad)
            if all(v == 0 for v in pad):
                kwargs["padding"] = (10, 10)
            else:
                kwargs["padding"] = pad
        else:
            kwargs["padding"] = (10, 10)

        super().__init__(**kwargs)

        # --- Styling (your original code) ---
        self.background_color = get_color_from_hex("#FFFFFF")  # White background
        self.color = get_color_from_hex("#005EA5")             # GOVUK_BLUE text color
        self.background_normal = ""                            # Remove default background image

        # 🔑 Bind text_size dynamically to width and window resize
        self.bind(width=self._update_text_size)
        Window.bind(size=lambda *_: self._update_text_size())

    def _update_text_size(self, *args):
        self.text_size = (self.width - 20, None)



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

        # GOV.UK white background
        self.canvas.before.clear()
        with self.canvas.before:
            Color(1, 1, 1, 1)  # white
            self.bg = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self._update_bg, size=self._update_bg)

        if icon_path:
            self.add_widget(Image(
                source=icon_path,
                size_hint=(None, None),
                size=(28, 28),
                allow_stretch=True,
                keep_ratio=True
            ))

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


class GovUkIconSpinner(GovUkSpinner):
    def __init__(self, icon_map=None, **kwargs):
        self.icon_map = icon_map or {}
        super().__init__(**kwargs)

    def _build_dropdown(self):
        dropdown = DropDown()
    
        # Background (already working)
        with dropdown.canvas.before:
            Color(1, 1, 1, 1)
            dropdown.bg = Rectangle(pos=dropdown.pos, size=dropdown.size)
    
        dropdown.bind(on_select=lambda instance, value: setattr(self, "text", value))
    
        for value in self.values:
            icon_path = self.icon_map.get(value, None)
            row = IconRow(text=value, icon_path=icon_path)
    
            # When row is clicked, tell dropdown what was selected
            row.bind(on_release=lambda row_instance: dropdown.select(row_instance.label.text))
    
            dropdown.add_widget(row)
    
        self._dropdown = dropdown





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

def show_loading(self, message="Loading..."):
    if hasattr(self, "loading_overlay") and self.loading_overlay.parent:
        return

    overlay = AnchorLayout(size_hint=(1, 1), opacity=0)

    box = BoxLayout(
        orientation="vertical",
        size_hint=(None, None),
        size=(300, 180),
        padding=20,
        spacing=15,
        pos_hint={"center_x": 0.5, "center_y": 0.5},
    )

    with box.canvas.before:
        Color(0, 0, 0, 0.75)
        self.bg_rect = Rectangle(size=box.size, pos=box.pos)
    box.bind(size=lambda inst, val: setattr(self.bg_rect, "size", val))
    box.bind(pos=lambda inst, val: setattr(self.bg_rect, "pos", val))

    loader = PNGSequenceAnimationWidget(size_hint=(None, None), size=(80, 80))
    box.add_widget(loader)

    label = Label(
        text=message,
        font_size=22,
        font_name="roboto",
        color=get_color_from_hex("#FFFFFF"),
        halign="center",
        valign="middle",
        text_size=(280, None)
    )
    box.add_widget(label)

    overlay.add_widget(box)
    self.loading_overlay = overlay
    self.root.add_widget(overlay)

    Animation(opacity=1, duration=0.25).start(overlay)


def hide_loading(self):
    if not hasattr(self, "loading_overlay") or not self.loading_overlay.parent:
        return

    overlay = self.loading_overlay
    anim = Animation(opacity=0, duration=0.25)
    anim.bind(on_complete=lambda *args: self.root.remove_widget(overlay))
    anim.start(overlay)


# Define the Settings Screen
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


# Define the Splash Screen
class SplashScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Main vertical layout
        layout = BoxLayout(orientation="vertical", spacing=30, padding=30)

        # Header pinned to top
        header_anchor = AnchorLayout(anchor_x="center", anchor_y="top", size_hint_y=None, height=80)
        build_header(header_anchor, "Benefit Buddy")
        layout.add_widget(header_anchor)

        # Logo centered and resized
        logo_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=0.4)
        logo = Image(
            source="images/logo.png",          # ensure correct path
            size_hint=(0.5, 0.5),  # half the width/height of its anchor
            allow_stretch=True,
            keep_ratio=True
        )
        logo_anchor.add_widget(logo)
        layout.add_widget(logo_anchor)

        # Loading animation centered below logo
        loading_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=120)
        loading_animation = PNGSequenceAnimationWidget(
            size_hint=(None, None), size=(100, 100),
            pos_hint={"center_x": 0.5}
        )
        loading_anchor.add_widget(loading_animation)
        layout.add_widget(loading_anchor)

        # Footer pinned to bottom
        footer_anchor = AnchorLayout(anchor_x="center", anchor_y="bottom", size_hint_y=None, height=60)
        build_footer(footer_anchor)
        layout.add_widget(footer_anchor)

        self.add_widget(layout)

    def on_enter(self):
        Clock.schedule_once(self.switch_to_disclaimer, 5)

    def switch_to_disclaimer(self, dt):
        self.manager.current = "disclaimer"


# Disclaimer Screen
class DisclaimerScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", spacing=10, padding=20)

        disclaimer_text = SafeLabel(
            text=("Disclaimer: This app is currently still in development and may not be fully accurate.\n\n"
                  "It is for informational purposes only and does not constitute financial advice.\n\n\n"
                  "Guest access has limited functionality and will not save your data."),
            font_size=18,
            halign="center",
            valign="middle",
            color=get_color_from_hex("#FFFFFF")
        )
        disclaimer_text.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
        layout.add_widget(disclaimer_text)

        build_footer(layout)
        self.add_widget(layout)

    def on_enter(self):
        Clock.schedule_once(self.switch_to_main, 5)

    def switch_to_main(self, dt):
        self.manager.current = "main"

# Define the main screen for the app
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
class Calculator(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Central state dictionary
        self.user_data = {
            "claimant_dob": "",
            "partner_dob": "",
            "relationship": "",
            "income": "",
            "savings": "",
            "debts": "",
            "housing_type": "",
            "rent": "",
            "mortgage": "",
            "postcode": "",
            "brma": "",
            "children": [],
            "carer": False,
            "disability": False,
            "childcare": "",
            "sanction_type": "",
            "sanction_duration": "",
            "advance_amount": "",
            "repayment_period": ""
        }
        
        layout = BoxLayout(orientation="vertical", spacing=30, padding=20)

        # Header
        header_anchor = AnchorLayout(anchor_x="center", anchor_y="top", size_hint_y=None, height=80)
        build_header(header_anchor, "Benefit Buddy")
        layout.add_widget(header_anchor)

        # Spacer
        layout.add_widget(Widget(size_hint_y=0.05))

        # Back button (consistent style, centered)
        button_style = {
            "size_hint": (None, None),
            "size": (250, 60),
            "background_color": (0, 0, 0, 0),
            "background_normal": "",
            "pos_hint": {"center_x": 0.5},
            "halign": "center",
            "valign": "middle",
            "text_size": (250, None)
        }
        back_button = RoundedButton(
            text="Back to Guest Access",
            **button_style,
            font_size=20, font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            on_press=lambda x: setattr(self.manager, 'current', "main_guest_access")
        )
        layout.add_widget(back_button)

        # Spacer before spinner
        layout.add_widget(Widget(size_hint_y=0.05))

        # Define screens
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


        # Spinner
        spinner_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=70)
        
        self.screen_spinner = GovUkIconSpinner(
            text="Introduction",
            icon_map=ICON_PATHS,
            values=[name for name, _ in self.screens],
        )
        
        spinner_anchor.add_widget(self.screen_spinner)
        layout.add_widget(spinner_anchor)


        # Container for screen content
        self.screen_content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        self.screen_content.add_widget(self.create_intro_screen())

        def on_screen_select(_, text):
            clean_text = text.replace(" ▼", "")
            self.screen_content.clear_widgets()
            for name, builder in self.screens:
                if name == clean_text:
                    widget = builder()
                    self.screen_content.add_widget(widget)
                    # Manually trigger the right pre_enter
                    if name == "Introduction":
                        self.on_pre_enter_intro()
                    elif name == "Claimant Details":
                        self.on_pre_enter_claimant()
                    elif name == "Finances":
                        self.on_pre_enter_finances()
                    elif name == "Housing":
                        self.on_pre_enter_housing()
                    elif name == "Children":
                        self.on_pre_enter_children()
                    elif name == "Additional Elements":
                        self.on_pre_enter_additional()
                    elif name == "Sanctions":
                        self.on_pre_enter_sanctions()
                    elif name == "Advanced Payments":
                        self.on_pre_enter_advance()
                    elif name == "Summary":
                        self.on_pre_enter_summary()
                    break

        self.screen_spinner.bind(text=on_screen_select)
        layout.add_widget(self.screen_content)

        # Spacer before footer
        layout.add_widget(Widget(size_hint_y=0.05))

        # Footer
        footer_anchor = AnchorLayout(anchor_x="center", anchor_y="bottom", size_hint_y=None, height=60)
        build_footer(footer_anchor)
        layout.add_widget(footer_anchor)

        self.add_widget(layout)

        
    def calculate(self, instance):
        try:
            data = self.manager.user_data  # central state dictionary
    
            # Claimant details
            dob_str = data.get("claimant_dob", "")
            if not dob_str:
                content = SafeLabel(text="Please enter your date of birth.", halign="center", valign="middle")
                Popup(title="Missing Input", content=content, size_hint=(0.8, 0.4)).open()
                return
    
            try:
                dob = datetime.strptime(dob_str, "%d/%m/%Y")
            except Exception:
                content = SafeLabel(text="Please enter DOB in format DD/MM/YYYY.", halign="center", valign="middle")
                Popup(title="Invalid Input", content=content, size_hint=(0.8, 0.4)).open()
                return
    
            age = (datetime.now() - dob).days // 365
            is_single = data.get("relationship", "single").lower() == "single"
    
            partner_age = None
            if data.get("relationship") == "couple" and data.get("partner_dob"):
                try:
                    partner_dob = datetime.strptime(data["partner_dob"], "%d/%m/%Y")
                    partner_age = (datetime.now() - partner_dob).days // 365
                except Exception:
                    content = SafeLabel(text="Partner DOB must be DD/MM/YYYY.", halign="center", valign="middle")
                    Popup(title="Invalid Input", content=content, size_hint=(0.8, 0.4)).open()
                    return
    
            # Income and capital
            try:
                income = float(data.get("income", 0) or 0)
            except Exception:
                Popup(title="Invalid Input", content=SafeLabel(text="Income must be a number."), size_hint=(0.8, 0.4)).open()
                return
    
            try:
                capital = float(data.get("savings", 0) or 0)
            except Exception:
                Popup(title="Invalid Input", content=SafeLabel(text="Savings must be a number."), size_hint=(0.8, 0.4)).open()
                return
    
            # Children
            child_elements = 0
            children_dobs = data.get("children", [])
            for i, dob_str in enumerate(children_dobs):
                try:
                    child_dob = datetime.strptime(dob_str, "%d/%m/%Y")
                    if i == 0:
                        child_elements += 339 if child_dob < datetime(2017, 4, 6) else 292.81
                    elif i == 1:
                        child_elements += 292.81
                    else:
                        child_elements += 292.81  # add special flags if stored
                except Exception:
                    Popup(title="Invalid Date", content=SafeLabel(text="Children DOBs must be DD/MM/YYYY."), size_hint=(0.8, 0.4)).open()
                    return
    
            # Additional elements
            carer_element = 201.68 if data.get("carer") else 0
            childcare_costs = float(data.get("childcare", 0) or 0)
    
            # Work capability
            work_capability = 0
            if data.get("lcwra"):
                work_capability = 423.27
            elif data.get("lcw_2017"):
                work_capability = 158.76
    
            # Standard allowance
            standard_allowance = 0
            if is_single:
                standard_allowance = 316.98 if age < 25 else 400.14
            else:
                if partner_age is not None:
                    standard_allowance = 497.55 if age < 25 and partner_age < 25 else 628.10
    
            # Housing element
            housing_element = 0
            housing_type = data.get("housing_type", "").lower()
            if housing_type == "rent":
                rent_value = float(data.get("rent", 0) or 0)
                brma = data.get("brma", "")
                location = data.get("location", "")
                if not location or not brma:
                    Popup(title="Missing Housing Info", content=SafeLabel(text="Please select Location and BRMA."), size_hint=(0.8, 0.4)).open()
                    return
                # TODO: plug in your LHA lookup logic here
                lha_rate = rent_value
                housing_element = min(rent_value, lha_rate)
            elif housing_type == "own":
                housing_element = float(data.get("mortgage", 0) or 0)
            elif housing_type == "shared accommodation":
                housing_element = float(data.get("rent", 0) or 0)
    
            # Work allowance
            has_children = len(children_dobs) > 0
            receives_housing_support = housing_type == "rent"
            work_allowance = 411 if (has_children or data.get("lcw")) and receives_housing_support else (684 if has_children else 0)
    
            # Total before deductions
            total_allowance = (
                standard_allowance +
                housing_element +
                child_elements +
                childcare_costs +
                carer_element +
                work_capability
            )
    
            # Capital income deduction
            capital_income = 0
            if capital < 6000:
                capital_income = 0
            elif capital >= 16000:
                Popup(title="Calculation Result", content=SafeLabel(text="Not eligible due to capital over £16,000."), size_hint=(0.8, 0.4)).open()
                return
            else:
                blocks = ((capital - 6000) + 249) // 250
                capital_income = blocks * 4.35
    
            # Sanctions
            sanctions = float(data.get("sanctions", 0) or 0)
    
            # Advance payments
            advance_amount = float(data.get("advance_amount", 0) or 0)
            repayment_period = int(data.get("repayment_period", 0) or 0)
            advance_payments = advance_amount / repayment_period if repayment_period > 0 else 0
    
            # Final entitlement
            entitlement = total_allowance - capital_income - sanctions - advance_payments
            
            # Update summary label
            self.summary_label.text = f"Your predicted entitlement is: £{entitlement:.2f}"
            
            # ALSO show a popup
            content = SafeLabel(
                text=f"Your predicted entitlement is: £{entitlement:.2f}",
                halign="center", valign="middle"
            )
            Popup(title="Calculation Result", content=content, size_hint=(0.8, 0.4)).open()
    
        except Exception as e:
            Popup(title="Error", content=SafeLabel(text=str(e)), size_hint=(0.8, 0.4)).open()

     
    def create_intro_screen(self):
        # Use a ScrollView to make the intro screen vertically scrollable
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
        layout = BoxLayout(orientation="vertical", spacing=30, padding=20, size_hint=(1, None))
        layout.bind(minimum_height=layout.setter('height'))  # Let layout expand vertically
    
        # Introductory text
        layout.add_widget(wrapped_SafeLabel("Welcome to the Benefit Buddy Calculator", 18, 30))
        layout.add_widget(wrapped_SafeLabel("This calculator will help you estimate your Universal Credit entitlement.", 16, 30))
        layout.add_widget(wrapped_SafeLabel("Please follow the steps to enter your details.", 14, 24))
        layout.add_widget(wrapped_SafeLabel("You can navigate through the screens using the dropdown menu above.", 14, 24))
        layout.add_widget(wrapped_SafeLabel("Before you start, please ensure you have the following information ready:", 14, 24))
        layout.add_widget(wrapped_SafeLabel("- Your personal details (name, date of birth, etc.)", 14, 24))
        layout.add_widget(wrapped_SafeLabel("- Your income and capital details", 14, 24))
        layout.add_widget(wrapped_SafeLabel("- Your housing situation (rent or own)", 14, 24))
        layout.add_widget(wrapped_SafeLabel("- Details of any children or dependents", 14, 24))
        layout.add_widget(wrapped_SafeLabel("- Any additional elements that may apply to you", 14, 24))
    
        # Proceed button centered with proper text alignment
        proceed_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=80)
        proceed_button = RoundedButton(
            text="Proceed to Claimant Details",
            size_hint=(None, None),
            size=(250, 60),
            background_normal="",
            background_color=get_color_from_hex("#FFDD00"),  # GOV.UK yellow
            font_size=20,
            font_name="roboto",
            color=get_color_from_hex("#005EA5"),  # GOV.UK blue text
            halign="center", valign="middle",
            text_size=(250, None),
            on_press=self.save_intro_and_proceed
        )
        proceed_anchor.add_widget(proceed_button)
        layout.add_widget(proceed_anchor)
    
        scroll.add_widget(layout)
        return scroll
    
    def save_intro_and_proceed(self, instance):
        """Mark intro as seen and move to claimant details"""
        self.user_data["intro_seen"] = True
        # Switch spinner to Claimant Details
        self.screen_spinner.text = "👤 Claimant Details"
    
    def on_pre_enter_intro(self, *args):
        """Repopulate intro state when re-entering"""
        if self.user_data.get("intro_seen"):
            # Optionally disable the proceed button or change its text
            # Example: show 'Continue' instead of 'Proceed'
            for child in self.screen_content.children:
                if isinstance(child, RoundedButton) and child.text.startswith("Proceed"):
                    child.text = "Continue to Claimant Details"

        
    def on_couple_claim_checkbox_active(self, checkbox, value):
        # Enable/disable partner fields based on checkbox
        self.partner_name_input.disabled = not value
        self.partner_dob_input.disabled = not value


    def create_claimant_details_screen(self):
        # Match other screens: wrap everything in an AnchorLayout
        outer = AnchorLayout(anchor_x="center", anchor_y="center")

        # Main vertical layout
        layout = BoxLayout(
            orientation="vertical",
            spacing=20,
            padding=20,
            size_hint=(1, None)
        )
        layout.bind(minimum_height=layout.setter("height"))
        outer.add_widget(layout)

        # Section header
        header_anchor = AnchorLayout(anchor_x="center", anchor_y="top", size_hint_y=None, height=60)
        header_label = SafeLabel(
            text="Select Claimant Type",
            font_size=20,
            halign="center",
            valign="middle",
            color=get_color_from_hex(WHITE)
        )
        header_label.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
        header_anchor.add_widget(header_label)
        layout.add_widget(header_anchor)

        # Horizontal layout for checkboxes and labels
        claimant_type_layout = BoxLayout(
            orientation="horizontal",
            spacing=20,
            size_hint_y=None
        )
        claimant_type_layout.bind(
            minimum_height=claimant_type_layout.setter("height")
        )

        self.single_claimant_checkbox = CheckBox(group="claimant_type")
        self.couple_claim_checkbox = CheckBox(group="claimant_type")

        # Labels for checkboxes
        single_label = SafeLabel(
            text="Single",
            font_size=18,
            halign="center",
            valign="middle",
            color=get_color_from_hex(WHITE)
        )
        single_label.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))

        couple_label = SafeLabel(
            text="Couple",
            font_size=18,
            halign="center",
            valign="middle",
            color=get_color_from_hex(WHITE)
        )
        couple_label.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))

        claimant_type_layout.add_widget(single_label)
        claimant_type_layout.add_widget(self.single_claimant_checkbox)
        claimant_type_layout.add_widget(couple_label)
        claimant_type_layout.add_widget(self.couple_claim_checkbox)

        layout.add_widget(claimant_type_layout)

        # Bind couple checkbox to enable partner fields
        self.couple_claim_checkbox.bind(active=self.on_couple_claim_checkbox_active)

        # Claimant details section
        claimant_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=60)
        claimant_label = SafeLabel(
            text="Enter Claimant Details",
            font_size=20,
            halign="center",
            valign="middle",
            color=get_color_from_hex(WHITE)
        )
        claimant_label.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
        claimant_anchor.add_widget(claimant_label)
        layout.add_widget(claimant_anchor)

        # Full-width inputs (matching other screens)
        self.name_input = CustomTextInput(
            hint_text="Name",
            multiline=False,
            font_size=18,
            size_hint=(1, None),
            height=50,
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE)
        )
        layout.add_widget(self.name_input)

        self.dob_input = DOBInput(
            hint_text="DD/MM/YYYY",
            multiline=False,
            font_size=18,
            size_hint=(1, None),
            height=50,
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE)
        )
        layout.add_widget(self.dob_input)

        # Partner details section
        partner_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=60)
        partner_label = SafeLabel(
            text="Enter Partner Details",
            font_size=20,
            halign="center",
            valign="middle",
            color=get_color_from_hex(WHITE)
        )
        partner_label.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
        partner_anchor.add_widget(partner_label)
        layout.add_widget(partner_anchor)

        self.partner_name_input = CustomTextInput(
            hint_text="Partner Name",
            multiline=False,
            font_size=18,
            size_hint=(1, None),
            height=50,
            disabled=True,
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE)
        )
        layout.add_widget(self.partner_name_input)

        self.partner_dob_input = DOBInput(
            hint_text="DD/MM/YYYY",
            multiline=False,
            font_size=18,
            size_hint=(1, None),
            height=50,
            disabled=True,
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE)
        )
        layout.add_widget(self.partner_dob_input)

        # Shared button style for consistency
        button_style = {
            "size_hint": (None, None),
            "size": (250, 60),
            "background_color": (0, 0, 0, 0),
            "background_normal": "",
            "pos_hint": {"center_x": 0.5}
        }

        # Save button
        save_button = RoundedButton(
            text="Save Claimant Details",
            **button_style,
            font_size=20,
            font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            halign="center",
            valign="middle",
            text_size=(250, None),
            on_press=self.save_claimant_details
        )
        layout.add_widget(save_button)

        return outer

    
    def save_claimant_details(self, instance):
        """Save claimant details into user_data"""
        # Relationship based on checkbox state
        if self.single_claimant_checkbox.active:
            self.user_data["relationship"] = "single"
        elif self.couple_claim_checkbox.active:
            self.user_data["relationship"] = "couple"
        else:
            self.user_data["relationship"] = ""
    
        # Claimant details
        self.user_data["claimant_name"] = self.name_input.text.strip()
        self.user_data["claimant_dob"] = self.dob_input.text.strip()
    
        # Partner details (only if couple selected)
        if self.couple_claim_checkbox.active:
            self.user_data["partner_name"] = self.partner_name_input.text.strip()
            self.user_data["partner_dob"] = self.partner_dob_input.text.strip()
        else:
            self.user_data["partner_name"] = ""
            self.user_data["partner_dob"] = ""
    
    def on_pre_enter_claimant(self, *args):
        """Repopulate inputs when re-entering the screen"""
        self.name_input.text = self.user_data.get("claimant_name", "")
        self.dob_input.text = self.user_data.get("claimant_dob", "")
    
        # Relationship checkboxes
        rel = self.user_data.get("relationship", "")
        self.single_claimant_checkbox.active = (rel == "single")
        self.couple_claim_checkbox.active = (rel == "couple")
    
        # Partner fields
        self.partner_name_input.text = self.user_data.get("partner_name", "")
        self.partner_dob_input.text = self.user_data.get("partner_dob", "")
        # Disable if not couple
        is_couple = (rel == "couple")
        self.partner_name_input.disabled = not is_couple
        self.partner_dob_input.disabled = not is_couple


    def create_finances_screen(self):
        # Outer anchor to center content vertically
        outer = AnchorLayout(anchor_x="center", anchor_y="center")
        layout = BoxLayout(orientation="vertical", spacing=20, padding=20, size_hint=(1, None))
        layout.bind(minimum_height=layout.setter("height"))
        outer.add_widget(layout)
    
        # Instruction label
        instruction = SafeLabel(
            text="Enter your financial details:",
            font_size=18,
            halign="center",
            valign="middle",
            color=get_color_from_hex(WHITE)
        )
        instruction.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
        layout.add_widget(instruction)
    
        # Income input
        self.income_input = TextInput(
            hint_text="Monthly income (£)",
            multiline=False, font_size=18,
            size_hint=(1, None), height=50,
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE)
        )
        layout.add_widget(self.income_input)
    
        # Savings input
        self.savings_input = TextInput(
            hint_text="Total savings (£)",
            multiline=False, font_size=18,
            size_hint=(1, None), height=50,
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE)
        )
        layout.add_widget(self.savings_input)
    
        # Debts input
        self.debts_input = TextInput(
            hint_text="Outstanding debts (£)",
            multiline=False, font_size=18,
            size_hint=(1, None), height=50,
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE)
        )
        layout.add_widget(self.debts_input)
    
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
            ("Save Finances", self.save_finances),
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
    
        return outer
    
    def save_finances(self, instance):
        self.user_data["income"] = self.income_input.text.strip()
        self.user_data["savings"] = self.savings_input.text.strip()
        self.user_data["debts"] = self.debts_input.text.strip()
    
    def on_pre_enter_finances(self, *args):
        self.income_input.text = self.user_data.get("income", "")
        self.savings_input.text = self.user_data.get("savings", "")
        self.debts_input.text = self.user_data.get("debts", "")

    
    def create_housing_screen(self):
        outer = AnchorLayout(anchor_x="center", anchor_y="center")
        layout = BoxLayout(
            orientation="vertical",
            spacing=20,
            padding=20,
            size_hint=(1, None)
        )
        layout.bind(minimum_height=layout.setter("height"))
        outer.add_widget(layout)
    
        # ---------------------------------------------------------
        # HOUSING TYPE SPINNER (with emojis)
        # ---------------------------------------------------------
        housing_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=70)
    
        self.housing_type_spinner = GovUkSpinner(
            text="Housing Type",
            values=(
                "🏠 Rent",
                "🔑 Own",
                "👥 Shared Accommodation"
            )
        )
        housing_anchor.add_widget(self.housing_type_spinner)
        layout.add_widget(housing_anchor)
    
        # Rent/Mortgage inputs
        self.rent_input = TextInput(
            hint_text="Enter monthly rent amount (£)",
            multiline=False,
            font_size=18,
            size_hint=(1, None),
            height=50,
            background_color=get_color_from_hex("#FFFFFF"),
            foreground_color=get_color_from_hex("#005EA5")
        )
    
        self.mortgage_input = TextInput(
            hint_text="Enter monthly mortgage amount (£)",
            multiline=False,
            font_size=18,
            size_hint=(1, None),
            height=50,
            background_color=get_color_from_hex("#FFFFFF"),
            foreground_color=get_color_from_hex("#005EA5")
        )
    
        def update_amount_input(spinner, value):
            if self.rent_input.parent:
                layout.remove_widget(self.rent_input)
            if self.mortgage_input.parent:
                layout.remove_widget(self.mortgage_input)
    
            if "Rent" in value:
                layout.add_widget(self.rent_input)
            elif "Own" in value:
                layout.add_widget(self.mortgage_input)
    
        self.housing_type_spinner.bind(text=update_amount_input)
        update_amount_input(self.housing_type_spinner, self.housing_type_spinner.text)
    
        # ---------------------------------------------------------
        # POSTCODE INPUT
        # ---------------------------------------------------------
        self.postcode_input = TextInput(
            hint_text="Enter postcode (e.g. SW1A 1AA)",
            multiline=False,
            font_size=18,
            size_hint=(1, None),
            height=50,
            background_color=get_color_from_hex("#FFFFFF"),
            foreground_color=get_color_from_hex("#005EA5")
        )
        layout.add_widget(self.postcode_input)
    
        # ---------------------------------------------------------
        # LOCATION SPINNER
        # ---------------------------------------------------------
        location_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=70)
    
        self.location_spinner = GovUkSpinner(
            text="Select Location",
            values=("England", "Scotland", "Wales")
        )
        location_anchor.add_widget(self.location_spinner)
        layout.add_widget(location_anchor)
    
        # ---------------------------------------------------------
        # BRMA SPINNER
        # ---------------------------------------------------------
        brma_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=70)
    
        self.brma_spinner = GovUkSpinner(
            text="Select BRMA",
            values=["Select BRMA"]
        )
        brma_anchor.add_widget(self.brma_spinner)
        layout.add_widget(brma_anchor)
    
        # ---------------------------------------------------------
        # AUTO-POPULATE BRMA BASED ON LOCATION
        # ---------------------------------------------------------
        def populate_brmas_for_country(spinner, country):
            csv_path = resource_find("pcode_brma_lookup.csv")
            if not csv_path:
                print("BRMA CSV not found")
                return
    
            brmas = set()
    
            try:
                with open(csv_path, newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        brma = row.get("brma_name", "").strip()
                        if not brma:
                            continue
    
                        if country == "England" and row.get("country") == "E":
                            brmas.add(brma)
                        elif country == "Scotland" and row.get("country") == "S":
                            brmas.add(brma)
                        elif country == "Wales" and row.get("country") == "W":
                            brmas.add(brma)
    
            except Exception as e:
                print("Error populating BRMAs:", e)
    
            if brmas:
                sorted_brmas = sorted(brmas)
                self.brma_spinner.values = sorted_brmas
                self.brma_spinner.text = sorted_brmas[0]
                self.brma_spinner._update_dropdown()
    
        self.location_spinner.bind(text=populate_brmas_for_country)
    
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
            postcode = self.postcode_input.text.strip().upper()
    
            self.show_loading("Finding BRMA...")
    
            def do_lookup(dt):
                brma_name = self.lookup_brma(postcode)
    
                self.brma_spinner.values = [brma_name]
                self.brma_spinner.text = brma_name
                self.brma_spinner._update_dropdown()
    
                self.hide_loading()
    
            Clock.schedule_once(do_lookup, 0.1)
    
        find_brma_btn.bind(on_press=on_find_brma)
    
        # ---------------------------------------------------------
        # SAVE BUTTON
        # ---------------------------------------------------------
        save_button = RoundedButton(
            text="Save Housing",
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
            pos_hint={"center_x": 0.5},
            on_press=self.save_housing_details
        )
        layout.add_widget(save_button)
    
        return outer
    
    
    def lookup_brma(self, postcode):
        """Lookup BRMA name for a given postcode from CSV."""
        csv_path = resource_find("pcode_brma_lookup.csv")
        if not csv_path:
            print("BRMA CSV not found in packaged resources")
            return "BRMA not found"
    
        try:
            with open(csv_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                print("CSV columns:", reader.fieldnames)
    
                for row in reader:
                    pcd = row.get("PCD", "").strip().upper()
                    pcd2 = row.get("PCD2", "").strip().upper()
                    pcds = row.get("PCDS", "").strip().upper()
    
                    if postcode in (pcd, pcd2, pcds):
                        return row.get("brma_name", "BRMA found")
    
        except Exception as e:
            print(f"Error reading BRMA CSV: {e}")
    
        return "BRMA not found"

    
    def save_housing_details(self, instance):
        self.user_data["housing_type"] = self.housing_type_spinner.text.strip().lower()
        self.user_data["rent"] = self.rent_input.text.strip()
        self.user_data["mortgage"] = self.mortgage_input.text.strip()
        self.user_data["postcode"] = self.postcode_input.text.strip()
        self.user_data["location"] = self.location_spinner.text.strip()
        self.user_data["brma"] = self.brma_spinner.text.strip()
    
    def on_pre_enter_housing(self, *args):
        self.housing_type_spinner.text = self.user_data.get("housing_type", "Rent").capitalize()
        self.rent_input.text = self.user_data.get("rent", "")
        self.mortgage_input.text = self.user_data.get("mortgage", "")
        self.postcode_input.text = self.user_data.get("postcode", "")
        self.location_spinner.text = self.user_data.get("location", "Select Location")
        self.brma_spinner.text = self.user_data.get("brma", "Select BRMA")
    
        # Ensure correct input is visible based on housing type
        parent_layout = self.housing_type_spinner.parent.parent
        if self.housing_type_spinner.text.lower() == "rent":
            if not self.rent_input.parent:
                parent_layout.add_widget(self.rent_input)
        elif self.housing_type_spinner.text.lower() == "own":
            if not self.mortgage_input.parent:
                parent_layout.add_widget(self.mortgage_input)


    def create_children_screen(self):
        # Outer anchor to center content vertically
        outer = AnchorLayout(anchor_x="center", anchor_y="center")
        layout = BoxLayout(orientation="vertical", spacing=20, padding=20, size_hint=(1, None))
        layout.bind(minimum_height=layout.setter("height"))
        outer.add_widget(layout)
    
        # Keep a reference for add_child_input
        self.children_layout = layout
    
        # Instruction label
        instruction = SafeLabel(
            text="Enter children details:",
            font_size=18,
            halign="center",
            valign="middle",
            color=get_color_from_hex("#005EA5")  # GOV.UK blue for visibility
        )
        instruction.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
        layout.add_widget(instruction)
    
        # Dynamic list of child DOB inputs
        self.children_dob_inputs = []
    
        # Add first child input by default if none saved
        if not self.user_data.get("children"):
            self.add_child_input()
        else:
            # Repopulate saved children
            for dob in self.user_data["children"]:
                self.add_child_input(prefill_text=dob)
    
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
            ("Add Another Child", self.add_child_input),
            ("Save Children Details", self.save_children_details),
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
    
        # Save button (duplicate of above, now styled consistently)
        save_button = RoundedButton(
            text="Save Children",
            **button_style,
            font_size=20,
            font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            halign="center", valign="middle",
            text_size=(250, None),
            on_press=self.save_children_details
        )
        layout.add_widget(save_button)
    
        return outer
    
    def add_child_input(self, instance=None, prefill_text=""):
        """Add a new child DOB input to the layout"""
        child_input = DOBInput(
            hint_text="Child Date of Birth (DD/MM/YYYY)",
            multiline=False, font_size=18,
            size_hint=(1, None), height=50,
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE),
            text=prefill_text
        )
        self.children_dob_inputs.append(child_input)
        # Insert above the buttons box (last two widgets are spacer + buttons)
        if hasattr(self, "children_layout"):
            self.children_layout.add_widget(child_input, index=len(self.children_layout.children)-2)
    
    def save_children_details(self, instance):
        """Save children DOBs into user_data"""
        self.user_data["children"] = [
            child.text.strip() for child in self.children_dob_inputs if child.text.strip()
        ]
    
    def on_pre_enter_children(self, *args):
        """Repopulate child DOB inputs when re-entering the screen"""
        children = self.user_data.get("children", [])
        # Ensure enough inputs exist
        while len(self.children_dob_inputs) < len(children):
            # Add extra inputs if needed
            child_input = DOBInput(
                hint_text="Child Date of Birth (DD/MM/YYYY)",
                multiline=False, font_size=18,
                size_hint=(1, None), height=50,
                background_color=get_color_from_hex(WHITE),
                foreground_color=get_color_from_hex(GOVUK_BLUE)
            )
            self.children_dob_inputs.append(child_input)
    
        # Repopulate texts
        for i, child_input in enumerate(self.children_dob_inputs):
            child_input.text = children[i] if i < len(children) else ""

    
    def create_additional_elements_screen(self):
        # Outer anchor to center content vertically
        outer = AnchorLayout(anchor_x="center", anchor_y="center")
        layout = BoxLayout(orientation="vertical", spacing=20, padding=20, size_hint=(1, None))
        layout.bind(minimum_height=layout.setter("height"))
        outer.add_widget(layout)
    
        # Instruction label
        instruction = SafeLabel(
            text="Enter additional elements:",
            font_size=18,
            halign="center",
            valign="middle",
            color=get_color_from_hex("#005EA5")  # GOV.UK blue for visibility
        )
        instruction.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
        layout.add_widget(instruction)
    
        # Carer status input
        self.is_carer_input = TextInput(
            hint_text="Are you a carer? (yes/no)",
            multiline=False, font_size=18,
            size_hint=(1, None), height=50,
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE)
        )
        layout.add_widget(self.is_carer_input)
    
        # Disability status input
        self.disability_input = TextInput(
            hint_text="Do you have a disability? (yes/no)",
            multiline=False, font_size=18,
            size_hint=(1, None), height=50,
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE)
        )
        layout.add_widget(self.disability_input)
    
        # Childcare costs input
        self.childcare_input = TextInput(
            hint_text="Monthly childcare costs (£)",
            multiline=False, font_size=18,
            size_hint=(1, None), height=50,
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE)
        )
        layout.add_widget(self.childcare_input)
    
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
            ("Save Additional Elements", self.save_additional_elements),
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
    
        # Save button (duplicate of above, now styled consistently)
        save_button = RoundedButton(
            text="Save Additional Elements",
            **button_style,
            font_size=20,
            font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            halign="center", valign="middle",
            text_size=(250, None),
            on_press=self.save_additional_elements
        )
        layout.add_widget(save_button)
    
        return outer
    
    def save_additional_elements(self, instance):
        """Save additional elements into user_data"""
        self.user_data["carer"] = self.is_carer_input.text.strip().lower() == "yes"
        self.user_data["disability"] = self.disability_input.text.strip().lower() == "yes"
        self.user_data["childcare"] = self.childcare_input.text.strip()
    
    def on_pre_enter_additional(self, *args):
        """Repopulate inputs when re-entering the screen"""
        # Only repopulate with "yes" if true, otherwise leave blank so hint text shows
        self.is_carer_input.text = "yes" if self.user_data.get("carer") else ""
        self.disability_input.text = "yes" if self.user_data.get("disability") else ""
        self.childcare_input.text = self.user_data.get("childcare", "")


    
    def create_sanction_screen(self):
        # Outer anchor to center content vertically
        outer = AnchorLayout(anchor_x="center", anchor_y="center")
        layout = BoxLayout(orientation="vertical", spacing=20, padding=20, size_hint=(1, None))
        layout.bind(minimum_height=layout.setter("height"))
        outer.add_widget(layout)
    
        # Instruction label
        instruction = SafeLabel(
            text="Enter sanction details:",
            font_size=18,
            halign="center",
            valign="middle",
            color=get_color_from_hex("#005EA5")  # GOV.UK blue for visibility
        )
        instruction.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
        layout.add_widget(instruction)
    
        # Sanction type input
        self.sanction_type_input = TextInput(
            hint_text="Sanction type (e.g. low/medium/high)",
            multiline=False, font_size=18,
            size_hint=(1, None), height=50,
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE)
        )
        layout.add_widget(self.sanction_type_input)
    
        # Sanction duration input
        self.sanction_duration_input = TextInput(
            hint_text="Sanction duration (weeks)",
            multiline=False, font_size=18,
            size_hint=(1, None), height=50,
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE)
        )
        layout.add_widget(self.sanction_duration_input)
    
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
            ("Save Sanction Details", self.save_sanction_details),
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
    
        # Save button (duplicate of above, now styled consistently)
        save_button = RoundedButton(
            text="Save Sanctions",
            **button_style,
            font_size=20,
            font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            halign="center", valign="middle",
            text_size=(250, None),
            on_press=self.save_sanction_details
        )
        layout.add_widget(save_button)
    
        return outer
    
    def save_sanction_details(self, instance):
        """Save sanction details into user_data"""
        self.user_data["sanction_type"] = self.sanction_type_input.text.strip().lower()
        self.user_data["sanction_duration"] = self.sanction_duration_input.text.strip()
    
    def on_pre_enter_sanctions(self, *args):
        """Repopulate inputs when re-entering the screen"""
        self.sanction_type_input.text = self.user_data.get("sanction_type", "")
        self.sanction_duration_input.text = self.user_data.get("sanction_duration", "")



    def create_advance_payments_screen(self):
        # Outer anchor to center content vertically
        outer = AnchorLayout(anchor_x="center", anchor_y="center")
        layout = BoxLayout(orientation="vertical", spacing=20, padding=20, size_hint=(1, None))
        layout.bind(minimum_height=layout.setter("height"))
        outer.add_widget(layout)
    
        # Instruction label
        instruction = SafeLabel(
            text="Enter advance payment details:",
            font_size=18,
            halign="center",
            valign="middle",
            color=get_color_from_hex("#005EA5")  # GOV.UK blue for visibility
        )
        instruction.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
        layout.add_widget(instruction)
    
        # Advance payment amount input
        self.advance_amount_input = TextInput(
            hint_text="Advance payment amount (£)",
            multiline=False, font_size=18,
            size_hint=(1, None), height=50,
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE),
            text=self.user_data.get("advance_amount", "")
        )
        layout.add_widget(self.advance_amount_input)
    
        # Repayment period input
        self.repayment_period_input = TextInput(
            hint_text="Repayment period (months)",
            multiline=False, font_size=18,
            size_hint=(1, None), height=50,
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE),
            text=self.user_data.get("repayment_period", "")
        )
        layout.add_widget(self.repayment_period_input)
    
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
            ("Save Advance Payment", self.save_advance_payment),
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
    
        return outer
    
    def save_advance_payment(self, instance):
        """Save advance payment details into user_data"""
        self.user_data["advance_amount"] = self.advance_amount_input.text.strip()
        self.user_data["repayment_period"] = self.repayment_period_input.text.strip()
    
    def on_pre_enter_advance(self, *args):
        """Repopulate inputs when re-entering the screen"""
        self.advance_amount_input.text = self.user_data.get("advance_amount", "")
        self.repayment_period_input.text = self.user_data.get("repayment_period", "")

            
    def create_calculate_screen(self):
        # Outer anchor to center content vertically
        outer = AnchorLayout(anchor_x="center", anchor_y="center")
        layout = BoxLayout(orientation="vertical", spacing=20, padding=20, size_hint=(1, None))
        layout.bind(minimum_height=layout.setter("height"))
        outer.add_widget(layout)
    
        # Instruction label
        instruction = SafeLabel(
            text="Summary of your Universal Credit calculation:",
            font_size=18,
            halign="center",
            valign="middle",
            color=get_color_from_hex("#005EA5")  # GOV.UK blue for visibility
        )
        instruction.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
        layout.add_widget(instruction)
    
        # Result label placeholder
        self.summary_label = SafeLabel(
            text=self.user_data.get("calculation_result", "No calculation yet."),
            font_size=16,
            halign="center",
            valign="middle",
            color=get_color_from_hex("#005EA5")
        )
        self.summary_label.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
        layout.add_widget(self.summary_label)
    
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
            ("Run Calculation", self.run_calculation),
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
    
        return outer
    
    def run_calculation(self, instance):
        """Perform calculation and update summary label + user_data"""
        # Call your existing calculation logic here
        try:
            # Example: entitlement calculation already implemented elsewhere
            entitlement = self.calculate_entitlement()  # replace with your actual method
            result_text = f"Your predicted entitlement is: £{entitlement:.2f}"
        except Exception as e:
            result_text = f"Error during calculation: {str(e)}"
    
        # Update label and user_data
        self.summary_label.text = result_text
        self.user_data["calculation_result"] = result_text
    
    def on_pre_enter_summary(self, *args):
        """Repopulate summary when re-entering the screen"""
        self.summary_label.text = self.user_data.get("calculation_result", "No calculation yet.")


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





















































































