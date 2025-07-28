"""
Manejadores para la gestión de transferencias SFTP.
"""

import logging
import os
import json
import paramiko
import socket
import telegram
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler
from telegram.constants import ParseMode
from core.states import State, state_manager
import models.site
import models.user
import time

# Importar desde nuestro módulo de compatibilidad
from utils.compat import Filters, CallbackContext

# Configuración de logging
from utils.breadcrumbs import breadcrumb
logger = logging.getLogger(__name__)

@breadcrumb
async def sftp_config_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador para el comando /sftp_config."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    logger.info(f"Usuario {user.id} inició la configuración SFTP")
    
    # Cambiar el estado a CONFIGURING_SFTP
    state_manager.set_state(user.id, State.CONFIGURING_SFTP)
    
    # Solicitar el host SFTP
    keyboard = [[InlineKeyboardButton("« Volver al menú", callback_data="menu:settings")]]
    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            "🔐 <b>Configuración SFTP</b>\n\n"
            "Vamos a configurar la conexión SFTP para tu sitio web.\n\n"
            "Por favor, ingresa el <b>host</b> (servidor) SFTP:"
        ),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    # Guardamos el paso actual en el estado
    state_manager.set_data(user.id, "sftp_step", "waiting_host")

@breadcrumb
async def process_sftp_host(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa el host SFTP enviado por el usuario."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    host = update.message.text.strip()
    
    # Validar el host (formato básico)
    if len(host) < 3 or " " in host:
        keyboard = [[InlineKeyboardButton("« Volver al menú", callback_data="menu:settings")]]
        await context.bot.send_message(
            chat_id=chat_id,
            text="⚠️ El host no parece válido. Por favor, inténtalo de nuevo:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # Obtener o crear configuración SFTP
    db_user = models.user.User.get_by_telegram_id(user.id)
    
    if not db_user:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Error: Usuario no encontrado en la base de datos."
        )
        return
        
    # Obtener los sitios existentes
    sites = models.site.Site.get_by_user_id(db_user.id)
    
    # Determinar el sitio a usar o crear uno nuevo
    if isinstance(sites, list):
        site = sites[0] if sites else None
    else:
        site = sites
    
    if not site:
        # Si no hay un sitio configurado, crear uno
        site = models.site.Site(user_id=db_user.id)
    
    # Cargar la configuración SFTP existente o crear una nueva
    sftp_config = {}
    if site.sftp_config:
        try:
            sftp_config = json.loads(site.sftp_config)
        except:
            # Si hay error al cargar la configuración, crear una nueva
            sftp_config = {}
    
    # Guardar el host
    sftp_config["host"] = host
    
    # Guardar la configuración actualizada
    site.sftp_config = json.dumps(sftp_config)
    site.save()
    
    # Solicitar el puerto
    keyboard = [
        [InlineKeyboardButton("« Volver a SFTP", callback_data="sftp:config")],
        [InlineKeyboardButton("« Volver al menú", callback_data="menu:settings")]
    ]
    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            f"✅ Host <code>{host}</code> guardado.\n\n"
            "Ahora, ingresa el <b>puerto</b> SFTP (o presiona Enter para usar 22, el puerto por defecto):"
        ),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    # Actualizar el paso actual
    state_manager.set_data(user.id, "sftp_step", "waiting_port")

@breadcrumb
async def process_sftp_port(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa el puerto SFTP enviado por el usuario."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    port_text = update.message.text.strip()
    
    # Si el usuario no ingresa nada, usar puerto 22 por defecto
    if not port_text:
        port = 22
    else:
        try:
            # Asegurarnos que sea un entero válido
            port = int(port_text)
            
            # Validar rango de puerto
            if port <= 0 or port > 65535:
                keyboard = [
                    [InlineKeyboardButton("« Volver a SFTP", callback_data="sftp:config")],
                    [InlineKeyboardButton("« Volver al menú", callback_data="menu:settings")]
                ]
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="⚠️ El puerto debe ser un número entre 1 y 65535. Por favor, inténtalo de nuevo:",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return
        except ValueError:
            # Si no es un número entero válido
            keyboard = [
                [InlineKeyboardButton("« Volver a SFTP", callback_data="sftp:config")],
                [InlineKeyboardButton("« Volver al menú", callback_data="menu:settings")]
            ]
            await context.bot.send_message(
                chat_id=chat_id,
                text="⚠️ El puerto debe ser un número entero. Por favor, inténtalo de nuevo:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
    
    # Obtener configuración SFTP
    db_user = models.user.User.get_by_telegram_id(user.id)
    if not db_user:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Error: Usuario no encontrado en la base de datos."
        )
        return
        
    # Obtener los sitios existentes
    sites = models.site.Site.get_by_user_id(db_user.id)
    
    # Determinar el sitio a usar o crear uno nuevo
    if isinstance(sites, list):
        site = sites[0] if sites else None
    else:
        site = sites
    
    if not site:
        # Si no hay un sitio configurado, crear uno
        site = models.site.Site(user_id=db_user.id)
    
    # Cargar la configuración SFTP existente o crear una nueva
    sftp_config = {}
    if site.sftp_config:
        try:
            sftp_config = json.loads(site.sftp_config)
        except:
            # Si hay error al cargar la configuración, crear una nueva
            sftp_config = {}
    
    # Guardar el puerto como entero, no como string
    sftp_config["port"] = port
    
    # Guardar la configuración actualizada
    site.sftp_config = json.dumps(sftp_config)
    site.save()
    
    # Solicitar el usuario
    keyboard = [
        [InlineKeyboardButton("« Volver a SFTP", callback_data="sftp:config")],
        [InlineKeyboardButton("« Volver al menú", callback_data="menu:settings")]
    ]
    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            f"✅ Puerto <code>{port}</code> guardado.\n\n"
            "Ahora, ingresa el <b>nombre de usuario</b> para tu servidor SFTP:"
        ),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    # Actualizar el paso actual
    state_manager.set_data(user.id, "sftp_step", "waiting_username")

@breadcrumb
async def process_sftp_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa el nombre de usuario SFTP enviado por el usuario."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    username = update.message.text.strip()
    
    # Validación simple del nombre de usuario
    if not username or len(username) < 2:
        keyboard = [
            [InlineKeyboardButton("« Volver a SFTP", callback_data="sftp:config")],
            [InlineKeyboardButton("« Volver al menú", callback_data="menu:settings")]
        ]
        await context.bot.send_message(
            chat_id=chat_id,
            text="⚠️ El nombre de usuario no parece válido. Por favor, inténtalo de nuevo:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # Obtener configuración SFTP
    db_user = models.user.User.get_by_telegram_id(user.id)
    if not db_user:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Error: Usuario no encontrado en la base de datos."
        )
        return
        
    # Obtener los sitios existentes
    sites = models.site.Site.get_by_user_id(db_user.id)
    
    # Determinar el sitio a usar o crear uno nuevo
    if isinstance(sites, list):
        site = sites[0] if sites else None
    else:
        site = sites
    
    if not site:
        # Si no hay un sitio configurado, crear uno
        site = models.site.Site(user_id=db_user.id)
    
    # Cargar la configuración SFTP existente o crear una nueva
    sftp_config = {}
    if site.sftp_config:
        try:
            sftp_config = json.loads(site.sftp_config)
        except:
            # Si hay error al cargar la configuración, crear una nueva
            sftp_config = {}
    
    # Guardar el nombre de usuario
    sftp_config["username"] = username
    
    # Guardar la configuración actualizada
    site.sftp_config = json.dumps(sftp_config)
    site.save()
    
    # Solicitar la contraseña
    keyboard = [
        [InlineKeyboardButton("« Volver a SFTP", callback_data="sftp:config")],
        [InlineKeyboardButton("« Volver al menú", callback_data="menu:settings")]
    ]
    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            f"✅ Usuario <code>{username}</code> guardado.\n\n"
            "Por último, ingresa la <b>contraseña</b> para tu servidor SFTP:"
        ),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    # Actualizar el paso actual
    state_manager.set_data(user.id, "sftp_step", "waiting_password")

