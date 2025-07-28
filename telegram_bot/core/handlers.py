"""
Manejadores principales para los eventos del bot de Telegram.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.breadcrumbs import breadcrumb
from telegram.constants import ParseMode
import os

# Configuración de logging
logger = logging.getLogger(__name__)

@breadcrumb
async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, is_new_message=True):
    """Envía el menú principal con botones interactivos"""
    user = update.effective_user
    
    # Verificar si el usuario es admin para mostrar opciones adicionales
    from models.user import User
    db_user = User.get_by_telegram_id(user.id)
    is_admin = db_user and db_user.role == "admin"
    
    # Botones básicos (en disposición 2x2)
    keyboard = [
        [
            InlineKeyboardButton("📝 Crear Post", callback_data="action:new_post"),
            InlineKeyboardButton("📋 Ver Posts", callback_data="action:list_posts")
        ],
        [
            InlineKeyboardButton("🏷️ Categorías", callback_data="action:categories"),
            InlineKeyboardButton("🏷️ Etiquetas", callback_data="action:tags")
        ],
        [
            InlineKeyboardButton("⚙️ Configuración", callback_data="menu:settings"),
            InlineKeyboardButton("❓ Ayuda", callback_data="action:help")
        ]
    ]
    
    # Añadir opciones de administrador si corresponde
    if is_admin:
        keyboard.append([
            InlineKeyboardButton("👥 Gestión Usuarios", callback_data="admin:users"),
            InlineKeyboardButton("📊 Estadísticas", callback_data="admin:stats")
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Verificar si hay un saludo personalizado en context.user_data
    greeting = context.user_data.get("custom_greeting", "")
    if greeting:
        menu_text = (
            f"{greeting}\n\n"
            "📱 <b>MENÚ PRINCIPAL</b>\n\n"
            "Selecciona una acción:"
        )
        # Limpiar el saludo personalizado para que no se repita en futuras llamadas
        context.user_data.pop("custom_greeting", None)
    else:
        menu_text = (
            "📱 <b>MENÚ PRINCIPAL</b>\n\n"
            "Selecciona una acción:"
        )
    
    if is_new_message:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=menu_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    else:
        await update.callback_query.edit_message_text(
            text=menu_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

@breadcrumb
async def send_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Envía el menú de configuración"""
    keyboard = [
        [
            InlineKeyboardButton("🌐 Sitio Web", callback_data="settings:site"),
            InlineKeyboardButton("🔐 SFTP", callback_data="settings:sftp")
        ],
        [
            InlineKeyboardButton("📄 Plantilla", callback_data="settings:template"),
            InlineKeyboardButton("« Volver", callback_data="menu:main")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text="⚙️ <b>CONFIGURACIÓN</b>\n\nSelecciona qué quieres configurar:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

@breadcrumb
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador para el comando /start."""
    user = update.effective_user
    logger.info(f"Usuario {user.id} ha iniciado el bot")
    
    # Verificar si el usuario está registrado
    from models.user import User
    db_user = User.get_by_telegram_id(user.id)
    
    # Para debug, mostrar información del usuario encontrado en la base de datos
    if db_user:
        logger.info(f"Usuario encontrado en BD: ID={db_user.id}, TG_ID={db_user.telegram_id}, Nombre={db_user.name}, Estado={db_user.status}")
    else:
        logger.info(f"Usuario {user.id} no encontrado en la base de datos")
    
    # Solo enviar logo si es un usuario nuevo o no está registrado
    if not db_user or not db_user.is_active():
        try:
            # Buscar el logo en la raíz del directorio telegram_bot
            logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logo.webp')
            if os.path.exists(logo_path):
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=open(logo_path, 'rb'),
                    caption="<b>Knowmad Writer</b> - Tu asistente para gestión de contenido web",
                    parse_mode=ParseMode.HTML
                )
            else:
                # Buscar en la raíz principal (un nivel arriba)
                logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logo.webp')
                if os.path.exists(logo_path):
                    await context.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=open(logo_path, 'rb'),
                        caption="<b>Knowmad Writer</b> - Tu asistente para gestión de contenido web",
                        parse_mode=ParseMode.HTML
                    )
                else:
                    logger.warning(f"Logo no encontrado en las rutas buscadas")
        except Exception as e:
            logger.error(f"Error al enviar logo: {e}")
    
    if db_user and db_user.is_active():
        # Usuario ya registrado, no mostrar mensaje extra, ir directo al menú principal
        # con un saludo personalizado
        context.user_data["custom_greeting"] = f"¡Hola de nuevo, {db_user.name}! Bienvenido/a al Bot de gestión de contenidos web."
        await send_main_menu(update, context)
    else:
        # Usuario no registrado, mostrar mensaje de registro
        await update.message.reply_html(
            f"¡Hola, {user.mention_html()}! "
            f"Bienvenido/a al Bot de gestión de contenidos web.\n\n"
            f"Para empezar, debes registrarte usando el comando /register."
        )

@breadcrumb
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador para el comando /help."""
    help_text = (
        "<b>📚 Comandos disponibles:</b>\n\n"
        "/start - Inicia el bot\n"
        "/help - Muestra este mensaje de ayuda\n"
        "/register - Registra tu cuenta (si tienes código de autorización)\n"
        "/mysite - Configura o edita tu sitio web\n"
        "/newpost - Crea un nuevo post\n"
        "/editpost - Edita un post existente\n"
        "/categories - Gestiona tus categorías\n"
        "/featured - Gestiona tus posts destacados\n\n"
        "<b>⚙️ Configuración avanzada:</b>\n"
        "/sftp - Configura tu conexión SFTP\n"
        "/template - Gestiona tu plantilla HTML\n\n"
        "<b>ℹ️ Ayuda:</b>\n"
        "Si necesitas asistencia, contacta al administrador."
    )
    
    await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)

@breadcrumb
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador para callbacks de botones interactivos."""
    query = update.callback_query
    await query.answer()
    
    # Importaciones necesarias
    from core.states import state_manager, State
    from models.site import Site
    from models.user import User
    
    # Formato esperado: acción:parámetro1:parámetro2...
    callback_data = query.data.split(':')
    action = callback_data[0]
    
    logger.info(f"Callback recibido: {action} de usuario {update.effective_user.id}")
    
    # Para callbacks de SFTP, no hacemos nada
    # El manejador específico ya lo habrá procesado
    if action == "sftp":
        return
    
    # Redirigir a los manejadores específicos según la acción
    if action == "menu":
        # Acciones del menú principal
        sub_action = callback_data[1] if len(callback_data) > 1 else None
        
        if sub_action == "main" or sub_action is None:
            # Volver al menú principal
            
            # Si estamos en medio de la configuración de placeholders, mostrar confirmación
            if state_manager.get_state(update.effective_user.id) == State.CONFIGURING_CUSTOM_PLACEHOLDER:
                await query.edit_message_text(
                    "⚠️ <b>¿Cancelar configuración?</b>\n\n"
                    "Estás a punto de cancelar la configuración de placeholders personalizados.\n"
                    "Los cambios realizados hasta ahora no se guardarán.\n\n"
                    "¿Estás seguro?",
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("✅ Sí, cancelar", callback_data="menu:cancel_placeholders"),
                            InlineKeyboardButton("❌ No, continuar", callback_data="menu:continue_placeholders")
                        ]
                    ])
                )
                return
                
            await send_main_menu(update, context, is_new_message=False)
        elif sub_action == "settings":
            # Mostrar menú de configuración
            await send_settings_menu(update, context)
        elif sub_action == "cancel_placeholders":
            # Cancelar la configuración de placeholders
            state_manager.set_state(update.effective_user.id, State.IDLE)
            state_manager.set_data(update.effective_user.id, "placeholder_configs", [])
            state_manager.set_data(update.effective_user.id, "custom_placeholders", [])
            
            await query.edit_message_text(
                "❌ <b>Configuración cancelada</b>\n\n"
                "Has cancelado la configuración de placeholders personalizados.\n"
                "Ningún placeholder ha sido guardado.",
                parse_mode=ParseMode.HTML
            )
            
            # Volver al menú principal
            await send_main_menu(update, context)
        elif sub_action == "continue_placeholders":
            # Continuar con la configuración de placeholders
            # Simplemente mostrar el placeholder actual de nuevo
            current_index = state_manager.get_data(update.effective_user.id, "current_placeholder_index")
            custom_placeholders = state_manager.get_data(update.effective_user.id, "custom_placeholders")
            
            if custom_placeholders and current_index < len(custom_placeholders):
                current_placeholder = custom_placeholders[current_index]
                
                # Crear teclado con opciones
                keyboard = [
                    [InlineKeyboardButton("📝 Configurar", callback_data=f"placeholder:configure:{current_placeholder}")],
                    [InlineKeyboardButton("❌ No usar este placeholder", callback_data=f"placeholder:skip:{current_placeholder}")],
                    [InlineKeyboardButton("« Volver al menú", callback_data="menu:main")]
                ]
                
                await query.edit_message_text(
                    f"📝 <b>Configurando placeholder: {current_placeholder}</b>\n\n"
                    f"¿Qué deseas hacer con este placeholder?",
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                # Caso improbable: no hay más placeholders para configurar
                await configure_next_custom_placeholder(update, context)
    elif action == "placeholder":
        # Manejar acciones de placeholders
        sub_action = callback_data[1] if len(callback_data) > 1 else None
        user = update.effective_user
        
        if sub_action == "configure":
            # Iniciar configuración del placeholder actual
            placeholder = callback_data[2]
            state_manager.set_data(user.id, "configuring_placeholder", placeholder)
            state_manager.set_data(user.id, "placeholder_config_step", "display_name")
            
            await query.edit_message_text(
                f"📝 <b>Configurando placeholder: {placeholder}</b>\n\n"
                f"¿Qué nombre deseas mostrar para este campo en el formulario?\n\n"
                f"Por ejemplo: 'Número de referencia', 'URL del video', etc.",
                parse_mode=ParseMode.HTML
            )
            
        elif sub_action == "skip":
            # Omitir este placeholder
            placeholder = callback_data[2]
            current_index = state_manager.get_data(user.id, "current_placeholder_index")
            state_manager.set_data(user.id, "current_placeholder_index", current_index + 1)
            
            await query.edit_message_text(
                f"⏭️ <b>Placeholder omitido</b>\n\n"
                f"El placeholder <b>{placeholder}</b> ha sido omitido.\n"
                f"No se solicitará información para este campo al crear contenido.",
                parse_mode=ParseMode.HTML
            )
            
            # Iniciar configuración del siguiente placeholder
            await configure_next_custom_placeholder(update, context)
            
        elif sub_action == "cancel":
            # Cancelar la configuración actual
            await query.edit_message_text(
                "❌ <b>Configuración cancelada</b>\n\n"
                "Has cancelado la configuración del placeholder actual.",
                parse_mode=ParseMode.HTML
            )
            
            # Volver al menú principal
            state_manager.set_state(user.id, State.IDLE)
            await send_main_menu(update, context)
            
        elif sub_action == "type":
            # Manejar selección de tipo de placeholder
            placeholder_type = callback_data[2]
            
            # Guardar el tipo
            state_manager.set_data(user.id, "placeholder_type", placeholder_type)
            
            # Obtener el placeholder que se está configurando
            placeholder = state_manager.get_data(user.id, "configuring_placeholder")
            display_name = state_manager.get_data(user.id, "display_name")
            
            if placeholder_type == "desplegable":
                # Para tipo desplegable, solicitar opciones
                state_manager.set_data(user.id, "placeholder_config_step", "options")
                
                await query.edit_message_text(
                    f"✅ Tipo seleccionado: <b>{placeholder_type}</b>\n\n"
                    f"Por favor, introduce las opciones para <b>{placeholder}</b> separadas por comas.\n\n"
                    f"Ejemplo: <i>Opción 1, Opción 2, Opción 3</i>",
                    parse_mode=ParseMode.HTML
                )
            else:
                # Para otros tipos, acumular la configuración en lugar de crear el placeholder
                # Eliminar llaves para guardar el nombre del placeholder
                placeholder_name = placeholder
                if placeholder_name.startswith("{{") and placeholder_name.endswith("}}"):
                    placeholder_name = placeholder_name[2:-2]
                
                # Acumular la configuración del placeholder
                placeholder_configs = state_manager.get_data(user.id, "placeholder_configs") or []
                placeholder_configs.append({
                    "placeholder_name": placeholder_name,
                    "display_name": display_name,
                    "placeholder_type": placeholder_type,
                    "options": None
                })
                state_manager.set_data(user.id, "placeholder_configs", placeholder_configs)
                
                # Mostrar confirmación
                await query.edit_message_text(
                    f"✅ <b>Placeholder configurado correctamente</b>\n\n"
                    f"• <b>Placeholder:</b> {placeholder}\n"
                    f"• <b>Nombre:</b> {display_name}\n"
                    f"• <b>Tipo:</b> {placeholder_type}\n\n"
                    f"El placeholder se aplicará cuando se complete la configuración.",
                    parse_mode=ParseMode.HTML
                )
                
                # Avanzar al siguiente placeholder
                current_index = state_manager.get_data(user.id, "current_placeholder_index")
                state_manager.set_data(user.id, "current_placeholder_index", current_index + 1)
                
                # Iniciar configuración del siguiente placeholder usando mensaje nuevo
                await configure_next_custom_placeholder(update, context)
    elif action == "action":
        # Acciones principales
        sub_action = callback_data[1] if len(callback_data) > 1 else None
        
        if sub_action == "new_post":
            await handle_new_post(update, context)
        elif sub_action == "list_posts":
            await handle_list_posts(update, context)
        elif sub_action == "categories":
            await handle_categories(update, context)
        elif sub_action == "tags":
            await handle_tags(update, context)
        elif sub_action == "help":
            await help_command(update, context)
    elif action == "settings":
        # Acciones del menú de configuración
        sub_action = callback_data[1] if len(callback_data) > 1 else None
        
        if sub_action == "site":
            # Mostrar opciones de configuración del sitio con formulario
            user_id = update.effective_user.id
            from models.site import Site
            from models.user import User
            
            db_user = User.get_by_telegram_id(user_id)
            site = Site.get_by_user_id(db_user.id) if db_user else None
            
            # Determinar el sitio a usar o crear uno nuevo
            if isinstance(site, list):
                site = site[0] if site else None
            
            if site:
                # Mostrar la configuración actual
                keyboard = [
                    [InlineKeyboardButton("✏️ Nombre del sitio", callback_data="site:edit_name")],
                    [InlineKeyboardButton("🌐 Dominio", callback_data="site:edit_domain")],
                    [InlineKeyboardButton("« Volver", callback_data="menu:settings")]
                ]
                
                await update.callback_query.edit_message_text(
                    text=f"🌐 <b>CONFIGURACIÓN DEL SITIO</b>\n\n"
                         f"<b>Nombre actual:</b> {site.name or 'No configurado'}\n"
                         f"<b>Dominio actual:</b> {site.domain or 'No configurado'}\n\n"
                         f"Selecciona qué deseas modificar:",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode=ParseMode.HTML
                )
            else:
                # No hay configuración, crear una nueva
                await update.callback_query.edit_message_text(
                    text="🌐 <b>CONFIGURACIÓN DEL SITIO</b>\n\n"
                         "No tienes un sitio configurado. Vamos a configurar uno nuevo.\n\n"
                         "Por favor, ingresa el <b>nombre</b> de tu sitio web:",
                    parse_mode=ParseMode.HTML
                )
                
                # Establecer estado para esperar el nombre del sitio
                from core.states import State, state_manager
                state_manager.set_state(user_id, State.CONFIGURING_SITE)
                state_manager.set_data(user_id, "site_step", "waiting_name")
        elif sub_action == "sftp":
            # Redirigir a configuración SFTP
            from modules.sftp.handlers import sftp_config_menu
            await sftp_config_menu(update, context)
        elif sub_action == "template":
            # Mostrar opciones de configuración de plantilla
            keyboard = [
                [InlineKeyboardButton("📤 Subir plantilla", callback_data="template:upload")],
                [InlineKeyboardButton("🔍 Ver placeholders", callback_data="template:view_placeholders")],
                [InlineKeyboardButton("« Volver", callback_data="menu:settings")]
            ]
            
            await update.callback_query.edit_message_text(
                text="📄 <b>CONFIGURACIÓN DE PLANTILLA</b>\n\n"
                     "Aquí puedes gestionar la plantilla HTML que se usará para tus posts.\n\n"
                     "Una plantilla debe contener ciertos placeholders que serán reemplazados "
                     "con la información de cada post cuando se publique.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
    elif action == "site":
        # Manejo de callbacks para configuración del sitio
        sub_action = callback_data[1] if len(callback_data) > 1 else None
        user_id = update.effective_user.id
        
        if sub_action == "edit_name":
            await update.callback_query.edit_message_text(
                text="✏️ <b>Nombre del Sitio</b>\n\n"
                     "Por favor, ingresa el nuevo nombre para tu sitio web:",
                parse_mode=ParseMode.HTML
            )
            
            # Establecer estado para esperar el nombre del sitio
            from core.states import State, state_manager
            state_manager.set_state(user_id, State.CONFIGURING_SITE)
            state_manager.set_data(user_id, "site_step", "waiting_name")
            
        elif sub_action == "edit_domain":
            await update.callback_query.edit_message_text(
                text="🌐 <b>Dominio del Sitio</b>\n\n"
                     "Por favor, ingresa el dominio de tu sitio web (ejemplo: https://misitio.com):",
                parse_mode=ParseMode.HTML
            )
            
            # Establecer estado para esperar el dominio
            from core.states import State, state_manager
            state_manager.set_state(user_id, State.CONFIGURING_SITE)
            state_manager.set_data(user_id, "site_step", "waiting_domain")
    
    elif action == "template":
        # Manejo de callbacks para configuración de plantilla
        sub_action = callback_data[1] if len(callback_data) > 1 else None
        user_id = update.effective_user.id
        
        if sub_action == "upload":
            await update.callback_query.edit_message_text(
                text="📤 <b>Subir Plantilla HTML</b>\n\n"
                     "Por favor, envía tu archivo HTML de plantilla.\n\n"
                     "<i>La plantilla debe contener ciertos placeholders como {{TITLE}}, {{CONTENT}}, etc.</i>",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("« Volver", callback_data="settings:template")
                ]])
            )
            
            # Establecer estado para esperar la plantilla
            from core.states import State, state_manager
            state_manager.set_state(user_id, State.UPLOADING_TEMPLATE)
            
        elif sub_action == "view_placeholders":
            # Mostrar lista de placeholders disponibles
            await update.callback_query.edit_message_text(
                text="🔍 <b>Placeholders Disponibles</b>\n\n"
                     "<b>Obligatorios:</b>\n"
                     "• {{TITLE}} - Título del post\n"
                     "• {{META_DESCRIPTION}} - Meta descripción\n"
                     "• {{FEATURE_IMAGE}} - Imagen principal\n"
                     "• {{PUBLISHED_TIME}} - Fecha de publicación\n"
                     "• {{CATEGORY}} - Categoría\n"
                     "• {{SITE_URL}} - URL del sitio\n"
                     "• {{ARTICLE_URL}} - URL del artículo\n"
                     "• {{CONTENT}} - Contenido HTML\n\n"
                     "<b>Generados automáticamente:</b>\n"
                     "• {{SITE_NAME}} - Nombre del sitio (de la configuración)\n"
                     "• {{SLUG}} - URL amigable (del título)\n\n"
                     "<b>Opcionales:</b>\n"
                     "• {{LAST_MODIFIED}} - Última modificación\n"
                     "• {{FEATURE_IMAGE_ALT}} - Alt de imagen\n"
                     "• {{READING_TIME}} - Tiempo de lectura\n"
                     "• {{SOURCE_LIST}} - Lista de fuentes\n"
                     "• {{POST_MONTH}} - Mes de publicación",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("« Volver", callback_data="settings:template")
                ]])
            )
    elif action == "admin":
        # Acciones de administrador
        sub_action = callback_data[1] if len(callback_data) > 1 else None
        
        # Verificar que el usuario es admin
        from models.user import User
        db_user = User.get_by_telegram_id(update.effective_user.id)
        is_admin = db_user and db_user.role == "admin"
        
        if not is_admin:
            await update.callback_query.edit_message_text(
                text="⛔ <b>ACCESO DENEGADO</b>\n\n"
                     "No tienes permisos de administrador para acceder a esta función.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("« Volver", callback_data="menu:main")
                ]]),
                parse_mode=ParseMode.HTML
            )
            return
        
        if sub_action == "users":
            await handle_admin_users(update, context)
        elif sub_action == "stats":
            await handle_admin_stats(update, context)
        elif sub_action.startswith("user_"):
            # Acciones específicas de gestión de usuarios
            user_action = sub_action.split("_")[1]
            if user_action == "new":
                await update.callback_query.edit_message_text(
                    text="➕ <b>AÑADIR NUEVO USUARIO</b>\n\n"
                         "Esta función te permitirá pre-registrar nuevos usuarios.\n\n"
                         "Estamos implementando esta función. ¡Estará disponible pronto!",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("« Volver", callback_data="admin:users")
                    ]]),
                    parse_mode=ParseMode.HTML
                )
            elif user_action == "list":
                # Listar usuarios (simplificado)
                users = User.get_all()
                users_text = "\n".join([f"• {u.name} (@{u.telegram_id}) - {u.role} - {u.status}" for u in users[:10]])
                
                await update.callback_query.edit_message_text(
                    text="📋 <b>LISTADO DE USUARIOS</b>\n\n"
                         f"{users_text}\n\n"
                         f"Mostrando {min(10, len(users))} de {len(users)} usuarios.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("« Volver", callback_data="admin:users")
                    ]]),
                    parse_mode=ParseMode.HTML
                )
    elif action == "cat":
        # Acciones de categorías
        await update.callback_query.edit_message_text(
            text="🏷️ <b>CATEGORÍAS</b>\n\n"
                 "Esta función estará disponible próximamente.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Volver", callback_data="action:categories")
            ]]),
            parse_mode=ParseMode.HTML
        )
    elif action == "tag":
        # Acciones de etiquetas
        await update.callback_query.edit_message_text(
            text="🏷️ <b>ETIQUETAS</b>\n\n"
                 "Esta función estará disponible próximamente.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Volver", callback_data="action:tags")
            ]]),
            parse_mode=ParseMode.HTML
        )
    elif action == "register":
        # Implementar lógica de registro
        pass
    elif action == "site_config":
        # Implementar lógica de configuración de sitio
        pass
    elif action == "content":
        # Implementar lógica de gestión de contenido
        pass
    else:
        # Debug para identificar callbacks no capturados
        logger.warning(f"Callback no reconocido en el manejador principal: {query.data}")
        
        # Mensajero para el usuario
        await update.callback_query.edit_message_text(
            text=f"⚠️ <b>Callback no reconocido</b>\n\n"
                 f"El callback <code>{query.data}</code> no fue reconocido por el sistema.\n\n"
                 f"Por favor, vuelve al menú principal e intenta nuevamente.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Volver al menú", callback_data="menu:main")
            ]]),
            parse_mode=ParseMode.HTML
        )

@breadcrumb
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador para mensajes de texto."""
    user = update.effective_user
    
    # Si el usuario no está en la base de datos, mostrar mensaje de error
    from models.user import User
    db_user = User.get_by_telegram_id(user.id)
    
    if not db_user:
        await update.message.reply_text(
            "❌ <b>Error: Usuario no registrado</b>\n\n"
            "No estás registrado en el sistema. Por favor, inicia el bot con /start "
            "y completa el proceso de registro.",
            parse_mode=ParseMode.HTML
        )
        return
    
    # Si el usuario está bloqueado, mostrar mensaje
    if db_user.status == User.STATUS_BLOCKED:
        await update.message.reply_text(
            "🚫 <b>Tu cuenta ha sido bloqueada</b>\n\n"
            "Tu acceso al bot ha sido restringido. Por favor, contacta con el administrador "
            "si crees que esto es un error.",
            parse_mode=ParseMode.HTML
        )
        return
    
    # Obtener el estado actual del usuario
    from core.states import state_manager, State
    
    current_state = state_manager.get_state(user.id)
    
    # Manejar según el estado
    if current_state == State.CONFIGURING_SITE:
        await handle_site_configuration(update, context)
        return
    elif current_state == State.CONFIGURING_SFTP:
        # Dejar que el manejador de SFTP procese el mensaje
        from modules.sftp.handlers import sftp_message_handler
        was_handled = await sftp_message_handler(update, context)
        if was_handled:
            return
    elif current_state == State.UPLOADING_TEMPLATE:
        # Manejar subida de plantilla
        if update.message.document:
            # Si es un documento, procesarlo como plantilla
            await handle_document_upload(update, context)
        elif update.message.text:
            # Si es texto, procesarlo como plantilla en texto plano
            await handle_template_upload(update, context)
        return
    elif current_state == State.CONFIGURING_CUSTOM_PLACEHOLDER:
        # Manejar configuración de placeholder personalizado
        await handle_custom_placeholder_configuration(update, context)
        return
    
    # Si llegamos aquí, el mensaje no fue manejado por ningún estado especial
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="🤔 No estoy seguro de qué hacer con este mensaje. Por favor, usa los comandos o botones del menú.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Menú Principal", callback_data="menu:main")],
            [InlineKeyboardButton("Ayuda", callback_data="action:help")]
        ])
    )

