"""
Manejadores para el módulo de administración.

Este archivo contiene los manejadores para las funcionalidades administrativas,
incluyendo gestión de usuarios, estadísticas y configuración global.
"""

import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler, MessageHandler, filters

from core.states import State, state_manager
from models.user import User
from database.connection import get_db

logger = logging.getLogger(__name__)

# Estados para la conversación de administración
ADMIN_WAITING_USER_ID = 1
ADMIN_WAITING_ROLE = 2
ADMIN_WAITING_STATUS = 3
ADMIN_WAITING_CONFIRM = 4

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /admin."""
    user = update.effective_user
    logger.info(f"Usuario {user.id} ha solicitado acceso al panel de administración")
    
    # Verificar si el usuario es administrador
    db_user = User.get_by_telegram_id(user.id)
    if not db_user or db_user.role != "admin":
        await update.message.reply_text(
            "⛔ No tienes permisos de administrador para acceder a esta función.",
            parse_mode=ParseMode.HTML
        )
        return
    
    # Mostrar el panel de administración
    await send_admin_panel(update, context)

async def send_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE, is_new_message=True):
    """Envía el panel de administración."""
    keyboard = [
        [
            InlineKeyboardButton("👥 Gestión Usuarios", callback_data="admin:users"),
            InlineKeyboardButton("📊 Estadísticas", callback_data="admin:stats")
        ],
        [
            InlineKeyboardButton("⚙️ Configuración", callback_data="admin:config"),
            InlineKeyboardButton("« Menú Principal", callback_data="menu:main")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "🔐 <b>PANEL DE ADMINISTRACIÓN</b>\n\n"
        "Bienvenido al panel de administración. Desde aquí puedes:\n"
        "• Gestionar usuarios (añadir, bloquear, cambiar roles)\n"
        "• Ver estadísticas del sistema\n"
        "• Configurar parámetros globales"
    )
    
    if is_new_message and hasattr(update, 'message'):
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    elif hasattr(update, 'callback_query'):
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else:
        # Fallback por si hay algún caso no contemplado
        chat_id = update.effective_chat.id
        await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def admin_users_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el panel de gestión de usuarios."""
    keyboard = [
        [
            InlineKeyboardButton("➕ Nuevo Usuario", callback_data="admin:user_new"),
            InlineKeyboardButton("📋 Listar Usuarios", callback_data="admin:user_list")
        ],
        [
            InlineKeyboardButton("🔄 Cambiar Rol", callback_data="admin:user_role"),
            InlineKeyboardButton("❌ Bloquear Usuario", callback_data="admin:user_block")
        ],
        [
            InlineKeyboardButton("« Volver", callback_data="admin:panel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text="👥 <b>GESTIÓN DE USUARIOS</b>\n\n"
             "Selecciona una acción para gestionar los usuarios del sistema:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lista los usuarios registrados en el sistema."""
    users = User.get_all()
    
    if not users:
        await update.callback_query.edit_message_text(
            text="👥 <b>LISTADO DE USUARIOS</b>\n\n"
                 "No hay usuarios registrados en el sistema.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Volver", callback_data="admin:users")
            ]]),
            parse_mode=ParseMode.HTML
        )
        return
    
    # Añadir cabecera para el listado
    header = "<b>NOMBRE</b>   <b>ID</b>   <b>ROL</b>   <b>ESTADO</b>"
    
    # Crear texto con información de usuarios (limitado a 10 para no sobrepasar límites de Telegram)
    user_info = []
    for u in users[:10]:
        role = "👑 Admin" if u.role == "admin" else "👤 Usuario"
        status = "Activo" if u.status == "active" else "Inactivo"
        status_emoji = "✅" if u.status == "active" else "❌"
        user_info.append(f"• {u.name} (@{u.telegram_id}) - {role} - {status_emoji} {status}")
    
    user_text = "\n".join(user_info)
    
    await update.callback_query.edit_message_text(
        text=f"👥 <b>LISTADO DE USUARIOS</b>\n\n"
             f"{header}\n"
             f"────────────────────\n"
             f"{user_text}\n\n"
             f"Mostrando {min(10, len(users))} de {len(users)} usuarios.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("« Volver", callback_data="admin:users")
        ]]),
        parse_mode=ParseMode.HTML
    )

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra estadísticas del sistema."""
    # Contar usuarios
    total_users = User.count_all()
    active_users = User.count_active()
    admin_users = sum(1 for u in User.get_all() if u.role == "admin")
    
    # Obtener estadísticas de contenido
    conn, cur = get_db()
    cur.execute("SELECT COUNT(*) as count FROM user_config WHERE key LIKE 'sftp_%'")
    sftp_configs = cur.fetchone()['count'] // 4  # Aproximadamente 4 campos por configuración
    
    await update.callback_query.edit_message_text(
        text="📊 <b>ESTADÍSTICAS DEL SISTEMA</b>\n\n"
             f"<b>Usuarios:</b>\n"
             f"• Total: {total_users}\n"
             f"• Activos: {active_users}\n"
             f"• Administradores: {admin_users}\n\n"
             f"<b>Conexiones SFTP:</b>\n"
             f"• Configuradas: {sftp_configs}\n\n"
             f"<b>Fecha del servidor:</b>\n"
             f"• {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
             f"Esta pantalla se ampliará con más estadísticas en próximas versiones.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("« Volver", callback_data="admin:panel")
        ]]),
        parse_mode=ParseMode.HTML
    )

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja los callbacks específicos de administración."""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split(':')
    action = data[1] if len(data) > 1 else None
    
    # Verificar que el usuario es admin
    user = User.get_by_telegram_id(update.effective_user.id)
    if not user or user.role != "admin":
        await query.edit_message_text(
            "⛔ No tienes permisos de administrador para acceder a esta función.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Menú Principal", callback_data="menu:main")
            ]])
        )
        return
    
    # Procesar la acción
    if action == "panel":
        await send_admin_panel(update, context, is_new_message=False)
    elif action == "users":
        await admin_users_panel(update, context)
    elif action == "stats":
        await show_stats(update, context)
    elif action == "user_list":
        await list_users(update, context)
    elif action == "user_new":
        # Implementación pendiente
        await query.edit_message_text(
            "👤 <b>AÑADIR NUEVO USUARIO</b>\n\n"
            "Esta función te permitirá pre-registrar nuevos usuarios en el sistema.\n\n"
            "Estamos implementando esta función. ¡Estará disponible pronto!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Volver", callback_data="admin:users")
            ]]),
            parse_mode=ParseMode.HTML
        )
    elif action == "user_role":
        # Implementación pendiente
        await query.edit_message_text(
            "👤 <b>CAMBIAR ROL DE USUARIO</b>\n\n"
            "Esta función te permitirá cambiar el rol de los usuarios entre normal y administrador.\n\n"
            "Estamos implementando esta función. ¡Estará disponible pronto!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Volver", callback_data="admin:users")
            ]]),
            parse_mode=ParseMode.HTML
        )
    elif action == "user_block":
        # Implementación pendiente
        await query.edit_message_text(
            "👤 <b>BLOQUEAR USUARIO</b>\n\n"
            "Esta función te permitirá bloquear o desbloquear usuarios.\n\n"
            "Estamos implementando esta función. ¡Estará disponible pronto!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Volver", callback_data="admin:users")
            ]]),
            parse_mode=ParseMode.HTML
        )
    elif action == "config":
        # Implementación pendiente
        await query.edit_message_text(
            "⚙️ <b>CONFIGURACIÓN GLOBAL</b>\n\n"
            "Esta función te permitirá configurar parámetros globales del sistema.\n\n"
            "Estamos implementando esta función. ¡Estará disponible pronto!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Volver", callback_data="admin:panel")
            ]]),
            parse_mode=ParseMode.HTML
        )
    else:
        await query.edit_message_text(
            "⚠️ Acción no reconocida. Por favor, intenta nuevamente.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Volver", callback_data="admin:panel")
            ]])
        )

def setup_admin_handlers(application):
    """Configura los manejadores para el módulo de administración."""
    application.add_handler(CommandHandler("admin", admin_command))
    
    # Callback para gestionar las interacciones con el menú de administración
    application.add_handler(CallbackQueryHandler(
        admin_callback_handler, pattern="^admin:"
    ))
    
    logger.info("Manejadores de administración configurados correctamente") 