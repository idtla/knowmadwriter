"""
Handlers para el módulo de etiquetas.

Este módulo contiene los handlers para gestionar etiquetas en el sitio web, 
incluyendo creación, edición, visualización y eliminación de etiquetas.
"""

import json
import os
import logging
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler

# Importar desde nuestro módulo de compatibilidad
from utils.compat import Filters
from utils.file_operations import read_json_file, write_json_file
from utils.breadcrumbs import breadcrumb
from models.tag import Tag

# Estados para la conversación
SELECTING_ACTION, SELECT_TAG, CREATING_TAG, ENTER_TAG_NAME = range(4)

# Paths
DATA_DIR = Path('data')
TAGS_FILE = DATA_DIR / 'tags.json'
POSTS_FILE = DATA_DIR / 'posts.json'

# Asegurar que los directorios existan
DATA_DIR.mkdir(exist_ok=True)

# Logger
logger = logging.getLogger(__name__)

# Funciones de utilidad
def load_tags():
    """Carga las etiquetas del archivo JSON."""
    if not TAGS_FILE.exists():
        # Crear estructura inicial si no existe
        default_data = {
            "tags": [
                {"id": "web001", "name": "Web", "post_count": 0},
                {"id": "dev001", "name": "Desarrollo", "post_count": 0},
                {"id": "mar001", "name": "Marketing", "post_count": 0}
            ]
        }
        write_json_file(TAGS_FILE, default_data)
        return default_data
    return read_json_file(TAGS_FILE)

def save_tags(tags_data):
    """Guarda las etiquetas en el archivo JSON."""
    write_json_file(TAGS_FILE, tags_data)

# Handlers
@breadcrumb
async def start_tags(update: Update, context: CallbackContext) -> int:
    """Inicia el flujo de gestión de etiquetas."""
    keyboard = [
        [
            InlineKeyboardButton("🔍 Ver Etiquetas", callback_data="view_tags"),
            InlineKeyboardButton("➕ Nueva Etiqueta", callback_data="new_tag")
        ],
        [
            InlineKeyboardButton("✏️ Editar Etiqueta", callback_data="edit_tag"),
            InlineKeyboardButton("🗑️ Eliminar Etiqueta", callback_data="delete_tag")
        ],
        [InlineKeyboardButton("🔄 Actualizar Contadores", callback_data="update_counts")],
        [InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        "🏷️ *Gestión de Etiquetas*\n\n"
        "Puedes ver, crear, editar o eliminar etiquetas para tus posts.\n\n"
        "Selecciona una opción:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return SELECTING_ACTION

@breadcrumb
async def view_tags(update: Update, context: CallbackContext) -> int:
    """Muestra la lista de etiquetas existentes."""
    tags_data = load_tags()
    tags = tags_data.get("tags", [])
    
    # Ordenar por conteo de posts (mayor a menor)
    tags.sort(key=lambda x: x.get("post_count", 0), reverse=True)
    
    message = "📋 *Etiquetas Disponibles*\n\n"
    
    if not tags:
        message += "No hay etiquetas definidas."
    else:
        # Añadir cabecera para el listado
        message += "*NOMBRE*   *POSTS*\n"
        message += "─────────────────\n\n"
        
        for i, tag in enumerate(tags, 1):
            message += f"{i}. *{tag['name']}*\n"
            message += f"   📊 Posts: {tag['post_count']}\n\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Volver", callback_data="back_to_tags")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return SELECTING_ACTION

@breadcrumb
async def new_tag(update: Update, context: CallbackContext) -> int:
    """Inicia el proceso de creación de una nueva etiqueta."""
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        "➕ *Crear Nueva Etiqueta*\n\n"
        "Por favor, ingresa el nombre para la nueva etiqueta:",
        parse_mode='Markdown'
    )
    return ENTER_TAG_NAME