@breadcrumb
async def handle_site_configuration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador para procesar la configuración del sitio."""
    user = update.effective_user
    text = update.message.text
    
    from core.states import state_manager, State
    from models.site import Site
    from models.user import User
    
    current_step = state_manager.get_data(user.id, "site_step")
    db_user = User.get_by_telegram_id(user.id)
    
    if not db_user:
        await update.message.reply_text("❌ Error: Usuario no encontrado. Por favor, reinicia el bot con /start.")
        return
    
    # Buscar el sitio existente o crear uno nuevo
    site = Site.get_by_user_id(db_user.id)
    
    # Determinar el sitio a usar o crear uno nuevo
    if isinstance(site, list):
        site = site[0] if site else None
        
    if not site:
        site = Site(user_id=db_user.id)
    
    if current_step == "waiting_name":
        # Procesar el nombre del sitio
        if not text or len(text) < 3:
            await update.message.reply_text(
                "⚠️ El nombre debe tener al menos 3 caracteres. Por favor, inténtalo de nuevo:"
            )
            return
        
        site.name = text
        site.save()
        
        # Si aún no hay dominio, preguntar por él
        if not site.domain:
            await update.message.reply_text(
                "✅ Nombre guardado.\n\n"
                "Ahora, ingresa el <b>dominio</b> de tu sitio web (ejemplo: https://misitio.com):",
                parse_mode=ParseMode.HTML
            )
            state_manager.set_data(user.id, "site_step", "waiting_domain")
        else:
            # Mostrar configuración completa
            await update.message.reply_text(
                f"✅ <b>Nombre actualizado</b>\n\n"
                f"La configuración de tu sitio ha sido actualizada:\n\n"
                f"<b>Nombre:</b> {site.name}\n"
                f"<b>Dominio:</b> {site.domain}\n\n"
                f"Puedes seguir configurando tu sitio desde el menú de configuración.",
                parse_mode=ParseMode.HTML
            )
            state_manager.set_state(user.id, State.IDLE)
            
            # Mostrar menú principal
            await send_main_menu(update, context)
    
    elif current_step == "waiting_domain":
        # Procesar el dominio del sitio
        import re
        
        # Validar formato básico del dominio
        if not re.match(r'^(https?://)?[a-zA-Z0-9][-a-zA-Z0-9.]*\.[a-zA-Z]{2,}(/.*)?$', text):
            await update.message.reply_text(
                "⚠️ El formato del dominio no parece válido. Debe ser similar a 'https://ejemplo.com'. "
                "Por favor, inténtalo de nuevo:"
            )
            return
        
        # Asegurarse de que el dominio tenga https:// al inicio
        if not text.startswith(('http://', 'https://')):
            text = 'https://' + text
        
        # Eliminar slash final si existe
        if text.endswith('/'):
            text = text[:-1]
        
        site.domain = text
        site.save()
        
        # Configuración completa
        await update.message.reply_text(
            f"✅ <b>Configuración completa</b>\n\n"
            f"La configuración de tu sitio ha sido guardada:\n\n"
            f"<b>Nombre:</b> {site.name}\n"
            f"<b>Dominio:</b> {site.domain}\n\n"
            f"Ahora puedes proceder a configurar SFTP y subir tu plantilla HTML.",
            parse_mode=ParseMode.HTML
        )
        state_manager.set_state(user.id, State.IDLE)
        
        # Mostrar menú principal
        await send_main_menu(update, context)

@breadcrumb
async def handle_template_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador para procesar la subida de plantilla como texto."""
    user = update.effective_user
    html_content = update.message.text
    
    from core.states import state_manager, State
    from models.site import Site
    from models.user import User
    
    db_user = User.get_by_telegram_id(user.id)
    if not db_user:
        await update.message.reply_text("❌ Error: Usuario no encontrado. Por favor, reinicia el bot con /start.")
        return
    
    # Obtener el sitio del usuario - get_by_user_id devuelve una lista
    sites = Site.get_by_user_id(db_user.id)
    site = sites[0] if sites else None
    
    if not site:
        await update.message.reply_text(
            "❌ Error: Primero debes configurar tu sitio. Usa /settings para hacerlo."
        )
        return
    
    # Validar los placeholders obligatorios - excluyendo SITE_NAME y SLUG
    required_placeholders = [
        "{{TITLE}}", "{{META_DESCRIPTION}}", "{{FEATURE_IMAGE}}",
        "{{PUBLISHED_TIME}}", "{{CATEGORY}}", "{{SITE_URL}}", "{{ARTICLE_URL}}",
        "{{CONTENT}}"
    ]
    
    # Placeholders generados automáticamente
    auto_placeholders = [
        "{{SITE_NAME}}", "{{SLUG}}"
    ]
    
    optional_placeholders = [
        "{{LAST_MODIFIED}}", "{{FEATURE_IMAGE_ALT}}", "{{READING_TIME}}",
        "{{SOURCE_LIST}}", "{{POST_MONTH}}"
    ]
    
    # Comprobar los placeholders presentes
    missing_required = []
    for ph in required_placeholders:
        if ph not in html_content:
            missing_required.append(ph)
    
    present_optional = []
    for ph in optional_placeholders:
        if ph in html_content:
            present_optional.append(ph)
    
    present_auto = []
    for ph in auto_placeholders:
        if ph in html_content:
            present_auto.append(ph)
    
    # Buscar placeholders desconocidos
    import re
    all_known = required_placeholders + optional_placeholders + auto_placeholders
    pattern = r"{{([^}]+)}}"
    matches = re.findall(pattern, html_content)
    
    unknown_placeholders = []
    for match in matches:
        placeholder = "{{" + match + "}}"
        if placeholder not in all_known and placeholder not in unknown_placeholders:
            unknown_placeholders.append(placeholder)
    
    # Evaluar resultado de la validación
    if missing_required:
        missing_text = "\n".join([f"• {ph}" for ph in missing_required])
        await update.message.reply_text(
            f"⚠️ <b>Faltan placeholders obligatorios</b>\n\n"
            f"Tu plantilla no contiene los siguientes placeholders requeridos:\n\n"
            f"{missing_text}\n\n"
            f"Por favor, añádelos a tu plantilla e inténtalo de nuevo.",
            parse_mode=ParseMode.HTML
        )
        return
    
    # Guardar la plantilla
    site.template = html_content
    site.save()
    
    # Informar del resultado
    result_message = f"✅ <b>Plantilla guardada correctamente</b>\n\n"
    
    # Mensajes sobre placeholders automáticos
    auto_message = ""
    if "{{SITE_NAME}}" not in present_auto:
        auto_message += "• {{SITE_NAME}} - Se rellenará con el nombre del sitio configurado\n"
    if "{{SLUG}}" not in present_auto:
        auto_message += "• {{SLUG}} - Se generará automáticamente a partir del título del post\n"
    
    if auto_message:
        result_message += f"<b>Placeholders que se generarán automáticamente:</b>\n{auto_message}\n"
    
    if present_optional:
        optional_text = "\n".join([f"• {ph}" for ph in present_optional])
        result_message += f"<b>Placeholders opcionales detectados:</b>\n{optional_text}\n\n"
    
    if unknown_placeholders:
        unknown_text = "\n".join([f"• {ph}" for ph in unknown_placeholders])
        result_message += f"<b>Placeholders personalizados detectados:</b>\n{unknown_text}\n\n"
        
        # Guardar los placeholders desconocidos para configuración
        state_manager.set_data(user.id, "custom_placeholders", unknown_placeholders)
        
        await update.message.reply_text(
            result_message + "\n"
            "A continuación configuraremos cada placeholder personalizado detectado.\n"
            "Esto permitirá validar y solicitar valores apropiados al crear contenido.",
            parse_mode=ParseMode.HTML
        )
        
        # Iniciar el flujo de configuración de placeholders personalizados
        state_manager.set_data(user.id, "current_placeholder_index", 0)
        state_manager.set_state(user.id, State.CONFIGURING_CUSTOM_PLACEHOLDER)
        
        # Iniciar la configuración del primer placeholder
        await configure_next_custom_placeholder(update, context)
    else:
        await update.message.reply_text(
            result_message,
            parse_mode=ParseMode.HTML
        )
        
        # Volver al estado idle y mostrar menú principal
        state_manager.set_state(user.id, State.IDLE)
        await send_main_menu(update, context)

