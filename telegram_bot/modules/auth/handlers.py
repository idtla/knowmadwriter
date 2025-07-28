"""
Manejadores para la autenticación y el registro de usuarios.
"""

import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler
from telegram.constants import ParseMode

# Importar desde nuestro módulo de compatibilidad
from utils.compat import Filters, CallbackContext

from utils.breadcrumbs import breadcrumb
# Configuración de logging
logger = logging.getLogger(__name__)

# Importar modelos y estados
from models.user import User
from core.states import State, state_manager

@breadcrumb
async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador para el comando /register."""
    user = update.effective_user
    chat_id = update.effective_chat.id

    logger.info(f"Usuario {user.id} inició el proceso de registro")

    # Verificar si el usuario ya está registrado
    existing_user = User.get_by_telegram_id(user.id)
    
    if existing_user:
        logger.info(f"Usuario {user.id} encontrado en la base de datos con estado: {existing_user.status}")
        
    if existing_user and existing_user.is_active():
        # En lugar de solo informar, mostrar el menú principal
        from core.handlers import send_main_menu
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"Ya estás registrado en el sistema como {existing_user.name} ({existing_user.email}). Accediendo al menú principal."
        )
        await send_main_menu(update, context)
        return

    # Cambiar el estado a REGISTERING
    state_manager.set_state(user.id, State.REGISTERING)
    
    # Marcar que el logo ya fue enviado para evitar enviarlo nuevamente en otros mensajes
    state_manager.set_data(user.id, "logo_sent", True)

    # NO enviamos el logo en el proceso de registro
    # El logo ya se muestra en el mensaje de bienvenida

    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            f"👤 <b>Registro de Usuario</b>\n\n"
            f"Bienvenido al proceso de registro, {user.first_name}.\n\n"
            f"Para continuar, necesito tu código de autorización. "
            f"Este código debería haberte sido proporcionado por el administrador del bot.\n\n"
            f"Por favor, envíame el código a continuación."
        ),
        parse_mode=ParseMode.HTML
    )

    # Guardamos el paso actual en el estado
    state_manager.set_data(user.id, "register_step", "waiting_auth_code")

@breadcrumb
async def process_auth_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa el código de autorización enviado por el usuario."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    auth_code = update.message.text.strip()

    logger.info(f"Usuario {user.id} envió código de autorización: {auth_code}")

    # Verificar el código en la base de datos
    # Por ahora, aceptamos "12345678" como código válido para pruebas
    valid_codes = ["12345678", "87654321", "11223344"]
    if auth_code in valid_codes:
        # Guardar el código de autorización en el estado (no borramos otros datos aquí)
        state_manager.set_data(user.id, "auth_code", auth_code)
        
        # Código válido, continuar con el registro
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "✅ Código de autorización válido.\n\n"
                "Ahora necesito algunos datos para completar tu registro.\n\n"
                "Por favor, introduce tu nombre completo:"
            )
        )

        # Actualizar el paso actual en el estado
        state_manager.set_data(user.id, "register_step", "waiting_name")
    else:
        # Código inválido
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "❌ El código de autorización no es válido.\n\n"
                "Por favor, verifica e intenta nuevamente, o contacta al administrador."
            )
        )

@breadcrumb
async def process_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa el nombre enviado por el usuario."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    name = update.message.text.strip()

    # Evitar confundir el código de autorización con el nombre
    auth_code = state_manager.get_data(user.id, "auth_code", "")
    if name == auth_code:
        # Si el nombre es igual al código de autorización, es probable que sea un error
        # Es posible que el sistema haya recibido el mismo mensaje dos veces
        logger.warning(f"Usuario {user.id} envió un nombre igual al código de autorización")
        await context.bot.send_message(
            chat_id=chat_id,
            text="Por favor, introduce tu nombre:"
        )
        return

    logger.info(f"Usuario {user.id} envió nombre: {name}")

    # Validar el nombre
    if len(name) < 3:
        await context.bot.send_message(
            chat_id=chat_id,
            text="El nombre es demasiado corto. Por favor, introduce tu nombre:"
        )
        return

    # Guardar el nombre en el estado
    state_manager.set_data(user.id, "name", name)

    # Solicitar el email
    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            f"Gracias, {name}.\n\n"
            f"Ahora necesito tu dirección de email:"
        )
    )

    # Actualizar el paso actual en el estado
    state_manager.set_data(user.id, "register_step", "waiting_email")

@breadcrumb
async def process_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa el email enviado por el usuario."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    email = update.message.text.strip()

    logger.info(f"Usuario {user.id} envió email: {email}")

    # Validar el email
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        await context.bot.send_message(
            chat_id=chat_id,
            text="El email no es válido. Por favor, introduce una dirección de email válida:"
        )
        return

    # Verificar si el email ya está registrado
    existing_user = User.get_by_email(email)
    if existing_user:
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "❌ Este email ya está registrado en el sistema.\n\n"
                "Por favor, utiliza otro email o contacta al administrador."
            )
        )
        return

    # Guardar el email en el estado
    state_manager.set_data(user.id, "email", email)

    # Obtener los datos guardados
    user_data = state_manager.get_conversation(user.id).data
    name = user_data.get("name", "")

    # Mostrar resumen y solicitar confirmación
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirmar", callback_data="register:confirm"),
            InlineKeyboardButton("❌ Cancelar", callback_data="register:cancel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            f"<b>Resumen de Registro</b>\n\n"
            f"Nombre: {name}\n"
            f"Email: {email}\n"
            f"ID de Telegram: {user.id}\n\n"
            f"¿Confirmas estos datos?"
        ),
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

    # Actualizar el paso actual en el estado
    state_manager.set_data(user.id, "register_step", "waiting_confirmation")

@breadcrumb
async def register_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa los callbacks del proceso de registro."""
    query = update.callback_query
    user = update.effective_user
    chat_id = update.effective_chat.id

    await query.answer()

    # Formato esperado: register:acción
    callback_data = query.data.split(':')
    action = callback_data[1] if len(callback_data) > 1 else ""

    logger.info(f"Usuario {user.id} seleccionó {action} en el registro")

    if action == "confirm":
        # Obtener los datos guardados
        user_data = state_manager.get_conversation(user.id).data
        name = user_data.get("name", "")
        email = user_data.get("email", "")

        logger.info(f"Datos de registro para usuario {user.id}: nombre={name}, email={email}")

        # Verificar si el usuario ya existe
        existing_user = User.get_by_telegram_id(user.id)
        if existing_user:
            # Si ya existe, actualizarlo
            existing_user.name = name
            existing_user.email = email
            existing_user.status = "active"
            success = existing_user.save()
            logger.info(f"Usuario existente {user.id} actualizado con estado='active'")
        else:
            # Crear el usuario en la base de datos
            new_user = User(
                telegram_id=user.id,
                name=name,
                email=email,
                status="active",
                role="user"
            )
            success = new_user.save()
            logger.info(f"Nuevo usuario {user.id} creado con estado='active'")

        if success:
            # Limpiar el estado
            state_manager.set_state(user.id, State.IDLE)
            
            # Verificar que el usuario se registró correctamente
            db_user = User.get_by_telegram_id(user.id)
            
            if db_user and db_user.is_active():
                logger.info(f"Usuario {user.id} verificado en la base de datos como activo: estado={db_user.status}")
                
                # Mensaje de confirmación
                await query.edit_message_text(
                    text=(
                        "✅ <b>¡Registro Completado!</b>\n\n"
                        f"Bienvenido, {name}. Tu cuenta ha sido creada correctamente."
                    ),
                    parse_mode=ParseMode.HTML
                )
                
                # Esperar un segundo para que el usuario pueda leer el mensaje
                import asyncio
                await asyncio.sleep(1)
                
                # Mostrar el menú principal
                from core.handlers import send_main_menu
                await send_main_menu(update, context)
            else:
                logger.error(f"Error: Usuario {user.id} no se activó correctamente. Estado actual: {db_user.status if db_user else 'No encontrado'}")
                await query.edit_message_text(
                    text=(
                        "⚠️ <b>Registro Incompleto</b>\n\n"
                        f"Se ha creado tu cuenta pero hubo un problema al activarla.\n\n"
                        f"Por favor, contacta al administrador o intenta nuevamente con /register."
                    ),
                    parse_mode=ParseMode.HTML
                )
        else:
            logger.error(f"Error al guardar el usuario {user.id} en la base de datos")
            await query.edit_message_text(
                text=(
                    "❌ <b>Error en el Registro</b>\n\n"
                    f"Lo sentimos, ha ocurrido un error al crear tu cuenta.\n\n"
                    f"Por favor, intenta nuevamente más tarde o contacta al administrador."
                ),
                parse_mode=ParseMode.HTML
            )
    elif action == "cancel":
        await query.edit_message_text(
            text="❌ Registro cancelado. Puedes intentarlo nuevamente cuando lo desees."
        )
        # Limpiar el estado
        state_manager.clear_state(user.id)
    else:
        await query.edit_message_text(
            text="❓ Acción no reconocida. Por favor, intenta nuevamente."
        )

