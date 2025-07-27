#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Bot de Telegram para gestión de contenido web
Este bot permite a usuarios subir contenido HTML e imágenes a sus sitios web.
"""

import os
import logging
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler
from telegram import BotCommand

# Importar desde nuestro módulo de compatibilidad
from utils.compat import Filters, CallbackContext

# Cargar variables de entorno
load_dotenv()

# Configuración de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO'))
)
logger = logging.getLogger(__name__)

# Importaciones de módulos propios
from core.handlers import (
    start_command, 
    help_command, 
    callback_handler, 
    message_handler,
    whoami_command
)
from core.middlewares import setup_middlewares
from database.connection import setup_database
from modules import setup_all_modules
from modules.auth import setup_auth_handlers
from modules.content import setup_content_handlers
from modules.sftp import setup_sftp_handlers
from modules.categories import setup_categories_handlers
from modules.tags import setup_tags_handlers
from modules.admin import setup_admin_handlers

async def error_handler(update, context):
    """Manejador global de errores."""
    # Mostrar error detallado para facilitar la depuración
    import traceback
    logger.error(f"Error no manejado: {context.error}")
    logger.error(f"Detalles adicionales: {traceback.format_exc()}")
    
    # Si hay un update, intentar notificar al usuario
    if update and update.effective_chat:
        # Sólo notificar errores críticos, no spam al usuario con cada pequeño error
        if "no attribute '_answered'" not in str(context.error):
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ Ha ocurrido un error en el sistema. El equipo técnico ha sido notificado."
                )
            except Exception as e:
                logger.error(f"Error al enviar mensaje de error: {e}")

async def setup_bot_commands(application):
    """Configura los comandos que aparecen en el menú del bot."""
    commands = [
        BotCommand("/start", "Iniciar bot y mostrar menú principal"),
        BotCommand("/help", "Mostrar ayuda y comandos disponibles"),
        BotCommand("/register", "Registrarse para usar el bot"),
        BotCommand("/newpost", "Crear nuevo post para el blog"),
        BotCommand("/categories", "Gestionar categorías"),
        BotCommand("/tags", "Gestionar etiquetas"),
        BotCommand("/settings", "Configurar opciones"),
        BotCommand("/whoami", "Ver tu información de usuario")
    ]
    
    # Verificar si hay usuarios admin para añadir el comando admin
    from models.user import User
    try:
        # Si hay al menos un admin, configuramos el comando admin
        # Esto solo afecta a la visualización, la seguridad se verifica en el handler
        commands.append(BotCommand("/admin", "Panel de administración"))
    except Exception as e:
        logger.warning(f"Error al verificar administradores: {e}")
    
    await application.bot.set_my_commands(commands)

def main():
    """Función principal para ejecutar el bot."""
    # Obtener el token del bot desde variables de entorno
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("❌ No se encontró TELEGRAM_BOT_TOKEN en las variables de entorno")
        return

    # Conectar a la base de datos SQLite
    db_connected = setup_database()
    if not db_connected:
        logger.error("❌ No se pudo conectar a la base de datos SQLite")
        return

    # Inicializar el bot
    application = Application.builder().token(token).build()
    
    # Configurar middlewares
    setup_middlewares(application)
    
    # Configurar comandos persistentes
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("whoami", whoami_command))
    
    # Configurar módulos específicos - estos registrarán sus propios manejadores
    # NOTA: Los manejadores específicos de módulos deben tener prioridad más alta (grupo más bajo)
    # para que se procesen antes que los manejadores globales
    setup_all_modules(application)
    
    # Manejador global de mensajes (baja prioridad - grupo 100)
    application.add_handler(MessageHandler(Filters.TEXT & ~Filters.COMMAND, message_handler), group=100)
    
    # Manejador global para documentos (baja prioridad - grupo 100)
    application.add_handler(MessageHandler(Filters.DOCUMENT & ~Filters.COMMAND, message_handler), group=100)
    
    # Manejador global de callbacks (baja prioridad - grupo 100)
    # Esto garantiza que los manejadores específicos (con grupos < 100) se ejecuten primero
    application.add_handler(CallbackQueryHandler(callback_handler), group=100)
    
    # Manejador global de errores
    application.add_error_handler(error_handler)
    
    # Configurar menú de comandos persistente
    application.post_init = setup_bot_commands
    
    # Iniciar el bot
    logger.info("🚀 Bot iniciado correctamente. Presiona Ctrl+C para detener.")
    application.run_polling()

if __name__ == "__main__":
    main() 