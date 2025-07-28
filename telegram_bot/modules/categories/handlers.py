"""
Handlers para el módulo de categorías.

Este módulo contiene los handlers para gestionar categorías en el sitio web, 
incluyendo creación, edición, visualización y eliminación de categorías.
"""

import json
import os
import logging
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler

# Importar desde nuestro módulo de compatibilidad
from utils.compat import Filters, CallbackContext

from utils.breadcrumbs import breadcrumb
from utils.file_operations import read_json_file, write_json_file

# Estados para la conversación
SELECTING_ACTION, SELECT_CATEGORY, CREATING_CATEGORY, ENTER_CATEGORY_NAME, ENTER_CATEGORY_COLOR = range(5)

# Paths
DATA_DIR = Path('data')
CATEGORIES_FILE = DATA_DIR / 'categories.json'
POSTS_FILE = DATA_DIR / 'posts.json'

# Asegurar que los directorios existan
DATA_DIR.mkdir(exist_ok=True)

# Logger
logger = logging.getLogger(__name__)

# Funciones de utilidad
def load_categories():
    """Carga las categorías del archivo JSON."""
    if not CATEGORIES_FILE.exists():
        # Crear estructura inicial si no existe
        default_data = {
            "categories": [
                {"name": "General", "color": "#007BFF"},
                {"name": "Tecnología", "color": "#28A745"},
                {"name": "Negocios", "color": "#DC3545"}
            ]
        }
        write_json_file(CATEGORIES_FILE, default_data)
        return default_data
    return read_json_file(CATEGORIES_FILE)

def save_categories(categories_data):
    """Guarda las categorías en el archivo JSON."""
    write_json_file(CATEGORIES_FILE, categories_data)

# Handlers
@breadcrumb
async def start_categories(update: Update, context: CallbackContext) -> int:
    """Inicia el flujo de gestión de categorías."""
    keyboard = [
        [
            InlineKeyboardButton("🔍 Ver Categorías", callback_data="view_categories"),
            InlineKeyboardButton("➕ Nueva Categoría", callback_data="new_category")
        ],
        [
            InlineKeyboardButton("✏️ Editar Categoría", callback_data="edit_category"),
            InlineKeyboardButton("🗑️ Eliminar Categoría", callback_data="delete_category")
        ],
        [InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        "🏷️ *Gestión de Categorías*\n\n"
        "Puedes ver, crear, editar o eliminar categorías para tus posts.\n\n"
        "Selecciona una opción:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return SELECTING_ACTION

@breadcrumb
async def view_categories(update: Update, context: CallbackContext) -> int:
    """Muestra la lista de categorías existentes."""
    categories_data = load_categories()
    categories = categories_data.get("categories", [])
    
    # Intentar cargar posts para contar cuántos hay por categoría
    try:
        posts_data = read_json_file(POSTS_FILE)
        posts = posts_data.get("posts", [])
    except (FileNotFoundError, json.JSONDecodeError):
        posts = []
    
    message = "📋 *Categorías Disponibles*\n\n"
    
    if not categories:
        message += "No hay categorías definidas."
    else:
        # Añadir cabecera para el listado
        message += "*NOMBRE*   *COLOR*   *POSTS*\n"
        message += "─────────────────────\n\n"
        
        for i, category in enumerate(categories, 1):
            # Contar posts en esta categoría
            post_count = sum(1 for post in posts if post.get("category") == category["name"])
            
            message += f"{i}. *{category['name']}*\n"
            message += f"   🎨 Color: {category['color']}\n"
            message += f"   📝 Posts: {post_count}\n\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Volver", callback_data="back_to_categories")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return SELECTING_ACTION

@breadcrumb
async def new_category(update: Update, context: CallbackContext) -> int:
    """Inicia el proceso de creación de una nueva categoría."""
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        "➕ *Crear Nueva Categoría*\n\n"
        "Por favor, ingresa el nombre para la nueva categoría:",
        parse_mode='Markdown'
    )
    return ENTER_CATEGORY_NAME