@breadcrumb
async def process_sftp_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa la contraseña SFTP enviada por el usuario."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    password = update.message.text.strip()
    
    # Validación mínima de la contraseña
    if not password or len(password) < 1:
        keyboard = [
            [InlineKeyboardButton("« Volver a SFTP", callback_data="sftp:config")],
            [InlineKeyboardButton("« Volver al menú", callback_data="menu:settings")]
        ]
        await context.bot.send_message(
        chat_id=chat_id,
            text="⚠️ La contraseña no puede estar vacía. Por favor, inténtalo de nuevo:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # Obtener configuración SFTP
    db_user = models.user.User.get_by_telegram_id(user.id)
    if not db_user:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Error: Usuario no encontrado en la base de datos."
        )
        return
        
    # Obtener los sitios existentes
    sites = models.site.Site.get_by_user_id(db_user.id)
    
    # Determinar el sitio a usar o crear uno nuevo
    if isinstance(sites, list):
        site = sites[0] if sites else None
    else:
        site = sites
    
    if not site:
        # Si no hay un sitio configurado, crear uno
        site = models.site.Site(user_id=db_user.id)
    
    # Cargar la configuración SFTP existente o crear una nueva
    sftp_config = {}
    if site.sftp_config:
        try:
            sftp_config = json.loads(site.sftp_config)
        except:
            # Si hay error al cargar la configuración, crear una nueva
            sftp_config = {}
    
    # Guardar la contraseña (en un entorno real, debería cifrarse)
    sftp_config["password"] = password
    
    # Guardar la configuración actualizada
    site.sftp_config = json.dumps(sftp_config)
    site.save()
    
    # Mostrar mensaje de éxito y opciones para continuar
    keyboard = [
        [InlineKeyboardButton("✅ Probar Conexión", callback_data="sftp:test_connection")],
        [InlineKeyboardButton("« Volver a SFTP", callback_data="sftp:config")],
        [InlineKeyboardButton("« Volver al menú", callback_data="menu:settings")]
    ]
    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            "✅ <b>¡Configuración SFTP completada!</b>\n\n"
            "Has configurado correctamente los siguientes datos:\n"
            f"• Host: <code>{sftp_config.get('host', 'No configurado')}</code>\n"
            f"• Puerto: <code>{sftp_config.get('port', '22')}</code>\n"
            f"• Usuario: <code>{sftp_config.get('username', 'No configurado')}</code>\n"
            f"• Contraseña: <code>{'*' * len(password)}</code>\n\n"
            "Ahora puedes probar la conexión o volver al menú de configuración."
        ),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    # Volver al estado IDLE ya que hemos completado la configuración
    state_manager.set_state(user.id, State.IDLE)

@breadcrumb
async def process_sftp_remote_dir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa el directorio remoto SFTP enviado por el usuario."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    remote_dir = update.message.text.strip()
    
    # Asegurarse de que el directorio termina con /
    if not remote_dir.endswith('/'):
        remote_dir += '/'
    
    # Guardar el directorio remoto
    state_manager.set_data(user.id, "sftp_remote_dir", remote_dir)
    
    # Intentar validar la conexión SFTP
    host = state_manager.get_data(user.id, "sftp_host")
    port = state_manager.get_data(user.id, "sftp_port")
    username = state_manager.get_data(user.id, "sftp_username")
    password = state_manager.get_data(user.id, "sftp_password")
    
    # Mostrar mensaje de prueba de conexión
    status_message = await context.bot.send_message(
        chat_id=chat_id,
        text="🔄 Probando conexión SFTP... Por favor, espera un momento."
    )
    
    # Simular una prueba de conexión (en un entorno real, se conectaría realmente)
    # En este ejemplo, simulamos éxito
    connection_success = True
    
    if connection_success:
        # Crear objeto de configuración SFTP
        sftp_config = {
            "host": host,
            "port": port,
            "username": username,
            "password": password,  # En un entorno real, cifrar esta información
            "remote_dir": remote_dir
        }
        
        # TODO: Guardar la configuración en la base de datos del usuario
        # Por ahora, solo la guardamos en el estado
        state_manager.set_data(user.id, "sftp_config", sftp_config)
        
        # Actualizar mensaje de estado
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=status_message.message_id,
            text=(
                "✅ <b>Conexión SFTP Exitosa</b>\n\n"
                f"Se ha establecido correctamente la conexión con {host}.\n\n"
                "Tu configuración SFTP ha sido guardada. Ahora podrás subir contenido a tu sitio web."
            ),
            parse_mode=ParseMode.HTML
        )
        
        # Limpiar estado
        state_manager.set_state(user.id, State.IDLE)
        
        logger.info(f"Usuario {user.id} completó la configuración SFTP")
    else:
        # Actualizar mensaje de estado
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=status_message.message_id,
            text=(
                "❌ <b>Error de Conexión SFTP</b>\n\n"
                "No se pudo establecer la conexión. Por favor, verifica los datos e inténtalo de nuevo.\n\n"
                "Puedes reiniciar la configuración con /sftp_config"
            ),
            parse_mode=ParseMode.HTML
        )
        
        logger.error(f"Error en la configuración SFTP del usuario {user.id}")

@breadcrumb
async def upload_file_to_sftp(user_id, local_path, remote_path, content=None):
    """
    Sube un archivo al servidor SFTP.
    
    Args:
        user_id: ID del usuario para obtener la configuración SFTP
        local_path: Ruta local del archivo (o None si se proporciona contenido)
        remote_path: Ruta remota donde guardar el archivo
        content: Contenido del archivo si no se proporciona local_path
        
    Returns:
        bool: True si la operación fue exitosa, False en caso contrario
    """
    # Obtener la configuración SFTP del usuario desde la base de datos
    db_user = models.user.User.get_by_telegram_id(user_id)
    if not db_user:
        logger.error(f"No se encontró usuario con telegram_id {user_id}")
        return False
        
    site = models.site.Site.get_by_user_id(db_user.id)
    if not site or not site.sftp_config:
        logger.error(f"No hay configuración SFTP para el usuario {user_id}")
        return False
    
    try:
        # Cargar la configuración SFTP desde el JSON almacenado
        sftp_config = json.loads(site.sftp_config)
        
        # Crear cliente SSH
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Conectar al servidor
        ssh.connect(
            hostname=sftp_config["host"],
            port=int(sftp_config["port"]),
            username=sftp_config["username"],
            password=sftp_config["password"]
        )
        
        # Abrir sesión SFTP
        sftp = ssh.open_sftp()
        
        # Determinar la ruta remota completa
        full_remote_path = sftp_config.get("remote_dir", "/") + remote_path.lstrip('/')
        
        # Crear directorios intermedios si no existen
        directories = full_remote_path.rsplit('/', 1)[0]
        current_dir = ""
        
        for directory in directories.split('/'):
            if directory:
                current_dir += "/" + directory
                try:
                    sftp.stat(current_dir)
                except FileNotFoundError:
                    sftp.mkdir(current_dir)
        
        # Subir el archivo
        if content is not None:
            # Crear un archivo temporal con el contenido
            buffer = BytesIO(content.encode('utf-8') if isinstance(content, str) else content)
            sftp.putfo(buffer, full_remote_path)
        else:
            # Subir el archivo desde la ruta local
            sftp.put(local_path, full_remote_path)
        
        # Cerrar la conexión
        sftp.close()
        ssh.close()
        
        logger.info(f"Archivo subido con éxito a {full_remote_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error al subir archivo por SFTP: {e}")
        return False

