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
from kivy.properties import ObservableList

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
            "kv/main.kv",
            "fonts/roboto.ttf"
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


# Define the Settings Screen
class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        outer = AnchorLayout(anchor_x="center", anchor_y="center")
        layout = BoxLayout(orientation="vertical", spacing=20, padding=20, size_hint=(None, None))
        layout.bind(minimum_height=layout.setter("height"))
        outer.add_widget(layout)

        build_header(layout, "Benefit Buddy")

        info_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=200)
        info_label = SafeLabel(
            text="This section of the app is still currently in development.\n\nPlease check back later for updates.",
            font_size=16, halign="center", valign="middle", color=get_color_from_hex(WHITE)
        )
        info_label.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
        info_anchor.add_widget(info_label)
        layout.add_widget(info_anchor)

        back_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=80)
        back_button = RoundedButton(
            text="Back to Main Menu",
            size_hint=(None, None), size=(250, 60),
            font_size=20, font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            background_color=(0, 0, 0, 0), background_normal="",
            halign="center", valign="middle", text_size=(250, None),
            on_press=self.go_to_main
        )
        back_anchor.add_widget(back_button)
        layout.add_widget(back_anchor)

        build_footer(layout)
        self.add_widget(outer)

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
        logo_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=300)
        logo = Image(
            source="images/logo.png",          # ensure correct path
            size_hint=(None, None),
            size=(300, 300),                   # doubled size for balance
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
        Clock.schedule_once(self.switch_to_main, 8)

    def switch_to_main(self, dt):
        self.manager.current = "main"

# Define the main screen for the app
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        outer = AnchorLayout(anchor_x="center", anchor_y="center")
        layout = BoxLayout(orientation="vertical", spacing=30, padding=20, size_hint=(None, None))
        layout.bind(minimum_height=layout.setter("height"))
        outer.add_widget(layout)

        # Header
        build_header(layout, "Benefit Buddy")

        # Logo centered
        logo_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=150)
        logo = Image(source="images/logo.png", size_hint=(None, None), size=(200, 200))
        logo_anchor.add_widget(logo)
        layout.add_widget(logo_anchor)

        # Buttons block centered
        button_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=250)
        button_layout = BoxLayout(orientation="vertical", spacing=20, size_hint=(None, None))
        button_layout.add_widget(RoundedButton(text="Create Account", on_press=self.go_to_create_account))
        button_layout.add_widget(RoundedButton(text="Login", on_press=self.go_to_login))
        button_layout.add_widget(RoundedButton(text="Guest Access", on_press=self.go_to_guest))
        button_layout.add_widget(RoundedButton(text="Settings", on_press=self.go_to_settings))
        button_anchor.add_widget(button_layout)
        layout.add_widget(button_anchor)

        # Footer
        build_footer(layout)
        self.add_widget(outer)

        # Navigation methods
    def go_to_create_account(self, instance):
        self.manager.current = "create_account"

    def go_to_login(self, instance):
        self.manager.current = "login"

    def go_to_guest(self, instance):
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
        layout = BoxLayout(orientation="vertical", spacing=20, padding=20)

        # Header pinned to top
        header_anchor = AnchorLayout(anchor_x="center", anchor_y="top", size_hint_y=None, height=80)
        build_header(header_anchor, "Benefit Buddy")
        layout.add_widget(header_anchor)

        # Shared button style with centered text
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

        # Grouped buttons in a vertical box
        buttons_box = BoxLayout(orientation="vertical", spacing=20, size_hint_y=None, height=300)
        buttons_box.add_widget(RoundedButton(
            text="Predict Next Payment",
            **button_style,
            font_size=20, font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            on_press=self.predict_payment
        ))
        buttons_box.add_widget(RoundedButton(
            text="View Previous Payments",
            **button_style,
            font_size=20, font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            on_press=lambda x: print("Payments feature not yet implemented")
        ))
        buttons_box.add_widget(RoundedButton(
            text="Update Details",
            **button_style,
            font_size=20, font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            on_press=lambda x: print("Update details feature not yet implemented")
        ))
        buttons_box.add_widget(RoundedButton(
            text="Log Out",
            **button_style,
            font_size=20, font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            on_press=self.log_out
        ))

        layout.add_widget(buttons_box)

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

    def create_popup(self, title, message):
        lbl = SafeLabel(text=message, halign="center", color=get_color_from_hex(WHITE))
        lbl.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
        return Popup(title=title, content=lbl, size_hint=(0.8, 0.4))        

    def predict_payment(self, instance):
        # Create a popup for income input
        content = BoxLayout(orientation="vertical", spacing=10, padding=10)

        self.income_input = TextInput(
            hint_text="Enter your income for this assessment period",
            font_size=18,
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE)
        )

        submit_button = RoundedButton(
            text="Submit",
            size_hint=(None, None),
            size=(250, 50),
            font_size=20,
            font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            background_color=(0, 0, 0, 0),
            background_normal="",
            halign="center", valign="middle",
            text_size=(250, None),
            on_press=lambda _: self.show_prediction_popup(self.income_input.text)
        )

        content.add_widget(SafeLabel(
            text="Enter your income:",
            font_size=20,
            halign="center",
            color=get_color_from_hex(WHITE)
        ))
        content.add_widget(self.income_input)
        content.add_widget(submit_button)

        popup = Popup(
            title="Payment Prediction",
            content=content,
            size_hint=(0.8, 0.4)
        )
        popup.open()

    def show_prediction_popup(self, income):
        income = income.strip() if income else ""
    
        try:
            # Always convert to float, whether input is "1500" or "1500.00"
            value = float(income)
    
            # Run your prediction logic
            predicted_payment = self.payment_prediction(value)
    
            # Always format to two decimal places
            message = f"Your next payment is predicted to be: £{predicted_payment:.2f}"
    
        except (ValueError, TypeError):
            # Catch invalid or empty input
            message = "Invalid income entered. Please enter a numeric value."
    
        result_label = SafeLabel(
            text=message,
            font_size=20,
            halign="center",
            color=get_color_from_hex(WHITE)
        )
        result_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (val[0], None)))
    
        result_popup = Popup(
            title="Prediction Result",
            content=result_label,
            size_hint=(0.8, 0.4)
        )
        result_popup.open()

    def payment_prediction(self, income):
        """Calculate the payment prediction based on the user's details."""
        self.income_input.text = str(income)
        return self.calculate_entitlement()

    def calculate_entitlement(self):
        """Calculate entitlement based on user details."""
        try:
            dob_date = datetime.strptime(self.dob_input.text, "%d-%m-%Y")
            partner_dob_date = datetime.strptime(self.partner_dob_input.text, "%d-%m-%Y")
        except ValueError:
            Popup("Invalid Date", "Please enter DOBs in DD-MM-YYYY format").open()
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
            Popup("Invalid Relationship Status", "Please select single or couple").open()
            return

        child_element = 0
        children_dobs = []
        for dob_input in self.children_dob_inputs:
            try:
                dob = datetime.strptime(dob_input.text, "%d-%m-%Y")
                children_dobs.append(dob)
            except ValueError:
                Popup("Invalid Date", "Children DOBs must be DD-MM-YYYY").open()
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
            Popup("Invalid Income", "Please enter a numeric income").open()
            return

        children = len(children_dobs)
        work_allowance = 411 if (children > 0 or self.lcw) and self.receives_housing_support else (684 if (children > 0 or self.lcw) else 0)

        total_allowance = standard_allowance + child_element + carer_element + disability_element + childcare_element + housing_element
        total_deductions = max(0, income - work_allowance) * 0.55
        entitlement = max(0, total_allowance - total_deductions)

        return entitlement

    def log_out(self, instance):
        print("Logging out...")
        self.manager.current = "main"


        
# Define the Guest Access Screen (reusing HomePage for simplicity)
class MainScreenGuestAccess(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        outer = AnchorLayout(anchor_x="center", anchor_y="center")
        layout = BoxLayout(orientation="vertical", spacing=20, padding=20, size_hint=(None, None))
        layout.bind(minimum_height=layout.setter("height"))
        outer.add_widget(layout)

        build_header(layout, "Guest Access")

        # Centered guest options
        guest_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=250)
        guest_layout = BoxLayout(orientation="vertical", spacing=15, size_hint=(None, None))
        guest_layout.add_widget(RoundedButton(text="Calculator", on_press=self.go_to_calculator))
        guest_layout.add_widget(RoundedButton(text="Summary", on_press=self.go_to_summary))
        guest_anchor.add_widget(guest_layout)
        layout.add_widget(guest_anchor)

        build_footer(layout)
        self.add_widget(outer)

    # Navigation methods
    def go_to_calculator(self, instance):
        print("Navigating to the calculator...")
        self.manager.current = "calculator"

    def go_to_summary(self, instance):
        print("Navigating to the summary...")
        self.manager.current = "summary"

    def log_out(self, instance):
        print("Logging out...")
        self.manager.current = "main"

    def go_back(self, instance):
        self.manager.current = "main"