@breadcrumb
async def auth_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador global para mensajes relacionados con autenticación."""
    user = update.effective_user
    message_text = update.message.text.strip()
    
    # Verificar si el usuario está en algún estado de registro
    state = state_manager.get_state(user.id)
    if state != State.REGISTERING:
        # No está en proceso de registro, ignorar
        return
    
    # Evitar el procesamiento duplicado verificando si el mensaje ya ha sido procesado
    # Agregamos una marca temporal para evitar procesamiento duplicado
    message_id = update.message.message_id
    last_processed = state_manager.get_data(user.id, "last_processed_message_id", 0)
    
    if message_id <= last_processed:
        # Este mensaje ya ha sido procesado, ignorarlo
        logger.debug(f"Mensaje {message_id} ya procesado, ignorando")
        return
    
    # Marcar este mensaje como procesado
    state_manager.set_data(user.id, "last_processed_message_id", message_id)
    
    # Obtener el paso actual del registro
    register_step = state_manager.get_data(user.id, "register_step", "")
    
    logger.info(f"Usuario {user.id} en paso {register_step} envió: {message_text}")
    
    # Procesar según el paso actual
    if register_step == "waiting_auth_code":
        # En lugar de limpiar todos los datos, solo actualizamos el paso actual
        await process_auth_code(update, context)
    elif register_step == "waiting_name":
        # Verificar que no estamos utilizando el código de autorización como nombre
        auth_code = state_manager.get_data(user.id, "auth_code", "")
        if message_text == auth_code:
            # Si el usuario envía nuevamente el código de autorización como nombre
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Por favor, introduce tu nombre:"
            )
            return
        await process_name(update, context)
    elif register_step == "waiting_email":
        await process_email(update, context)
    else:
        # Paso no reconocido, ignorar
        logger.warning(f"Paso de registro no reconocido para usuario {user.id}: {register_step}")

def setup_auth_handlers(application):
    """Configurar los manejadores de autenticación."""
    # Comando de registro
    application.add_handler(CommandHandler("register", register_command))
    
    # Manejador de callbacks para el proceso de registro
    application.add_handler(CallbackQueryHandler(register_callback, pattern="^register:"))
    
    # Manejador de mensajes para el proceso de registro (mayor prioridad que otros manejadores)
    # Usando grupo -1 para asegurar que se procese antes que todos los demás manejadores
    application.add_handler(MessageHandler(Filters.TEXT & ~Filters.COMMAND, auth_message_handler), group=-1)
    
    logger.info("Manejadores de autenticación configurados correctamente") 