@breadcrumb
async def handle_document_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador para procesar la subida de plantilla como documento HTML."""
    user = update.effective_user
    document = update.message.document
    
    from core.states import state_manager, State
    from models.site import Site
    from models.user import User
    import io
    
    db_user = User.get_by_telegram_id(user.id)
    if not db_user:
        await update.message.reply_text("❌ Error: Usuario no encontrado. Por favor, reinicia el bot con /start.")
        return
    
    # Obtener el sitio del usuario - get_by_user_id devuelve una lista
    sites = Site.get_by_user_id(db_user.id)
    site = sites[0] if sites else None
    
    if not site:
        await update.message.reply_text(
            "❌ Error: Primero debes configurar tu sitio. Usa /settings para hacerlo."
        )
        return
    
    # Verificar que el documento sea un archivo HTML o texto
    file_name = document.file_name.lower() if document.file_name else ""
    if not (file_name.endswith('.html') or file_name.endswith('.htm') or document.mime_type in ['text/html', 'text/plain']):
        await update.message.reply_text(
            "❌ Error: Por favor, envía un archivo HTML válido. "
            "El archivo debe tener extensión .html o .htm."
        )
        return
    
    # Mensaje de carga
    loading_message = await update.message.reply_text(
        "⏳ Descargando y procesando la plantilla..."
    )
    
    try:
        # Descargar el archivo
        file = await context.bot.get_file(document.file_id)
        buffer = io.BytesIO()
        await file.download_to_memory(buffer)
        buffer.seek(0)
        html_content = buffer.read().decode('utf-8')
        
        # Validar los placeholders obligatorios - excluyendo SITE_NAME y SLUG
        required_placeholders = [
            "{{TITLE}}", "{{META_DESCRIPTION}}", "{{FEATURE_IMAGE}}",
            "{{PUBLISHED_TIME}}", "{{CATEGORY}}", "{{SITE_URL}}", "{{ARTICLE_URL}}",
            "{{CONTENT}}"
        ]
        
        # Placeholders generados automáticamente
        auto_placeholders = [
            "{{SITE_NAME}}", "{{SLUG}}"
        ]
        
        optional_placeholders = [
            "{{LAST_MODIFIED}}", "{{FEATURE_IMAGE_ALT}}", "{{READING_TIME}}",
            "{{SOURCE_LIST}}", "{{POST_MONTH}}"
        ]
        
        # Comprobar los placeholders presentes
        missing_required = []
        for ph in required_placeholders:
            if ph not in html_content:
                missing_required.append(ph)
        
        present_optional = []
        for ph in optional_placeholders:
            if ph in html_content:
                present_optional.append(ph)
        
        present_auto = []
        for ph in auto_placeholders:
            if ph in html_content:
                present_auto.append(ph)
        
        # Buscar placeholders desconocidos
        import re
        all_known = required_placeholders + optional_placeholders + auto_placeholders
        pattern = r"{{([^}]+)}}"
        matches = re.findall(pattern, html_content)
        
        unknown_placeholders = []
        for match in matches:
            placeholder = "{{" + match + "}}"
            if placeholder not in all_known and placeholder not in unknown_placeholders:
                unknown_placeholders.append(placeholder)
        
        # Eliminar mensaje de carga
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=loading_message.message_id
            )
        except Exception as e:
            logger.warning(f"No se pudo eliminar mensaje de carga: {e}")
        
        # Evaluar resultado de la validación
        if missing_required:
            missing_text = "\n".join([f"• {ph}" for ph in missing_required])
            await update.message.reply_text(
                f"⚠️ <b>Faltan placeholders obligatorios</b>\n\n"
                f"Tu plantilla no contiene los siguientes placeholders requeridos:\n\n"
                f"{missing_text}\n\n"
                f"Por favor, añádelos a tu plantilla e inténtalo de nuevo.",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Guardar la plantilla
        site.template = html_content
        site.save()
        
        # Informar del resultado
        result_message = f"✅ <b>Plantilla guardada correctamente</b>\n\n"
        
        # Mensajes sobre placeholders automáticos
        auto_message = ""
        if "{{SITE_NAME}}" not in present_auto:
            auto_message += "• {{SITE_NAME}} - Se rellenará con el nombre del sitio configurado\n"
        if "{{SLUG}}" not in present_auto:
            auto_message += "• {{SLUG}} - Se generará automáticamente a partir del título del post\n"
        
        if auto_message:
            result_message += f"<b>Placeholders que se generarán automáticamente:</b>\n{auto_message}\n"
        
        if present_optional:
            optional_text = "\n".join([f"• {ph}" for ph in present_optional])
            result_message += f"<b>Placeholders opcionales detectados:</b>\n{optional_text}\n\n"
        
        if unknown_placeholders:
            unknown_text = "\n".join([f"• {ph}" for ph in unknown_placeholders])
            result_message += f"<b>Placeholders personalizados detectados:</b>\n{unknown_text}\n\n"
            
            # Guardar los placeholders desconocidos para configuración
            state_manager.set_data(user.id, "custom_placeholders", unknown_placeholders)
            # Inicializar lista para guardar configuraciones de placeholders
            state_manager.set_data(user.id, "placeholder_configs", [])
            
            await update.message.reply_text(
                result_message + "\n"
                "A continuación configuraremos cada placeholder personalizado detectado.\n"
                "Esto permitirá validar y solicitar valores apropiados al crear contenido.",
                parse_mode=ParseMode.HTML
            )
            
            # Iniciar el flujo de configuración de placeholders personalizados
            state_manager.set_data(user.id, "current_placeholder_index", 0)
            state_manager.set_state(user.id, State.CONFIGURING_CUSTOM_PLACEHOLDER)
            
            # Iniciar la configuración del primer placeholder
            await configure_next_custom_placeholder(update, context)
        else:
            await update.message.reply_text(
                result_message,
                parse_mode=ParseMode.HTML
            )
            
            # Volver al estado idle y mostrar menú principal
            state_manager.set_state(user.id, State.IDLE)
            await send_main_menu(update, context)
    
    except Exception as e:
        # En caso de error, eliminar mensaje de carga y mostrar error
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=loading_message.message_id
            )
        except:
            pass
        
        import traceback
        logger.error(f"Error al procesar plantilla: {e}")
        logger.error(traceback.format_exc())
        
        await update.message.reply_text(
            "❌ <b>Error al procesar la plantilla</b>\n\n"
            f"Ocurrió un error: {str(e)}\n\n"
            "Por favor, verifica que el archivo sea un HTML válido e inténtalo de nuevo.",
            parse_mode=ParseMode.HTML
        )

@breadcrumb
async def configure_next_custom_placeholder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia la configuración del siguiente placeholder personalizado."""
    user = update.effective_user
    
    from core.states import state_manager, State
    from models.site import Site
    from models.user import User
    from database.connection import get_db
    
    # Obtener datos del estado
    custom_placeholders = state_manager.get_data(user.id, "custom_placeholders")
    current_index = state_manager.get_data(user.id, "current_placeholder_index")
    
    # Verificar si hay más placeholders para configurar
    if not custom_placeholders or current_index >= len(custom_placeholders):
        # Completado, guardar todos los placeholders configurados
        placeholder_configs = state_manager.get_data(user.id, "placeholder_configs") or []
        
        # Obtener información del usuario y sitio
        db_user = User.get_by_telegram_id(user.id)
        sites = Site.get_by_user_id(db_user.id) if db_user else []
        site = sites[0] if sites else None
        
        if site and placeholder_configs:
            # Primero limpiar los placeholders existentes para evitar conflictos
            try:
                conn, cur = get_db()
                cur.execute('DELETE FROM custom_placeholders WHERE site_id = ?', (site.id,))
                conn.commit()
            except Exception as e:
                logger.error(f"Error al limpiar placeholders existentes: {e}")
                
            # Luego guardar todos los nuevos placeholders
            success_count = 0
            for config in placeholder_configs:
                try:
                    new_placeholder = site.add_custom_placeholder(
                        placeholder_name=config["placeholder_name"],
                        display_name=config["display_name"],
                        placeholder_type=config["placeholder_type"],
                        options=config.get("options")
                    )
                    if new_placeholder:
                        success_count += 1
                except Exception as e:
                    logger.error(f"Error al crear placeholder {config['placeholder_name']}: {e}")
            
            # Mensaje de completado
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    f"✅ <b>Configuración de placeholders completada</b>\n\n"
                    f"Se han configurado {success_count} de {len(placeholder_configs)} placeholders personalizados.",
                    parse_mode=ParseMode.HTML
                )
            else:
                await update.message.reply_text(
                    f"✅ <b>Configuración de placeholders completada</b>\n\n"
                    f"Se han configurado {success_count} de {len(placeholder_configs)} placeholders personalizados.",
                    parse_mode=ParseMode.HTML
                )
        else:
            # Mensaje de completado sin configuraciones
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    "✅ <b>Configuración de placeholders completada</b>\n\n"
                    "No se han configurado placeholders personalizados.",
                    parse_mode=ParseMode.HTML
                )
            else:
                await update.message.reply_text(
                    "✅ <b>Configuración de placeholders completada</b>\n\n"
                    "No se han configurado placeholders personalizados.",
                    parse_mode=ParseMode.HTML
                )
        
        # Volver al estado IDLE
        state_manager.set_state(user.id, State.IDLE)
        await send_main_menu(update, context)
        return
    
    # Obtener el placeholder actual
    current_placeholder = custom_placeholders[current_index]
    
    # Crear teclado con opciones
    keyboard = [
        [InlineKeyboardButton("📝 Configurar", callback_data=f"placeholder:configure:{current_placeholder}")],
        [InlineKeyboardButton("❌ No usar este placeholder", callback_data=f"placeholder:skip:{current_placeholder}")],
        [InlineKeyboardButton("« Volver al menú", callback_data="menu:main")]
    ]
    
    # Usar el método apropiado según el contexto (callback o mensaje directo)
    if update.callback_query:
        await update.callback_query.edit_message_text(
            f"📝 <b>Configurando placeholder: {current_placeholder}</b>\n\n"
            f"¿Qué deseas hacer con este placeholder?",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            f"📝 <b>Configurando placeholder: {current_placeholder}</b>\n\n"
            f"¿Qué deseas hacer con este placeholder?",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

@breadcrumb
async def handle_new_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja la creación de un nuevo post"""
    await update.callback_query.edit_message_text(
        text="📝 <b>CREAR NUEVO POST</b>\n\n"
             "Para crear un nuevo post, envíame:\n"
             "- Tu contenido HTML o\n"
             "- El texto plano para el post\n\n"
             "Puedes usar /cancel para cancelar.",
        parse_mode=ParseMode.HTML
    )
    # Cambiar el estado a CREATING_POST
    from core.states import State, state_manager
    state_manager.set_state(update.effective_user.id, State.CREATING_POST)

@breadcrumb
async def handle_list_posts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja la visualización de posts existentes"""
    # Aquí iría el código para cargar los posts desde la base de datos o archivo JSON
    # Por ahora solo mostramos el mensaje de "próximamente"
    
    # Ejemplo de cómo sería con cabeceras:
    # if posts:
    #     message = "📋 <b>TUS POSTS</b>\n\n"
    #     message += "<b>TÍTULO</b>   <b>FECHA</b>   <b>CATEGORÍA</b>\n"
    #     message += "───────────────────────────\n\n"
    #     
    #     for post in posts:
    #         message += f"• <b>{post['title']}</b>\n"
    #         message += f"  📅 {post['date']} | 🏷️ {post['category']}\n\n"
    # else:
    #     message = "No hay posts disponibles"
    
    await update.callback_query.edit_message_text(
        text="📋 <b>TUS POSTS</b>\n\n"
             "Esta función te permitirá ver y editar tus posts existentes.\n\n"
             "Estamos implementando esta función. ¡Estará disponible pronto!",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("« Volver", callback_data="menu:main")
        ]]),
        parse_mode=ParseMode.HTML
    )