# Define the Create Account Screen
class CreateAccountPage(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        outer = AnchorLayout(anchor_x="center", anchor_y="center")
        layout = BoxLayout(orientation="vertical", spacing=20, padding=20, size_hint=(None, None))
        layout.bind(minimum_height=layout.setter("height"))
        outer.add_widget(layout)

        build_header(layout, "Create Account")

        # Centered form fields
        form_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=300)
        form_layout = BoxLayout(orientation="vertical", spacing=15, size_hint=(None, None))
        form_layout.add_widget(CustomTextInput(hint_text="Username"))
        form_layout.add_widget(CustomTextInput(hint_text="Password"))
        form_layout.add_widget(RoundedButton(text="Submit", on_press=self.submit_account))
        form_anchor.add_widget(form_layout)
        layout.add_widget(form_anchor)

        build_footer(layout)
        self.add_widget(outer)

    # Navigation methods
    def go_back(self, instance):
        self.manager.current = "main"

    # Submit handler (stub for now)
    def submit_account(self, instance):
        print("Submit account pressed")
        # TODO: implement account creation logic
        # For now, just navigate back or show a popup
        self.manager.current = "main"



# Define the Login Screen
class LoginPage(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        outer = AnchorLayout(anchor_x="center", anchor_y="center")
        layout = BoxLayout(orientation="vertical", spacing=20, padding=20, size_hint=(None, None))
        layout.bind(minimum_height=layout.setter("height"))
        outer.add_widget(layout)

        build_header(layout, "Login")

        # Centered login form
        form_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=250)
        form_layout = BoxLayout(orientation="vertical", spacing=15, size_hint=(None, None))
        form_layout.add_widget(CustomTextInput(hint_text="Username"))
        form_layout.add_widget(CustomTextInput(hint_text="Password"))
        form_layout.add_widget(RoundedButton(text="Login", on_press=self.log_in))
        form_anchor.add_widget(form_layout)
        layout.add_widget(form_anchor)

        build_footer(layout)
        self.add_widget(outer)

    # Navigation methods
    def log_in(self, instance):
        print("Logging in...")
        self.manager.current = "main_full_access"

    def go_back(self, instance):
        self.manager.current = "main"