@breadcrumb
async def enter_tag_name(update: Update, context: CallbackContext) -> int:
    """Recibe el nombre de la etiqueta y la crea."""
    tag_name = update.message.text.strip()
    
    # Validar que el nombre no esté vacío
    if not tag_name:
        await update.message.reply_text(
            "⚠️ El nombre de la etiqueta no puede estar vacío. Por favor, intenta de nuevo."
        )
        return ENTER_TAG_NAME
    
    # Validar que no exista ya una etiqueta con ese nombre
    tags_data = load_tags()
    tags = tags_data.get("tags", [])
    
    if any(tag["name"].lower() == tag_name.lower() for tag in tags):
        await update.message.reply_text(
            "⚠️ Ya existe una etiqueta con ese nombre. Por favor, elige otro nombre."
        )
        return ENTER_TAG_NAME
    
    # Crear la nueva etiqueta con contador en 0
    tag = Tag(name=tag_name)
    Tag.save(tag)
    
    # Limpiar datos de usuario si hay alguno
    if "new_tag_name" in context.user_data:
        del context.user_data["new_tag_name"]
    
    # Mostrar mensaje de confirmación
    keyboard = [[InlineKeyboardButton("🔙 Volver a Etiquetas", callback_data="back_to_tags")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"✅ ¡Etiqueta *{tag_name}* creada exitosamente!\n\n"
        f"El contador de posts se incrementará automáticamente cuando se creen posts con esta etiqueta.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return SELECTING_ACTION

@breadcrumb
async def select_tag_to_edit(update: Update, context: CallbackContext) -> int:
    """Muestra la lista de etiquetas para seleccionar una a editar."""
    tags_data = load_tags()
    tags = tags_data.get("tags", [])
    
    if not tags:
        keyboard = [[InlineKeyboardButton("🔙 Volver", callback_data="back_to_tags")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(
            "❌ No hay etiquetas para editar.",
            reply_markup=reply_markup
        )
        return SELECTING_ACTION
    
    keyboard = []
    for tag in tags:
        keyboard.append([
            InlineKeyboardButton(
                f"{tag['name']} ({tag['post_count']} posts)",
                callback_data=f"edit_{tag['name']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="back_to_tags")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        "✏️ *Editar Etiqueta*\n\n"
        "Selecciona la etiqueta que deseas editar:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return SELECT_TAG

@breadcrumb
async def edit_tag(update: Update, context: CallbackContext) -> int:
    """Muestra opciones para editar una etiqueta específica."""
    tag_name = update.callback_query.data.split("_")[1]
    context.user_data["edit_tag"] = tag_name
    
    # Buscar la etiqueta para mostrar sus datos actuales
    tag = Tag.get_by_name(tag_name)
    
    if not tag:
        await update.callback_query.answer("Etiqueta no encontrada")
        return await select_tag_to_edit(update, context)
    
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        f"✏️ *Editar Etiqueta: {tag_name}*\n\n"
        f"Datos actuales:\n"
        f"- Nombre: {tag.name}\n"
        f"- Posts: {tag.post_count}\n\n"
        f"Por favor, ingresa el nuevo nombre para esta etiqueta:",
        parse_mode='Markdown'
    )
    
    return ENTER_TAG_NAME

@breadcrumb
async def update_tag_name(update: Update, context: CallbackContext) -> int:
    """Actualiza el nombre de la etiqueta."""
    old_tag_name = context.user_data.get("edit_tag")
    new_tag_name = update.message.text.strip()
    
    # Validar que el nombre no esté vacío
    if not new_tag_name:
        await update.message.reply_text(
            "⚠️ El nombre de la etiqueta no puede estar vacío. Por favor, intenta de nuevo."
        )
        return ENTER_TAG_NAME
    
    # Validar que no exista otra etiqueta con ese nombre
    tag = Tag.get_by_name(old_tag_name)
    existing_tag = Tag.get_by_name(new_tag_name)
    
    if existing_tag and existing_tag.id != tag.id:
        await update.message.reply_text(
            "⚠️ Ya existe otra etiqueta con ese nombre. Por favor, elige un nombre diferente."
        )
        return ENTER_TAG_NAME
    
    # Guardar el nombre anterior para actualizar posts
    old_name = tag.name
    
    # Actualizar el nombre de la etiqueta
    tag.name = new_tag_name
    Tag.save(tag)
    
    # Actualizar también la etiqueta en los posts
    try:
        posts_data = read_json_file(POSTS_FILE)
        posts = posts_data.get("posts", [])
        updated_posts = 0
        
        for post in posts:
            tags_list = post.get("tags", [])
            if old_name in tags_list:
                # Actualizar la etiqueta en la lista
                index = tags_list.index(old_name)
                tags_list[index] = new_tag_name
                post["tags"] = tags_list
                updated_posts += 1
        
        if updated_posts > 0:
            write_json_file(POSTS_FILE, posts_data)
            logger.info(f"Actualizada etiqueta '{old_name}' a '{new_tag_name}' en {updated_posts} posts")
    except Exception as e:
        logger.error(f"Error al actualizar etiqueta en posts: {e}")
    
    # Limpiar datos de usuario
    if "edit_tag" in context.user_data:
        del context.user_data["edit_tag"]
    
    # Mostrar mensaje de confirmación
    keyboard = [[InlineKeyboardButton("🔙 Volver a Etiquetas", callback_data="back_to_tags")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"✅ ¡Etiqueta actualizada exitosamente de '{old_name}' a '{new_tag_name}'!",
        reply_markup=reply_markup
    )
    return SELECTING_ACTION

@breadcrumb
async def select_tag_to_delete(update: Update, context: CallbackContext) -> int:
    """Muestra la lista de etiquetas para seleccionar una a eliminar."""
    tags_data = load_tags()
    tags = tags_data.get("tags", [])
    
    if not tags:
        keyboard = [[InlineKeyboardButton("🔙 Volver", callback_data="back_to_tags")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(
            "❌ No hay etiquetas para eliminar.",
            reply_markup=reply_markup
        )
        return SELECTING_ACTION
    
    keyboard = []
    for tag in tags:
        keyboard.append([
            InlineKeyboardButton(
                f"🗑️ {tag['name']} ({tag['post_count']} posts)",
                callback_data=f"delete_{tag['name']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="back_to_tags")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        "🗑️ *Eliminar Etiqueta*\n\n"
        "⚠️ ADVERTENCIA: Al eliminar una etiqueta, se eliminará de todos los posts que la utilizan.\n\n"
        "Selecciona la etiqueta que deseas eliminar:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return SELECT_TAG

@breadcrumb
async def delete_tag(update: Update, context: CallbackContext) -> int:
    """Elimina una etiqueta y la actualiza en los posts."""
    tag_name = update.callback_query.data.split("_")[1]
    
    tag = Tag.get_by_name(tag_name)
    if not tag:
        await update.callback_query.answer("Etiqueta no encontrada")
        return await select_tag_to_delete(update, context)
    
    # Eliminar la etiqueta
    Tag.delete(tag.id)
    
    # Actualizar los posts que tenían esta etiqueta
    try:
        posts_data = read_json_file(POSTS_FILE)
        posts = posts_data.get("posts", [])
        updated_posts = 0
        
        for post in posts:
            tags_list = post.get("tags", [])
            if tag_name in tags_list:
                # Eliminar la etiqueta de la lista
                tags_list.remove(tag_name)
                post["tags"] = tags_list
                updated_posts += 1
        
        if updated_posts > 0:
            write_json_file(POSTS_FILE, posts_data)
            logger.info(f"Eliminada etiqueta '{tag_name}' de {updated_posts} posts")
            tag_update_msg = f"\n\n✅ Etiqueta eliminada de {updated_posts} posts."
        else:
            tag_update_msg = "\n\nℹ️ No había posts con esta etiqueta."
    except Exception as e:
        logger.error(f"Error al actualizar posts: {e}")
        tag_update_msg = "\n\n⚠️ No se pudieron actualizar los posts asociados."
    
    keyboard = [[InlineKeyboardButton("🔙 Volver a Etiquetas", callback_data="back_to_tags")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        f"✅ Etiqueta *{tag_name}* eliminada exitosamente.{tag_update_msg}",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return SELECTING_ACTION

@breadcrumb
async def update_tag_counts(update: Update, context: CallbackContext) -> int:
    """Actualiza los contadores de todas las etiquetas basados en los posts."""
    await update.callback_query.answer()
    
    # Mostrar mensaje de espera
    wait_message = await update.callback_query.message.edit_text(
        "🔄 Actualizando contadores de etiquetas...\nEsto puede tomar unos segundos."
    )
    
    # Actualizar contadores
    success = Tag.update_post_counts_from_posts()
    
    # Obtener las etiquetas actualizadas
    tags = Tag.get_all()
    tags.sort(key=lambda t: t.post_count, reverse=True)
    
    # Construir mensaje con resultados
    if success:
        message = "✅ *Contadores de etiquetas actualizados correctamente*\n\n"
        message += "*Etiquetas ordenadas por número de posts:*\n\n"
        
        for i, tag in enumerate(tags, 1):
            message += f"{i}. *{tag.name}*: {tag.post_count} posts\n"
    else:
        message = "❌ *Error al actualizar los contadores de etiquetas*\n\n"
        message += "Por favor, verifica que el archivo de posts exista y sea válido."
    
    keyboard = [[InlineKeyboardButton("🔙 Volver a Etiquetas", callback_data="back_to_tags")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(
        message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return SELECTING_ACTION

@breadcrumb
async def back_handler(update: Update, context: CallbackContext) -> int:
    """Maneja los botones de regreso."""
    query = update.callback_query
    data = query.data
    
    if data == "back_to_main":
        # Volver al menú principal (esto debería ser manejado fuera de este módulo)
        await query.answer()
        await query.message.edit_text(
            "🔄 Volviendo al menú principal...",
        )
        return ConversationHandler.END
    
    elif data == "back_to_tags":
        # Volver al menú de etiquetas
        return await start_tags(update, context)
    
    await query.answer("Acción no reconocida")
    return SELECTING_ACTION

def setup_tags_handlers(application):
    """Configura los handlers para el módulo de etiquetas."""
    # Crear directorio y archivo de etiquetas si no existen
    if not TAGS_FILE.exists():
        Tag.ensure_file_exists()
    
    # Definir el conversation handler
    tags_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_tags, pattern='^/tags$')],
        states={
            SELECTING_ACTION: [
                CallbackQueryHandler(view_tags, pattern='^view_tags$'),
                CallbackQueryHandler(new_tag, pattern='^new_tag$'),
                CallbackQueryHandler(select_tag_to_edit, pattern='^edit_tag$'),
                CallbackQueryHandler(select_tag_to_delete, pattern='^delete_tag$'),
                CallbackQueryHandler(update_tag_counts, pattern='^update_counts$'),
                CallbackQueryHandler(back_handler, pattern='^back_to_')
            ],
            SELECT_TAG: [
                CallbackQueryHandler(edit_tag, pattern='^edit_'),
                CallbackQueryHandler(delete_tag, pattern='^delete_'),
                CallbackQueryHandler(back_handler, pattern='^back_to_')
            ],
            ENTER_TAG_NAME: [
                MessageHandler(Filters.text & ~Filters.command, lambda u, c: 
                    enter_tag_name(u, c) if "edit_tag" not in c.user_data else update_tag_name(u, c))
            ]
        },
        fallbacks=[
            CommandHandler('cancel', lambda u, c: ConversationHandler.END),
            CallbackQueryHandler(back_handler, pattern='^back_to_main$')
        ],
        name="tags_conversation",
        persistent=False
    )
    
    application.add_handler(tags_conv_handler)
    
    logger.info("Handlers de etiquetas configurados")
    
    return tags_conv_handler 