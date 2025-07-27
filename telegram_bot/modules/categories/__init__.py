"""
Módulo para la gestión de categorías del sitio.
"""

# Asegurarse de que el módulo utils esté en el path
import sys
import os
from pathlib import Path

# Añadir el directorio raíz al path para importar utils
root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

from .handlers import setup_categories_handlers

__all__ = ['setup_categories_handlers'] 