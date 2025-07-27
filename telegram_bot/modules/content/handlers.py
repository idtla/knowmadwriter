"""
Manejadores para la gestión de contenido web.
"""

import logging
import uuid
import json
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler
from telegram.constants import ParseMode
from core.states import State, state_manager
import models.site
import models.user

# Importar desde nuestro módulo de compatibilidad
from utils.compat import Filters, CallbackContext

# Configuración de logging
logger = logging.getLogger(__name__)

# Rutas de archivos JSON para plantillas
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'templates')
POSTS_TEMPLATE = os.path.join(TEMPLATES_DIR, 'posts.json')
CATEGORIES_TEMPLATE = os.path.join(TEMPLATES_DIR, 'categories.json')
TAGS_TEMPLATE = os.path.join(TEMPLATES_DIR, 'tags.json')

async def newpost_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador para el comando /newpost."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    logger.info(f"Usuario {user.id} inició la creación de un nuevo post")
    
    # Verificar si el usuario tiene un sitio configurado
    # TODO: Comprobar en la base de datos
    # De momento, simulamos que tiene un sitio configurado
    
    # Cambiar el estado a CREATING_CONTENT
    state_manager.set_state(user.id, State.CREATING_CONTENT)
    
    # Solicitar el título del post
    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            "📝 <b>Crear Nuevo Post</b>\n\n"
            "Vamos a crear un nuevo artículo para tu sitio web.\n\n"
            "Por favor, escribe el <b>título</b> del artículo:"
        ),
        parse_mode=ParseMode.HTML
    )
    
    # Guardamos el paso actual en el estado
    state_manager.set_data(user.id, "content_step", "waiting_title")

async def process_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa el título enviado por el usuario."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    title = update.message.text.strip()
    
    # Validar el título (debe tener al menos 10 caracteres)
    if len(title) < 10:
        await context.bot.send_message(
            chat_id=chat_id,
            text="⚠️ El título es demasiado corto. Debe tener al menos 10 caracteres. Inténtalo de nuevo:"
        )
        return
    
    # Guardar el título
    state_manager.set_data(user.id, "post_title", title)
    
    # Generar un slug a partir del título
    slug = title.lower()
    # Eliminar caracteres especiales y espacios
    import re
    slug = re.sub(r'[^a-z0-9áéíóúñ\s]', '', slug)
    # Reemplazar acentos
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ñ': 'n'
    }
    for a, b in replacements.items():
        slug = slug.replace(a, b)
    # Reemplazar espacios por guiones
    slug = re.sub(r'\s+', '-', slug)
    
    state_manager.set_data(user.id, "post_slug", slug)
    
    # Solicitar la descripción
    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            "✅ Título guardado.\n\n"
            "Ahora, escribe una <b>descripción breve</b> para el artículo (máximo 250 caracteres):"
        ),
        parse_mode=ParseMode.HTML
    )
    
    # Actualizar el paso actual
    state_manager.set_data(user.id, "content_step", "waiting_description")

async def process_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa la descripción enviada por el usuario."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    description = update.message.text.strip()
    
    # Validar la descripción
    if len(description) < 20:
        await context.bot.send_message(
            chat_id=chat_id,
            text="⚠️ La descripción es demasiado corta. Debe tener al menos 20 caracteres. Inténtalo de nuevo:"
        )
        return
    
    if len(description) > 250:
        description = description[:247] + "..."
        await context.bot.send_message(
            chat_id=chat_id,
            text="⚠️ La descripción era demasiado larga y ha sido truncada."
        )
    
    # Guardar la descripción
    state_manager.set_data(user.id, "post_description", description)
    
    # Solicitar la URL o contenido
    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            "✅ Descripción guardada.\n\n"
            "Ahora, tienes dos opciones:\n"
            "1) Enviar una <b>URL externa</b> (si es un recorte de otra web)\n"
            "2) Escribir <code>/contenido</code> para comenzar a escribir el contenido HTML"
        ),
        parse_mode=ParseMode.HTML
    )
    
    # Actualizar el paso actual
    state_manager.set_data(user.id, "content_step", "waiting_url_or_content")

