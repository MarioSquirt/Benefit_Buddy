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
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget

# Import your main app (must define BenefitBuddy class)
import benefit_calculator


class SplashScreen(App):
    """Animated GOV-themed splash screen before loading main app."""

    def build(self):
        # GOV Blue background
        Window.clearcolor = (29/255, 112/255, 184/255, 1)

        layout = BoxLayout(orientation='vertical', spacing=15, padding=60)

        # ✅ App logo
        logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
        if os.path.exists(logo_path):
            logo = Image(source=logo_path, size_hint=(1, 0.5))
            layout.add_widget(logo)
        else:
            Logger.warning("BenefitBuddy: logo.png not found, skipping image.")

        # ✅ App name
        self.label = Label(
            text="Benefit Buddy",
            font_size="32sp",
            bold=True,
            color=(1, 1, 1, 1),  # White text
            size_hint=(1, 0.2)
        )
        layout.add_widget(self.label)

        # ✅ Animated subtext
        self.sub = Label(
            text="Checking benefit entitlements...",
            font_size="18sp",
            color=(1, 1, 1, 0.8),
            size_hint=(1, 0.15)
        )
        layout.add_widget(self.sub)

        # ✅ Simple spinner imitation (pulsing GOV yellow dot)
        self.dot = Label(
            text="●",
            font_size="36sp",
            color=(1, 221/255, 0, 0.0),  # GOV yellow but start transparent
            size_hint=(1, 0.15)
        )
        layout.add_widget(self.dot)

        # Animate pulsing yellow dot
        anim = Animation(color=(1, 221/255, 0, 1), duration=0.6) + Animation(color=(1, 221/255, 0, 0.1), duration=0.6)
        anim.repeat = True
        anim.start(self.dot)

        # Animate fade pulse on the title too
        title_anim = Animation(color=(1, 1, 1, 0.7), duration=1.2) + Animation(color=(1, 1, 1, 1), duration=1.2)
        title_anim.repeat = True
        title_anim.start(self.label)

        # ✅ After 3 seconds, start the real app
        Clock.schedule_once(self.start_main_app, 3)
        return layout

    def start_main_app(self, *args):
        Logger.info("BenefitBuddy: Splash done, launching main app.")
        self.stop()
        benefit_calculator.BenefitBuddy().run()


def open_benefit_calculator():
    """Main entry point: splash then launch calculator."""

    is_android = hasattr(sys, 'getandroidapilevel')

    if is_android:
        Logger.info("BenefitBuddy: Launching on Android with GOV splash.")
        SplashScreen().run()
        return

    # Desktop fallback
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
    Logger.info("BenefitBuddy: Starting with GOV splash.")
    open_benefit_calculator()