@breadcrumb
async def handle_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja la gestión de categorías"""
    keyboard = [
        [
            InlineKeyboardButton("➕ Nueva Categoría", callback_data="cat:new"),
            InlineKeyboardButton("📋 Ver Categorías", callback_data="cat:list")
        ],
        [
            InlineKeyboardButton("✏️ Editar Categoría", callback_data="cat:edit"),
            InlineKeyboardButton("« Volver", callback_data="menu:main")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text="🏷️ <b>GESTIÓN DE CATEGORÍAS</b>\n\nSelecciona una opción:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

@breadcrumb
async def handle_tags(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja la gestión de etiquetas"""
    keyboard = [
        [
            InlineKeyboardButton("➕ Nueva Etiqueta", callback_data="tag:new"),
            InlineKeyboardButton("📋 Ver Etiquetas", callback_data="tag:list")
        ],
        [
            InlineKeyboardButton("✏️ Editar Etiqueta", callback_data="tag:edit"),
            InlineKeyboardButton("« Volver", callback_data="menu:main")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text="🏷️ <b>GESTIÓN DE ETIQUETAS</b>\n\nSelecciona una opción:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

@breadcrumb
async def handle_admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja la gestión de usuarios (solo admin)"""
    keyboard = [
        [
            InlineKeyboardButton("➕ Nuevo Usuario", callback_data="admin:user_new"),
            InlineKeyboardButton("📋 Listar Usuarios", callback_data="admin:user_list")
        ],
        [
            InlineKeyboardButton("❌ Bloquear Usuario", callback_data="admin:user_block"),
            InlineKeyboardButton("« Volver", callback_data="menu:main")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text="👥 <b>GESTIÓN DE USUARIOS</b>\n\nComo administrador, puedes gestionar los usuarios del sistema:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

@breadcrumb
async def handle_admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra estadísticas (solo admin)"""
    from models.user import User
    
    # Contar usuarios totales y activos
    total_users = User.count_all()
    active_users = User.count_active()
    
    await update.callback_query.edit_message_text(
        text="📊 <b>ESTADÍSTICAS DEL SISTEMA</b>\n\n"
             f"Usuarios totales: {total_users}\n"
             f"Usuarios activos: {active_users}\n\n"
             "Esta función mostrará más estadísticas en futuras versiones.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("« Volver", callback_data="menu:main")
        ]]),
        parse_mode=ParseMode.HTML
    )