async def process_url_or_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa la URL o la indicación de contenido enviada por el usuario."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    text = update.message.text.strip()
    
    if text.lower() == "/contenido":
        # El usuario quiere escribir contenido HTML
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "📄 <b>Redacción de Contenido</b>\n\n"
                "Por favor, escribe o pega el contenido HTML de tu artículo. "
                "Puedes usar etiquetas básicas como <code>&lt;p&gt;</code>, <code>&lt;h2&gt;</code>, <code>&lt;ul&gt;</code>, etc.\n\n"
                "Cuando hayas terminado, escribe <code>/fin</code> en una línea separada."
            ),
            parse_mode=ParseMode.HTML
        )
        
        # Inicializar el buffer de contenido
        state_manager.set_data(user.id, "content_buffer", "")
        
        # Actualizar el paso actual
        state_manager.set_data(user.id, "content_step", "waiting_content")
    
    elif text.startswith("http://") or text.startswith("https://"):
        # El usuario ha enviado una URL
        state_manager.set_data(user.id, "post_url", text)
        
        # Solicitar la categoría
        await request_category(update, context)
    
    else:
        # Entrada no válida
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "⚠️ Por favor, envía una URL válida (que comience con http:// o https://) "
                "o escribe <code>/contenido</code> para redactar el contenido HTML."
            ),
            parse_mode=ParseMode.HTML
        )

async def process_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa el contenido HTML enviado por el usuario."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    text = update.message.text
    
    if text.strip() == "/fin":
        # El usuario ha terminado de escribir contenido
        content_buffer = state_manager.get_data(user.id, "content_buffer", "")
        
        if not content_buffer:
            await context.bot.send_message(
                chat_id=chat_id,
                text="⚠️ No has escrito ningún contenido. Por favor, escribe algo antes de finalizar:"
            )
            return
        
        # Guardar el contenido final
        html_content = content_buffer.strip()
        
        # TODO: Procesar y validar el HTML
        
        # Generar la URL del post basada en el slug y categoría (por defecto "general")
        category = "general"
        slug = state_manager.get_data(user.id, "post_slug")
        url = f"/{category}/{slug}.html"
        
        state_manager.set_data(user.id, "post_url", url)
        
        # Solicitar la categoría
        await request_category(update, context)
    
    else:
        # Agregar el texto al buffer de contenido
        content_buffer = state_manager.get_data(user.id, "content_buffer", "")
        content_buffer += text + "\n"
        state_manager.set_data(user.id, "content_buffer", content_buffer)
        
        # Confirmar recepción
        await context.bot.send_message(
            chat_id=chat_id,
            text="✅ Contenido recibido. Continúa escribiendo o envía /fin cuando hayas terminado."
        )

async def request_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Solicita al usuario que seleccione una categoría."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Cargar categorías disponibles desde el archivo JSON de plantilla
    try:
        with open(CATEGORIES_TEMPLATE, 'r', encoding='utf-8') as f:
            categories_data = json.load(f)
            categories = categories_data['categories']
    except Exception as e:
        logger.error(f"Error al cargar las categorías: {e}")
        categories = [
            {"id": "desarrollo", "name": "Desarrollo"},
            {"id": "salud", "name": "Salud"},
            {"id": "alimentacion", "name": "Alimentación"},
            {"id": "crianza", "name": "Crianza"},
            {"id": "embarazo", "name": "Embarazo"},
            {"id": "pareja", "name": "Pareja"}
        ]
    
    # Crear teclado con las categorías
    keyboard = []
    row = []
    for i, category in enumerate(categories):
        row.append(InlineKeyboardButton(category['name'], callback_data=f"content:category:{category['id']}"))
        if (i + 1) % 2 == 0 or i == len(categories) - 1:
            keyboard.append(row)
            row = []
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            "🔖 <b>Selecciona una categoría para tu artículo:</b>"
        ),
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )
    
    # Actualizar el paso actual
    state_manager.set_data(user.id, "content_step", "waiting_category")