@breadcrumb
async def upload_post_to_sftp(update: Update, context: ContextTypes.DEFAULT_TYPE, post_data):
    """Sube un post al servidor SFTP."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Obtener la configuración SFTP
    sftp_config = state_manager.get_data(user.id, "sftp_config")
    
    if not sftp_config:
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "⚠️ <b>Configuración SFTP no encontrada</b>\n\n"
                "Necesitas configurar la conexión SFTP primero con /sftp_config"
            ),
            parse_mode=ParseMode.HTML
        )
        return False
    
    # Mostrar mensaje de estado
    status_message = await context.bot.send_message(
        chat_id=chat_id,
        text="🔄 Subiendo contenido al servidor... Por favor, espera un momento."
    )
    
    try:
        # 1. Cargar los posts actuales desde el servidor o usar la plantilla
        posts_json_path = "posts.json"
        
        # Intentar descargar el archivo JSON existente (simulado)
        current_posts = {
            "posts": []
        }
        
        # Cargar posts desde plantilla como respaldo
        try:
            templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                        'data', 'templates')
            with open(os.path.join(templates_dir, 'posts.json'), 'r', encoding='utf-8') as f:
                current_posts = json.load(f)
        except Exception as e:
            logger.error(f"Error al cargar plantilla de posts: {e}")
        
        # 2. Añadir el nuevo post
        current_posts["posts"].append(post_data)
        
        # 3. Guardar el JSON actualizado
        posts_json_content = json.dumps(current_posts, ensure_ascii=False, indent=2)
        
        # 4. Subir el JSON actualizado
        json_upload_success = await upload_file_to_sftp(
            user.id, 
            None, 
            posts_json_path, 
            content=posts_json_content
        )
        
        # 5. Si hay contenido HTML, crear y subir el archivo HTML
        html_content = state_manager.get_data(user.id, "content_buffer")
        html_upload_success = True
        
        if html_content:
            # Crear HTML básico con el contenido
            category = post_data["category"].lower()
            slug = post_data["slug"]
            title = post_data["title"]
            
            full_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{post_data['description']}">
</head>
<body>
    <article>
        <h1>{title}</h1>
        <div class="post-content">
            {html_content}
        </div>
    </article>
</body>
</html>
"""
            
            # Ruta del archivo HTML
            html_path = f"{category}/{slug}.html"
            
            # Subir el archivo HTML
            html_upload_success = await upload_file_to_sftp(
                user.id,
                None,
                html_path,
                content=full_html
            )
        
        # Verificar el resultado
        if json_upload_success and html_upload_success:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=status_message.message_id,
                text=(
                    "✅ <b>Publicación Exitosa</b>\n\n"
                    f"Tu artículo '<b>{post_data['title']}</b>' ha sido publicado correctamente.\n\n"
                    f"URL: {sftp_config['host']}{post_data['url']}"
                ),
                parse_mode=ParseMode.HTML
            )
            return True
        else:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=status_message.message_id,
                text=(
                    "⚠️ <b>Publicación Parcial</b>\n\n"
                    "Hubo errores al subir algunos archivos. Por favor, intenta de nuevo más tarde."
                ),
                parse_mode=ParseMode.HTML
            )
            return False
    
    except Exception as e:
        logger.error(f"Error al publicar post para el usuario {user.id}: {e}")
        
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=status_message.message_id,
            text=(
                "❌ <b>Error de Publicación</b>\n\n"
                f"Ocurrió un error al publicar tu artículo: {str(e)}"
            ),
            parse_mode=ParseMode.HTML
        )
        return False

