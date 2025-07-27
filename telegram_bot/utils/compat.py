"""
Archivo de compatibilidad para versiones más recientes de python-telegram-bot.
Este archivo facilita la migración de código antiguo a la versión 20.x.
"""

from telegram.ext import filters

# Crear una clase que simule el comportamiento de Filters de versiones anteriores
class FiltersCompat:
    """Clase de compatibilidad para Filters."""
    # Definir atributos para acceso sencillo
    TEXT = filters.TEXT  # Filtro para mensajes de texto
    COMMAND = filters.COMMAND  # Filtro para comandos
    PHOTO = filters.PHOTO  # Filtro para fotos
    # En ptb 20.x, DOCUMENT es una clase, no una constante
    DOCUMENT = filters.Document.ALL  # Filtro para documentos
    
    # Para retrocompatibilidad con nombres en minúscula
    text = filters.TEXT
    command = filters.COMMAND
    photo = filters.PHOTO
    document = filters.Document.ALL
    
    # Para permitir el acceso dinámico a los atributos
    def __getattr__(self, name):
        try:
            # Intentar obtener el atributo directamente
            return getattr(filters, name)
        except AttributeError:
            # Si falla, intentar con otras variantes del nombre
            if name.upper() in dir(filters):
                return getattr(filters, name.upper())
            elif name.lower() in dir(filters):
                return getattr(filters, name.lower())
            elif name.capitalize() in dir(filters):
                return getattr(filters, name.capitalize())
            else:
                raise AttributeError(f"Filters no tiene atributo '{name}'")

# Crear una instancia de FiltersCompat
Filters = FiltersCompat()

from telegram.ext import ContextTypes
# Mantener compatibilidad con CallbackContext
CallbackContext = ContextTypes.DEFAULT_TYPE

# Para ParseMode
from telegram.constants import ParseMode 

# Función de utilidad para depuración
def debug_print(message):
    """Imprime un mensaje de depuración."""
    print(f"[DEBUG] {message}") 