@breadcrumb
async def whoami_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador para el comando /whoami que muestra información del usuario."""
    user = update.effective_user
    logger.info(f"Usuario {user.id} ha solicitado su información")
    
    # Verificar si el usuario está registrado
    from models.user import User
    db_user = User.get_by_telegram_id(user.id)
    
    if not db_user:
        await update.message.reply_html(
            f"<b>No estás registrado en el sistema.</b>\n\n"
            f"Utiliza el comando /register para registrarte."
        )
        return
    
    # Mostrar información del usuario
    role_text = "👑 Administrador" if db_user.role == "admin" else "👤 Usuario normal"
    status_text = "✅ Activo" if db_user.status == "active" else "❌ No activo"
    
    await update.message.reply_html(
        f"<b>Tu información de usuario:</b>\n\n"
        f"ID: {user.id}\n"
        f"Nombre: {db_user.name}\n"
        f"Rol: {role_text}\n"
        f"Estado: {status_text}\n"
        f"Fecha registro: {db_user.created_at if hasattr(db_user, 'created_at') else 'N/A'}"
    )

@breadcrumb
async def handle_custom_placeholder_configuration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador para procesar la configuración de placeholders personalizados."""
    user = update.effective_user
    text = update.message.text
    
    from core.states import state_manager, State
    from models.site import Site
    from models.user import User
    
    db_user = User.get_by_telegram_id(user.id)
    if not db_user:
        await update.message.reply_text("❌ Error: Usuario no encontrado. Por favor, reinicia el bot con /start.")
        return
    
    # Obtener el sitio del usuario
    sites = Site.get_by_user_id(db_user.id)
    site = sites[0] if sites else None
    
    if not site:
        await update.message.reply_text(
            "❌ Error: Primero debes configurar tu sitio. Usa /settings para hacerlo."
        )
        state_manager.set_state(user.id, State.IDLE)
        return
    
    # Obtener datos del estado
    placeholder = state_manager.get_data(user.id, "configuring_placeholder")
    config_step = state_manager.get_data(user.id, "placeholder_config_step")
    
    # Eliminar llaves para guardar el nombre del placeholder
    placeholder_name = placeholder
    if placeholder_name.startswith("{{") and placeholder_name.endswith("}}"):
        placeholder_name = placeholder_name[2:-2]
    
    # Procesar según el paso actual
    if config_step == "display_name":
        # Guardar el nombre para mostrar y solicitar el tipo
        state_manager.set_data(user.id, "display_name", text)
        state_manager.set_data(user.id, "placeholder_config_step", "placeholder_type")
        
        # Mostrar opciones de tipo
        keyboard = [
            [InlineKeyboardButton("Texto", callback_data="placeholder:type:texto")],
            [InlineKeyboardButton("Número", callback_data="placeholder:type:numero")],
            [InlineKeyboardButton("URL", callback_data="placeholder:type:url")],
            [InlineKeyboardButton("Desplegable", callback_data="placeholder:type:desplegable")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="placeholder:cancel")]
        ]
        
        await update.message.reply_text(
            f"✅ Nombre guardado: <b>{text}</b>\n\n"
            f"Ahora, selecciona el tipo de dato para <b>{placeholder}</b>:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif config_step == "options":
        # Procesar opciones para tipo desplegable
        options = text.strip()
        
        if not options:
            await update.message.reply_text(
                "⚠️ Por favor, introduce al menos una opción para el desplegable.\n\n"
                "Las opciones deben estar separadas por comas. Ejemplo: Opción 1, Opción 2, Opción 3"
            )
            return
        
        # Guardar las opciones y crear el placeholder
        display_name = state_manager.get_data(user.id, "display_name")
        placeholder_type = state_manager.get_data(user.id, "placeholder_type")
        
        # Acumular la configuración del placeholder en lugar de crearlo
        placeholder_configs = state_manager.get_data(user.id, "placeholder_configs") or []
        placeholder_configs.append({
            "placeholder_name": placeholder_name,
            "display_name": display_name,
            "placeholder_type": placeholder_type,
            "options": options
        })
        state_manager.set_data(user.id, "placeholder_configs", placeholder_configs)
        
        await update.message.reply_text(
            f"✅ <b>Placeholder configurado correctamente</b>\n\n"
            f"• <b>Placeholder:</b> {placeholder}\n"
            f"• <b>Nombre:</b> {display_name}\n"
            f"• <b>Tipo:</b> {placeholder_type}\n"
            f"• <b>Opciones:</b> {options}\n\n"
            f"El placeholder se aplicará cuando se complete la configuración.",
            parse_mode=ParseMode.HTML
        )
        
        # Avanzar al siguiente placeholder
        current_index = state_manager.get_data(user.id, "current_placeholder_index")
        state_manager.set_data(user.id, "current_placeholder_index", current_index + 1)
        
        # Iniciar configuración del siguiente placeholder
        await configure_next_custom_placeholder(update, context) 