@breadcrumb
async def enter_category_name(update: Update, context: CallbackContext) -> int:
    """Recibe el nombre de la categoría y pide el color."""
    category_name = update.message.text.strip()
    
    # Validar que el nombre no esté vacío
    if not category_name:
        await update.message.reply_text(
            "⚠️ El nombre de la categoría no puede estar vacío. Por favor, intenta de nuevo."
        )
        return ENTER_CATEGORY_NAME
    
    # Validar que no exista ya una categoría con ese nombre
    categories_data = load_categories()
    categories = categories_data.get("categories", [])
    
    if any(category["name"].lower() == category_name.lower() for category in categories):
        await update.message.reply_text(
            "⚠️ Ya existe una categoría con ese nombre. Por favor, elige otro nombre."
        )
        return ENTER_CATEGORY_NAME
    
    # Guardar el nombre en el contexto
    context.user_data["new_category_name"] = category_name
    
    await update.message.reply_text(
        f"✅ Nombre de categoría: *{category_name}*\n\n"
        "Ahora, ingresa el color para esta categoría en formato hexadecimal (ejemplo: #FF0000):\n\n"
        "🎨 [Selector de Colores](https://htmlcolorcodes.com/es/) para ayudarte a elegir.",
        parse_mode='Markdown',
        disable_web_page_preview=True
    )
    return ENTER_CATEGORY_COLOR