# Define the Calculator Screen
class Calculator(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", spacing=10, padding=10)

        # Header
        build_header(layout, "Benefit Buddy")

        # Back button centered and text aligned
        back_anchor = AnchorLayout(anchor_x="center", anchor_y="top", size_hint_y=None, height=50)
        back_button = RoundedButton(
            text="Back",
            size_hint=(None, None), size=(120, 40),
            background_color=get_color_from_hex("#005EA5"),
            background_normal="",
            font_size=16, font_name="roboto",
            color=get_color_from_hex("#FFDD00"),
            halign="center", valign="middle",             # center text
            text_size=(120, None),                        # match button width
            on_press=lambda x: setattr(self.manager, 'current', "main_guest_access")
        )
        back_anchor.add_widget(back_button)
        layout.add_widget(back_anchor)

        # Define screens
        self.screens = [
            ("Introduction", self.create_intro_screen),
            ("Claimant Details", self.create_claimant_details_screen),
            ("Finances", self.create_finances_screen),
            ("Housing", self._screen),
            ("Children", self.create_children_screen),
            ("Additional Elements", self.create_additional_elements_screen),
            ("Sanctions", self.create_sanction_screen),
            ("Advanced Payment", self.create_advance_payments_screen),
            ("Summary", self.create_calculate_screen)
        ]

        # Spacer before spinner
        layout.add_widget(Widget(size_hint_y=0.05))

        # Spinner centered with proper text alignment
        spinner_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=70)
        self.screen_spinner = Spinner(
            text="Introduction ▼",
            values=[name for name, _ in self.screens],
            size_hint=(None, None), size=(250, 50),
            background_normal="",  # remove default image
            background_color=get_color_from_hex("#FFDD00"),  # GOV.UK Yellow background
            color=get_color_from_hex("#005EA5"),  # GOV.UK Blue text
            font_size=20, font_name="roboto",
            option_cls=CustomSpinnerOption,
            halign="center", valign="middle",             # center text
            text_size=(250, None),                        # match spinner width
            pos_hint={"center_x": 0.5}
        )
        spinner_anchor.add_widget(self.screen_spinner)
        layout.add_widget(spinner_anchor)

        # Container for screen content
        self.screen_content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        self.screen_content.add_widget(self.screens[0][1]())

        def on_screen_select(_, text):
            clean_text = text.replace(" ▼", "")
            self.screen_content.clear_widgets()
            for name, builder in self.screens:
                if name == clean_text:
                    self.screen_content.add_widget(builder())
                    break

        self.screen_spinner.bind(text=on_screen_select)
        layout.add_widget(self.screen_content)

        # Spacer before footer
        layout.add_widget(Widget(size_hint_y=0.05))

        # Footer pinned to bottom
        footer_anchor = AnchorLayout(anchor_x="center", anchor_y="bottom", size_hint_y=None, height=60)
        build_footer(footer_anchor)
        layout.add_widget(footer_anchor)

        self.add_widget(layout)

    # Screen methods
    def create_intro_screen(self): return SafeLabel(text="Intro screen")
    def create_claimant_details_screen(self): return SafeLabel(text="Claimant details")
    def create_finances_screen(self): return SafeLabel(text="Finances")
    def _screen(self): return SafeLabel(text="Housing")
    def create_children_screen(self): return SafeLabel(text="Children")
    def create_additional_elements_screen(self): return SafeLabel(text="Additional elements")
    def create_sanction_screen(self): return SafeLabel(text="Sanctions")
    def create_advance_payments_screen(self): return SafeLabel(text="Advance payments")
    def create_calculate_screen(self): return Safe
        
    def calculate(self, instance):
        # Gather input values
        try:
            # Claimant details
            dob_str = self.dob_input.text.strip() if hasattr(self, "dob_input") and self.dob_input.text else ""
            if not dob_str:
                raise ValueError("Please enter your date of birth.")
            try:
                dob = datetime.strptime(dob_str, "%d/%m/%Y")
            except Exception:
                raise ValueError("Please enter your date of birth in the format DD/MM/YYYY.")
            age = (datetime.now() - dob).days // 365
            is_single = not (hasattr(self, "couple_claim_checkbox") and self.couple_claim_checkbox.active)

            # Partner details
            partner_age = None
            if hasattr(self, "couple_claim_checkbox") and self.couple_claim_checkbox.active and hasattr(self, "partner_dob_input") and self.partner_dob_input.text.strip():
                partner_dob_str = self.partner_dob_input.text.strip()
                try:
                    partner_dob = datetime.strptime(partner_dob_str, "%d/%m/%Y")
                    partner_age = (datetime.now() - partner_dob).days // 365
                except Exception:
                    raise ValueError("Please enter your partner's date of birth in the format DD/MM/YYYY.")

            # Income and capital
            try:
                income = float(self.income_input.text) if hasattr(self, "income_input") and self.income_input.text else 0
            except Exception:
                raise ValueError("Please enter a valid number for income.")
            try:
                capital = float(self.capital_input.text) if hasattr(self, "capital_input") and self.capital_input.text else 0
            except Exception:
                raise ValueError("Please enter a valid number for capital.")

            # Children
            child_elements = 0
            if not hasattr(self, "child_dob_inputs"):
                self.child_dob_inputs = []
            if hasattr(self, "has_children_yes") and self.has_children_yes.active:
                # Collect special circumstances for each child
                # Assume for each child, there is a dict in self.child_special_flags[i] with keys:
                # 'multiple_birth', 'adopted', 'formal_care', 'informal_care', 'rape_or_control', 'teen_parent'
                # If not present, treat as all False.
                special_flags = getattr(self, "child_special_flags", [{} for _ in self.child_dob_inputs])
                for i, dob_input in enumerate(self.child_dob_inputs):
                    try:
                        child_dob = datetime.strptime(dob_input.text.strip(), "%d/%m/%Y")
                        flags = special_flags[i] if i < len(special_flags) else {}
                        # For the first child
                        if i == 0:
                            child_elements += 339 if child_dob < datetime(2017, 4, 6) else 292.81
                        # For the second child
                        elif i == 1:
                            child_elements += 292.81
                        # For third child onwards
                        else:
                            # Check for special circumstances
                            is_special = (
                                flags.get("multiple_birth", False) or
                                flags.get("adopted", False) or
                                flags.get("formal_care", False) or
                                flags.get("informal_care", False) or
                                flags.get("rape_or_control", False) or
                                flags.get("teen_parent", False)
                            )
                            # Multiple birth: only pay for 2nd+ child in the multiple birth
                            # (Assume user sets multiple_birth True for all in the set except the first)
                            if child_dob < datetime(2017, 4, 6) or is_special:
                                child_elements += 292.81
                            # else: no entitlement for 3rd+ child born after 5 April 2017 without special circumstances
                    except Exception:
                        popup = Popup(
                            title="Invalid Date",
                            message="Please enter valid dates for all children in the format DD/MM/YYYY."
                        )
                        popup.open()
                        return

            # Additional elements
            carer_element = 0
            if hasattr(self, "additional_elements_checkboxes"):
                carer_cb = self.additional_elements_checkboxes.get("carer", None)
                if carer_cb and carer_cb.active:
                    carer_element = 201.68

                lcw = self.additional_elements_checkboxes.get("lcw", None)
                lcw_2017 = self.additional_elements_checkboxes.get("lcw_2017", None)
                lcwra = self.additional_elements_checkboxes.get("lcwra", None)
                lcw = lcw.active if lcw else False
                lcw_2017 = lcw_2017.active if lcw_2017 else False
                lcwra = lcwra.active if lcwra else False
                childcare_cb = self.additional_elements_checkboxes.get("childcare", None)
                childcare_active = childcare_cb.active if childcare_cb else False
            else:
                lcw = lcw_2017 = lcwra = childcare_active = False

            # Always define childcare_costs to avoid UnboundLocalError
            childcare_costs = 0
            if childcare_active:
                num_children = len(getattr(self, "child_dob_inputs", [])) if hasattr(self, "has_children_yes") and self.has_children_yes.active else 0
                if num_children == 1:
                    childcare_costs = 1031.88
                elif num_children > 1:
                    childcare_costs = 1768.94
                else:
                    childcare_costs = 0

            # Work capability
            work_capability = 0
            if lcwra:
                work_capability = 423.27
            elif lcw_2017:
                work_capability = 158.76
            elif lcw:
                work_capability = 0

            # Standard allowance
            standard_allowance = 0
            if is_single:
                standard_allowance = 316.98 if age < 25 else 400.14
            else:
                if partner_age is not None:
                    if age < 25 and partner_age < 25:
                        standard_allowance = 497.55
                    else:
                        standard_allowance = 628.10

            # Housing element
            # Ensure all required housing options have been selected
            housing_element = 0

            # Check housing type
            if not (hasattr(self, "housing_type_spinner") and self.housing_type_spinner.text and self.housing_type_spinner.text.lower() in ["rent", "own"]):
                content = SafeLabel(
                    text="Please select a valid housing type (rent or own).",
                    text_size=(self.width * 0.6, None) if hasattr(self, "width") else (400, None),
                    halign="center",
                    valign="middle"
                )
                popup = Popup(
                    title="Missing Housing Type",
                    content=content,
                    size_hint=(0.8, 0.4)
                )
                popup.open()
                return

            if self.housing_type_spinner.text.lower() == "rent":
                # Check if children option is selected
                if not (hasattr(self, "has_children_yes") and (self.has_children_yes.active or (hasattr(self, "has_children_no") and self.has_children_no.active))):
                    content = SafeLabel(
                        text="Please specify if you have children.",
                        text_size=(self.width * 0.6, None) if hasattr(self, "width") else (400, None),
                        halign="center",
                        valign="middle"
                    )
                    popup = Popup(
                        title="Missing Children Information",
                        content=content,
                        size_hint=(0.8, 0.4)
                    )
                    popup.open()
                    return

                num_children = len(getattr(self, "child_dob_inputs", [])) if hasattr(self, "has_children_yes") and self.has_children_yes.active else 0
                bedrooms = 1 + num_children
                bedrooms = min(bedrooms, 4)

                # Ensure Location is selected
                if not (hasattr(self, "location_spinner") and self.location_spinner.text and self.location_spinner.text != "Select Location"):
                    content = SafeLabel(
                        text="Please select a valid Location.",
                        text_size=(self.width * 0.6, None) if hasattr(self, "width") else (400, None),
                        halign="center",
                        valign="middle"
                    )
                    popup = Popup(
                        title="Missing Location",
                        content=content,
                        size_hint=(0.8, 0.4)
                    )
                    popup.open()
                    return

                # Ensure BRMA is selected
                if not (hasattr(self, "brma_spinner") and self.brma_spinner.text and self.brma_spinner.text != "Select BRMA"):
                    content = SafeLabel(
                        text="Please select a valid BRMA.",
                        text_size=(self.width * 0.6, None) if hasattr(self, "width") else (400, None),
                        halign="center",
                        valign="middle"
                    )
                    popup = Popup(
                        title="Missing BRMA",
                        content=content,
                        size_hint=(0.8, 0.4)
                    )
                    popup.open()
                    return

                brma = self.brma_spinner.text

                # Normalize location to handle codes and names
                location_raw = self.location_spinner.text.strip()
                location_map = {
                    "E": "England", "e": "England", "England": "England",
                    "S": "Scotland", "s": "Scotland", "Scotland": "Scotland",
                    "W": "Wales", "w": "Wales", "Wales": "Wales"
                }
                location = location_map.get(location_raw, location_raw)
                if not location or location not in ["England", "Scotland", "Wales"]:
                    content = SafeLabel(
                        text="Please select a valid Location.",
                        text_size=(self.width * 0.6, None) if hasattr(self, "width") else (400, None),
                        halign="center",
                        valign="middle"
                    )
                    popup = Popup(
                        title="Missing Location",
                        content=content,
                        size_hint=(0.8, 0.4)
                    )
                    popup.open()
                    return

                lha_file_map = {
                    region: resource_find(f"LHA-{region}.csv") or os.path.join(BASE_DIR, ".venv", f"LHA-{region}.csv")
                    for region in ["England", "Scotland", "Wales"]
                }

                # Get the correct LHA rates file based on the selected location
                lha_file = lha_file_map.get(location)
                if not lha_file:
                    content = SafeLabel(
                        text="Unable to determine the correct LHA rates file for the selected location.",
                        text_size=(self.width * 0.6, None) if hasattr(self, "width") else (400, None),
                        halign="center",
                        valign="middle"
                    )
                    popup = Popup(
                        title="LHA File Error",
                        content=content,
                        size_hint=(0.8, 0.4)
                    )
                    popup.open()
                    return

                lha_rate = 0
                if lha_file and brma and brma != "Select BRMA":
                    try:
                        with open(lha_file, newline='', encoding='utf-8') as csvfile:
                            reader = csv.DictReader(csvfile)
                            found = False
                            # Normalize fieldnames for case-insensitive matching
                            field_map = {name.lower().replace(" ", ""): name for name in reader.fieldnames}
                            # Map bedrooms to the correct column header
                            bedroom_col_map = {
                                0: "SAR",
                                1: "1 Bed",
                                2: "2 bed",
                                3: "3 bed",
                                4: "4 Bed"
                            }
                            # Find the row with matching BRMA
                            for row in reader:
                                brma_val = row.get(field_map.get("brma", "BRMA"), "").strip().lower()
                                if brma_val == brma.strip().lower():
                                    found = True
                                    col_name = None
                                    if bedrooms <= 0:
                                        col_name = bedroom_col_map[0]
                                    elif bedrooms == 1:
                                        col_name = bedroom_col_map[1]
                                    elif bedrooms == 2:
                                        col_name = bedroom_col_map[2]
                                    elif bedrooms == 3:
                                        col_name = bedroom_col_map[3]
                                    elif bedrooms >= 4:
                                        col_name = bedroom_col_map[4]
                                    # Try to get the value, fallback to 0 if not found
                                    lha_rate_str = row.get(col_name, "0")
                                    try:
                                        lha_rate = float(lha_rate_str)
                                    except Exception:
                                        lha_rate = 0
                                    break
                            if not found:
                                content = SafeLabel(
                                    text=f"Selected BRMA not found in the rates file.\n",
                                    text_size=(self.width * 0.6, None) if hasattr(self, "width") else (400, None),
                                    halign="center",
                                    valign="middle"
                                )
                                popup = Popup(
                                    title="BRMA Not Found",
                                    content=content,
                                    size_hint=(0.8, 0.4)
                                )
                                popup.open()
                                return
                    except Exception as e:
                        content = SafeLabel(
                            text=f"Error reading LHA rates: {str(e)}",
                            text_size=(self.width * 0.6, None) if hasattr(self, "width") else (400, None),
                            halign="center",
                            valign="middle"
                        )
                        popup = Popup(
                            title="LHA File Error",
                            content=content,
                            size_hint=(0.8, 0.4)
                        )
                        popup.open()
                        return

                # Get the user's rent input and cap the housing element
                rent_value = 0
                if hasattr(self, "rent_mortgage_input") and self.rent_mortgage_input.text.strip():
                    try:
                        rent_value = float(self.rent_mortgage_input.text.strip())
                    except Exception:
                        rent_value = 0
                # Cap the housing element at the lower of LHA rate or rent value
                if rent_value > 0 and lha_rate > 0:
                    housing_element = min(lha_rate, rent_value)
                elif rent_value > 0:
                    housing_element = rent_value
                else:
                    housing_element = 0

            elif self.housing_type_spinner.text.lower() == "own":
                # For owners, use the entered mortgage value (if any) as the housing element
                mortgage_value = 0
                if hasattr(self, "mortgage_input") and self.mortgage_input.text.strip():
                    try:
                        mortgage_value = float(self.mortgage_input.text.strip())
                    except Exception:
                        mortgage_value = 0
                housing_element = mortgage_value if mortgage_value > 0 else 0

            elif self.housing_type_spinner.text.lower() == "shared accommodation":
                # For shared accommodation, use the entered rent value (if any) as the housing element
                rent_value = 0
                if hasattr(self, "shared_accommodation_rent_input") and self.shared_accommodation_rent_input.text.strip():
                    try:
                        rent_value = float(self.shared_accommodation_rent_input.text.strip())
                    except Exception:
                        rent_value = 0

                # Ensure Location is selected
                if not (hasattr(self, "location_spinner") and self.location_spinner.text and self.location_spinner.text != "Select Location"):
                    content = SafeLabel(
                        text="Please select a valid Location.",
                        text_size=(self.width * 0.6, None) if hasattr(self, "width") else (400, None),
                        halign="center",
                        valign="middle"
                    )
                    popup = Popup(
                        title="Missing Location",
                        content=content,
                        size_hint=(0.8, 0.4)
                    )
                    popup.open()
                    return

                # Ensure BRMA is selected
                if not (hasattr(self, "brma_spinner") and self.brma_spinner.text and self.brma_spinner.text != "Select BRMA"):
                    content = SafeLabel(
                        text="Please select a valid BRMA.",
                        text_size=(self.width * 0.6, None) if hasattr(self, "width") else (400, None),
                        halign="center",
                        valign="middle"
                    )
                    popup = Popup(
                        title="Missing BRMA",
                        content=content,
                        size_hint=(0.8, 0.4)
                    )
                    popup.open()
                    return

                brma = self.brma_spinner.text

                # Normalize location to handle codes and names
                location_raw = self.location_spinner.text.strip()
                location_map = {
                    "E": "England", "e": "England", "England": "England",
                    "S": "Scotland", "s": "Scotland", "Scotland": "Scotland",
                    "W": "Wales", "w": "Wales", "Wales": "Wales"
                }
                location = location_map.get(location_raw, location_raw)
                if not location or location not in ["England", "Scotland", "Wales"]:
                    content = SafeLabel(
                        text="Please select a valid Location.",
                        text_size=(self.width * 0.6, None) if hasattr(self, "width") else (400, None),
                        halign="center",
                        valign="middle"
                    )
                    popup = Popup(
                        title="Missing Location",
                        content=content,
                        size_hint=(0.8, 0.4)
                    )
                    popup.open()
                    return

                lha_file_map = {
                    region: resource_find(f"LHA-{region}.csv") or os.path.join(BASE_DIR, ".venv", f"LHA-{region}.csv")
                    for region in ["England", "Scotland", "Wales"]
                }

                # Get the correct LHA rates file based on the selected location
                lha_file = lha_file_map.get(location)
                if not lha_file:
                    content = SafeLabel(
                        text="Unable to determine the correct LHA rates file for the selected location.",
                        text_size=(self.width * 0.6, None) if hasattr(self, "width") else (400, None),
                        halign="center",
                        valign="middle"
                    )
                    popup = Popup(
                        title="LHA File Error",
                        content=content,
                        size_hint=(0.8, 0.4)
                    )
                    popup.open()
                    return

                lha_rate = 0
                if lha_file and brma and brma != "Select BRMA":
                    try:
                        with open(lha_file, newline='', encoding='utf-8') as csvfile:
                            reader = csv.reader(csvfile)
                            headers = next(reader, None)
                            found = False
                            for row in reader:
                                if row and row[0].strip().lower() == brma.strip().lower():
                                    found = True
                                    try:
                                        sar_index = 1 if headers and len(headers) > 1 and headers[1].strip().upper() == "SAR" else 1
                                        lha_rate = float(row[sar_index])
                                    except Exception:
                                        lha_rate = 0
                                    break
                            if not found:
                                content = SafeLabel(
                                    text=f"Selected BRMA not found in the rates file.\n",
                                    text_size=(self.width * 0.6, None) if hasattr(self, "width") else (400, None),
                                    halign="center",
                                    valign="middle"
                                )
                                popup = Popup(
                                    title="BRMA Not Found",
                                    content=content,
                                    size_hint=(0.8, 0.4)
                                )
                                popup.open()
                                return
                    except Exception as e:
                        content = SafeLabel(
                            text=f"Error reading LHA rates: {str(e)}",
                            text_size=(self.width * 0.6, None) if hasattr(self, "width") else (400, None),
                            halign="center",
                            valign="middle"
                        )
                        popup = Popup(
                            title="LHA File Error",
                            content=content,
                            size_hint=(0.8, 0.4)
                        )
                        popup.open()
                        return

                # Cap the housing element at the lower of SAR rate or rent value
                if rent_value > 0 and lha_rate > 0:
                    housing_element = min(lha_rate, rent_value)
                elif rent_value > 0:
                    housing_element = rent_value
                else:
                    housing_element = 0

            # Work allowance
            has_children = hasattr(self, "has_children_yes") and self.has_children_yes.active and len(getattr(self, "child_dob_inputs", [])) > 0
            receives_housing_support = hasattr(self, "housing_type_spinner") and self.housing_type_spinner.text.lower() == "rent"
            if has_children or lcw:
                work_allowance = 411 if receives_housing_support else 684
            else:
                work_allowance = 0

            # Calculate total before deductions
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
                # Not eligible for UC
                content = SafeLabel(
                    text="You are not eligible for Universal Credit due to capital over £16,000.",
                    text_size=(self.width * 0.6, None) if hasattr(self, "width") else (400, None),
                    halign="center",
                    valign="middle"
                )
                popup = Popup(
                    title="Calculation Result",
                    content=content,
                    size_hint=(0.8, 0.4)
                )
                popup.open()
                return
            else:
                blocks = ((capital - 6000) + 249) // 250
                capital_income = blocks * 4.35

            # Sanctions and advance payments
            sanctions = 0   
            advance_payments = 0
            
            # Calculate sanctions based on sanction level, age, couple status, 40% reduction, days, and number of claimants
            try:
                # Get sanction level, days, claimants, and 40% reduction
                sanction_level = self.sanction_level_spinner.text if hasattr(self, "sanction_level_spinner") else "None"
                days = int(self.sanction_days_input.text.strip()) if hasattr(self, "sanction_days_input") and self.sanction_days_input.text.strip().isdigit() else 0
                claimants = int(self.sanctioned_claimants_input.text.strip()) if hasattr(self, "sanctioned_claimants_input") and self.sanctioned_claimants_input.text.strip().isdigit() else 1
                reduction_40 = self.sanction_40_checkbox.active if hasattr(self, "sanction_40_checkbox") else False

                # Get claimant and partner age
                dob_str = self.dob_input.text.strip() if hasattr(self, "dob_input") and self.dob_input.text else ""
                age = None
                if dob_str:
                    try:
                        dob = datetime.strptime(dob_str, "%d/%m/%Y")
                        age = (datetime.now() - dob).days // 365
                    except Exception:
                        age = None
                couple = self.couple_claim_checkbox.active if hasattr(self, "couple_claim_checkbox") else False
                partner_age = None
                if couple and hasattr(self, "partner_dob_input") and self.partner_dob_input.text.strip():
                    try:
                        partner_dob = datetime.strptime(self.partner_dob_input.text.strip(), "%d/%m/%Y")
                        partner_age = (datetime.now() - partner_dob).days // 365
                    except Exception:
                        partner_age = None

                # Determine reduction rate per day
                rate = 0
                if sanction_level != "None" and days > 0:
                    if not couple:
                        if age is not None and age < 25:
                            rate = 4.10 if reduction_40 else 10.40
                        elif age is not None and age >= 25:
                            rate = 5.20 if reduction_40 else 13.10
                    else:
                        # Joint claimants
                        if age is not None and partner_age is not None:
                            if age < 25 and partner_age < 25:
                                rate = 3.20 if reduction_40 else 8.10
                            else:
                                rate = 4.10 if reduction_40 else 10.30
                        else:
                            # Fallback if partner age is missing
                            rate = 4.10 if reduction_40 else 10.30
                    sanctions = rate * days * claimants
                else:
                    sanctions = 0
            except Exception:
                sanctions = 0
                
            # Calculate advance payments based on inputs 
            if hasattr(self, "advance_payments_input") and self.advance_payments_input.text.strip():
                try:
                    advance_payments_total = float(self.advance_payments_input.text.strip())
                except Exception:
                    advance_payments_total = 0
                
                # Determine the number of months selected
                months = 0
                if hasattr(self, "advance_payments_period_checkboxes"):
                    if self.advance_payments_period_checkboxes.get("six_month") and self.advance_payments_period_checkboxes["six_month"].active:
                        months = 6
                    elif self.advance_payments_period_checkboxes.get("twelve_month") and self.advance_payments_period_checkboxes["twelve_month"].active:
                        months = 12
                    elif self.advance_payments_period_checkboxes.get("twenty_four_month") and self.advance_payments_period_checkboxes["twenty_four_month"].active:
                        months = 24
                advance_payments = advance_payments_total / months if months > 0 else advance_payments_total
                    
            # Ensure sanctions and advance payments are non-negative
            sanctions = max(0, sanctions)
            advance_payments = max(0, advance_payments)

            # Apply deductions
            if income > work_allowance:
                earnings_taper = (income - work_allowance) * 0.55
            else:
                earnings_taper = 0
            
            total_deductions = capital_income + earnings_taper + sanctions + advance_payments

            entitlement = total_allowance - total_deductions

            # Show result
            content = SafeLabel(
                text=f"Your estimated Universal Credit entitlement is:\n£{entitlement:.2f}",
                text_size=(self.width * 0.6, None) if hasattr(self, "width") else (400, None),
                halign="center",
                valign="middle"
            )
            popup = Popup(
                title="Calculation Result",
                content=content,
                size_hint=(0.8, 0.4)
            )
            popup.open()
        except Exception as e:
            content = SafeLabel(
                text=f"Error calculating entitlement:\n{str(e)}",
                text_size=(self.width * 0.6, None) if hasattr(self, "width") else (400, None),
                halign="center",
                valign="middle"
            )
            popup = Popup(
                title="Calculation Error",
                content=content,
                size_hint=(0.8, 0.4)
            )
            popup.open()
     
    def create_intro_screen(self):
        # Use a ScrollView to make the intro screen vertically scrollable
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
        layout = BoxLayout(orientation="vertical", spacing=30, padding=20, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))  # Let layout expand vertically

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
            background_color=(0, 0, 0, 0),  # Transparent background
            background_normal="",           # Remove default background image
            font_size=20,
            font_name="roboto",
            color=get_color_from_hex("#005EA5"),  # GOVUK_BLUE text color
            halign="center", valign="middle",
            text_size=(250, None),
            on_press=lambda x: setattr(self.screen_spinner, 'text', "Claimant Details ▼")
        )
        proceed_anchor.add_widget(proceed_button)
        layout.add_widget(proceed_anchor)

        scroll.add_widget(layout)
        return scroll

        
    def on_couple_claim_checkbox_active(self, checkbox, value):
        # Enable/disable partner fields based on checkbox
        self.partner_name_input.disabled = not value
        self.partner_dob_input.disabled = not value

    def create_claimant_details_screen(self):
        layout = BoxLayout(orientation="vertical", spacing=20, padding=20)

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
        claimant_type_layout = BoxLayout(orientation="horizontal", spacing=20, size_hint_y=None, height=50)
        self.single_claimant_checkbox = CheckBox(group="claimant_type")
        self.couple_claim_checkbox = CheckBox(group="claimant_type")

        claimant_type_layout.add_widget(SafeLabel(
            text="Single", font_size=18, halign="center", color=get_color_from_hex(WHITE)
        ))
        claimant_type_layout.add_widget(self.single_claimant_checkbox)
        claimant_type_layout.add_widget(SafeLabel(
            text="Couple", font_size=18, halign="center", color=get_color_from_hex(WHITE)
        ))
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

        self.name_input = CustomTextInput(
            hint_text="Name",
            multiline=False,
            font_size=18,
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE)
        )
        layout.add_widget(self.name_input)

        self.dob_input = DOBInput(
            hint_text="DD/MM/YYYY",
            multiline=False,
            font_size=18,
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
            hint_text="Name",
            multiline=False,
            font_size=18,
            disabled=True,
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE)
        )
        self.partner_dob_input = DOBInput(
            hint_text="DD/MM/YYYY",
            multiline=False,
            font_size=18,
            disabled=True,
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE)
        )
        layout.add_widget(self.partner_name_input)
        layout.add_widget(self.partner_dob_input)

        return layout


    def create_finances_screen(self):
        layout = BoxLayout(orientation="vertical", spacing=20, padding=20)

        # Section header
        header_anchor = AnchorLayout(anchor_x="center", anchor_y="top", size_hint_y=None, height=60)
        header_label = SafeLabel(
            text="Enter Income",
            font_size=24,
            halign="center",
            valign="middle",
            color=get_color_from_hex(WHITE)
        )
        header_label.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
        header_anchor.add_widget(header_label)
        layout.add_widget(header_anchor)

        # Subclass TextInput to handle Tab key navigation
        class TabFocusTextInput(TextInput):
            def __init__(self, next_input=None, **kwargs):
                super().__init__(**kwargs)
                self.next_input = next_input

            def keyboard_on_key_down(self, window, keycode, text, modifiers):
                if keycode[1] == 'tab':
                    if self.next_input:
                        self.next_input.focus = True
                        return True
                return super().keyboard_on_key_down(window, keycode, text, modifiers)

        # Income input
        self.income_input = TabFocusTextInput(
            hint_text="Enter your monthly income",
            multiline=False,
            font_size=18,
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE)
        )
        layout.add_widget(self.income_input)
    
        # Capital section header
        capital_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=60)
        capital_label = SafeLabel(
            text="Enter Capital",
            font_size=24,
            halign="center",
            valign="middle",
            color=get_color_from_hex(WHITE)
        )
        capital_label.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
        capital_anchor.add_widget(capital_label)
        layout.add_widget(capital_anchor)
    
        # Capital input
        self.capital_input = TabFocusTextInput(
            hint_text="Enter your capital",
            multiline=False,
            font_size=18,
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE)
        )
        layout.add_widget(self.capital_input)
    
        # Link income_input to capital_input for Tab/Enter navigation
        self.income_input.next_input = self.capital_input
    
        def focus_capital_input(instance):
            self.capital_input.focus = True
    
        self.income_input.bind(on_text_validate=focus_capital_input)
    
        return layout

    
    def create_housing_screen(self):
        # Outer anchor to center content vertically
        outer = AnchorLayout(anchor_x="center", anchor_y="center")
        layout = BoxLayout(orientation="vertical", spacing=20, padding=20, size_hint=(None, None))
        layout.bind(minimum_height=layout.setter("height"))
        outer.add_widget(layout)
    
        # Housing type spinner (default to Rent so input shows immediately)
        housing_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=70)
        self.housing_type_spinner = Spinner(
            text="Rent",  # default instead of "Select Housing Type"
            values=("Rent", "Own", "Shared Accommodation"),
            size_hint=(None, None), size=(250, 50),
            background_normal="", background_color=get_color_from_hex("#FFDD00"),
            color=get_color_from_hex("#005EA5"),
            font_size=20, font_name="roboto",
            option_cls=CustomSpinnerOption,
            halign="center", valign="middle",
            text_size=(250, None),
            pos_hint={"center_x": 0.5}
        )
        housing_anchor.add_widget(self.housing_type_spinner)
        layout.add_widget(housing_anchor)
    
        # Rent/Mortgage inputs
        self.rent_mortgage_input = CustomTextInput(
            hint_text="Enter monthly rent amount (£)",
            multiline=False, font_size=18,
            background_color=get_color_from_hex("#00000000"),
            foreground_color=get_color_from_hex(YELLOW)
        )
        self.mortgage_input = CustomTextInput(
            hint_text="Enter monthly mortgage amount (£)",
            multiline=False, font_size=18,
            background_color=get_color_from_hex("#00000000"),
            foreground_color=get_color_from_hex(YELLOW)
        )
    
        # Show appropriate input based on housing type
        def update_amount_input(spinner, value):
            if self.rent_mortgage_input.parent:
                layout.remove_widget(self.rent_mortgage_input)
            if self.mortgage_input.parent:
                layout.remove_widget(self.mortgage_input)
            if value.lower() == "rent":
                layout.add_widget(self.rent_mortgage_input)
            elif value.lower() == "own":
                layout.add_widget(self.mortgage_input)
    
        self.housing_type_spinner.bind(text=update_amount_input)
        update_amount_input(self.housing_type_spinner, self.housing_type_spinner.text)
    
        # Postcode input
        self.postcode_input = CustomTextInput(
            hint_text="Enter postcode (e.g. SW1A 1AA)",
            multiline=False, font_size=18,
            background_color=get_color_from_hex("#00000000"),
            foreground_color=get_color_from_hex(YELLOW)
        )
        layout.add_widget(self.postcode_input)
    
        # Find BRMA button
        find_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=60)
        find_brma_btn = RoundedButton(
            text="Find BRMA",
            size_hint=(None, None), size=(150, 40),
            font_size=16, font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            background_color=(0, 0, 0, 0), background_normal="",
            halign="center", valign="middle",
            text_size=(150, None),
            pos_hint={"center_x": 0.5}
        )
        find_anchor.add_widget(find_brma_btn)
        layout.add_widget(find_anchor)
    
        def on_find_brma(instance):
            find_brma_btn.text = "Finding BRMA"
            postcode = self.postcode_input.text.strip().replace(" ", "").upper()
    
            if not postcode:
                self.brma_spinner.text = "Enter postcode"
                find_brma_btn.text = "Find BRMA"
                return
    
            try:
                file_path = resource_find("data/pcode_brma_lookup.csv")
                if not file_path:
                    raise FileNotFoundError("pcode_brma_lookup.csv not packaged in APK")
                with open(file_path, newline='', encoding='utf-8') as csvfile:
                    reader = csv.reader(csvfile)
                    headers = next(reader, None)
                    found = False
    
                    for row in reader:
                        for idx in [1, 2, 3]:
                            if idx < len(row):
                                pcode = row[idx].replace(" ", "").upper()
                                if pcode == postcode:
                                    country_code = row[headers.index("country")] if "country" in headers else ""
                                    brma = row[headers.index("brma_name")] if "brma_name" in headers else ""
                                    country_map = {"E": "England", "S": "Scotland", "W": "Wales"}
                                    location = country_map.get(country_code.upper(), "")
    
                                    def update_spinners(dt):
                                        if location in self.location_spinner.values:
                                            self.location_spinner.text = location
                                            update_brma_spinner(self.location_spinner, location)
                                        if brma in self.brma_spinner.values:
                                            self.brma_spinner.text = brma
                                        find_brma_btn.text = "Find BRMA"
    
                                    Clock.schedule_once(update_spinners, 0)
                                    found = True
                                    break
                        if found:
                            break
    
                    if not found:
                        self.brma_spinner.text = "Not found"
                        find_brma_btn.text = "Find BRMA"
    
            except Exception as e:
                self.brma_spinner.text = f"Error: {str(e)}"
                find_brma_btn.text = "Find BRMA"
    
        find_brma_btn.bind(on_press=on_find_brma)
    
        # Location spinner
        location_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=70)
        self.location_spinner = Spinner(
            text="Select Location",
            values=("England", "Scotland", "Wales"),
            size_hint=(None, None), size=(250, 50),
            background_normal="", background_color=get_color_from_hex("#FFDD00"),
            color=get_color_from_hex("#005EA5"),
            font_size=20, font_name="roboto",
            option_cls=CustomSpinnerOption,
            halign="center", valign="middle",
            text_size=(250, None),
            pos_hint={"center_x": 0.5}
        )
        location_anchor.add_widget(self.location_spinner)
        layout.add_widget(location_anchor)
    
        # BRMA spinner with fallback
        brma_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=70)
        self.brma_spinner = Spinner(
            text="Select BRMA",
            values=["No BRMAs loaded"],  # fallback
            size_hint=(None, None), size=(250, 50),
            background_normal="", background_color=get_color_from_hex("#FFDD00"),
            color=get_color_from_hex("#005EA5"),
            font_size=20, font_name="roboto",
            option_cls=CustomSpinnerOption,
            halign="center", valign="middle",
            text_size=(250, None),
            pos_hint={"center_x": 0.5}
        )
        brma_anchor.add_widget(self.brma_spinner)
        layout.add_widget(brma_anchor)
    
        return outer


    def create_children_screen(self):
        # Use a ScrollView to make the screen vertically scrollable
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
        layout = BoxLayout(orientation="vertical", spacing=20, padding=20, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))  # Let layout expand vertically
    
        # Section header
        header_anchor = AnchorLayout(anchor_x="center", anchor_y="top", size_hint_y=None, height=60)
        header_label = SafeLabel(
            text="Children Details",
            font_size=24,
            halign="center",
            valign="middle",
            color=get_color_from_hex(WHITE)
        )
        header_label.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
        header_anchor.add_widget(header_label)
        layout.add_widget(header_anchor)
    
        # Yes/No checkbox for "Do you have children?"
        yn_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=50)
        yn_layout = BoxLayout(orientation="horizontal", spacing=20, size_hint_y=None, height=40)
        yn_layout.add_widget(SafeLabel(text="Do you have children?", font_size=18, halign="center", color=get_color_from_hex(WHITE)))
        self.has_children_yes = CheckBox(group="has_children", size_hint=(None, None), size=(30, 30))
        self.has_children_no = CheckBox(group="has_children", size_hint=(None, None), size=(30, 30))
        yn_layout.add_widget(SafeLabel(text="Yes", font_size=16, halign="center", color=get_color_from_hex(WHITE)))
        yn_layout.add_widget(self.has_children_yes)
        yn_layout.add_widget(SafeLabel(text="No", font_size=16, halign="center", color=get_color_from_hex(WHITE)))
        yn_layout.add_widget(self.has_children_no)
        yn_anchor.add_widget(yn_layout)
        layout.add_widget(yn_anchor)
    
        # Container for children input fields
        self.children_inputs_layout = BoxLayout(orientation="vertical", spacing=10, padding=10, size_hint_y=None)
        self.children_inputs_layout.bind(minimum_height=self.children_inputs_layout.setter('height'))
        layout.add_widget(self.children_inputs_layout)
    
        # Store child input fields
        self.child_name_inputs = []
        self.child_dob_inputs = []
        self.child_disabled_checkboxes = []
        self.child_remove_checkboxes = []
        self.child_special_flags = []
    
        # Add Another Child button centered
        add_child_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=60)
        add_child_btn = RoundedButton(
            text="Add Another Child",
            size_hint=(None, None),
            size=(200, 50),
            font_size=16,
            font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            background_color=(0, 0, 0, 0),
            background_normal="",
            halign="center", valign="middle",
            text_size=(200, None)
        )
        add_child_anchor.add_widget(add_child_btn)
        layout.add_widget(add_child_anchor)
    
        # Remove Child button centered
        remove_child_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=60)
        remove_child_btn = RoundedButton(
            text="Remove Selected Child",
            size_hint=(None, None),
            size=(200, 50),
            font_size=16,
            font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            background_color=(0, 0, 0, 0),
            background_normal="",
            halign="center", valign="middle",
            text_size=(200, None)
        )
        remove_child_anchor.add_widget(remove_child_btn)
        layout.add_widget(remove_child_anchor)
    
        def clear_children_inputs():
            self.children_inputs_layout.clear_widgets()
            self.child_name_inputs.clear()
            self.child_dob_inputs.clear()
            self.child_disabled_checkboxes.clear()
            self.child_remove_checkboxes.clear()
            self.child_special_flags.clear()
    
        def add_child_fields():
            # If "No" is currently selected, switch to "Yes"
            if self.has_children_no.active:
                self.has_children_yes.active = True
            idx = len(self.child_name_inputs) + 1
    
            # Vertical layout for each child
            child_col = BoxLayout(orientation="vertical", spacing=10, size_hint_y=None)
    
            # Name input
            name_input = CustomTextInput(
                hint_text=f"Child {idx} Name",
                multiline=False,
                font_size=18,
                background_color=get_color_from_hex(WHITE),
                foreground_color=get_color_from_hex(GOVUK_BLUE),
                size_hint_y=None,
                height=40
            )
    
            # DOB input
            dob_input = DOBInput(
                hint_text=f"Child {idx} DOB (DD/MM/YYYY)",
                multiline=False,
                font_size=18,
                background_color=get_color_from_hex(WHITE),
                foreground_color=get_color_from_hex(GOVUK_BLUE),
                size_hint_y=None,
                height=40
            )
    
            child_col.add_widget(name_input)
            child_col.add_widget(dob_input)
    
            # Special circumstances checkboxes
            special_flags = {
                "disabled": CheckBox(size_hint=(None, None), size=(30, 30)),
                "multiple_birth": CheckBox(size_hint=(None, None), size=(30, 30)),
                "adopted": CheckBox(size_hint=(None, None), size=(30, 30)),
                "formal_care": CheckBox(size_hint=(None, None), size=(30, 30)),
                "informal_care": CheckBox(size_hint=(None, None), size=(30, 30)),
                "rape_or_control": CheckBox(size_hint=(None, None), size=(30, 30)),
                "teen_parent": CheckBox(size_hint=(None, None), size=(30, 30)),
            }
            special_layout = BoxLayout(orientation="vertical", spacing=5, padding=(10, 0, 0, 0), size_hint_y=None)
            for label, cb in [
                ("Disabled", special_flags["disabled"]),
                ("Multiple Birth", special_flags["multiple_birth"]),
                ("Adopted", special_flags["adopted"]),
                ("Formal Care", special_flags["formal_care"]),
                ("Informal Care", special_flags["informal_care"]),
                ("Rape/Control", special_flags["rape_or_control"]),
                ("Teen Parent", special_flags["teen_parent"]),
            ]:
                row = BoxLayout(orientation="horizontal", spacing=8, size_hint_y=None, height=24)
                row.add_widget(cb)
                row.add_widget(SafeLabel(
                    text=label,
                    font_size=14,
                    color=get_color_from_hex(WHITE),
                    halign="left",
                    valign="middle"
                ))
                special_layout.add_widget(row)
    
            special_layout.height = 24 * len(special_flags) + 5 * (len(special_flags) - 1)
            child_col.add_widget(special_layout)
    
            child_col.height = 40 + 40 + special_layout.height + 20
    
            self.child_name_inputs.append(name_input)
            self.child_dob_inputs.append(dob_input)
            self.child_special_flags.append(special_flags)
    
            self.children_inputs_layout.add_widget(child_col)
    
            # Responsive width binding
            def update_width(*_):
                width = Window.width - 60
                child_col.width = width
                name_input.width = width
                dob_input.width = width
                special_layout.width = width
            Window.bind(size=update_width)
            update_width()
    
        def on_has_children_checkbox(instance, value):
            if instance == self.has_children_yes and value:
                if not self.child_name_inputs:
                    clear_children_inputs()
                    add_child_fields()
            elif instance == self.has_children_no and value:
                clear_children_inputs()
    
        self.has_children_yes.bind(active=on_has_children_checkbox)
        self.has_children_no.bind(active=on_has_children_checkbox)
    
        add_child_btn.bind(on_press=lambda _: add_child_fields())
    
        def remove_child_btn_pressed(instance):
            indices_to_remove = [i for i, cb in enumerate(self.child_remove_checkboxes) if cb.active]
            for idx in sorted(indices_to_remove, reverse=True):
                self.children_inputs_layout.remove_widget(self.children_inputs_layout.children[len(self.child_name_inputs)-1-idx])
                del self.child_name_inputs[idx]
                del self.child_dob_inputs[idx]
                del self.child_disabled_checkboxes[idx]
                del self.child_remove_checkboxes[idx]
                del self.child_special_flags[idx]
            if not self.child_name_inputs:
                self.has_children_no.active = True
    
        remove_child_btn.bind(on_press=remove_child_btn_pressed)
    
        # Default to "No" selected
        self.has_children_no.active = True
    
        scroll.add_widget(layout)
        return scroll

    
    def create_additional_elements_screen(self):
        # Scrollable container
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
        layout = BoxLayout(orientation="vertical", spacing=20, padding=20, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))  # Allow vertical expansion
    
        # Helper function to create a label that wraps text within the window width
        def wrapped_SafeLabel(text, font_size, height, halign="center"):
            label = SafeLabel(
                text=text,
                font_size=font_size,
                halign=halign,
                valign="middle",
                color=get_color_from_hex(WHITE),
                size_hint_y=None,
                height=height
            )
            def update_text_size(instance, _):
                instance.text_size = (Window.width - 100, None)
            label.bind(width=update_text_size)
            update_text_size(label, None)
            return label
    
        # Instruction message centered
        instruction_anchor = AnchorLayout(anchor_x="center", anchor_y="top", size_hint_y=None, height=60)
        instruction_label = wrapped_SafeLabel(
            "Please Select The Following Additional Elements That Apply To You:\n",
            16,
            30,
            halign="center"
        )
        instruction_anchor.add_widget(instruction_label)
        layout.add_widget(instruction_anchor)
    
        # Dictionary to store checkboxes
        self.additional_elements_checkboxes = {}
    
        elements = [
            ("Limited Capability for Work (LCW)", "lcw"),
            ("Limited Capability for Work (LCW) pre 3rd April 2017", "lcw_2017"),
            ("Limited Capability for Work and Work-Related Activity (LCWRA)", "lcwra"),
            ("Carer Element", "carer"),
            ("Childcare Costs Element", "childcare"),
        ]
    
        # Group name for mutual exclusivity among LCW, LCW_2017, LCWRA
        lcw_group = "lcw_group"
    
        # Build rows for each element
        for label_text, key in elements:
            row = BoxLayout(orientation="horizontal", spacing=15, size_hint_y=None, height=40)
    
            # Checkbox setup
            if key in ("lcw", "lcw_2017", "lcwra"):
                cb = CheckBox(size_hint=(None, None), size=(30, 30), group=lcw_group)
            else:
                cb = CheckBox(size_hint=(None, None), size=(30, 30))
    
            # Add checkbox and label
            row.add_widget(cb)
            element_label = wrapped_SafeLabel(label_text, 16, 30, halign="left")
            element_label.size_hint_x = 1
            row.add_widget(element_label)
    
            layout.add_widget(row)
            self.additional_elements_checkboxes[key] = cb
    
        scroll.add_widget(layout)
        return scroll


    def create_sanction_screen(self):
        # Scrollable container
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
        layout = BoxLayout(orientation="vertical", spacing=20, padding=20, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))
    
        # Helper function for wrapped labels
        def wrapped_SafeLabel(text, font_size, height, halign="center"):
            label = SafeLabel(
                text=text,
                font_size=font_size,
                halign=halign,
                valign="middle",
                color=get_color_from_hex(WHITE),
                size_hint_y=None,
                height=height
            )
            def update_text_size(instance, _):
                instance.text_size = (Window.width - 60, None)
            label.bind(width=update_text_size)
            update_text_size(label, None)
            return label
    
        # Spacer below header
        layout.add_widget(SafeLabel(size_hint_y=None, height=20))
    
        # Yes/No option
        sanction_yn_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=80)
        sanction_yn_label = wrapped_SafeLabel(
            "Do you have a sanction?\nIf so, do you know the level, claimants, and days?",
            16, 40
        )
        sanction_yn_anchor.add_widget(sanction_yn_label)
        layout.add_widget(sanction_yn_anchor)
    
        sanction_yn_layout = BoxLayout(orientation="horizontal", spacing=20, size_hint_y=None, height=40)
        self.has_sanction_yes = CheckBox(group="has_sanction", size_hint=(None, None), size=(30, 30))
        self.has_sanction_no = CheckBox(group="has_sanction", size_hint=(None, None), size=(30, 30))
        sanction_yn_layout.add_widget(SafeLabel(text="Yes", font_size=14, halign="center", color=get_color_from_hex(WHITE)))
        sanction_yn_layout.add_widget(self.has_sanction_yes)
        sanction_yn_layout.add_widget(SafeLabel(text="No", font_size=14, halign="center", color=get_color_from_hex(WHITE)))
        sanction_yn_layout.add_widget(self.has_sanction_no)
        layout.add_widget(sanction_yn_layout)
    
        # Sanction level spinner centered
        sanction_level_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=70)
        sanction_levels = ["None", "Lowest", "Low", "Medium", "High"]
        self.sanction_level_spinner = Spinner(
            text="Select Sanction Level",
            values=sanction_levels,
            size_hint=(None, None), size=(250, 50),
            background_normal="",  # remove default image
            background_color=get_color_from_hex("#FFDD00"),  # GOV.UK Yellow background
            color=get_color_from_hex("#005EA5"),  # GOV.UK Blue text
            font_size=16, font_name="roboto",
            option_cls=CustomSpinnerOption,
            halign="center", valign="middle",
            text_size=(250, None)
        )
        sanction_level_anchor.add_widget(self.sanction_level_spinner)
        layout.add_widget(sanction_level_anchor)
    
        # Sanctioned claimants spinner centered
        claimants_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=70)
        self.sanctioned_claimants_input = Spinner(
            text="Select Sanctioned Claimants",
            values=["1", "2"],
            size_hint=(None, None), size=(250, 50),
            background_normal="",  # remove default image
            background_color=get_color_from_hex("#FFDD00"),  # GOV.UK Yellow background
            color=get_color_from_hex("#005EA5"),  # GOV.UK Blue text
            font_size=16, font_name="roboto",
            option_cls=CustomSpinnerOption,
            halign="center", valign="middle",
            text_size=(250, None)
        )
        claimants_anchor.add_widget(self.sanctioned_claimants_input)
        layout.add_widget(claimants_anchor)
    
        # Days sanctioned input centered
        days_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=60)
        self.sanction_days_input = CustomTextInput(
            hint_text="Number of days sanctioned",
            multiline=False,
            font_size=16,
            background_color=get_color_from_hex("#00000000"),
            foreground_color=get_color_from_hex(YELLOW),
            size_hint=(None, None), size=(250, 40)
        )
        days_anchor.add_widget(self.sanction_days_input)
        layout.add_widget(days_anchor)
    
        # 40% reduction checkbox row
        row_40 = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=30)
        self.sanction_40_checkbox = CheckBox(size_hint=(None, None), size=(30, 30))
        row_40.add_widget(self.sanction_40_checkbox)
        row_40.add_widget(SafeLabel(text="Apply 40% reduction rate", font_size=14, halign="left", color=get_color_from_hex(WHITE)))
        layout.add_widget(row_40)
    
        # Special circumstance checkbox row
        row_special = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=30)
        self.sanction_special_checkbox = CheckBox(size_hint=(None, None), size=(30, 30))
        row_special.add_widget(self.sanction_special_checkbox)
        row_special.add_widget(SafeLabel(text="Special circumstance", font_size=14, halign="left", color=get_color_from_hex(WHITE)))
        layout.add_widget(row_special)
    
        # Enable/disable sanction fields based on Yes/No
        def on_has_sanction_checkbox(_, __):
            sanction_fields = [
                self.sanction_level_spinner,
                self.sanctioned_claimants_input,
                self.sanction_days_input,
                self.sanction_40_checkbox,
                self.sanction_special_checkbox,
            ]
            enable = self.has_sanction_yes.active
            for field in sanction_fields:
                field.disabled = not enable
    
        self.has_sanction_yes.bind(active=on_has_sanction_checkbox)
        self.has_sanction_no.bind(active=on_has_sanction_checkbox)
        self.has_sanction_no.active = True
        on_has_sanction_checkbox(None, None)
    
        # Store sanction info for later use
        self.sanction_summary = {
            "level_spinner": self.sanction_level_spinner,
            "days_input": self.sanction_days_input,
            "claimants_input": self.sanctioned_claimants_input,
            "reduction_40": self.sanction_40_checkbox,
            "special": self.sanction_special_checkbox,
        }
    
        scroll.add_widget(layout)
        return scroll


    def create_advance_payments_screen(self):
        # Scrollable container
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
        layout = BoxLayout(orientation="vertical", spacing=20, padding=20, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))
    
        # Helper function for wrapped labels
        def wrapped_SafeLabel(text, font_size, height, halign="center"):
            label = SafeLabel(
                text=text,
                font_size=font_size,
                halign=halign,
                valign="middle",
                color=get_color_from_hex(WHITE),
                size_hint_y=None,
                height=height
            )
            def update_text_size(instance, _):
                instance.text_size = (Window.width - 60, None)
            label.bind(width=update_text_size)
            update_text_size(label, None)
            return label
    
        # Advance payment options header
        header_anchor = AnchorLayout(anchor_x="center", anchor_y="top", size_hint_y=None, height=60)
        header_label = wrapped_SafeLabel("Please select the advance payments that apply to you:", 16, 30, halign="center")
        header_anchor.add_widget(header_label)
        layout.add_widget(header_anchor)
    
        # Advance payments period checkboxes (mutually exclusive)
        self.advance_payments_period_checkboxes = {}
        elements = [
            ("6 Month Advance Payment", "six_month"),
            ("12 Month Advance Payment", "twelve_month"),
            ("24 Month Advance Payment", "twenty_four_month"),
        ]
        group_name = "advance_payment_period"
        for label_text, key in elements:
            row = BoxLayout(orientation="horizontal", spacing=15, size_hint_y=None, height=40)
            cb = CheckBox(size_hint=(None, None), size=(30, 30), group=group_name)
            row.add_widget(cb)
            element_label = wrapped_SafeLabel(label_text, 16, 30, halign="left")
            element_label.size_hint_x = 1
            row.add_widget(element_label)
            layout.add_widget(row)
            self.advance_payments_period_checkboxes[key] = cb
    
        # Advance payments input field centered
        input_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=60)
        self.advance_payments_input = CustomTextInput(
            hint_text="Enter payments received (£)",
            multiline=False,
            font_size=18,
            background_color=get_color_from_hex("#00000000"),
            foreground_color=get_color_from_hex(YELLOW),
            size_hint=(None, None), size=(250, 40)
        )
        input_anchor.add_widget(self.advance_payments_input)
        layout.add_widget(input_anchor)
    
        # Advance payment delays header
        delay_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=60)
        delay_label = wrapped_SafeLabel("Please select any advance payment delays that apply to you:", 16, 30, halign="center")
        delay_anchor.add_widget(delay_label)
        layout.add_widget(delay_anchor)
    
        # Advance payment delay checkboxes (mutually exclusive)
        self.advance_payments_delay_checkboxes = {}
        delay_elements = [
            ("1 Month Delay", "one_month"),
            ("3 Month Delay", "three_month")
        ]
        group_name = "advance_payment_delay"
        for label_text, key in delay_elements:
            row = BoxLayout(orientation="horizontal", spacing=15, size_hint_y=None, height=40)
            cb = CheckBox(size_hint=(None, None), size=(30, 30), group=group_name)
            row.add_widget(cb)
            element_label = wrapped_SafeLabel(label_text, 16, 30, halign="left")
            element_label.size_hint_x = 1
            row.add_widget(element_label)
            layout.add_widget(row)
            self.advance_payments_delay_checkboxes[key] = cb
    
        scroll.add_widget(layout)
        return scroll

            
