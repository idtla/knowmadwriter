"""
Middlewares para el bot de Telegram.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

# Configuración de logging
logger = logging.getLogger(__name__)

# En python-telegram-bot 20.x no hay un sistema directo de middlewares
# como existía en versiones anteriores. En su lugar, se pueden usar 
# los event handlers o crear handlers personalizados.

async def user_access_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Verificar el acceso de usuarios.
    Esta función puede usarse como un handler para verificar acceso.
    """
    if not update.effective_user:
        return

    user_id = update.effective_user.id

    # Lista de comandos públicos que no requieren verificación
    public_commands = ["/start", "/help", "/register"]

    # Verificar si es un comando público
    if update.message and update.message.text:
        command = update.message.text.split()[0].lower()
        if command in public_commands:
            logger.debug(f"Usuario {user_id} usa comando público: {command}")
            return True
    
    # Aquí implementaremos la verificación de acceso
    # Consultando la base de datos para comprobar si el usuario está registrado
    # Por ahora, solo registramos el acceso
    logger.info(f"Verificando acceso para usuario {user_id}")
    
    # De momento, permitir todos los accesos
    return True

def setup_middlewares(application):
    """
    Configurar middlewares para la aplicación.
    En python-telegram-bot 20.x, esto se hace de manera diferente.
    """
    # En esta versión, simplemente registramos que la función fue llamada
    logger.info("Configuración de middlewares: los middlewares tradicionales no están disponibles en python-telegram-bot 20.x")
    
    # En lugar de middlewares, se pueden usar los handlers y event handlers
    # application.add_handler(...)
    
    logger.info("Middlewares configurados correctamente (simulado)") 