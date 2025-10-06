#main.py

import subprocess
import sys
import os

def open_benefit_calculator():
    script_path = os.path.join(os.path.dirname(__file__), 'benefit_calculator.py')
    if not os.path.isfile(script_path):
        print("benefit_calculator.py not found.")
        return
    subprocess.run([sys.executable, script_path])

if __name__ == "__main__":

    open_benefit_calculator()