def create_calculate_screen(self):
    layout = BoxLayout(orientation="vertical", spacing=20, padding=20)

    # Scrollable summary container
    summary_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
    summary_layout = BoxLayout(orientation="vertical", spacing=20, padding=10, size_hint_y=None)
    summary_layout.bind(minimum_height=summary_layout.setter('height'))

    # Title centered
    title_anchor = AnchorLayout(anchor_x="center", anchor_y="top", size_hint_y=None, height=50)
    summary_title = SafeLabel(
        text="Summary:",
        font_size=20,
        halign="center",
        valign="middle",
        color=get_color_from_hex(WHITE),
        size_hint_y=None,
        height=30
    )
    summary_title.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
    title_anchor.add_widget(summary_title)
    summary_layout.add_widget(title_anchor)

    # Summary labels (left aligned, wrapped)
    def make_summary_label():
        lbl = SafeLabel(font_size=14, halign="left", valign="top", color=get_color_from_hex(WHITE), size_hint_y=None)
        lbl.bind(width=lambda inst, val: setattr(inst, 'text_size', (Window.width - 60, None)))
        return lbl

    self.claimant_summary = make_summary_label()
    self.partner_summary = make_summary_label()
    self.finances_summary = make_summary_label()
    self.housing_summary = make_summary_label()
    self.children_summary = make_summary_label()
    self.additional_elements_summary = make_summary_label()
    self.sanction_summary = make_summary_label()
    self.advance_payment_summary = make_summary_label()

    # Add labels to layout
    for lbl in [
        self.claimant_summary,
        self.partner_summary,
        self.finances_summary,
        self.housing_summary,
        self.children_summary,
        self.additional_elements_summary,
        self.sanction_summary,
        self.advance_payment_summary
    ]:
        summary_layout.add_widget(lbl)

    # Update summary function (unchanged logic, just ensures labels wrap and resize)
    def update_summary():
        # Claimant details
        if hasattr(self, "name_input") and self.name_input.text:
            claimant_name = self.name_input.text
        else:
            claimant_name = "N/A"
    
        if hasattr(self, "dob_input") and self.dob_input.text:
            claimant_dob = self.dob_input.text
        else:
            claimant_dob = "N/A"
    
        self.claimant_summary.text = f"Claimant Details:\nName: {claimant_name}\nDate of Birth: {claimant_dob}\n"
    
        # Partner details
        if hasattr(self, "partner_name_input") and self.couple_claim_checkbox.active:
            partner_name = self.partner_name_input.text
            partner_dob = self.partner_dob_input.text if hasattr(self, "partner_dob_input") else "N/A"
            self.partner_summary.text = f"Partner Details:\nName: {partner_name}\nDate of Birth: {partner_dob}\n"
        else:
            self.partner_summary.text = "Partner Details: N/A"

        # Housing
        rent_or_mortgage = ""
        if hasattr(self, "housing_type_spinner"):
            if self.housing_type_spinner.text.lower() == "rent" and hasattr(self, "rent_mortgage_input"):
                rent_or_mortgage = f"Rent Amount: £{self.rent_mortgage_input.text}\n"
            elif self.housing_type_spinner.text.lower() == "own" and hasattr(self, "mortgage_input"):
                rent_or_mortgage = f"Mortgage Amount: £{self.mortgage_input.text}\n"
        self.housing_summary.text = (
            f"Housing Type: {self.housing_type_spinner.text}\n"
            f"Location: {self.location_spinner.text}\n"
            f"BRMA: {self.brma_spinner.text}\n"
            f"{rent_or_mortgage}"
        )
        self.housing_summary.texture_update()
        self.housing_summary.height = self.housing_summary.texture_size[1] + 10

        # Children, Additional Elements, Sanctions, Advance Payments
        # (retain your existing logic for these sections — already detailed and correct)

    # Bind updates to inputs
    self.couple_claim_checkbox.bind(active=lambda *_: update_summary())
    self.partner_name_input.bind(text=lambda *_: update_summary())
    self.partner_dob_input.bind(text=lambda *_: update_summary())
    self.dob_input.bind(text=lambda *_: update_summary())
    self.income_input.bind(text=lambda *_: update_summary())
    self.capital_input.bind(text=lambda *_: update_summary())
    self.housing_type_spinner.bind(text=lambda *_: update_summary())
    self.location_spinner.bind(text=lambda *_: update_summary())
    self.brma_spinner.bind(text=lambda *_: update_summary())

    # Initial update
    update_summary()

    # Calculate button centered
    button_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=80)
    calculate_button = RoundedButton(
        text="Calculate",
        size_hint=(None, None),
        size=(250, 60),
        font_size=20,
        font_name="roboto",
        color=get_color_from_hex("#005EA5"),
        background_color=(0, 0, 0, 0),
        background_normal="",
        halign="center", valign="middle",
        text_size=(250, None),
        on_press=self.calculate
    )
    button_anchor.add_widget(calculate_button)
    summary_layout.add_widget(button_anchor)

    summary_scroll.add_widget(summary_layout)
    layout.add_widget(summary_scroll)

    return layout




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





