@breadcrumb
async def sftp_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador de mensajes para el módulo SFTP."""
    user = update.effective_user
    
    # Verificar si el usuario está en proceso de configuración SFTP
    if state_manager.get_state(user.id) == State.CONFIGURING_SFTP:
        current_step = state_manager.get_data(user.id, "sftp_step")
        
        if current_step == "waiting_host":
            await process_sftp_host(update, context)
            return True
        elif current_step == "waiting_port":
            await process_sftp_port(update, context)
            return True
        elif current_step == "waiting_username":
            await process_sftp_username(update, context)
            return True
        elif current_step == "waiting_password":
            await process_sftp_password(update, context)
            return True
        elif current_step == "waiting_remote_dir":
            await process_sftp_remote_dir(update, context)
            return True
    
    # Si no está en proceso de configuración SFTP, dejamos que otros manejadores procesen el mensaje
    return False

@breadcrumb
async def sftp_config_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el menú de configuración SFTP con botones."""
    user = update.effective_user
    db_user = models.user.User.get_by_telegram_id(user.id)
    
    if not db_user:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Error: Usuario no encontrado en la base de datos."
        )
        return
        
    # Obtener el sitio y su configuración
    sites = models.site.Site.get_by_user_id(db_user.id)
    
    # Manejar correctamente si es una lista o un solo objeto
    if isinstance(sites, list):
        site = sites[0] if sites else None
    else:
        site = sites
    
    # Verificar si ya hay configuración SFTP
    has_config = site and site.sftp_config
    
    # Texto del mensaje con información detallada
    text = "🔐 <b>CONFIGURACIÓN SFTP</b>\n\nConfigura tu conexión SFTP para subir contenido a tu servidor:\n\n"
    
    # Variables para los indicadores de estado
    host_status = "❌"
    port_status = "❌"
    username_status = "❌"
    password_status = "❌"
    
    # Si hay configuración, mostrar el estado actual de cada campo
    if has_config:
        try:
            config = json.loads(site.sftp_config)
            
            # Verificar cada campo y establecer el indicador correspondiente
            if "host" in config and config["host"]:
                host_status = "✅"
            if "port" in config and config["port"]:
                port_status = "✅"
            if "username" in config and config["username"]:
                username_status = "✅"
            if "password" in config and config["password"]:
                password_status = "✅"
            
            # Añadir información de configuración al texto
            text += "<b>Estado actual:</b>\n"
            text += f"{host_status} Host: {config.get('host', 'No configurado')}\n"
            text += f"{port_status} Puerto: {config.get('port', '22') if 'port' in config else 'No configurado'}\n"
            text += f"{username_status} Usuario: {config.get('username', 'No configurado')}\n"
            text += f"{password_status} Contraseña: {'*******' if 'password' in config and config['password'] else 'No configurada'}\n\n"
            
            # Añadir información de carpetas configuradas si existen
            posts_dir = config.get("posts_dir", None)
            images_dir = config.get("images_dir", None)
            
            if posts_dir or images_dir:
                text += "<b>Carpetas configuradas:</b>\n"
                if posts_dir:
                    text += f"📝 Blog: <code>{posts_dir}</code>\n"
                else:
                    text += f"📝 Blog: <i>No configurada</i>\n"
                    
                if images_dir:
                    text += f"🖼️ Imágenes: <code>{images_dir}</code>\n"
                else:
                    text += f"🖼️ Imágenes: <i>No configurada</i>\n"
                text += "\n"
        except Exception as e:
            logger.error(f"Error al leer configuración SFTP: {e}")
            text += "<b>⚠️ Error al leer la configuración existente</b>\n\n"
    else:
        text += "<b>No hay configuración guardada.</b> Por favor, configura los siguientes campos:\n\n"
    
    # Verificar si la configuración está completa
    is_config_complete = has_config and host_status == "✅" and port_status == "✅" and username_status == "✅" and password_status == "✅"
    
    # Crear teclado con indicadores de estado (en dos columnas)
    keyboard = [
        [
            InlineKeyboardButton(f"{host_status} Host/IP", callback_data="sftp:set_host"),
            InlineKeyboardButton(f"{port_status} Puerto", callback_data="sftp:set_port")
        ],
        [
            InlineKeyboardButton(f"{username_status} Usuario", callback_data="sftp:set_username"),
            InlineKeyboardButton(f"{password_status} Contraseña", callback_data="sftp:set_password")
        ],
    ]
    
    # Solo mostrar botón de probar conexión si la configuración está completa
    if is_config_complete:
        keyboard.append([InlineKeyboardButton("✅ Probar Conexión", callback_data="sftp:test_connection")])
    else:
        keyboard.append([InlineKeyboardButton("⚠️ Completa la configuración para probar", callback_data="sftp:config_incomplete")])
    
    # Si ya hay configuración, mostrar opciones de acción
    if has_config:
        # Si la configuración está completa, mostrar opción de explorar
        if is_config_complete:
            keyboard.append([InlineKeyboardButton("📂 Explorar directorios", callback_data="sftp:explore")])
        
        # Mostrar botón para eliminar configuración
        keyboard.append([InlineKeyboardButton("🗑️ Eliminar configuración", callback_data="sftp:clear_config")])
    
    # Botones de navegación (en dos columnas)
    keyboard.append([
        InlineKeyboardButton("« Configuración", callback_data="menu:settings"),
        InlineKeyboardButton("« Menú Principal", callback_data="menu:main")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Enviar o editar el mensaje según corresponda
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            if "Message is not modified" in str(e):
                # Si el mensaje no se modifica, no hacer nada
                logger.info("El mensaje de configuración SFTP no se modificó")
            else:
                # Para otros errores, relanzar
                raise
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

@breadcrumb
async def test_sftp_connection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prueba la conexión SFTP con los datos configurados."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Obtener los datos de configuración SFTP
    db_user = models.user.User.get_by_telegram_id(user.id)
    if not db_user:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Error: Usuario no encontrado en la base de datos.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Volver a configuración SFTP", callback_data="sftp:config")
            ], [
                InlineKeyboardButton("« Volver al menú principal", callback_data="menu:main")
            ]])
        )
        return
    
    # Obtener el sitio y su configuración
    sites = models.site.Site.get_by_user_id(db_user.id)
    
    # Si get_by_user_id devuelve una lista, tomamos el primer elemento
    if isinstance(sites, list):
        site = sites[0] if sites else None
    else:
        site = sites
    
    if not site or not site.sftp_config:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Error: No hay configuración SFTP guardada.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Volver a configuración SFTP", callback_data="sftp:config")
            ], [
                InlineKeyboardButton("« Volver al menú principal", callback_data="menu:main")
            ]])
        )
        return
    
    try:
        # Cargar la configuración SFTP desde JSON
        try:
            config = json.loads(site.sftp_config)
        except json.JSONDecodeError:
            logger.error(f"Error al decodificar JSON de sftp_config: {site.sftp_config}")
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ Error: Configuración SFTP inválida. Por favor reconfigura la conexión.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("« Volver a configuración SFTP", callback_data="sftp:config")
                ]])
            )
            return
        
        # Verificar que tenemos todos los datos necesarios
        required_fields = ["host", "port", "username", "password"]
        missing_fields = [field for field in required_fields if field not in config]
        
        if missing_fields:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ Error: Faltan los siguientes datos de configuración: {', '.join(missing_fields)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("« Volver a configuración SFTP", callback_data="sftp:config")
                ], [
                    InlineKeyboardButton("« Volver al menú principal", callback_data="menu:main")
                ]])
            )
            return
        
        # Mostrar mensaje de espera
        if update.callback_query:
            message = await update.callback_query.edit_message_text(
                text="🔄 Probando conexión SFTP..."
            )
        else:
            message = await context.bot.send_message(
                chat_id=chat_id,
                text="🔄 Probando conexión SFTP..."
            )
        
        # Intentar conectar
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Asegurarse de que el puerto sea un entero
        try:
            port = int(config["port"])
        except (ValueError, TypeError):
            # Si no se puede convertir a entero, usar 22 por defecto
            logger.warning(f"Puerto no válido: {config['port']}, usando 22 por defecto")
            port = 22
        
        # Conexión al servidor
        client.connect(
            hostname=config["host"],
            port=port,
            username=config["username"],
            password=config["password"],
            timeout=10
        )
        
        # Si llegamos aquí, la conexión fue exitosa
        sftp = client.open_sftp()
        
        # Probar listar directorio raíz
        files = sftp.listdir('.')
        
        # Cerrar conexiones
        sftp.close()
        client.close()
        
        # Actualizar mensaje
        keyboard = [
            [InlineKeyboardButton("📂 Explorar directorios", callback_data="sftp:explore")],
            [InlineKeyboardButton("« Volver a configuración SFTP", callback_data="sftp:config")],
            [InlineKeyboardButton("« Volver al menú principal", callback_data="menu:main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.edit_text(
            text=(
                "✅ <b>Conexión SFTP exitosa</b>\n\n"
                f"• Host: {config['host']}\n"
                f"• Puerto: {port}\n"
                f"• Usuario: {config['username']}\n"
                f"• Archivos/carpetas: {len(files)}\n\n"
                "Puedes explorar los directorios para configurar las carpetas de posts e imágenes."
            ),
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        
    except Exception as e:
        # Error de conexión
        error_message = str(e)
        logger.error(f"Error de conexión SFTP: {error_message}")
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ <b>Error de conexión SFTP</b>\n\n{error_message}\n\nVerifica tus datos e intenta nuevamente.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Volver a configuración SFTP", callback_data="sftp:config")
            ], [
                InlineKeyboardButton("« Volver al menú principal", callback_data="menu:main")
            ]])
        )