@breadcrumb
async def enter_category_color(update: Update, context: CallbackContext) -> int:
    """Recibe el color de la categoría y la crea."""
    category_color = update.message.text.strip()
    
    # Validar el formato del color (hexadecimal)
    import re
    if not re.match(r'^#(?:[0-9a-fA-F]{3}){1,2}$', category_color):
        await update.message.reply_text(
            "⚠️ El color debe estar en formato hexadecimal (ejemplo: #FF0000). Por favor, intenta de nuevo."
        )
        return ENTER_CATEGORY_COLOR
    
    # Obtener el nombre guardado previamente
    category_name = context.user_data.get("new_category_name")
    
    # Guardar la nueva categoría
    categories_data = load_categories()
    categories = categories_data.get("categories", [])
    categories.append({"name": category_name, "color": category_color})
    categories_data["categories"] = categories
    save_categories(categories_data)
    
    # Limpiar datos de usuario
    if "new_category_name" in context.user_data:
        del context.user_data["new_category_name"]
    
    # Mostrar mensaje de confirmación
    keyboard = [[InlineKeyboardButton("🔙 Volver a Categorías", callback_data="back_to_categories")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"✅ ¡Categoría *{category_name}* creada exitosamente!\n\n"
        f"🎨 Color: {category_color}",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return SELECTING_ACTION

@breadcrumb
async def select_category_to_edit(update: Update, context: CallbackContext) -> int:
    """Muestra la lista de categorías para seleccionar una a editar."""
    categories_data = load_categories()
    categories = categories_data.get("categories", [])
    
    if not categories:
        keyboard = [[InlineKeyboardButton("🔙 Volver", callback_data="back_to_categories")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(
            "❌ No hay categorías para editar.",
            reply_markup=reply_markup
        )
        return SELECTING_ACTION
    
    keyboard = []
    for category in categories:
        keyboard.append([
            InlineKeyboardButton(
                f"{category['name']} ({category['color']})",
                callback_data=f"edit_{category['name']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="back_to_categories")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        "✏️ *Editar Categoría*\n\n"
        "Selecciona la categoría que deseas editar:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return SELECT_CATEGORY

@breadcrumb
async def edit_category(update: Update, context: CallbackContext) -> int:
    """Muestra opciones para editar una categoría específica."""
    category_name = update.callback_query.data.split("_")[1]
    context.user_data["edit_category"] = category_name
    
    keyboard = [
        [
            InlineKeyboardButton("📝 Cambiar Nombre", callback_data="change_name"),
            InlineKeyboardButton("🎨 Cambiar Color", callback_data="change_color")
        ],
        [InlineKeyboardButton("🔙 Volver", callback_data="back_to_edit_select")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Buscar la categoría para mostrar sus datos actuales
    categories_data = load_categories()
    categories = categories_data.get("categories", [])
    category = next((c for c in categories if c["name"] == category_name), None)
    
    if not category:
        await update.callback_query.answer("Categoría no encontrada")
        return await select_category_to_edit(update, context)
    
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        f"✏️ *Editar Categoría: {category_name}*\n\n"
        f"Datos actuales:\n"
        f"- Nombre: {category['name']}\n"
        f"- Color: {category['color']}\n\n"
        f"¿Qué deseas modificar?",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return SELECT_CATEGORY

@breadcrumb
async def change_category_name(update: Update, context: CallbackContext) -> int:
    """Solicita el nuevo nombre para la categoría."""
    category_name = context.user_data.get("edit_category")
    
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        f"📝 *Cambiar Nombre de Categoría*\n\n"
        f"Categoría actual: *{category_name}*\n\n"
        f"Por favor, ingresa el nuevo nombre para esta categoría:",
        parse_mode='Markdown'
    )
    
    context.user_data["edit_action"] = "name"
    return ENTER_CATEGORY_NAME

@breadcrumb
async def change_category_color(update: Update, context: CallbackContext) -> int:
    """Solicita el nuevo color para la categoría."""
    category_name = context.user_data.get("edit_category")
    
    # Buscar el color actual
    categories_data = load_categories()
    categories = categories_data.get("categories", [])
    category = next((c for c in categories if c["name"] == category_name), None)
    
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        f"🎨 *Cambiar Color de Categoría*\n\n"
        f"Categoría: *{category_name}*\n"
        f"Color actual: {category['color']}\n\n"
        f"Por favor, ingresa el nuevo color en formato hexadecimal (ejemplo: #FF0000):\n\n"
        f"🎨 [Selector de Colores](https://htmlcolorcodes.com/es/) para ayudarte a elegir.",
        parse_mode='Markdown',
        disable_web_page_preview=True
    )
    
    context.user_data["edit_action"] = "color"
    return ENTER_CATEGORY_COLOR

@breadcrumb
async def update_category_field(update: Update, context: CallbackContext) -> int:
    """Actualiza el campo de la categoría (nombre o color)."""
    category_name = context.user_data.get("edit_category")
    edit_action = context.user_data.get("edit_action")
    new_value = update.message.text.strip()
    
    categories_data = load_categories()
    categories = categories_data.get("categories", [])
    
    # Validaciones según el campo a editar
    if edit_action == "name":
        # Verificar que no exista otra categoría con ese nombre
        if any(c["name"].lower() == new_value.lower() and c["name"] != category_name for c in categories):
            await update.message.reply_text(
                "⚠️ Ya existe otra categoría con ese nombre. Por favor, elige un nombre diferente."
            )
            return ENTER_CATEGORY_NAME
        
        field_name = "nombre"
    elif edit_action == "color":
        # Validar formato de color hexadecimal
        import re
        if not re.match(r'^#(?:[0-9a-fA-F]{3}){1,2}$', new_value):
            await update.message.reply_text(
                "⚠️ El color debe estar en formato hexadecimal (ejemplo: #FF0000). Por favor, intenta de nuevo."
            )
            return ENTER_CATEGORY_COLOR
        
        field_name = "color"
    else:
        await update.message.reply_text("❌ Error: Acción de edición no válida.")
        return SELECTING_ACTION
    
    # Actualizar la categoría
    for category in categories:
        if category["name"] == category_name:
            # Si estamos actualizando el nombre, también actualizar la categoría en los posts
            if edit_action == "name":
                try:
                    posts_data = read_json_file(POSTS_FILE)
                    posts = posts_data.get("posts", [])
                    for post in posts:
                        if post.get("category") == category_name:
                            post["category"] = new_value
                    write_json_file(POSTS_FILE, posts_data)
                except Exception as e:
                    logger.error(f"Error al actualizar categoría en posts: {e}")
                
                category["name"] = new_value
            else:  # Estamos actualizando el color
                category["color"] = new_value
            break
    
    save_categories(categories_data)
    
    # Limpiar datos de usuario
    if "edit_category" in context.user_data:
        del context.user_data["edit_category"]
    if "edit_action" in context.user_data:
        del context.user_data["edit_action"]
    
    # Mostrar mensaje de confirmación
    keyboard = [[InlineKeyboardButton("🔙 Volver a Categorías", callback_data="back_to_categories")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"✅ ¡{field_name.capitalize()} de categoría actualizado exitosamente!",
        reply_markup=reply_markup
    )
    return SELECTING_ACTION

@breadcrumb
async def select_category_to_delete(update: Update, context: CallbackContext) -> int:
    """Muestra la lista de categorías para seleccionar una a eliminar."""
    categories_data = load_categories()
    categories = categories_data.get("categories", [])
    
    if not categories:
        keyboard = [[InlineKeyboardButton("🔙 Volver", callback_data="back_to_categories")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(
            "❌ No hay categorías para eliminar.",
            reply_markup=reply_markup
        )
        return SELECTING_ACTION
    
    keyboard = []
    for category in categories:
        keyboard.append([
            InlineKeyboardButton(
                f"🗑️ {category['name']}",
                callback_data=f"delete_{category['name']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="back_to_categories")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        "🗑️ *Eliminar Categoría*\n\n"
        "⚠️ ADVERTENCIA: Al eliminar una categoría, los posts asociados a ella se marcarán como 'Sin categoría'.\n\n"
        "Selecciona la categoría que deseas eliminar:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return SELECT_CATEGORY

@breadcrumb
async def delete_category(update: Update, context: CallbackContext) -> int:
    """Elimina una categoría y actualiza los posts asociados."""
    category_name = update.callback_query.data.split("_")[1]
    
    categories_data = load_categories()
    categories = categories_data.get("categories", [])
    
    # Verificar si la categoría existe
    if not any(c["name"] == category_name for c in categories):
        await update.callback_query.answer("Categoría no encontrada")
        return await select_category_to_delete(update, context)
    
    # Eliminar la categoría
    categories_data["categories"] = [c for c in categories if c["name"] != category_name]
    save_categories(categories_data)
    
    # Actualizar los posts que tenían esta categoría
    try:
        posts_data = read_json_file(POSTS_FILE)
        posts = posts_data.get("posts", [])
        updated_count = 0
        
        for post in posts:
            if post.get("category") == category_name:
                post["category"] = "Sin categoría"
                updated_count += 1
        
        write_json_file(POSTS_FILE, posts_data)
        category_update_msg = f"\n\n✅ {updated_count} posts actualizados a 'Sin categoría'."
    except Exception as e:
        logger.error(f"Error al actualizar posts: {e}")
        category_update_msg = "\n\n⚠️ No se pudieron actualizar los posts asociados."
    
    keyboard = [[InlineKeyboardButton("🔙 Volver a Categorías", callback_data="back_to_categories")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        f"✅ Categoría *{category_name}* eliminada exitosamente.{category_update_msg}",
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
    
    elif data == "back_to_categories":
        # Volver al menú de categorías
        return await start_categories(update, context)
    
    elif data == "back_to_edit_select":
        # Volver al selector de categorías para editar
        return await select_category_to_edit(update, context)
    
    await query.answer("Acción no reconocida")
    return SELECTING_ACTION

def setup_categories_handlers(application):
    """Configura los handlers para el módulo de categorías."""
    # Crear directorio y archivo de categorías si no existen
    if not CATEGORIES_FILE.exists():
        load_categories()  # Esto creará el archivo con categorías por defecto
    
    # Definir el conversation handler
    categories_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_categories, pattern='^/categorias$')],
        states={
            SELECTING_ACTION: [
                CallbackQueryHandler(view_categories, pattern='^view_categories$'),
                CallbackQueryHandler(new_category, pattern='^new_category$'),
                CallbackQueryHandler(select_category_to_edit, pattern='^edit_category$'),
                CallbackQueryHandler(select_category_to_delete, pattern='^delete_category$'),
                CallbackQueryHandler(back_handler, pattern='^back_to_')
            ],
            SELECT_CATEGORY: [
                CallbackQueryHandler(edit_category, pattern='^edit_'),
                CallbackQueryHandler(delete_category, pattern='^delete_'),
                CallbackQueryHandler(change_category_name, pattern='^change_name$'),
                CallbackQueryHandler(change_category_color, pattern='^change_color$'),
                CallbackQueryHandler(back_handler, pattern='^back_to_')
            ],
            ENTER_CATEGORY_NAME: [
                MessageHandler(Filters.text & ~Filters.command, enter_category_name)
            ],
            ENTER_CATEGORY_COLOR: [
                MessageHandler(Filters.text & ~Filters.command, enter_category_color)
            ],
            CREATING_CATEGORY: [
                MessageHandler(Filters.text & ~Filters.command, update_category_field)
            ]
        },
        fallbacks=[
            CommandHandler('cancel', lambda u, c: ConversationHandler.END),
            CallbackQueryHandler(back_handler, pattern='^back_to_main$')
        ],
        name="categories_conversation",
        persistent=False
    )
    
    application.add_handler(categories_conv_handler)
    
    logger.info("Handlers de categorías configurados")
    
    return categories_conv_handler 