async def process_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa la imagen enviada por el usuario."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Comprobar si se envió una imagen
    if update.message.photo:
        # Obtener la foto de mayor resolución
        photo = update.message.photo[-1]
        file_id = photo.file_id
        
        # TODO: Descargar y procesar la imagen
        # Por ahora, simulamos una URL
        image_url = f"https://example.com/uploads/{file_id}.jpg"
        
        # Guardar la URL de la imagen
        state_manager.set_data(user.id, "post_image", image_url)
        
        # Mostrar resumen y solicitar confirmación
        await show_post_summary(update, context)
    
    elif update.message.text and (update.message.text.startswith("http://") or update.message.text.startswith("https://")):
        # El usuario ha enviado una URL de imagen
        image_url = update.message.text.strip()
        
        # TODO: Validar que la URL sea una imagen
        
        # Guardar la URL de la imagen
        state_manager.set_data(user.id, "post_image", image_url)
        
        # Mostrar resumen y solicitar confirmación
        await show_post_summary(update, context)
    
    else:
        # No es una imagen válida
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "⚠️ Por favor, envía una imagen o una URL de imagen válida (que comience con http:// o https://)."
            )
        )

async def show_post_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra un resumen del post y solicita confirmación."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Obtener los datos del post
    title = state_manager.get_data(user.id, "post_title")
    description = state_manager.get_data(user.id, "post_description")
    url = state_manager.get_data(user.id, "post_url")
    image = state_manager.get_data(user.id, "post_image")
    category = state_manager.get_data(user.id, "post_category")
    slug = state_manager.get_data(user.id, "post_slug")
    
    # Crear botones de confirmación
    keyboard = [
        [
            InlineKeyboardButton("✅ Publicar", callback_data="content:confirm:publish"),
            InlineKeyboardButton("❌ Cancelar", callback_data="content:confirm:cancel"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            "<b>📋 Resumen del Post</b>\n\n"
            f"<b>Título:</b> {title}\n"
            f"<b>Descripción:</b> {description}\n"
            f"<b>URL:</b> {url}\n"
            f"<b>Imagen:</b> {image if image else 'No especificada'}\n"
            f"<b>Categoría:</b> {category}\n"
            f"<b>Slug:</b> {slug}\n\n"
            "¿Deseas publicar este artículo?"
        ),
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )
    
    # Actualizar el paso actual
    state_manager.set_data(user.id, "content_step", "waiting_confirmation")

async def content_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestiona los callbacks relacionados con la creación de contenido."""
    query = update.callback_query
    user = update.effective_user
    data_parts = query.data.split(":")
    action = data_parts[1]
    
    await query.answer()
    
    if action == "category":
        category_id = data_parts[2]
        
        # Cargar categorías para obtener el nombre
        try:
            with open(CATEGORIES_TEMPLATE, 'r', encoding='utf-8') as f:
                categories_data = json.load(f)
                categories = {cat['id']: cat['name'] for cat in categories_data['categories']}
                category_name = categories.get(category_id, category_id.capitalize())
        except Exception as e:
            logger.error(f"Error al cargar las categorías: {e}")
            category_name = category_id.capitalize()
        
        # Guardar la categoría
        state_manager.set_data(user.id, "post_category", category_name)
        state_manager.set_data(user.id, "post_category_id", category_id)
        
        # Actualizar la URL con la categoría correcta
        slug = state_manager.get_data(user.id, "post_slug")
        url = f"/{category_id}/{slug}.html"
        state_manager.set_data(user.id, "post_url", url)
        
        # Solicitar imagen
        await query.edit_message_text(
            text=(
                "✅ Categoría seleccionada: <b>{}</b>\n\n"
                "Ahora, por favor envía una <b>imagen destacada</b> para el artículo.\n"
                "Puedes subir una imagen directamente o enviar una URL de imagen."
            ).format(category_name),
            parse_mode=ParseMode.HTML
        )
        
        # Actualizar el paso actual
        state_manager.set_data(user.id, "content_step", "waiting_image")
    
    elif action == "confirm":
        if data_parts[2] == "publish":
            # Publicar el post
            # Obtener los datos del post
            title = state_manager.get_data(user.id, "post_title")
            description = state_manager.get_data(user.id, "post_description")
            url = state_manager.get_data(user.id, "post_url")
            image = state_manager.get_data(user.id, "post_image")
            category = state_manager.get_data(user.id, "post_category")
            category_id = state_manager.get_data(user.id, "post_category_id")
            slug = state_manager.get_data(user.id, "post_slug")
            
            # Generar un ID único
            post_id = str(uuid.uuid4())
            
            # Crear objeto de post
            new_post = {
                "id": post_id,
                "title": title,
                "description": description,
                "url": url,
                "image": image,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "category": category,
                "slug": slug
            }
            
            # Intentar subir el post al servidor vía SFTP
            try:
                # Importamos la función de subida SFTP
                from ..sftp.handlers import upload_post_to_sftp
                
                # Mensaje de estado temporal
                await query.edit_message_text(
                    text="🔄 Preparando para subir el contenido al servidor..."
                )
                
                # Llamar a la función de subida
                upload_result = await upload_post_to_sftp(update, context, new_post)
                
                if not upload_result:
                    # Si la subida falló pero no lanzó excepción, mostramos mensaje informativo
                    await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text=(
                            "ℹ️ <b>Información</b>\n\n"
                            "Tu artículo se ha creado correctamente, pero no se ha podido subir al servidor.\n\n"
                            "Puedes configurar la conexión SFTP con /sftp_config y volver a intentarlo más tarde."
                        ),
                        parse_mode=ParseMode.HTML
                    )
                
                # Guardamos el post en el estado del usuario (historial)
                user_posts = state_manager.get_data(user.id, "user_posts", [])
                user_posts.append(new_post)
                state_manager.set_data(user.id, "user_posts", user_posts)
                
            except ImportError:
                # Si el módulo SFTP no está disponible
                await query.edit_message_text(
                    text=(
                        "🎉 <b>¡Post Creado Exitosamente!</b>\n\n"
                        f"Tu artículo '<b>{title}</b>' ha sido creado.\n\n"
                        "⚠️ El módulo SFTP no está disponible. No se ha podido subir al servidor."
                    ),
                    parse_mode=ParseMode.HTML
                )
            except Exception as e:
                # Si ocurre un error durante la subida
                logger.error(f"Error al subir post: {e}")
                await query.edit_message_text(
                    text=(
                        "🎉 <b>¡Post Creado Exitosamente!</b>\n\n"
                        f"Tu artículo '<b>{title}</b>' ha sido creado.\n\n"
                        f"⚠️ Error al subir al servidor: {str(e)}"
                    ),
                    parse_mode=ParseMode.HTML
                )
            
            # Limpiar estado
            state_manager.set_state(user.id, State.IDLE)
            state_manager.clear_user_data(user.id)
            
            logger.info(f"Usuario {user.id} completó la creación de un post: {title}")
        
        elif data_parts[2] == "cancel":
            await query.edit_message_text(
                text="❌ Creación de post cancelada. Puedes intentarlo nuevamente usando /newpost."
            )
            
            # Limpiar estado
            state_manager.set_state(user.id, State.IDLE)
            state_manager.clear_user_data(user.id)
            
            logger.info(f"Usuario {user.id} canceló la creación de un post")
    
    elif action == "edit":
        # Manejar selección de post para editar
        if data_parts[2] == "cancel":
            await query.edit_message_text(
                text="❌ Edición cancelada."
            )
            state_manager.set_state(user.id, State.IDLE)
        else:
            # Cargar post para edición
            post_id = data_parts[2]
            await load_post_for_editing(update, context, post_id)
    
    elif action == "edit_field":
        # Manejar selección de campo a editar
        field = data_parts[2]
        await request_edit_field(update, context, field)
    
    elif action == "edit_save":
        # Manejar confirmación/cancelación de guardar cambios
        if data_parts[2] == "confirm":
            # Obtener los datos del post
            post_id = state_manager.get_data(user.id, "editing_post_id")
            title = state_manager.get_data(user.id, "post_title")
            description = state_manager.get_data(user.id, "post_description")
            url = state_manager.get_data(user.id, "post_url")
            image = state_manager.get_data(user.id, "post_image")
            category = state_manager.get_data(user.id, "post_category")
            slug = state_manager.get_data(user.id, "post_slug")
            
            # Actualizar el post
            updated_post = {
                "id": post_id,
                "title": title,
                "description": description,
                "url": url,
                "image": image,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "category": category,
                "slug": slug
            }
            
            # Actualizar lista de posts del usuario
            user_posts = state_manager.get_data(user.id, "user_posts", [])
            for i, post in enumerate(user_posts):
                if post.get('id') == post_id:
                    user_posts[i] = updated_post
                    break
            
            state_manager.set_data(user.id, "user_posts", user_posts)
            
            # Intentar subir el post actualizado al servidor vía SFTP
            try:
                # Importamos la función de subida SFTP
                from ..sftp.handlers import upload_post_to_sftp
                
                # Mensaje de estado temporal
                await query.edit_message_text(
                    text="🔄 Preparando para subir los cambios al servidor..."
                )
                
                # Llamar a la función de subida
                upload_result = await upload_post_to_sftp(update, context, updated_post)
                
                if not upload_result:
                    # Si la subida falló pero no lanzó excepción, mostramos mensaje informativo
                    await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text=(
                            "ℹ️ <b>Información</b>\n\n"
                            "Tu artículo se ha actualizado correctamente, pero no se ha podido subir al servidor.\n\n"
                            "Puedes configurar la conexión SFTP con /sftp_config y volver a intentarlo más tarde."
                        ),
                        parse_mode=ParseMode.HTML
                    )
                
            except ImportError:
                # Si el módulo SFTP no está disponible
                await query.edit_message_text(
                    text=(
                        "✅ <b>¡Post Actualizado Exitosamente!</b>\n\n"
                        f"Tu artículo '<b>{title}</b>' ha sido actualizado.\n\n"
                        "⚠️ El módulo SFTP no está disponible. No se ha podido subir al servidor."
                    ),
                    parse_mode=ParseMode.HTML
                )
            except Exception as e:
                # Si ocurre un error durante la subida
                logger.error(f"Error al subir post actualizado: {e}")
                await query.edit_message_text(
                    text=(
                        "✅ <b>¡Post Actualizado Exitosamente!</b>\n\n"
                        f"Tu artículo '<b>{title}</b>' ha sido actualizado.\n\n"
                        f"⚠️ Error al subir al servidor: {str(e)}"
                    ),
                    parse_mode=ParseMode.HTML
                )
            
            # Limpiar estado
            state_manager.set_state(user.id, State.IDLE)
            state_manager.clear_user_data(user.id)
            
            logger.info(f"Usuario {user.id} completó la edición del post: {title}")
        
        elif data_parts[2] == "cancel":
            await query.edit_message_text(
                text="❌ Edición cancelada."
            )
            state_manager.set_state(user.id, State.IDLE)
            state_manager.clear_user_data(user.id)

async def process_edit_field(update: Update, context: ContextTypes.DEFAULT_TYPE, field: str):
    """Procesa el nuevo valor para el campo que se está editando."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    query = update.callback_query
    
    # Guardar el campo que se está editando
    state_manager.set_data(user.id, "editing_field", field)
    
    # Dependiendo del campo, mostrar mensaje apropiado
    if field == "title":
        current_value = state_manager.get_data(user.id, "post_title", "")
        await query.edit_message_text(
            text=(
                "📝 <b>Editar Título</b>\n\n"
                f"Título actual: <i>{current_value}</i>\n\n"
                "Envía el nuevo título para tu artículo:"
            ),
            parse_mode=ParseMode.HTML
        )
    
    elif field == "description":
        current_value = state_manager.get_data(user.id, "post_description", "")
        await query.edit_message_text(
            text=(
                "📋 <b>Editar Descripción</b>\n\n"
                f"Descripción actual: <i>{current_value[:100]}...</i>\n\n"
                "Envía la nueva descripción para tu artículo:"
            ),
            parse_mode=ParseMode.HTML
        )
    
    elif field == "content":
        current_url = state_manager.get_data(user.id, "post_url", "")
        await query.edit_message_text(
            text=(
                "🌐 <b>Editar Contenido</b>\n\n"
                f"URL actual: <i>{current_url}</i>\n\n"
                "Envía una nueva URL o el contenido HTML para tu artículo:"
            ),
            parse_mode=ParseMode.HTML
        )
    
    elif field == "image":
        current_image = state_manager.get_data(user.id, "post_image", "")
        if current_image:
            # Mostrar la imagen actual
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=current_image,
                caption="Imagen actual"
            )
        
        await query.edit_message_text(
            text=(
                "🖼️ <b>Editar Imagen</b>\n\n"
                "Envía una nueva imagen para tu artículo o una URL de imagen:"
            ),
            parse_mode=ParseMode.HTML
        )
    
    elif field == "category":
        # Similar a la creación de post, mostrar categorías disponibles
        await request_category(update, context)
        return

