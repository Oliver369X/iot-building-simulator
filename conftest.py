import sys
from pathlib import Path

# Añadir el directorio src al PYTHONPATH
src_path = str(Path(__file__).parent)
if src_path not in sys.path:
    sys.path.insert(0, src_path) 