"""Space Wars - punto de entrada.

Ejecutar:  python main.py
"""
import os
import sys

# Permite ejecutar desde cualquier carpeta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from controller.app import App  # noqa: E402

if __name__ == "__main__":
    App().run()