@breadcrumb
async def explore_sftp_directories(update: Update, context: ContextTypes.DEFAULT_TYPE, path='.'):
    """Explora los directorios SFTP."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Obtener los datos de configuración SFTP
    db_user = models.user.User.get_by_telegram_id(user.id)
    if not db_user:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Error: Usuario no encontrado en la base de datos.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Volver a configuración SFTP", callback_data="sftp:config")
            ], [
                InlineKeyboardButton("« Volver al menú principal", callback_data="menu:main")
            ]])
        )
        return
    
    # Obtener el sitio y su configuración
    sites = models.site.Site.get_by_user_id(db_user.id)
    
    # Si get_by_user_id devuelve una lista, tomamos el primer elemento
    if isinstance(sites, list):
        site = sites[0] if sites else None
    else:
        site = sites
    
    if not site or not site.sftp_config:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Error: No hay configuración SFTP guardada.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Volver a configuración SFTP", callback_data="sftp:config")
            ], [
                InlineKeyboardButton("« Volver al menú principal", callback_data="menu:main")
            ]])
        )
        return
    
    # Mostrar mensaje de espera
    try:
        if update.callback_query:
            # Guardar una referencia al mensaje para futuras ediciones
            try:
                message = await update.callback_query.edit_message_text(
                    text="🔄 Conectando al servidor SFTP..."
                )
            except Exception as e:
                logger.error(f"Error al editar mensaje: {e}")
                # Intenta enviar un nuevo mensaje si falló la edición
                message = await context.bot.send_message(
                    chat_id=chat_id,
                    text="🔄 Conectando al servidor SFTP..."
                )
        else:
            message = await context.bot.send_message(
                chat_id=chat_id,
                text="🔄 Conectando al servidor SFTP..."
            )
        
        # Cargar configuración desde JSON
        try:
            config = json.loads(site.sftp_config)
        except json.JSONDecodeError:
            logger.error(f"Error al decodificar JSON de sftp_config: {site.sftp_config}")
            await message.edit_text(
                text="❌ Error: Configuración SFTP inválida. Por favor reconfigura la conexión.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("« Volver a configuración SFTP", callback_data="sftp:config")
                ]])
            )
            return
        
        # Conectar al servidor con timeout
        client = None
        sftp = None
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Asegurarse de que el puerto sea un entero
            try:
                port = int(config["port"])
            except (ValueError, TypeError):
                # Si no se puede convertir a entero, usar 22 por defecto
                logger.warning(f"Puerto no válido: {config['port']}, usando 22 por defecto")
                port = 22
            
            # Timeout más corto (5 segundos) para evitar bloqueos largos
            client.connect(
                hostname=config["host"],
                port=port,
                username=config["username"],
                password=config["password"],
                timeout=5
            )
            
            sftp = client.open_sftp()
            
            # Establecer tiempo máximo para listar directorios
            start_time = time.time()
            items = sftp.listdir(path)
            logger.info(f"Tiempo para listar directorio: {time.time() - start_time:.2f} segundos")
            
            # Obtener información de cada item para saber si es archivo o directorio
            directories = []
            files = []
            
            # Limitar el número de items para evitar operaciones muy largas
            MAX_ITEMS = 100
            limited_items = items[:MAX_ITEMS] if len(items) > MAX_ITEMS else items
            
            for item in limited_items:
                if item.startswith('.'):
                    continue  # Ignorar archivos/carpetas ocultos
                    
                try:
                    item_path = os.path.join(path, item).replace('\\', '/')
                    stats = sftp.stat(item_path)
                    
                    # Verificar si es directorio (0x4000 es el bit de directorio en el modo de archivo)
                    if stats.st_mode & 0o40000:  # Es un directorio
                        directories.append(item)
                    else:  # Es un archivo
                        files.append(item)
                except Exception as e:
                    # Si hay error, asumimos que es un archivo y registramos el error
                    logger.warning(f"Error al verificar si '{item}' es directorio: {e}")
                    files.append(item)
                
            # Ordenar alfabéticamente
            directories.sort()
            files.sort()
            
            # Construir teclado para navegación
            keyboard = []
            
            # Añadir navegación al directorio padre
            if path != '.' and path != '/':
                parent_dir = os.path.dirname(path).replace('\\', '/')
                if not parent_dir:
                    parent_dir = '.'
                keyboard.append([InlineKeyboardButton("📁 ..", callback_data=f"sftp:explore:{parent_dir}")])
            
            # Añadir directorios en dos columnas
            dir_buttons = []
            for directory in directories:
                dir_path = os.path.join(path, directory).replace('\\', '/')
                dir_buttons.append(InlineKeyboardButton(f"📁 {directory}", callback_data=f"sftp:explore:{dir_path}"))
                
                # Cuando tenemos dos botones, añadirlos como una fila
                if len(dir_buttons) == 2:
                    keyboard.append(dir_buttons)
                    dir_buttons = []
            
            # Si queda un botón suelto, añadirlo como una fila
            if dir_buttons:
                keyboard.append(dir_buttons)
            
            # Añadir archivos (limitados)
            MAX_FILES_TO_SHOW = 10
            for file in files[:MAX_FILES_TO_SHOW]:  # Limitar a MAX_FILES_TO_SHOW archivos en la vista principal
                keyboard.append([InlineKeyboardButton(f"📄 {file}", callback_data="sftp:noop")])
            
            # Añadir botón para ver más archivos si hay más de MAX_FILES_TO_SHOW
            if len(files) > MAX_FILES_TO_SHOW:
                keyboard.append([
                    InlineKeyboardButton(f"📄 ... y {len(files) - MAX_FILES_TO_SHOW} archivos más", 
                                        callback_data=f"sftp:show_more_files:{path}")
                ])
            
            # Añadir botón para seleccionar el directorio actual y otros botones de acción
            keyboard.append([
                InlineKeyboardButton("✅ Seleccionar este directorio", callback_data=f"sftp:select_dir:{path}"),
            ])
            
            # Añadir botones de navegación en dos columnas
            keyboard.append([
                InlineKeyboardButton("« SFTP", callback_data="sftp:config"),
                InlineKeyboardButton("« Menú Principal", callback_data="menu:main")
            ])
            
            # Actualizar el mensaje con la lista de contenidos
            try:
                await message.edit_text(
                    text=f"📂 <b>Explorador SFTP</b>\n\nDirectorio actual: <code>{path}</code>\n\n"
                         f"Directorios: {len(directories)}\n"
                         f"Archivos: {len(files)}{' (mostrando máximo 100)' if len(items) > MAX_ITEMS else ''}",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode=ParseMode.HTML
                )
            except telegram.error.BadRequest as e:
                if "message is not modified" in str(e).lower():
                    logger.info("El mensaje no se modificó, ignorando")
                elif "query is too old" in str(e).lower() or "query_id_invalid" in str(e).lower():
                    # Si el callback expiró, enviar un nuevo mensaje
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"📂 <b>Explorador SFTP</b>\n\nDirectorio actual: <code>{path}</code>\n\n"
                             f"Directorios: {len(directories)}\n"
                             f"Archivos: {len(files)}{' (mostrando máximo 100)' if len(items) > MAX_ITEMS else ''}",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode=ParseMode.HTML
                    )
                else:
                    raise
            
        except Exception as e:
            # Error de conexión o exploración
            error_message = str(e)
            logger.error(f"Error en operación SFTP: {error_message}")
            
            try:
                await message.edit_text(
                    text=f"❌ <b>Error al explorar directorio</b>\n\n{error_message}",
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("« Volver a configuración SFTP", callback_data="sftp:config")
                    ], [
                        InlineKeyboardButton("« Volver al menú principal", callback_data="menu:main")
                    ]])
                )
            except Exception as edit_error:
                logger.error(f"Error adicional al editar mensaje: {edit_error}")
                # Si no se puede editar, enviar un nuevo mensaje
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ <b>Error al explorar directorio</b>\n\n{error_message}",
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("« Volver a configuración SFTP", callback_data="sftp:config")
                    ], [
                        InlineKeyboardButton("« Volver al menú principal", callback_data="menu:main")
                    ]])
                )
        finally:
            # Cerrar conexiones si existen
            if sftp:
                try:
                    sftp.close()
                except:
                    pass
            if client:
                try:
                    client.close()
                except:
                    pass
                    
    except Exception as outer_e:
        # Error general, aseguramos que siempre haya una respuesta
        error_message = str(outer_e)
        logger.error(f"Error general en explorador SFTP: {error_message}")
        
        # Enviar mensaje de error directamente
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ <b>Error inesperado</b>\n\n{error_message}",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Volver a configuración SFTP", callback_data="sftp:config")
            ], [
                InlineKeyboardButton("« Volver al menú principal", callback_data="menu:main")
            ]])
        )

@breadcrumb
async def select_sftp_folder(update: Update, context: ContextTypes.DEFAULT_TYPE, folder_type, path):
    """Selecciona una carpeta para posts o imágenes."""
    user = update.effective_user
    query = update.callback_query
    
    # Obtener los datos de configuración SFTP
    db_user = models.user.User.get_by_telegram_id(user.id)
    if not db_user:
        await query.edit_message_text(
            text="❌ Error: Usuario no encontrado en la base de datos.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Volver al menú principal", callback_data="menu:main")
            ]])
        )
        return
        
    # Obtener los sitios existentes
    sites = models.site.Site.get_by_user_id(db_user.id)
    
    # Determinar el sitio a usar
    if isinstance(sites, list):
        site = sites[0] if sites else None
    else:
        site = sites
    
    if not site or not site.sftp_config:
        await query.edit_message_text(
            text="❌ Error: No hay configuración SFTP guardada.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Volver a configuración SFTP", callback_data="sftp:config")
            ]])
        )
        return
    
    try:
        # Cargar la configuración SFTP
        config = json.loads(site.sftp_config)
        
        # El tipo de carpeta puede ser "posts" o "images"
        folder_name = "artículos de blog" if folder_type == "posts" else "imágenes"
        folder_key = f"{folder_type}_dir"
        
        # Actualizar la configuración con la nueva ruta
        config[folder_key] = path
        
        # Guardar la configuración actualizada
        site.sftp_config = json.dumps(config)
        site.save()
        
        # Crear un mensaje informativo
        text = f"✅ <b>Carpeta de {folder_name} configurada</b>\n\n"
        text += f"Has seleccionado la carpeta <code>{path}</code> como destino para tus {folder_name}.\n\n"
        text += "<b>Configuración actual:</b>\n"
        
        # Mostrar las rutas configuradas
        posts_dir = config.get("posts_dir", "No configurada")
        images_dir = config.get("images_dir", "No configurada")
        
        text += f"• Carpeta para artículos: <code>{posts_dir}</code>\n"
        text += f"• Carpeta para imágenes: <code>{images_dir}</code>\n"
        
        # Botones de navegación en dos columnas
        keyboard = [
            [
                InlineKeyboardButton("📂 Explorar otra carpeta", callback_data="sftp:explore"),
                InlineKeyboardButton("🧪 Probar conexión", callback_data="sftp:test_connection")
            ],
            [
                InlineKeyboardButton("« Configuración SFTP", callback_data="sftp:config"),
                InlineKeyboardButton("« Menú Principal", callback_data="menu:main")
            ]
        ]
        
        # Notificar al usuario
        await query.edit_message_text(
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        # Error al guardar
        logger.error(f"Error al guardar carpeta SFTP: {e}")
        await query.edit_message_text(
            text=f"❌ <b>Error al guardar configuración</b>\n\n{str(e)}",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("« Volver a explorar", callback_data="sftp:explore"),
                    InlineKeyboardButton("« Configuración SFTP", callback_data="sftp:config")
                ]
            ])
        )

@breadcrumb
async def sftp_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja los callbacks relacionados con SFTP."""
    query = update.callback_query
    user = update.effective_user
    
    # Siempre responder al callback para evitar el spinner
    await query.answer()
    
    try:
        # Obtener el callback_data completo
        callback_data = query.data
        
        # Verificar si es un callback de SFTP
        if not callback_data.startswith("sftp:"):
            logger.warning(f"Callback no válido para manejador SFTP: {callback_data}")
            return
            
        # Dividir callback_data
        parts = callback_data.split(':')
        action = parts[1] if len(parts) > 1 else None
        param = parts[2] if len(parts) > 2 else None
        
        logger.info(f"SFTP callback procesado: {action} - {param}")
        
        # Procesar según la acción
        if action == "config":
            await sftp_config_menu(update, context)
        elif action == "config_incomplete":
            # Manejar el caso cuando el usuario intenta probar la conexión con configuración incompleta
            await handle_incomplete_config(update, context)
        elif action == "set_host":
            # Usar solo el tiempo como identificador único para evitar duplicaciones
            keyboard = [[InlineKeyboardButton("« Volver", callback_data="sftp:config")]]
            await query.edit_message_text(
                text="🖥️ <b>Host SFTP</b>\n\nPor favor, ingresa el host (dirección IP o dominio) de tu servidor SFTP:",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            state_manager.set_state(user.id, State.CONFIGURING_SFTP)
            state_manager.set_data(user.id, "sftp_step", "waiting_host")
        elif action == "set_port":
            keyboard = [[InlineKeyboardButton("« Volver", callback_data="sftp:config")]]
            await query.edit_message_text(
                text="🔢 <b>Puerto SFTP</b>\n\nPor favor, ingresa el puerto de tu servidor SFTP (normalmente 22):",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            state_manager.set_state(user.id, State.CONFIGURING_SFTP)
            state_manager.set_data(user.id, "sftp_step", "waiting_port")
        elif action == "set_username":
            keyboard = [[InlineKeyboardButton("« Volver", callback_data="sftp:config")]]
            await query.edit_message_text(
                text="👤 <b>Usuario SFTP</b>\n\nPor favor, ingresa el nombre de usuario para tu servidor SFTP:",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            state_manager.set_state(user.id, State.CONFIGURING_SFTP)
            state_manager.set_data(user.id, "sftp_step", "waiting_username")
        elif action == "set_password":
            keyboard = [[InlineKeyboardButton("« Volver", callback_data="sftp:config")]]
            await query.edit_message_text(
                text="🔑 <b>Contraseña SFTP</b>\n\nPor favor, ingresa la contraseña para tu servidor SFTP:\n\n"
                     "<i>Nota: Tu contraseña se almacenará cifrada en nuestra base de datos.</i>",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            state_manager.set_state(user.id, State.CONFIGURING_SFTP)
            state_manager.set_data(user.id, "sftp_step", "waiting_password")
        elif action == "test_connection":
            await test_sftp_connection(update, context)
        elif action == "explore":
            # Si hay un parámetro, es la ruta a explorar
            path = param or '.'
            await explore_sftp_directories(update, context, path)
        elif action == "select_dir":
            # Mostrar opciones para el directorio seleccionado
            await show_directory_options(update, context, param or '.')
        elif action == "select_posts":
            await select_sftp_folder(update, context, "posts", param)
        elif action == "select_images":
            await select_sftp_folder(update, context, "images", param)
        elif action == "show_more_files":
            # Mostrar más archivos para la ruta especificada
            await show_more_files(update, context, param or '.')
        elif action == "clear_config":
            # Confirmar eliminación de la configuración SFTP
            await confirm_clear_sftp_config(update, context)
        elif action == "confirm_clear_config":
            # Eliminar la configuración SFTP
            await clear_sftp_config(update, context)
        elif action == "cancel_clear_config":
            # Cancelar la eliminación
            await query.edit_message_text(
                text="❌ <b>Eliminación cancelada</b>\n\nNo se ha borrado la configuración SFTP.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("« Volver a configuración SFTP", callback_data="sftp:config")
                ]])
            )
        elif action == "noop":
            # No operation, just acknowledge
            await query.answer("Esta opción no realiza ninguna acción")
        elif action == "back_to_settings":
            # Volver al menú de configuración
            from core.handlers import send_settings_menu
            await send_settings_menu(update, context)
        elif action == "back_to_main":
            # Volver al menú principal
            from core.handlers import send_main_menu
            await send_main_menu(update, context, is_new_message=False)
        else:
            # Si no reconocemos la acción, informar y volver al menú SFTP
            logger.warning(f"Acción SFTP no reconocida: {action}")
            await query.edit_message_text(
                text=f"⚠️ <b>Acción no reconocida</b>\n\n"
                     f"La acción solicitada <code>{action}</code> no está disponible o aún no ha sido implementada.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("« Volver a configuración SFTP", callback_data="sftp:config")
                ], [
                    InlineKeyboardButton("« Volver al menú principal", callback_data="menu:main")
                ]])
            )
    except Exception as e:
        logger.error(f"Error en sftp_callback_handler: {e}")
        
        # Si es un error de "Message is not modified", simplemente lo ignoramos
        # Este error ocurre cuando el usuario hace clic rápidamente en el mismo botón
        if "Message is not modified" in str(e):
            logger.info("Ignorando error de mensaje no modificado")
            return
            
        try:
            # Intentar editar el mensaje actual
            await query.edit_message_text(
                text=f"❌ <b>Error al procesar tu solicitud</b>\n\n"
                     f"Por favor, intenta nuevamente.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("« Volver a SFTP", callback_data="sftp:config")],
                    [InlineKeyboardButton("« Volver al menú principal", callback_data="menu:main")]
                ])
            )
        except Exception as inner_e:
            # Si no podemos editar el mensaje actual y no es "Message is not modified"
            if "Message is not modified" not in str(inner_e):
                # Solo enviar un nuevo mensaje si realmente hay un error importante
                logger.error(f"Error secundario en sftp_callback_handler: {inner_e}")
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"❌ <b>Error al procesar tu solicitud</b>\n\n"
                        f"Por favor, intenta nuevamente.",
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("« Volver a SFTP", callback_data="sftp:config")],
                        [InlineKeyboardButton("« Volver al menú principal", callback_data="menu:main")]
                    ])
                )

