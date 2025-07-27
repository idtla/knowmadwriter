"""
Módulos funcionales del bot de Telegram.
"""

from .auth import setup_auth_handlers
from .content import setup_content_handlers
from .sftp import setup_sftp_handlers
from .categories import setup_categories_handlers
from .tags import setup_tags_handlers
from .admin import setup_admin_handlers

def setup_all_modules(application):
    """Configura todos los módulos disponibles para la aplicación."""
    
    # Configurar módulo de autenticación
    setup_auth_handlers(application)
    
    # Configurar módulo de contenido
    setup_content_handlers(application)
    
    # Configurar módulo SFTP
    setup_sftp_handlers(application)
    
    # Configurar módulo de categorías
    setup_categories_handlers(application)
    
    # Configurar módulo de etiquetas
    setup_tags_handlers(application)
    
    # Configurar módulo de administración
    setup_admin_handlers(application)
    
    # Aquí se añadirán más módulos a medida que se implementen
    # Ejemplo:
    # etc.
    
    return application 