import os
import sys
import platform
import subprocess
from kivy.logger import Logger
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.core.window import Window

# Import your main app
import benefit_calculator


class SplashScreen(App):
    """Animated splash screen before loading main app."""

    def build(self):
        Window.clearcolor = (1, 1, 1, 1)  # White background

        layout = BoxLayout(orientation='vertical', spacing=20, padding=40)

        # ✅ App logo
        logo_path = os.path.join(os.path.dirname(__file__), "images", "logo.png")
        if not os.path.exists(logo_path):
            Logger.warning("BenefitBuddy: logo.png not found, skipping image.")
        else:
            logo = Image(source=logo_path, size_hint=(1, 0.6))
            layout.add_widget(logo)

        # ✅ App name
        self.label = Label(
            text="Benefit Buddy",
            font_size="28sp",
            bold=True,
            color=(0.1, 0.2, 0.6, 1),  # GOV blue-ish
            size_hint=(1, 0.2)
        )
        layout.add_widget(self.label)

        # ✅ Subtext
        self.sub = Label(
            text="Calculating your benefits...",
            font_size="18sp",
            color=(0, 0, 0, 0.7),
            size_hint=(1, 0.2)
        )
        layout.add_widget(self.sub)

        # ✅ Animate fade-in for the text
        anim = Animation(color=(0.1, 0.2, 0.6, 1), duration=1.2) + Animation(color=(0.4, 0.4, 0.8, 1), duration=1.2)
        anim.repeat = True
        anim.start(self.label)

        # ✅ After 2.5 seconds, start the real app
        Clock.schedule_once(self.start_main_app, 2.5)
        return layout

    def start_main_app(self, *args):
        Logger.info("BenefitBuddy: Splash done, launching main app.")
        self.stop()  # stop splash
        benefit_calculator.BenefitBuddy().run()


def open_benefit_calculator():
    """Main entry point: splash then launch calculator."""

    is_android = hasattr(sys, 'getandroidapilevel')

    if is_android:
        Logger.info("BenefitBuddy: Launching on Android with splash.")
        SplashScreen().run()
        return

    # For desktop testing
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    script_path = os.path.join(base_path, 'benefit_calculator.py')

    if not os.path.isfile(script_path):
        Logger.error("BenefitBuddy: benefit_calculator.py not found.")
        print("Error: benefit_calculator.py not found.")
        return

    try:
        system = platform.system()
        Logger.info(f"BenefitBuddy: Launching calculator on {system}")

        if system == "Windows":
            subprocess.Popen(["start", "python", script_path], shell=True)
        elif system in ["Linux", "Darwin"]:
            subprocess.Popen(["python3", script_path])
        else:
            subprocess.Popen([sys.executable, script_path])
    except Exception as e:
        Logger.exception(f"BenefitBuddy: Failed to launch calculator — {e}")
        print(f"An error occurred while launching the calculator: {e}")


if __name__ == "__main__":
    Logger.info("BenefitBuddy: Starting with splash.")
    open_benefit_calculator()