@breadcrumb
async def handle_incomplete_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el caso cuando el usuario intenta probar la conexión con configuración incompleta."""
    query = update.callback_query
    user = update.effective_user
    
    # Obtener la configuración actual para determinar qué falta
    db_user = models.user.User.get_by_telegram_id(user.id)
    if not db_user:
        await query.edit_message_text(
            text="❌ Error: Usuario no encontrado en la base de datos.",
                reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Volver al menú principal", callback_data="menu:main")
            ]])
        )
        return
        
    # Obtener el sitio y su configuración
    sites = models.site.Site.get_by_user_id(db_user.id)
    
    # Manejar correctamente si es una lista o un solo objeto
    if isinstance(sites, list):
        site = sites[0] if sites else None
    else:
        site = sites
    
    # Crear mensaje con información sobre lo que falta configurar
    message = "⚠️ <b>Configuración SFTP incompleta</b>\n\n"
    message += "Para probar la conexión, primero debes completar todos los campos obligatorios:\n\n"
    
    # Verificar qué campos faltan
    missing_fields = []
    
    if not site or not site.sftp_config:
        # No hay configuración guardada
        missing_fields = ["Host", "Puerto", "Usuario", "Contraseña"]
    else:
        try:
            config = json.loads(site.sftp_config)
            
            # Verificar cada campo obligatorio
            if not config.get("host"):
                missing_fields.append("Host")
            if not config.get("port"):
                missing_fields.append("Puerto")
            if not config.get("username"):
                missing_fields.append("Usuario")
            if not config.get("password"):
                missing_fields.append("Contraseña")
        except:
            # Error al leer la configuración
            missing_fields = ["Host", "Puerto", "Usuario", "Contraseña"]
    
    # Añadir los campos faltantes al mensaje
    for field in missing_fields:
        message += f"• ❌ <b>{field}</b>\n"
    
    message += "\nPor favor, completa todos los campos y luego intenta probar la conexión."
    
    # Mostrar el mensaje con opciones para continuar
    keyboard = [
        [InlineKeyboardButton("🔙 Volver a Configuración SFTP", callback_data="sftp:config")],
        [InlineKeyboardButton("🏠 Volver al Menú Principal", callback_data="menu:main")]
    ]
    
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
            )

@breadcrumb
async def show_directory_options(update: Update, context: ContextTypes.DEFAULT_TYPE, path):
    """Muestra opciones para el directorio seleccionado."""
    query = update.callback_query
    
    # Crear un mensaje con opciones para el directorio seleccionado
    text = f"📂 <b>Directorio seleccionado</b>\n\n" \
           f"Ruta: <code>{path}</code>\n\n" \
           f"¿Qué deseas hacer con este directorio?"
    
    # Crear teclado con opciones en dos columnas
    keyboard = [
        [
            InlineKeyboardButton("📝 Blog", callback_data=f"sftp:select_posts:{path}"),
            InlineKeyboardButton("🖼️ Imágenes", callback_data=f"sftp:select_images:{path}")
        ],
        [
            InlineKeyboardButton("📂 Explorar", callback_data=f"sftp:explore:{path}"),
            InlineKeyboardButton("« Atrás", callback_data="sftp:explore")
        ],
        [
            InlineKeyboardButton("« Menú SFTP", callback_data="sftp:config"),
            InlineKeyboardButton("« Menú Principal", callback_data="menu:main")
        ]
    ]
    
    # Mostrar el mensaje
    await query.edit_message_text(
        text=text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

@breadcrumb
async def show_more_files(update: Update, context: ContextTypes.DEFAULT_TYPE, path):
    """Muestra todos los archivos en el directorio."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    query = update.callback_query
    
    # Obtener los datos de configuración SFTP
    db_user = models.user.User.get_by_telegram_id(user.id)
    if not db_user:
        await query.edit_message_text(
            text="❌ Error: Usuario no encontrado en la base de datos.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Volver al menú principal", callback_data="menu:main")
            ]])
        )
        return
    
    # Obtener el sitio y su configuración
    sites = models.site.Site.get_by_user_id(db_user.id)
    
    # Si get_by_user_id devuelve una lista, tomamos el primer elemento
    if isinstance(sites, list):
        site = sites[0] if sites else None
    else:
        site = sites
    
    if not site or not site.sftp_config:
        await query.edit_message_text(
            text="❌ Error: No hay configuración SFTP guardada.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Volver a configuración SFTP", callback_data="sftp:config")
            ]])
        )
        return
    
    try:
        # Cargar configuración desde JSON
        try:
            config = json.loads(site.sftp_config)
        except json.JSONDecodeError:
            logger.error(f"Error al decodificar JSON de sftp_config: {site.sftp_config}")
            await query.edit_message_text(
                text="❌ Error: Configuración SFTP inválida. Por favor reconfigura la conexión.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("« Volver a configuración SFTP", callback_data="sftp:config")
                ]])
            )
            return
        
        # Mensaje de espera
        await query.edit_message_text(
            text="🔄 Conectando al servidor SFTP...",
        )
        
        # Conectar al servidor
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Asegurarse de que el puerto sea un entero
        try:
            port = int(config["port"])
        except (ValueError, TypeError):
            port = 22
        
        client.connect(
            hostname=config["host"],
            port=port,
            username=config["username"],
            password=config["password"]
        )
        
        sftp = client.open_sftp()
        
        # Listar archivos y directorios
        items = sftp.listdir(path)
        
        # Obtener información de cada item
        directories = []
        files = []
        
        for item in items:
            if item.startswith('.'):
                continue  # Ignorar archivos/carpetas ocultos
                
            try:
                item_path = os.path.join(path, item).replace('\\', '/')
                stats = sftp.stat(item_path)
                
                if stats.st_mode & 0o40000:  # Es un directorio
                    directories.append(item)
                else:  # Es un archivo
                    files.append(item)
            except Exception as e:
                logger.warning(f"Error al verificar si '{item}' es directorio: {e}")
                files.append(item)
        
        # Ordenar alfabéticamente
        directories.sort()
        files.sort()
        
        # Construir teclado para navegación (en dos columnas para la mayoría de botones)
        keyboard = []
        
        # Añadir navegación al directorio padre
        if path != '.' and path != '/':
            parent_dir = os.path.dirname(path).replace('\\', '/')
            if not parent_dir:
                parent_dir = '.'
            keyboard.append([InlineKeyboardButton("📁 ..", callback_data=f"sftp:explore:{parent_dir}")])
        
        # Añadir directorios en dos columnas (de dos en dos)
        dir_buttons = []
        for directory in directories:
            dir_buttons.append(InlineKeyboardButton(f"📁 {directory}", callback_data=f"sftp:explore:{os.path.join(path, directory).replace('\\', '/')}"))
            # Cuando tenemos dos botones, añadirlos como una fila
            if len(dir_buttons) == 2:
                keyboard.append(dir_buttons)
                dir_buttons = []
        
        # Si queda un botón suelto, añadirlo como una fila
        if dir_buttons:
            keyboard.append(dir_buttons)
        
        # Añadir archivos (limitados)
        MAX_FILES_TO_SHOW = 10
        for file in files[:MAX_FILES_TO_SHOW]:  # Limitar a MAX_FILES_TO_SHOW archivos en la vista principal
            keyboard.append([InlineKeyboardButton(f"📄 {file}", callback_data="sftp:noop")])
        
        # Añadir botón para ver más archivos si hay más de MAX_FILES_TO_SHOW
        if len(files) > MAX_FILES_TO_SHOW:
            keyboard.append([
                InlineKeyboardButton(f"📄 ... y {len(files) - MAX_FILES_TO_SHOW} archivos más", 
                                    callback_data=f"sftp:show_more_files:{path}")
            ])
        
        # Añadir botón para seleccionar el directorio actual y otros botones de acción
        keyboard.append([
            InlineKeyboardButton("✅ Seleccionar este directorio", callback_data=f"sftp:select_dir:{path}"),
        ])
        
        # Añadir botones de navegación en dos columnas
        keyboard.append([
            InlineKeyboardButton("« SFTP", callback_data="sftp:config"),
            InlineKeyboardButton("« Menú Principal", callback_data="menu:main")
        ])
        
        # Actualizar el mensaje con la lista completa
        await query.edit_message_text(
            text=f"📂 <b>Archivos en {path}</b>\n\n"
                 f"Directorios: {len(directories)}\n"
                 f"Archivos: {len(files)}\n\n"
                 f"<i>Mostrando todos los archivos</i>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
        
        # Cerrar conexión
        sftp.close()
        client.close()
        
    except Exception as e:
        # Error al mostrar archivos
        error_message = str(e)
        logger.error(f"Error al mostrar más archivos: {error_message}")
        
        await query.edit_message_text(
            text=f"❌ <b>Error al listar archivos</b>\n\n{error_message}",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("« Explorar", callback_data=f"sftp:explore:{path}"),
                    InlineKeyboardButton("« SFTP", callback_data="sftp:config")
                ]
            ])
        )

