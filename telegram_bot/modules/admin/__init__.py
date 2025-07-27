"""
Módulo de administración para el bot de Telegram.

Este módulo proporciona funcionalidades administrativas como:
- Gestión de usuarios (listar, bloquear, promover)
- Estadísticas del sistema
- Configuración global
"""

from .handlers import setup_admin_handlers

__all__ = ['setup_admin_handlers'] 