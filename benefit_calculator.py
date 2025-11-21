#BenefitCalculator.py

# import necessary libraries
from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.graphics import Ellipse, Color
from kivy.animation import Animation
from math import sin, cos, radians
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.checkbox import CheckBox
from kivy.uix.spinner import Spinner
from kivy.uix.spinner import SpinnerOption
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup # type: ignore
from kivy.lang import Builder
from kivy.graphics import Color, Line, RoundedRectangle, Rectangle
import os
import sys
from datetime import datetime
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem, TabbedPanelHeader
import csv
from kivy.uix.scrollview import ScrollView
from kivy.core.image import Image as CoreImage
import tracemalloc
from kivy.resources import resource_add_path, resource_find

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
    title = Label(
        text=title_text,
        font_size="50sp",
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
    footer_label = Label(
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
        sm.add_widget(LoginPage(name="login"))
        sm.add_widget(MainScreenGuestAccess(name="main_guest_access"))
        sm.add_widget(MainScreenFullAccess(name="main_full_access"))
        sm.add_widget(Calculator(name="calculator")) 
        # Add more screens as needed
        return sm



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
        super().__init__(**kwargs)
        with self.canvas.before:  # Use canvas.before to draw behind the button text
            # Set the color of the widget
            self.color_instruction = Color(rgba=get_color_from_hex("#FFDD00"))  # GOVUK_YELLOW
            # Draw a RoundedRectangle with rounded corners
            self.rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[20]  # Radius for all corners
            )
        # Bind position and size to update the rectangle dynamically
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        # Ensure the rectangle's position and size are updated
        self.rect.pos = self.pos
        self.rect.size = self.size

# Customizing Spinner to change dropdown background color
class CustomSpinnerOption(SpinnerOption):
    # Customize the dropdown options
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = get_color_from_hex("#FFFFFF")  # White background
        self.color = get_color_from_hex("#005EA5")  # GOVUK_BLUE text color
        self.background_normal = ""  # Remove default background image

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
        layout = BoxLayout(orientation="vertical", spacing=10, padding=20)

        build_header(layout, "Benefit Buddy")

        info_label = Label(
            text="This section of the app is still currently in development.\n\nPlease check back later for updates.",
            font_size="16sp",
            halign="center",
            valign="middle",
            color=get_color_from_hex("#FFFFFF"),
            size_hint_y=None,
            height=Window.height * 0.3
        )
        info_label.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
        layout.add_widget(info_label)

        layout.add_widget(RoundedButton(
            text="Back to Main Menu",
            size_hint=(None, None), size=(250, 50),
            background_color=(0, 0, 0, 0), background_normal="",
            font_size="20sp", font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            on_press=self.go_to_main
        ))

        build_footer(layout)
        self.add_widget(layout)

    def go_to_main(self, instance):
        self.manager.current = "main"


# Define the Splash Screen
class SplashScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", spacing=50, padding=50)

        build_header(layout, "Benefit Buddy")

        logo = Image(source="logo.png", size_hint=(None, None), size=(150, 150))
        layout.add_widget(logo)

        loading_animation = PNGSequenceAnimationWidget(
            size_hint=(None, None), size=(100, 100),
            pos_hint={"center_x": 0.5, "center_y": 0.5}
        )
        layout.add_widget(loading_animation)

        build_footer(layout)
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

        disclaimer_text = Label(
            text=("Disclaimer: This app is currently still in development and may not be fully accurate.\n\n"
                  "It is for informational purposes only and does not constitute financial advice.\n\n\n"
                  "Guest access has limited functionality and will not save your data."),
            font_size="18sp",
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
        layout = BoxLayout(orientation='vertical', spacing=10, padding=20)

        # Reusable GOV.UK header
        build_header(layout, "Benefit Buddy")

        # Logo
        logo = Image(source="logo.png", size_hint=(None, None), size=(150, 150))
        layout.add_widget(logo)

        # Shared button style
        button_style = {
            "size_hint": (None, None),
            "size": (250, 50),
            "background_color": (0, 0, 0, 0),
            "background_normal": "",
            "pos_hint": {"center_x": 0.5}
        }

        # GOV.UK blue buttons
        layout.add_widget(RoundedButton(text="Create Account", **button_style,
                                        font_size="20sp", font_name="roboto",
                                        color=get_color_from_hex("#005EA5"),
                                        on_press=self.go_to_create_account))
        layout.add_widget(RoundedButton(text="Login", **button_style,
                                        font_size="20sp", font_name="roboto",
                                        color=get_color_from_hex("#005EA5"),
                                        on_press=self.go_to_login))
        layout.add_widget(RoundedButton(text="Guest", **button_style,
                                        font_size="20sp", font_name="roboto",
                                        color=get_color_from_hex("#005EA5"),
                                        on_press=self.go_to_guest_access))
        layout.add_widget(RoundedButton(text="Settings", **button_style,
                                        font_size="20sp", font_name="roboto",
                                        color=get_color_from_hex("#005EA5"),
                                        on_press=self.go_to_settings))
        layout.add_widget(RoundedButton(text="Exit", **button_style,
                                        font_size="20sp", font_name="roboto",
                                        color=get_color_from_hex("#005EA5"),
                                        on_press=self.exit_app))

        # Reusable GOV.UK footer
        build_footer(layout)

        self.add_widget(layout)

    # Navigation methods
    def go_to_create_account(self, instance):
        self.manager.current = "create_account"

    def go_to_login(self, instance):
        self.manager.current = "login"

    def go_to_guest_access(self, instance):
        self.manager.current = "main_guest_access"

    def go_to_settings(self, instance):
        self.manager.current = "settings"

    def go_to_home(self, instance):
        self.manager.current = "main"

    def exit_app(self, instance):
        App.get_running_app().stop()


# Define the Main Screen for Full Access
class MainScreenFullAccess(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", spacing=10, padding=20)

        build_header(layout, "Benefit Buddy")

        button_style = {
            "size_hint": (None, None),
            "size": (250, 50),
            "background_color": (0, 0, 0, 0),
            "background_normal": "",
            "pos_hint": {"center_x": 0.5}
        }

        layout.add_widget(RoundedButton(
            text="Predict Next Payment",
            **button_style,
            font_size="20sp", font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            on_press=self.predict_payment
        ))
        layout.add_widget(RoundedButton(
            text="View Previous Payments",
            **button_style,
            font_size="20sp", font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            on_press=lambda x: print("Payments feature not yet implemented")
        ))
        layout.add_widget(RoundedButton(
            text="Update Details",
            **button_style,
            font_size="20sp", font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            on_press=lambda x: print("Update details feature not yet implemented")
        ))
        layout.add_widget(RoundedButton(
            text="Log Out",
            **button_style,
            font_size="20sp", font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            on_press=self.log_out
        ))

        build_footer(layout)
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
        lbl = Label(text=message, halign="center", color=get_color_from_hex(WHITE))
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
            font_size="20sp",
            font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            background_color=(0, 0, 0, 0),
            background_normal="",
            on_press=lambda _: self.show_prediction_popup(self.income_input.text)
        )

        content.add_widget(Label(
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
        try:
            income = float(income)
            predicted_payment = self.payment_prediction(income)
            message = f"Your next payment is predicted to be: £{predicted_payment:.2f}"
        except ValueError:
            message = "Invalid income entered. Please enter a numeric value."

        result_label = Label(
            text=message,
            font_size=20,
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
        return self.calculate_entitlement()  # Ensure this method exists

        
    def calculate_entitlement(self):
        """Calculate entitlement based on user details."""

        # --- Gather inputs ---
        try:
            dob_date = datetime.strptime(self.dob_input.text, "%d-%m-%Y")
            partner_dob_date = datetime.strptime(self.partner_dob_input.text, "%d-%m-%Y")
        except ValueError:
            Popup("Invalid Date", "Please enter DOBs in DD-MM-YYYY format").open()
            return

        current_date = datetime.now()
        age = current_date.year - dob_date.year - ((current_date.month, current_date.day) < (dob_date.month, dob_date.day))
        partner_age = current_date.year - partner_dob_date.year - ((current_date.month, current_date.day) < (partner_dob_date.month, partner_dob_date.day))

        relationship_status = self.relationship_input.text.lower()  # e.g. "single" or "couple"

        # --- Standard allowance ---
        if relationship_status == "single":
            standard_allowance = 316.98 if age < 25 else 400.14
        elif relationship_status == "couple":
            if age < 25 and partner_age < 25:
                standard_allowance = 497.55
            else:
                standard_allowance = 628.10
        else:
            Popup("Invalid Relationship Status", "Please select single or couple").open()
            return

        # --- Child elements ---
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

        # --- Other elements ---
        carer_element = 201.68 if self.is_carer else 0
        disability_element = 0  # add LCW/LCWRA logic
        childcare_element = 0   # add childcare cost logic
        housing_element = 0     # add housing logic

        # --- Income & work allowance ---
        try:
            income = float(self.income_input.text)
        except ValueError:
            Popup("Invalid Income", "Please enter a numeric income").open()
            return

        children = len(children_dobs)
        if children > 0 or self.lcw:
            work_allowance = 411 if self.receives_housing_support else 684
        else:
            work_allowance = 0

        # --- Totals ---
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
        layout = BoxLayout(orientation="vertical", spacing=10, padding=20)

        # Reusable GOV.UK header
        build_header(layout, "Benefit Buddy")

        # Info label
        info_label = Label(
            text=("Guest Access has limited functionality.\n\n"
                  "A Full Access Mode with more features is currently in development.\n"
                  "Look out for updates and soon be able to have a payment prediction in seconds."),
            font_size="16sp",
            halign="center",
            valign="middle",
            color=get_color_from_hex(WHITE),
            size_hint_y=None,
            height=Window.height * 0.3
        )
        info_label.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
        layout.add_widget(info_label)

        # Shared button style
        button_style = {
            "size_hint": (None, None),
            "size": (250, 50),
            "background_color": (0, 0, 0, 0),
            "background_normal": "",
            "pos_hint": {"center_x": 0.5}
        }

        # Buttons
        layout.add_widget(RoundedButton(
            text="Calculate Universal Credit",
            **button_style,
            font_size="20sp", font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            on_press=self.go_to_calculator
        ))
        layout.add_widget(RoundedButton(
            text="Log Out",
            **button_style,
            font_size="20sp", font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            on_press=self.log_out
        ))

        # Reusable GOV.UK footer
        build_footer(layout)

        self.add_widget(layout)

    # Navigation methods
    def go_to_calculator(self, instance):
        print("Navigating to the calculator...")
        self.manager.current = "calculator"

    def log_out(self, instance):
        print("Logging out...")
        self.manager.current = "main"

    def go_back(self, instance):
        self.manager.current = "main"


# Define the Create Account Screen
class CreateAccountPage(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", spacing=10, padding=20)

        # Reusable GOV.UK header
        build_header(layout, "Benefit Buddy")

        # Info label
        info_label = Label(
            text="This section of the app is still currently in development.\n\nPlease check back later for updates.",
            font_size="16sp",
            halign="center",
            valign="middle",
            color=get_color_from_hex(WHITE),
            size_hint_y=None,
            height=Window.height * 0.3
        )
        info_label.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
        layout.add_widget(info_label)

        # Shared button style
        button_style = {
            "size_hint": (None, None),
            "size": (250, 50),
            "background_color": (0, 0, 0, 0),
            "background_normal": "",
            "pos_hint": {"center_x": 0.5}
        }

        # Back button
        layout.add_widget(RoundedButton(
            text="Back to Home",
            **button_style,
            font_size="20sp", font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            on_press=self.go_back
        ))

        # Reusable GOV.UK footer
        build_footer(layout)

        self.add_widget(layout)

    def go_back(self, instance):
        self.manager.current = "main"


# Define the Login Screen
class LoginPage(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", spacing=10, padding=20)

        # Reusable GOV.UK header
        build_header(layout, "Benefit Buddy")

        # Info label
        info_label = Label(
            text=("This section of the app is still currently in development.\n\n"
                  "When this feature is fully developed you will be able to have much more usability;\n"
                  "e.g. Returning monthly to only require inputting that month's income to see your predicted entitlement."),
            font_size="16sp",
            halign="center",
            valign="middle",
            color=get_color_from_hex(WHITE),
            size_hint_y=None,
            height=Window.height * 0.3
        )
        info_label.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
        layout.add_widget(info_label)

        # Shared button style
        button_style = {
            "size_hint": (None, None),
            "size": (250, 50),
            "background_color": (0, 0, 0, 0),
            "background_normal": "",
            "pos_hint": {"center_x": 0.5}
        }

        # Buttons
        layout.add_widget(RoundedButton(
            text="Log In",
            **button_style,
            font_size="20sp", font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            on_press=self.log_in
        ))
        layout.add_widget(RoundedButton(
            text="Back to Home",
            **button_style,
            font_size="20sp", font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            on_press=self.go_back
        ))

        # Reusable GOV.UK footer
        build_footer(layout)

        self.add_widget(layout)

    def log_in(self, instance):
        print("Logging in...")
        self.manager.current = "main_full_access"

    def go_back(self, instance):
        self.manager.current = "main"


# Define the Calculator Screen
class Calculator(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", spacing=5, padding=5)

        # Reusable GOV.UK header with back button
        build_header(layout, "Benefit Buddy")
        back_button = RoundedButton(
            text="Back",
            size_hint=(None, None), size=(100, 25),
            background_color=get_color_from_hex("#005EA5"),
            background_normal="",
            font_size="14sp", font_name="roboto",
            color=get_color_from_hex("#FFDD00"),
            on_press=lambda x: setattr(self.manager, 'current', "main_guest_access")
        )
        back_button.pos_hint = {"center_x": 0.5}
        layout.add_widget(back_button)

        # Define screens (stubbed for now)
        self.screens = [
            ("Introduction", self.create_intro_screen),
            ("Claimant Details", self.create_claimant_details_screen),
            ("Finances", self.create_finances_screen),
            ("Housing", self.create_housing_screen),
            ("Children", self.create_children_screen),
            ("Additional Elements", self.create_additional_elements_screen),
            ("Sanctions", self.create_sanction_screen),
            ("Advanced Payment", self.create_advance_payments_screen),
            ("Summary", self.create_calculate_screen)
        ]

        # Spinner
        self.screen_spinner = Spinner(
            text="Introduction ▼",
            values=[name for name, _ in self.screens],
            size_hint=(None, None), size=(250, 50),
            background_color=(0, 0, 0, 0), background_normal="",
            color=get_color_from_hex("#005EA5"),
            font_size="20sp", font_name="roboto",
            option_cls=CustomSpinnerOption,
            pos_hint={"center_x": 0.5}
        )

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

        layout.add_widget(self.screen_spinner)
        layout.add_widget(self.screen_content)

        # Reusable GOV.UK footer
        build_footer(layout)

        self.add_widget(layout)

    # Stub methods
    def create_intro_screen(self): return Label(text="Intro screen")
    def create_claimant_details_screen(self): return Label(text="Claimant details")
    def create_finances_screen(self): return Label(text="Finances")
    def create_housing_screen(self): return Label(text="Housing")
    def create_children_screen(self): return Label(text="Children")
    def create_additional_elements_screen(self): return Label(text="Additional elements")
    def create_sanction_screen(self): return Label(text="Sanctions")
    def create_advance_payments_screen(self): return Label(text="Advance payments")
    def create_calculate_screen(self): return Label(text="Summary")

        
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
                content = Label(
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
                    content = Label(
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
                    content = Label(
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
                    content = Label(
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
                    content = Label(
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
                    content = Label(
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
                                content = Label(
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
                        content = Label(
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
                    content = Label(
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
                    content = Label(
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
                    content = Label(
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
                    content = Label(
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
                                content = Label(
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
                        content = Label(
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
                content = Label(
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
            content = Label(
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
            content = Label(
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
        def wrapped_label(text, font_size, height):
            label = Label(
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

        layout.add_widget(wrapped_label("Welcome to the Benefit Buddy Calculator", 18, 30))
        layout.add_widget(wrapped_label("This calculator will help you estimate your Universal Credit entitlement.", 16, 30))
        layout.add_widget(wrapped_label("Please follow the steps to enter your details.", 14, 24))
        layout.add_widget(wrapped_label("You can navigate through the screens using the dropdown menu above.", 14, 24))
        layout.add_widget(wrapped_label("Before you start, please ensure you have the following information ready:", 14, 24))
        layout.add_widget(wrapped_label("- Your personal details (name, date of birth, etc.)", 14, 24))
        layout.add_widget(wrapped_label("- Your income and capital details", 14, 24))
        layout.add_widget(wrapped_label("- Your housing situation (rent or own)", 14, 24))
        layout.add_widget(wrapped_label("- Details of any children or dependents", 14, 24))
        layout.add_widget(wrapped_label("- Any additional elements that may apply to you", 14, 24))

        # Add a button to proceed to the next screen with consistent aesthetics
        proceed_button = RoundedButton(
            text="Proceed to Claimant Details",
            size_hint=(None, None),
            size=(250, 50),
            background_color=(0, 0, 0, 0),  # Transparent background
            background_normal="",  # Remove default background image
            font_size="20sp",
            font_name="roboto",
            color=get_color_from_hex("#005EA5"),  # GOVUK_BLUE text color
            on_press=lambda x: setattr(self.screen_spinner, 'text', "Claimant Details ▼")
        )
        proceed_button.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        layout.add_widget(proceed_button)

        scroll.add_widget(layout)
        return scroll
        
    def on_couple_claim_checkbox_active(self, checkbox, value):
        self.partner_name_input.disabled = not value
        self.partner_dob_input.disabled = not value

    def create_claimant_details_screen(self):
        layout = BoxLayout(orientation="vertical", spacing=10, padding=20)
        layout.add_widget(Label(text="Select Claimant Type", font_size=20, halign="center", color=get_color_from_hex(WHITE)))

        # Create a horizontal layout for checkboxes and their labels
        claimant_type_layout = BoxLayout(orientation="horizontal", spacing=10)
        self.single_claimant_checkbox = CheckBox(group="claimant_type")
        self.couple_claim_checkbox = CheckBox(group="claimant_type")
        claimant_type_layout.add_widget(Label(text="Single", font_size=18, color=get_color_from_hex(WHITE)))
        claimant_type_layout.add_widget(self.single_claimant_checkbox)
        claimant_type_layout.add_widget(Label(text="Couple", font_size=18, color=get_color_from_hex(WHITE)))
        claimant_type_layout.add_widget(self.couple_claim_checkbox)
        layout.add_widget(claimant_type_layout)

        self.couple_claim_checkbox.bind(active=self.on_couple_claim_checkbox_active)
        
        layout.add_widget(Label(text="Enter Claimant Details", font_size=20, halign="center", color=get_color_from_hex(WHITE)))
        self.name_input = (CustomTextInput(hint_text="Name", multiline=False, font_size=18, background_color=get_color_from_hex(WHITE), foreground_color=get_color_from_hex(GOVUK_BLUE)))
        layout.add_widget(self.name_input)
        self.dob_input = DOBInput(hint_text="DD/MM/YYYY", multiline=False, font_size=18, background_color=get_color_from_hex(WHITE), foreground_color=get_color_from_hex(GOVUK_BLUE))
        layout.add_widget(self.dob_input)
        
        layout.add_widget(Label(text="Enter Partner Details", font_size=20, halign="center", color=get_color_from_hex(WHITE)))
        self.partner_name_input = CustomTextInput(hint_text="Name", multiline=False, font_size=18, disabled=True, background_color=get_color_from_hex(WHITE), foreground_color=get_color_from_hex(GOVUK_BLUE))
        self.partner_dob_input = DOBInput(hint_text="DD/MM/YYYY", multiline=False, font_size=18, disabled=True, background_color=get_color_from_hex(WHITE), foreground_color=get_color_from_hex(GOVUK_BLUE))
        layout.add_widget(self.partner_name_input)
        layout.add_widget(self.partner_dob_input)
        
        return layout

    def create_finances_screen(self):
        layout = BoxLayout(orientation="vertical", spacing=10, padding=20)
        layout.add_widget(Label(text="Enter Income", font_size=24, halign="center", color=get_color_from_hex(WHITE)))

        # Subclass TextInput to handle Tab key
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

        self.capital_input = TabFocusTextInput(hint_text="Enter your capital", multiline=False, font_size=18, background_color=get_color_from_hex(WHITE), foreground_color=get_color_from_hex(GOVUK_BLUE))
        self.income_input = TabFocusTextInput(hint_text="Enter your monthly income", multiline=False, font_size=18, background_color=get_color_from_hex(WHITE), foreground_color=get_color_from_hex(GOVUK_BLUE), next_input=self.capital_input)

        layout.add_widget(self.income_input)
        layout.add_widget(Label(text="Enter capital", font_size=24, halign="center", color=get_color_from_hex(WHITE)))
        layout.add_widget(self.capital_input)

        # Bind Enter key on income_input to focus capital_input
        def focus_capital_input(instance):
            self.capital_input.focus = True
            self.income_input.bind(on_text_validate=focus_capital_input)

        return layout
    
    def create_housing_screen(self):
        layout = BoxLayout(orientation="vertical", spacing=10, padding=10)
        self.housing_type_spinner = Spinner(
            text="Select Housing Type",
            values=("Rent", "Own", "Shared Accommodation"),
            font_size=18,
            background_color=(0, 0, 0, 0),
            color=get_color_from_hex(WHITE)
        )
        layout.add_widget(self.housing_type_spinner)

        self.rent_mortgage_input = CustomTextInput(
            hint_text="Enter monthly rent amount (£)",
            multiline=False,
            font_size=18,
            background_color=get_color_from_hex("#00000000"),
            foreground_color=get_color_from_hex(YELLOW)  # Use GOVUK_YELLOW for text color
        )
        self.mortgage_input = CustomTextInput(
            hint_text="Enter monthly mortgage amount (£)",
            multiline=False,
            font_size=18,
            background_color=get_color_from_hex("#00000000"),
            foreground_color=get_color_from_hex(YELLOW)  # Use GOVUK_YELLOW for text color
        )

        # Only show the appropriate input based on housing type
        def update_amount_input(spinner, value):
            # Remove both if present
            if self.rent_mortgage_input.parent:
                layout.remove_widget(self.rent_mortgage_input)
            if self.mortgage_input.parent:
                layout.remove_widget(self.mortgage_input)
            if value.lower() == "rent":
                layout.add_widget(self.rent_mortgage_input)
            elif value.lower() == "own":
                layout.add_widget(self.mortgage_input)
        self.housing_type_spinner.bind(text=update_amount_input)
        # Show the correct input initially
        update_amount_input(self.housing_type_spinner, self.housing_type_spinner.text)

        # Add postcode input for BRMA lookup
        self.postcode_input = CustomTextInput(
            hint_text="Enter postcode (e.g. SW1A 1AA)",
            multiline=False,
            font_size=18,
            background_color=get_color_from_hex("#00000000"),
            foreground_color=get_color_from_hex(YELLOW)  # Use GOVUK_YELLOW for text color
        )
        layout.add_widget(self.postcode_input)

        # Add a "Find BRMA" button to look up BRMA and location from postcode
        find_brma_btn = RoundedButton(
            text="Find BRMA",
            size_hint=(None, None),
            size=(150, 40),
            font_size="16sp",
            font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            background_color=(0, 0, 0, 0),
            background_normal="",
            pos_hint = {"center_x": 0.5, "center_y": 0.5}  # Center the button
        )

        def on_find_brma(instance):
            find_brma_btn.text = "Finding BRMA"
            postcode = self.postcode_input.text.strip().replace(" ", "").upper()
            
            if not postcode:
                self.brma_spinner.text = "Enter postcode"
                find_brma_btn.text = "Find BRMA"
                return

            try:
                # Lookup postcode in the master CSV
                file_path = resource_find("pcode_brma_lookup.csv") or os.path.join(BASE_DIR, ".venv", "pcode_brma_lookup.csv")
                with open(file_path, newline='', encoding='utf-8') as csvfile:
                    reader = csv.reader(csvfile)
                    headers = next(reader, None)
                    found = False

                    for row in reader:
                        # Match against postcode columns (2, 3, or 4)
                        for idx in [1, 2, 3]:
                            if idx < len(row):
                                pcode = row[idx].replace(" ", "").upper()
                                if pcode == postcode:
                                    country_code = row[headers.index("country")] if "country" in headers else ""
                                    brma = row[headers.index("brma_name")] if "brma_name" in headers else ""
                                    country_map = {"E": "England", "S": "Scotland", "W": "Wales"}
                                    location = country_map.get(country_code.upper(), "")

                                    # Update UI on main thread
                                    def update_spinners(dt):
                                        if location in self.location_spinner.values:
                                            self.location_spinner.text = location
                                            update_brma_spinner(self.location_spinner, location)
                                        if brma in self.brma_spinner.values:
                                            self.brma_spinner.text = brma
                                            find_brma_btn.text = "Find BRMA"

                                    Clock.schedule_once(update_spinners, 0)
                                    found = True
                                    break # Break inner loop
                    
                        if found:
                            break # Break outer loop

                    if not found:
                        self.brma_spinner.text = "Not found"
                        find_brma_btn.text = "Find BRMA"

            except Exception as e:
                self.brma_spinner.text = f"Error: {str(e)}"
                find_brma_btn.text = "Find BRMA"

        # Bind the button
        find_brma_btn.bind(on_press=on_find_brma)
        layout.add_widget(find_brma_btn)

        # Location spinner
        self.location_spinner = Spinner(
             text="Select Location",
            values=("England", "Scotland", "Wales"),
            font_size=18,
            background_color=(0, 0, 0, 0),
            color=get_color_from_hex(WHITE)
        )
        layout.add_widget(self.location_spinner)

        # BRMA spinner
        self.brma_spinner = Spinner(
            text="Select BRMA",
            values=[],
            font_size=18,
            background_color=(0, 0, 0, 0),
            color=get_color_from_hex(WHITE)
        )
        layout.add_widget(self.brma_spinner)


        # Update BRMA spinner based on location selection
        LHA_FILES = {
            "England": "LHA-England.csv",
            "Scotland": "LHA-Scotland.csv",
            "Wales": "LHA-Wales.csv"
        }

        def update_brma_spinner(instance, value):
            try:
                if value not in LHA_FILES:
                    self.brma_spinner.values = []
                    self.brma_spinner.text = "Select BRMA"
                    return

                filename = LHA_FILES[value]
                file_path = resource_find(filename) or os.path.join(BASE_DIR, ".venv", filename)

                with open(file_path, newline='', encoding='utf-8') as csvfile:
                    reader = csv.reader(csvfile)
                    next(reader, None)  # Skip header
                    brma_values = [row[0] for row in reader if row]

                self.brma_spinner.values = brma_values[1:] if len(brma_values) > 1 else ["No BRMAs"]
                self.brma_spinner.text = self.brma_spinner.values[0]

            except FileNotFoundError:
                self.brma_spinner.values = ["Error: File not found"]
                self.brma_spinner.text = "Error"
            except Exception as e:
                self.brma_spinner.values = [f"Error: {str(e)}"]
                self.brma_spinner.text = "Error"

        self.location_spinner.bind(text=update_brma_spinner)
        
        # Style the Spinner widgets to match the RoundedButton appearance
        spinner_style = {
            "size_hint": (None, None),
            "size": (250, 50),
            "background_color": (0, 0, 0, 0),  # Transparent background
            "background_normal": "",  # Remove default background image
            "color": get_color_from_hex("#005EA5"),  # GOVUK_BLUE text color
            "font_size": "20sp",
            "font_name": "roboto"
        }

        for spinner in [self.housing_type_spinner, self.location_spinner, self.brma_spinner]:
            spinner.size_hint = spinner_style["size_hint"]
            spinner.size = spinner_style["size"]
            spinner.background_color = spinner_style["background_color"]
            spinner.background_normal = spinner_style["background_normal"]
            spinner.color = spinner_style["color"]
            spinner.font_size = spinner_style["font_size"]
            spinner.font_name = spinner_style["font_name"]
            spinner.option_cls = CustomSpinnerOption  # Use custom dropdown option

        # Add a canvas.before to draw rounded rectangle behind each spinner
        def add_spinner_background(spinner):
            with spinner.canvas.before:
                spinner.bg_color = Color(rgba=get_color_from_hex("#FFDD00"))  # GOVUK_YELLOW
                spinner.bg_rect = RoundedRectangle(
                    pos=spinner.pos,
                    size=spinner.size,
                    radius=[20]
                )
            def update_bg_rect(instance, value):
                spinner.bg_rect.pos = spinner.pos
                spinner.bg_rect.size = spinner.size
            spinner.bind(pos=update_bg_rect, size=update_bg_rect)

        add_spinner_background(self.housing_type_spinner)
        add_spinner_background(self.location_spinner)
        add_spinner_background(self.brma_spinner)
        
        return layout

    def create_children_screen(self):
        # Use a ScrollView to make the screen vertically scrollable
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
        layout = BoxLayout(orientation="vertical", spacing=10, padding=20, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))  # Let layout expand vertically

        layout.add_widget(Label(text="Children Details", font_size=24, halign="center", color=get_color_from_hex(WHITE), size_hint_y=None, height=40))

        # Yes/No checkbox for "Do you have children?"
        yn_layout = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=40)
        layout.add_widget(Label(text="Do you have children?", font_size=18, color=get_color_from_hex(WHITE), size_hint_y=None, height=30))
        self.has_children_yes = CheckBox(group="has_children", size_hint=(None, None), size=(30, 30))
        self.has_children_no = CheckBox(group="has_children", size_hint=(None, None), size=(30, 30))
        yn_layout.add_widget(Label(text="Yes", font_size=16, color=get_color_from_hex(WHITE), size_hint_x=None, width=40))
        yn_layout.add_widget(self.has_children_yes)
        yn_layout.add_widget(Label(text="No", font_size=16, color=get_color_from_hex(WHITE), size_hint_x=None, width=40))
        yn_layout.add_widget(self.has_children_no)
        layout.add_widget(yn_layout)

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

        # Add Another Child button
        add_child_btn = RoundedButton(
            text="Add Another Child",
            size_hint=(None, None),
            size=(200, 40),
            font_size="16sp",
            font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            background_color=(0, 0, 0, 0),
            background_normal=""
        )

        # Remove Child button
        remove_child_btn = RoundedButton(
            text="Remove Selected Child",
            size_hint=(None, None),
            size=(200, 40),
            font_size="16sp",
            font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            background_color=(0, 0, 0, 0),
            background_normal=""
        )

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
            child_col = BoxLayout(orientation="vertical", spacing=5, size_hint_y=None)
            # Name
            name_input = CustomTextInput(
                hint_text=f"Child {idx} Name",
                multiline=False,
                font_size=18,
                background_color=get_color_from_hex(WHITE),
                foreground_color=get_color_from_hex(GOVUK_BLUE),
                size_hint_x=1,
                size_hint_y=None,
                height=40
            )
            # DOB using DOBInput for proper date formatting and validation
            dob_input = DOBInput(
                hint_text=f"Child {idx} DOB (DD/MM/YYYY)",
                multiline=False,
                font_size=18,
                background_color=get_color_from_hex(WHITE),
                foreground_color=get_color_from_hex(GOVUK_BLUE),
                size_hint_x=1,
                size_hint_y=None,
                height=40
            )

            # Add name and dob fields first
            child_col.add_widget(name_input)
            child_col.add_widget(dob_input)

            # Special circumstances checkboxes (placed below input fields)
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
                row.add_widget(Label(
                    text=label,
                    font_size=14,
                    color=get_color_from_hex(WHITE),
                    size_hint_x=1,
                    halign="left",
                    valign="middle"
                ))
                special_layout.add_widget(row)
            # Set height after adding all rows
            special_layout.height = 24 * len(special_flags) + 5 * (len(special_flags) - 1)

            # Add special_layout below the input fields
            child_col.add_widget(special_layout)

            # Set height for child_col
            child_col.height = 40 + 40 + special_layout.height + 20

            self.child_name_inputs.append(name_input)
            self.child_dob_inputs.append(dob_input)
            self.child_special_flags.append(special_flags)

            self.children_inputs_layout.add_widget(child_col)

            # Bind width of child_col and its children to window width for responsiveness
            def update_width(*_):
                width = Window.width - 60  # account for padding/margins
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

        def add_child_btn_pressed(instance):
            add_child_fields()

        add_child_btn.bind(on_press=add_child_btn_pressed)

        def remove_child_btn_pressed(instance):
            indices_to_remove = [i for i, cb in enumerate(self.child_remove_checkboxes) if cb.active]
            for idx in sorted(indices_to_remove, reverse=True):
                self.children_inputs_layout.remove_widget(self.children_inputs_layout.children[len(self.child_name_inputs)-1-idx])
                del self.child_name_inputs[idx]
                del self.child_dob_inputs[idx]
                del self.child_disabled_checkboxes[idx]
                del self.child_remove_checkboxes[idx]
                del self.child_special_flags[idx]
            # If all children are removed, set "No" checkbox active
            if not self.child_name_inputs:
                self.has_children_no.active = True

        remove_child_btn.bind(on_press=remove_child_btn_pressed)

        layout.add_widget(add_child_btn)
        layout.add_widget(remove_child_btn)

        # Default to "No" selected
        self.has_children_no.active = True

        scroll.add_widget(layout)
        return scroll
    
    def create_additional_elements_screen(self):
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
        layout = BoxLayout(orientation="vertical", spacing=20, padding=20, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))  # Let layout expand vertically

        # Helper function to create a label that wraps text within the window width
        def wrapped_label(text, font_size, height):
            label = Label(
                text=text,
                font_size=font_size,
                halign="left",
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

        # Instruction message
        layout.add_widget(wrapped_label(
            "Please Select The Following Additional Elements That Apply To You:\n",
            16,
            30
        ))

        # List of additional elements with checkboxes
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

        for label_text, key in elements:
            row = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=40)
            # Make lcw, lcw_2017, lcwra mutually exclusive
            if key in ("lcw", "lcw_2017", "lcwra"):
                cb = CheckBox(size_hint=(None, None), size=(30, 30), group=lcw_group)
                row.add_widget(cb)
            elif key == "carer":
                cb = CheckBox(size_hint=(None, None), size=(30, 30))
                row.add_widget(cb)
            elif key == "childcare":
                cb = CheckBox(size_hint=(None, None), size=(30, 30))
                row.add_widget(cb)
            # Add a little spacing between checkbox and label
            row.add_widget(Label(size_hint_x=None, width=10))
            element_label = wrapped_label(label_text, 16, 30)
            element_label.size_hint_x = 1
            row.add_widget(element_label)
            layout.add_widget(row)
            self.additional_elements_checkboxes[key] = cb

        scroll.add_widget(layout)
        return scroll

    def create_sanction_screen(self):
        # Use a ScrollView to make the sanction screen vertically scrollable
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
        layout = BoxLayout(orientation="vertical", spacing=20, padding=20, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))  # Let layout expand vertically

        # Helper function to create a label that wraps text within the window width
        def wrapped_label(text, font_size, height):
            label = Label(
                text=text,
                font_size=font_size,
                halign="left",
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

        # Initialize sanction-related widgets as attributes before using them in callbacks
        self.sanction_level_spinner = None
        self.sanctioned_claimants_input = None
        self.sanction_days_input = None
        self.sanction_40_checkbox = None
        self.sanction_special_checkbox = None

        # Add vertical spacing to move the label down from the header
        layout.add_widget(Label(size_hint_y=None, height=20))  # Spacer

        # Yes/No option: "Do you have a sanction?" (put at the top, not in a row with the label)
        sanction_yn_label = wrapped_label(
            "Do you have a sanction?\nIf so do you know the level of sanction, the number of sanctioned claimants, and the number of days sanctioned for?",
            16, 40
        )
        layout.add_widget(sanction_yn_label)

        sanction_yn_layout = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=40)
        self.has_sanction_yes = CheckBox(group="has_sanction", size_hint=(None, None), size=(30, 30))
        self.has_sanction_no = CheckBox(group="has_sanction", size_hint=(None, None), size=(30, 30))
        sanction_yn_layout.add_widget(Label(text="Yes", font_size=14, color=get_color_from_hex(WHITE), size_hint_x=None, width=40))
        sanction_yn_layout.add_widget(self.has_sanction_yes)
        sanction_yn_layout.add_widget(Label(text="No", font_size=14, color=get_color_from_hex(WHITE), size_hint_x=None, width=40))
        sanction_yn_layout.add_widget(self.has_sanction_no)
        layout.add_widget(sanction_yn_layout)

        # Sanction level selection
        sanction_levels = ["None", "Lowest", "Low", "Medium", "High"]
        self.sanction_level_spinner = Spinner(
            text="Select Sanction Level",
            values=sanction_levels,
            font_size="16sp",
            font_name="roboto",
            size_hint=(None, None),
            size=(250, 50),
            background_color=(0, 0, 0, 0),  # Transparent background
            background_normal="",  # Remove default background image
            color=get_color_from_hex("#005EA5"),  # GOVUK_BLUE text color
            option_cls=CustomSpinnerOption
        )

        # Add rounded rectangle background to match RoundedButton
        with self.sanction_level_spinner.canvas.before:
            self.sanction_level_spinner_bg_color = Color(rgba=get_color_from_hex("#FFDD00"))  # GOVUK_YELLOW
            self.sanction_level_spinner_bg_rect = RoundedRectangle(
            pos=self.sanction_level_spinner.pos,
            size=self.sanction_level_spinner.size,
            radius=[20]
            )
        def update_bg_rect_spinner_level(_, __):
            self.sanction_level_spinner_bg_rect.pos = self.sanction_level_spinner.pos
            self.sanction_level_spinner_bg_rect.size = self.sanction_level_spinner.size
        self.sanction_level_spinner.bind(pos=update_bg_rect_spinner_level, size=update_bg_rect_spinner_level)

        layout.add_widget(self.sanction_level_spinner)

        # Spinner for number of sanctioned claimants
        self.sanctioned_claimants_input = Spinner(
            text="Select Sanctioned Claimants",
            values=["1", "2"],
            font_size="16sp",
            font_name="roboto",
            size_hint=(None, None),
            size=(250, 50),
            background_color=(0, 0, 0, 0),  # Transparent background
            background_normal="",  # Remove default background image
            color=get_color_from_hex("#005EA5"),  # GOVUK_BLUE text color
            option_cls=CustomSpinnerOption
        )

        # Add rounded rectangle background to match RoundedButton
        with self.sanctioned_claimants_input.canvas.before:
            self.sanctioned_claimants_input_bg_color = Color(rgba=get_color_from_hex("#FFDD00"))  # GOVUK_YELLOW
            self.sanctioned_claimants_input_bg_rect = RoundedRectangle(
            pos=self.sanctioned_claimants_input.pos,
            size=self.sanctioned_claimants_input.size,
            radius=[20]
            )
        def update_bg_rect_claimants_input(_, __):
            self.sanctioned_claimants_input_bg_rect.pos = self.sanctioned_claimants_input.pos
            self.sanctioned_claimants_input_bg_rect.size = self.sanctioned_claimants_input.size
        self.sanctioned_claimants_input.bind(pos=update_bg_rect_claimants_input, size=update_bg_rect_claimants_input)

        layout.add_widget(self.sanctioned_claimants_input)

        # Hide/show spinner backgrounds based on Yes/No selection
        def update_spinner_bg_visibility(*_):
            show = self.has_sanction_yes.active
            self.sanction_level_spinner_bg_color.a = 1 if show else 0
            self.sanctioned_claimants_input_bg_color.a = 1 if show else 0
            self.sanction_level_spinner.disabled = not show
            self.sanctioned_claimants_input.disabled = not show

        self.has_sanction_yes.bind(active=lambda instance, value: update_spinner_bg_visibility())
        self.has_sanction_no.bind(active=lambda instance, value: update_spinner_bg_visibility())
        # Set initial visibility
        update_spinner_bg_visibility()

        # Days sanction applies
        self.sanction_days_input = CustomTextInput(
            hint_text="Number of days sanctioned",
            multiline=False,
            font_size=16,
            background_color=get_color_from_hex("#00000000"),
            foreground_color=get_color_from_hex(YELLOW),  # Use GOVUK_YELLOW for text color
            size_hint=(None, None),
            size=(250, 40)
            )
        layout.add_widget(self.sanction_days_input)

        # 40% reduction eligibility (exceptions)
        self.sanction_40_checkbox = CheckBox(size_hint=(None, None), size=(30, 30))
        row_40 = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=30)
        row_40.add_widget(self.sanction_40_checkbox)
        row_40.add_widget(Label(
            text="Apply 40% reduction rate",
            font_size=14,
            color=get_color_from_hex(WHITE),
            halign="left",
            valign="middle"
            ))
        layout.add_widget(row_40)

        # Special circumstances (less money taken off)
        self.sanction_special_checkbox = CheckBox(size_hint=(None, None), size=(30, 30))
        row_special = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=30)
        row_special.add_widget(self.sanction_special_checkbox)
        row_special.add_widget(Label(
            text="Special circumstance",
            font_size=14,
            color=get_color_from_hex(WHITE),
            halign="left",
            valign="middle"
            ))
        layout.add_widget(row_special)

        # Function to enable/disable sanction info fields
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
        # Default to "No" selected and fields disabled
        self.has_sanction_no.active = True
        on_has_sanction_checkbox(None, None)

        # Helper function to calculate daily sanction rate
        def get_daily_sanction_rate(level, age, couple, over25, reduction40, standard_allowance):
            if level == "None":
                return 0.0
            if reduction40:
                if couple:
                    rate = (standard_allowance * 0.4) / 30 if standard_allowance else 0
                    return min(rate, (standard_allowance * 0.4) / 30 if standard_allowance else 0)
                else:
                    rate = (standard_allowance * 0.4) / 30 if standard_allowance else 0
                    return min(rate, (standard_allowance * 0.4) / 30 if standard_allowance else 0)
            if couple:
                if over25:
                    rate = 10.30
                else:
                    rate = 8.10
                max_rate = (standard_allowance / 2) / 30 if standard_allowance else rate
                return min(rate, max_rate)
            else:
                if age >= 25:
                    rate = 13.10
                else:
                    rate = 10.40
                max_rate = (standard_allowance) / 30 if standard_allowance else rate
                return min(rate, max_rate)

        # Store sanction info for use in calculation
        self.sanction_summary = {
            "level_spinner": self.sanction_level_spinner,
            "days_input": self.sanction_days_input,
            "claimants_input": self.sanctioned_claimants_input,
            "reduction_40": self.sanction_40_checkbox,
            "special": self.sanction_special_checkbox,
            "get_daily_rate": get_daily_sanction_rate
        }

        scroll.add_widget(layout)
        return scroll

    def create_advance_payments_screen(self):
        # Use a ScrollView to make the advance payments screen vertically scrollable
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
        layout = BoxLayout(orientation="vertical", spacing=20, padding=20, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))  # Let layout expand vertically
        
        # Helper function to create a label that wraps text within the window width
        def wrapped_label(text, font_size, height):
            label = Label(
                text=text,
                font_size=font_size,
                halign="left",
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
        
        # Add a label for advance payment options
        layout.add_widget(wrapped_label(
            "Please select the advance payments that apply to you:",
            16, 30
        ))

        # Add checkboxes for advance payments periods (mutually exclusive)
        self.advance_payments_period_checkboxes = {}
        elements = [
            ("6 Month Advance Payment", "six_month"),
            ("12 Month Advance Payment", "twelve_month"),
            ("24 Month Advance Payment", "twenty_four_month"),
        ]
        # Use a group name to make checkboxes mutually exclusive
        group_name = "advance_payment_period"
        for label_text, key in elements:
            row = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=40)
            cb = CheckBox(size_hint=(None, None), size=(30, 30), group=group_name)
            row.add_widget(cb)
            # Add a little spacing between checkbox and label
            row.add_widget(Label(size_hint_x=None, width=10))
            element_label = wrapped_label(label_text, 16, 30)
            element_label.size_hint_x = 1
            row.add_widget(element_label)
            layout.add_widget(row)
            self.advance_payments_period_checkboxes[key] = cb

        # Advance payments input field
        self.advance_payments_input = CustomTextInput(
            hint_text="Enter payments received (£)",
            multiline=False,
            font_size=18,
            background_color=get_color_from_hex("#00000000"),
            foreground_color=get_color_from_hex(YELLOW),  # Use GOVUK_YELLOW for text color
            size_hint=(None, None),
            size=(250, 40)
        )
        layout.add_widget(self.advance_payments_input)

        # Add a label for advance payments delays
        layout.add_widget(wrapped_label(
            "Please select any advance payment delays that apply to you:",
            16, 30
        ))

        # Add checkboxes for advance payment delays (mutually exclusive)
        self.advance_payments_delay_checkboxes = {}
        delay_elements = [
            ("1 Month Delay", "one_month"),
            ("3 Month Delay", "three_month")
        ]
        # Use a group name to make checkboxes mutually exclusive
        group_name = "advance_payment_delay"
        for label_text, key in delay_elements:
            row = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=40)
            cb = CheckBox(size_hint=(None, None), size=(30, 30), group=group_name)
            row.add_widget(cb)
            # Add a little spacing between checkbox and label
            row.add_widget(Label(size_hint_x=None, width=10))
            element_label = wrapped_label(label_text, 16, 30)
            element_label.size_hint_x = 1
            row.add_widget(element_label)
            layout.add_widget(row)
            self.advance_payments_delay_checkboxes[key] = cb
        
        scroll.add_widget(layout)
        return scroll
            
    def create_calculate_screen(self):
        layout = BoxLayout(orientation="vertical", spacing=10, padding=20)

        # Make the summary scrollable
        summary_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
        summary_layout = BoxLayout(orientation="vertical", spacing=20, padding=10, size_hint_y=None)  # Increased spacing from 10 to 20
        summary_layout.bind(minimum_height=summary_layout.setter('height'))

        # Add a title for the summary
        summary_title = Label(text="Summary:", font_size=20, halign="center", color=get_color_from_hex(WHITE), size_hint_y=None, height=30)
        summary_layout.add_widget(summary_title)

        # Create labels for the summary
        self.claimant_summary = Label(font_size=14, halign="left", color=get_color_from_hex(WHITE), size_hint_y=None)
        self.partner_summary = Label(font_size=14, halign="left", color=get_color_from_hex(WHITE), size_hint_y=None)
        self.finances_summary = Label(font_size=14, halign="left", color=get_color_from_hex(WHITE), size_hint_y=None)
        self.housing_summary = Label(font_size=14, halign="left", color=get_color_from_hex(WHITE), size_hint_y=None)
        self.children_summary = Label(font_size=14, halign="left", color=get_color_from_hex(WHITE), size_hint_y=None)
        self.additional_elements_summary = Label(font_size=14, halign="left", color=get_color_from_hex(WHITE), size_hint_y=None)
        self.sanction_summary = Label(font_size=14, halign="left", color=get_color_from_hex(WHITE), size_hint_y=None)
        self.advance_payment_summary = Label(font_size=14, halign="left", color=get_color_from_hex(WHITE), size_hint_y=None)

        # Add the labels to the layout
        summary_layout.add_widget(self.claimant_summary)
        summary_layout.add_widget(self.partner_summary)
        summary_layout.add_widget(self.finances_summary)
        summary_layout.add_widget(self.housing_summary)
        summary_layout.add_widget(self.children_summary)
        summary_layout.add_widget(self.additional_elements_summary)
        summary_layout.add_widget(self.sanction_summary)
        summary_layout.add_widget(self.advance_payment_summary)

        # Update the summary whenever the inputs change
        def update_summary():
            self.claimant_summary.text = (
                f"Claimant Details:\n"
                f"Name: {self.name_input.text}\n"
                f"Date of Birth: {self.dob_input.text}\n"
            )
            self.claimant_summary.texture_update()
            self.claimant_summary.height = self.claimant_summary.texture_size[1] + 10

            self.partner_summary.text = (
                f"Partner Details:\n"
                f"Name: {self.partner_name_input.text}\n"
                f"Date of Birth: {self.partner_dob_input.text}\n"
            ) if self.couple_claim_checkbox.active else "Partner Details: N/A"
            self.partner_summary.texture_update()
            self.partner_summary.height = self.partner_summary.texture_size[1] + 10

            self.finances_summary.text = (
                f"Income: £{self.income_input.text}\n"
                f"capital: £{self.capital_input.text}\n"
            )
            self.finances_summary.texture_update()
            self.finances_summary.height = self.finances_summary.texture_size[1] + 10

            rent_or_mortgage = ""
            if hasattr(self, "housing_type_spinner") and self.housing_type_spinner.text.lower() == "rent":
                if hasattr(self, "rent_mortgage_input"):
                    rent_or_mortgage = f"Rent Amount: £{self.rent_mortgage_input.text}\n"
            elif hasattr(self, "housing_type_spinner") and self.housing_type_spinner.text.lower() == "own":
                if hasattr(self, "mortgage_input"):
                    rent_or_mortgage = f"Mortgage Amount: £{self.mortgage_input.text}\n"

            self.housing_summary.text = (
                f"Housing Type: {self.housing_type_spinner.text}\n"
                f"Location: {self.location_spinner.text}\n"
                f"BRMA: {self.brma_spinner.text}\n"
                f"{rent_or_mortgage}"
            )
            self.housing_summary.texture_update()
            self.housing_summary.height = self.housing_summary.texture_size[1] + 10

            # Children details
            if hasattr(self, "has_children_yes") and self.has_children_yes.active and hasattr(self, "child_name_inputs"):
                children_details = []
                for i, (name_input, dob_input, special_flags) in enumerate(
                    zip(self.child_name_inputs, self.child_dob_inputs, self.child_special_flags)
                ):
                    name = name_input.text
                    dob = dob_input.text
                    # Collect special circumstances for this child
                    special_list = []
                    if special_flags.get("disabled") and special_flags["disabled"].active:
                        special_list.append("Disabled")
                    if special_flags.get("multiple_birth") and special_flags["multiple_birth"].active:
                        special_list.append("Multiple Birth")
                    if special_flags.get("adopted") and special_flags["adopted"].active:
                        special_list.append("Adopted")
                    if special_flags.get("formal_care") and special_flags["formal_care"].active:
                        special_list.append("Formal Care")
                    if special_flags.get("informal_care") and special_flags["informal_care"].active:
                        special_list.append("Informal Care")
                    if special_flags.get("rape_or_control") and special_flags["rape_or_control"].active:
                        special_list.append("Rape/Control")
                    if special_flags.get("teen_parent") and special_flags["teen_parent"].active:
                        special_list.append("Teen Parent")
                    # Add indentation for special circumstances
                    special_str = "\n        - " + "\n        - ".join(special_list) if special_list else "None"
                    children_details.append(
                        f"    Name: {name}\n    DOB: {dob}\n    Special Circumstances:{special_str}\n"
                    )
                # Join each child's details with a blank line for vertical stacking
                self.children_summary.text = "Children:\n" + ("\n\n".join(children_details) if children_details else "No children entered.")
            else:
                self.children_summary.text = "Children: N/A"
            self.children_summary.halign = "left"
            self.children_summary.text_size = (Window.width - 60, None)
            self.children_summary.padding_x = 20  # Add left padding so text is not cut off
            self.children_summary.texture_update()
            self.children_summary.height = self.children_summary.texture_size[1] + 10

            # Additional elements summary
            selected_elements = []
            if hasattr(self, "additional_elements_checkboxes"):
                for label, cb in self.additional_elements_checkboxes.items():
                    if cb.active:
                        # Use a more readable label for the summary
                        if label == "carer":
                            selected_elements.append("Carer Element")
                        elif label == "lcw":
                            selected_elements.append("Limited Capability for Work (LCW)")
                        elif label == "lcwra":
                            selected_elements.append("Limited Capability for Work and Work-Related Activity (LCWRA)")
                        elif label == "childcare":
                            selected_elements.append("Childcare Costs Element")
            # Format the selected elements as bullet points
            if selected_elements:
                additional_text = "\n".join(f"• {el}" for el in selected_elements)
            else:
                additional_text = "None"
            self.additional_elements_summary.halign = "left"
            self.additional_elements_summary.text_size = (Window.width - 60, None)
            self.additional_elements_summary.padding_x = 20  # Add left padding so text is not cut off
            self.additional_elements_summary.text = f"Additional Elements:\n{additional_text}\n"
            self.additional_elements_summary.texture_update()
            self.additional_elements_summary.height = self.additional_elements_summary.texture_size[1] + 10
            
            # Sanction info summary
            if hasattr(self, "has_sanction_yes") and self.has_sanction_yes.active:
                sanction_level = self.sanction_level_spinner.text
                if sanction_level == "Select Sanction Level":
                    sanction_level = "None"
                days = self.sanction_days_input.text.strip()
                if not days.isdigit():
                    days = "0"
                claimants = self.sanctioned_claimants_input.text.strip()
                if claimants == "Select Sanctioned Claimants":
                    claimants = "1"
                if not claimants.isdigit():
                    claimants = "1"
                reduction_40 = "Yes" if self.sanction_40_checkbox.active else "No"
                special = "Yes" if self.sanction_special_checkbox.active else "No"

                # Calculate daily sanction rate using the same logic as in create_sanction_screen
                daily_rate = ""
                total_sanction = ""
                try:
                    dob_str = self.dob_input.text.strip() if hasattr(self, "dob_input") and self.dob_input.text else ""
                    age = None
                    if dob_str:
                        try:
                            dob = datetime.strptime(dob_str, "%d/%m/%Y")
                            age = (datetime.now() - dob).days // 365
                        except Exception:
                            age = None
                    couple = self.couple_claim_checkbox.active if hasattr(self, "couple_claim_checkbox") else False
                    over25 = age is not None and age >= 25
                    # Standard allowance for sanction calculation
                    standard_allowance = 0
                    if couple:
                        partner_age = None
                        if hasattr(self, "partner_dob_input") and self.partner_dob_input.text.strip():
                            try:
                                partner_dob = datetime.strptime(self.partner_dob_input.text.strip(), "%d/%m/%Y")
                                partner_age = (datetime.now() - partner_dob).days // 365
                            except Exception:
                                partner_age = None
                        if age is not None and partner_age is not None:
                            if age < 25 and partner_age < 25:
                                standard_allowance = 497.55
                            else:
                                standard_allowance = 628.10
                    else:
                        if age is not None:
                            standard_allowance = 316.98 if age < 25 else 400.14

                    reduction_40_active = self.sanction_summary["reduction_40"].active
                    if (
                        sanction_level != "Select Sanction Level"
                        and sanction_level != "None"
                        and days.isdigit()
                        and claimants.isdigit()
                        and age is not None
                    ):
                        daily_rate_val = self.sanction_summary["get_daily_rate"](
                            sanction_level, age, couple, over25, reduction_40_active, standard_allowance
                        )
                        daily_rate = f"£{daily_rate_val:.2f}"
                        total_days = int(days)
                        total_claimants = int(claimants)
                        total_sanction_val = daily_rate_val * total_days * total_claimants
                        total_sanction = f"£{total_sanction_val:.2f}"
                    elif sanction_level == "None":
                        daily_rate = "£0.00"
                        total_sanction = "£0.00"
                    else:
                        daily_rate = "N/A"
                        total_sanction = "N/A"
                except Exception:
                    daily_rate = "N/A"
                    total_sanction = "N/A"

                self.sanction_summary.text = (
                    f"Sanction Level: {sanction_level}\n"
                    f"Days Sanction Applies: {days}\n"
                    f"Number of Sanctioned Claimants: {claimants}\n"
                    f"40% Reduction Rate: {reduction_40}\n"
                    f"Special Circumstances: {special}\n"
                    f"Daily Sanction Rate: {daily_rate}\n"
                    f"Total Sanction Deduction: {total_sanction}\n"
                )
            else:
                self.sanction_summary.text = "Sanctions: None"

            # Advance payments summary
            if hasattr(self, "advance_payments_input"):
                advance_payments = self.advance_payments_input.text.strip()
                if not advance_payments.isdigit():
                    advance_payments = "0"
                advance_payments = f"£{float(advance_payments):.2f}" if advance_payments else "N/A"

                selected_periods = [label for label, cb in self.advance_payments_period_checkboxes.items() if cb.active]
                selected_delays = [label for label, cb in self.advance_payments_delay_checkboxes.items() if cb.active]

                periods_text = ", ".join(selected_periods) if selected_periods else "None"
                delays_text = ", ".join(selected_delays) if selected_delays else "None"

                self.advance_payment_summary.text = (
                    f"Advance Payments Received: {advance_payments}\n"
                    f"Selected Advance Payment Periods: {periods_text}\n"
                    f"Selected Advance Payment Delays: {delays_text}\n"
                )
            else:
                self.advance_payment_summary.text = "Advance Payments: N/A"
                
                
        # Bind updates to relevant inputs
        self.couple_claim_checkbox.bind(active=update_summary)
        self.partner_name_input.bind(text=update_summary)
        self.partner_dob_input.bind(text=update_summary)
        self.dob_input.bind(text=update_summary)
        self.income_input.bind(text=update_summary)
        self.capital_input.bind(text=update_summary)
        self.housing_type_spinner.bind(text=update_summary)
        self.location_spinner.bind(text=update_summary)
        self.brma_spinner.bind(text=update_summary)
        if hasattr(self, "has_children_yes"):
            self.has_children_yes.bind(active=update_summary)
        if hasattr(self, "child_name_inputs"):
            for name_input in self.child_name_inputs:
                name_input.bind(text=update_summary)
        def adjust_font_size(instance):
            for label in [self.claimant_summary, self.partner_summary, self.finances_summary, self.housing_summary, self.children_summary, self.additional_elements_summary, summary_title]:
                label.font_size = max(14, min(20, instance.width / 50))
        if hasattr(self, "additional_element_input"):
            Window.bind(size=lambda instance, value: adjust_font_size(instance))

        # Call update_summary initially to populate the summary
        update_summary()

        # Adjust font size dynamically based on window size
        def adjust_font_size(instance, value):
            for label in [self.claimant_summary, self.partner_summary, self.finances_summary, self.housing_summary, self.children_summary, self.additional_elements_summary, summary_title]:
                label.font_size = max(14, min(20, instance.width / 50))

        # Bind the window size to adjust font sizes dynamically
        Window.bind(size=adjust_font_size)

        # Add a button to confirm and submit
        calculate_button = RoundedButton(
            text="Calculate",
            size_hint=(None, None),
            size=(250, 50),
            font_size="20sp",
            font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            background_color=(0, 0, 0, 0),  # Transparent background
            background_normal="",  # Remove default background image
            on_press=self.calculate
        )
        calculate_button.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        summary_layout.add_widget(calculate_button)

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