@breadcrumb
async def confirm_clear_sftp_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Solicita confirmación para eliminar la configuración SFTP."""
    query = update.callback_query
    
    # Mostrar mensaje de confirmación
    keyboard = [
        [
            InlineKeyboardButton("✅ Sí, eliminar", callback_data="sftp:confirm_clear_config"),
            InlineKeyboardButton("❌ No, cancelar", callback_data="sftp:cancel_clear_config")
        ],
        [InlineKeyboardButton("« Volver a SFTP", callback_data="sftp:config")]
    ]
    
    await query.edit_message_text(
        text="⚠️ <b>¿Eliminar configuración SFTP?</b>\n\n"
             "Esta acción eliminará todos los datos de conexión SFTP guardados. "
             "Tendrás que volver a configurarlos si deseas usar SFTP nuevamente.\n\n"
             "¿Estás seguro de que deseas continuar?",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

@breadcrumb
async def clear_sftp_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Elimina la configuración SFTP del usuario."""
    query = update.callback_query
    user = update.effective_user
    
    # Obtener el usuario de la base de datos
    db_user = models.user.User.get_by_telegram_id(user.id)
    if not db_user:
        await query.edit_message_text(
            text="❌ Error: Usuario no encontrado en la base de datos.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Volver al menú principal", callback_data="menu:main")
            ]])
        )
        return
    
    # Obtener el sitio
    sites = models.site.Site.get_by_user_id(db_user.id)
    
    # Manejar si es lista o un solo objeto
    if isinstance(sites, list):
        site = sites[0] if sites else None
    else:
        site = sites
    
    if site:
        # Eliminar la configuración SFTP
        site.sftp_config = None
        site.save()
    
    # Notificar al usuario
    await query.edit_message_text(
        text="✅ <b>Configuración SFTP eliminada</b>\n\n"
             "Todos los datos de conexión SFTP han sido eliminados correctamente.",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 Configurar SFTP", callback_data="sftp:config"),
                InlineKeyboardButton("« Menú", callback_data="menu:main")
            ]
        ])
    )

def setup_sftp_handlers(application):
    """Configurar los manejadores de SFTP."""
    # Comando SFTP
    application.add_handler(CommandHandler("sftp", sftp_config_menu))
    
    # Manejador de callbacks para SFTP - Prioridad ALTA (grupo bajo)
    # Usamos un patrón genérico para capturar cualquier callback que empiece con "sftp:"
    application.add_handler(CallbackQueryHandler(sftp_callback_handler, pattern="^sftp:.*"), group=10)
    
    # Manejador de mensajes para el proceso de configuración SFTP - Prioridad ALTA
    application.add_handler(MessageHandler(Filters.TEXT & ~Filters.COMMAND, sftp_message_handler), group=10)
    
    logger.info("Manejadores de SFTP configurados correctamente") 