async def content_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador de mensajes para el módulo de contenido."""
    user = update.effective_user
    
    # Verificar si el usuario está en proceso de creación de contenido
    if state_manager.get_state(user.id) == State.CREATING_CONTENT:
        current_step = state_manager.get_data(user.id, "content_step")
        
        if current_step == "waiting_title":
            await process_title(update, context)
            return True
        elif current_step == "waiting_description":
            await process_description(update, context)
            return True
        elif current_step == "waiting_url_or_content":
            await process_url_or_content(update, context)
            return True
        elif current_step == "waiting_content":
            await process_content(update, context)
            return True
        elif current_step == "waiting_image":
            await process_image(update, context)
            return True
    
    # Verificar si el usuario está en proceso de edición de contenido
    elif state_manager.get_state(user.id) == State.EDITING_CONTENT:
        # Si hay un campo específico en edición, procesarlo
        if state_manager.get_data(user.id, "editing_field"):
            handled = await process_edit_field(update, context)
            if handled:
                return True
    
    # Si no está en proceso de creación o edición, dejamos que otros manejadores procesen el mensaje
    return False

async def editpost_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador para el comando /editpost."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    logger.info(f"Usuario {user.id} inició la edición de un post")
    
    # Cambiar el estado a EDITING_CONTENT
    state_manager.set_state(user.id, State.EDITING_CONTENT)
    
    # Obtener los posts del usuario (desde el estado o simulados para este ejemplo)
    user_posts = state_manager.get_data(user.id, "user_posts", [])
    
    if not user_posts:
        # Si no hay posts, intentar cargar desde una simulación
        try:
            # Cargar posts desde plantilla como ejemplo
            templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                         'data', 'templates')
            with open(os.path.join(templates_dir, 'posts.json'), 'r', encoding='utf-8') as f:
                posts_data = json.load(f)
                user_posts = posts_data.get("posts", [])
            
            if not user_posts:
                raise ValueError("No hay posts disponibles")
                
        except Exception as e:
            logger.error(f"Error al cargar posts de ejemplo: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text=(
                    "❌ <b>No hay posts disponibles</b>\n\n"
                    "No se encontraron posts para editar. Crea un nuevo post con /newpost primero."
                ),
                parse_mode=ParseMode.HTML
            )
            state_manager.set_state(user.id, State.IDLE)
            return
    
    # Limitar a 10 posts para evitar botones excesivos
    user_posts = user_posts[:10]
    
    # Crear teclado con los posts disponibles
    keyboard = []
    for post in user_posts:
        keyboard.append([
            InlineKeyboardButton(
                text=f"📝 {post['title'][:30]}...", 
                callback_data=f"content:edit:{post['id']}"
            )
        ])
    
    # Añadir botón para cancelar
    keyboard.append([
        InlineKeyboardButton(
            text="❌ Cancelar", 
            callback_data="content:edit:cancel"
        )
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Mostrar mensaje con los posts disponibles
    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            "📋 <b>Editar Artículo</b>\n\n"
            "Selecciona el artículo que deseas editar:"
        ),
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def load_post_for_editing(update: Update, context: ContextTypes.DEFAULT_TYPE, post_id: str):
    """Carga un post para su edición."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    query = update.callback_query
    
    # Obtener posts del usuario
    user_posts = state_manager.get_data(user.id, "user_posts", [])
    
    # Si no hay posts en el estado, intentar cargar desde plantilla
    if not user_posts:
        try:
            templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                         'data', 'templates')
            with open(os.path.join(templates_dir, 'posts.json'), 'r', encoding='utf-8') as f:
                posts_data = json.load(f)
                user_posts = posts_data.get("posts", [])
        except Exception as e:
            logger.error(f"Error al cargar posts de plantilla: {e}")
    
    # Buscar el post por ID
    selected_post = None
    for post in user_posts:
        if post.get('id') == post_id:
            selected_post = post
            break
    
    if not selected_post:
        await query.edit_message_text(
            text=(
                "❌ <b>Error</b>\n\n"
                "No se encontró el artículo seleccionado."
            ),
            parse_mode=ParseMode.HTML
        )
        state_manager.set_state(user.id, State.IDLE)
        return
    
    # Guardar datos del post en el estado
    state_manager.set_data(user.id, "editing_post_id", post_id)
    state_manager.set_data(user.id, "post_original", selected_post)
    state_manager.set_data(user.id, "post_title", selected_post.get('title', ''))
    state_manager.set_data(user.id, "post_description", selected_post.get('description', ''))
    state_manager.set_data(user.id, "post_url", selected_post.get('url', ''))
    state_manager.set_data(user.id, "post_image", selected_post.get('image', ''))
    state_manager.set_data(user.id, "post_category", selected_post.get('category', ''))
    state_manager.set_data(user.id, "post_slug", selected_post.get('slug', ''))
    
    # Crear teclado con opciones de edición
    keyboard = [
        [InlineKeyboardButton(text="📝 Título", callback_data="content:edit_field:title")],
        [InlineKeyboardButton(text="📋 Descripción", callback_data="content:edit_field:description")],
        [InlineKeyboardButton(text="🌐 Contenido", callback_data="content:edit_field:content")],
        [InlineKeyboardButton(text="🖼️ Imagen", callback_data="content:edit_field:image")],
        [InlineKeyboardButton(text="📁 Categoría", callback_data="content:edit_field:category")],
        [InlineKeyboardButton(text="✅ Guardar Cambios", callback_data="content:edit_save:confirm")],
        [InlineKeyboardButton(text="❌ Cancelar", callback_data="content:edit_save:cancel")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Mostrar resumen del post a editar
    await query.edit_message_text(
        text=(
            f"📝 <b>Editando: {selected_post['title']}</b>\n\n"
            f"<b>Descripción:</b> {selected_post['description'][:100]}...\n"
            f"<b>Categoría:</b> {selected_post['category']}\n\n"
            "Selecciona qué campo deseas editar:"
        ),
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def request_edit_field(update: Update, context: ContextTypes.DEFAULT_TYPE, field: str):
    """Solicita al usuario que edite un campo específico del post."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    query = update.callback_query
    
    # Guardar el campo que se está editando
    state_manager.set_data(user.id, "editing_field", field)
    
    # Dependiendo del campo, mostrar mensaje apropiado
    if field == "title":
        current_value = state_manager.get_data(user.id, "post_title", "")
        await query.edit_message_text(
            text=(
                "📝 <b>Editar Título</b>\n\n"
                f"Título actual: <i>{current_value}</i>\n\n"
                "Envía el nuevo título para tu artículo:"
            ),
            parse_mode=ParseMode.HTML
        )
    
    elif field == "description":
        current_value = state_manager.get_data(user.id, "post_description", "")
        await query.edit_message_text(
            text=(
                "📋 <b>Editar Descripción</b>\n\n"
                f"Descripción actual: <i>{current_value[:100]}...</i>\n\n"
                "Envía la nueva descripción para tu artículo:"
            ),
            parse_mode=ParseMode.HTML
        )
    
    elif field == "content":
        current_url = state_manager.get_data(user.id, "post_url", "")
        await query.edit_message_text(
            text=(
                "🌐 <b>Editar Contenido</b>\n\n"
                f"URL actual: <i>{current_url}</i>\n\n"
                "Envía una nueva URL o el contenido HTML para tu artículo:"
            ),
            parse_mode=ParseMode.HTML
        )
    
    elif field == "image":
        current_image = state_manager.get_data(user.id, "post_image", "")
        if current_image:
            # Mostrar la imagen actual
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=current_image,
                caption="Imagen actual"
            )
        
        await query.edit_message_text(
            text=(
                "🖼️ <b>Editar Imagen</b>\n\n"
                "Envía una nueva imagen para tu artículo o una URL de imagen:"
            ),
            parse_mode=ParseMode.HTML
        )
    
    elif field == "category":
        # Similar a la creación de post, mostrar categorías disponibles
        await request_category(update, context)
        return

def setup_content_handlers(application):
    """Configura los manejadores para el módulo de contenido."""
    # Añadir manejadores de comandos
    application.add_handler(CommandHandler("newpost", newpost_command))
    application.add_handler(CommandHandler("editpost", editpost_command))
    
    # Añadir manejador de callbacks
    application.add_handler(CallbackQueryHandler(content_callback, pattern=r"^content:"))
    
    # Añadir manejador de mensajes (prioridad alta)
    application.add_handler(MessageHandler(Filters.TEXT | Filters.PHOTO, content_message_handler), group=1)
    
    logger.info("Manejadores de contenido configurados correctamente") 