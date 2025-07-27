"""
Gestión de estados para las conversaciones del bot.
"""

from enum import Enum, auto
from typing import Dict, Any, Optional
import json
import logging
from database.connection import get_db

# Configuración de logging
logger = logging.getLogger(__name__)

class State(Enum):
    """Estados posibles para las conversaciones."""
    IDLE = auto()                 # Estado inicial
    REGISTERING = auto()          # Proceso de registro
    CONFIGURING_SITE = auto()     # Configurando el sitio
    CONFIGURING_SFTP = auto()     # Configurando SFTP
    UPLOADING_TEMPLATE = auto()   # Subiendo plantilla
    CREATING_CONTENT = auto()     # Creando contenido
    UPLOADING_IMAGE = auto()      # Subiendo imagen
    EDITING_CONTENT = auto()      # Editando contenido
    MANAGING_CATEGORIES = auto()  # Gestionando categorías
    MANAGING_FEATURED = auto()    # Gestionando destacados
    CONFIRMING_PUBLISH = auto()   # Confirmando publicación
    CONFIGURING_CUSTOM_PLACEHOLDER = auto()  # Configurando placeholder personalizado

class ConversationData:
    """Clase para gestionar los datos de una conversación."""
    
    def __init__(self, initial_state: State = State.IDLE):
        self.state: State = initial_state
        self.data: Dict[str, Any] = {}
    
    def update_state(self, new_state: State) -> None:
        """Actualiza el estado de la conversación."""
        self.state = new_state
    
    def set_data(self, key: str, value: Any) -> None:
        """Guarda un dato en la conversación."""
        self.data[key] = value
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """Recupera un dato de la conversación."""
        return self.data.get(key, default)
    
    def clear_data(self) -> None:
        """Limpia todos los datos de la conversación."""
        self.data = {}
    
    def remove_data(self, key: str) -> None:
        """Elimina un dato específico de la conversación."""
        if key in self.data:
            del self.data[key]

class StateManager:
    """Gestor centralizado de estados de conversación con persistencia."""
    
    def __init__(self):
        self.conversations: Dict[int, ConversationData] = {}
        self._initialize_from_db()
    
    def _initialize_from_db(self):
        """Carga los estados guardados desde la base de datos."""
        try:
            conn, cur = get_db()
            # Verificar si existe la tabla de estados
            cur.execute('''
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='user_states'
            ''')
            if not cur.fetchone():
                # Crear la tabla si no existe
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS user_states (
                        telegram_id INTEGER PRIMARY KEY,
                        state_enum INTEGER NOT NULL,
                        state_data TEXT
                    )
                ''')
                conn.commit()
                logger.info("Tabla user_states creada correctamente")
            else:
                # Cargar estados existentes
                cur.execute('SELECT telegram_id, state_enum, state_data FROM user_states')
                
                # Importante: verificar si el usuario está registrado y activo
                from models.user import User
                
                rows = cur.fetchall()
                if rows:
                    for row in rows:
                        user_id = row['telegram_id']
                        state_enum = row['state_enum']
                        state_data = json.loads(row['state_data']) if row['state_data'] else {}
                        
                        # Verificar si el usuario está registrado y activo antes de restaurar su estado
                        db_user = User.get_by_telegram_id(user_id)
                        
                        # Solo restaurar si el usuario existe y está activo
                        if db_user and db_user.is_active():
                            conversation = ConversationData(State(state_enum))
                            conversation.data = state_data
                            self.conversations[user_id] = conversation
                            logger.debug(f"Estado restaurado para usuario {user_id}: {State(state_enum).name}")
                        else:
                            # Si el usuario no está activo, eliminarlo de la tabla de estados
                            if db_user:
                                logger.info(f"Usuario {user_id} encontrado pero no activo (estado={db_user.status}). No se restaura estado.")
                            else:
                                logger.info(f"Usuario {user_id} no encontrado en la base de datos. Eliminando su estado.")
                            
                            # Eliminar el estado si el usuario no existe o no está activo
                            cur.execute('DELETE FROM user_states WHERE telegram_id = ?', (user_id,))
                            conn.commit()
                    
                    logger.info(f"Estados cargados desde la base de datos: {len(self.conversations)}")
                else:
                    logger.info("No se encontraron estados guardados en la base de datos")
        except Exception as e:
            logger.error(f"Error al inicializar estados desde la base de datos: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _save_to_db(self, user_id: int):
        """Guarda el estado actual del usuario en la base de datos."""
        try:
            conn, cur = get_db()
            conversation = self.conversations.get(user_id)
            if conversation:
                state_enum = conversation.state.value
                state_data = json.dumps(conversation.data)
                
                cur.execute('''
                    INSERT OR REPLACE INTO user_states (telegram_id, state_enum, state_data)
                    VALUES (?, ?, ?)
                ''', (user_id, state_enum, state_data))
                conn.commit()
                logger.debug(f"Estado del usuario {user_id} guardado en la base de datos")
        except Exception as e:
            logger.error(f"Error al guardar estado en la base de datos: {e}")
    
    def get_conversation(self, user_id: int) -> ConversationData:
        """Obtiene la conversación de un usuario, creándola si no existe."""
        if user_id not in self.conversations:
            self.conversations[user_id] = ConversationData()
        return self.conversations[user_id]
    
    def set_state(self, user_id: int, state: State) -> None:
        """Actualiza el estado de un usuario y lo guarda en la base de datos."""
        self.get_conversation(user_id).update_state(state)
        self._save_to_db(user_id)
        logger.info(f"Estado de usuario {user_id} actualizado a {state.name}")
    
    def get_state(self, user_id: int) -> State:
        """Obtiene el estado actual de un usuario."""
        return self.get_conversation(user_id).state
    
    def set_data(self, user_id: int, key: str, value: Any) -> None:
        """Guarda un dato para un usuario y actualiza la base de datos."""
        self.get_conversation(user_id).set_data(key, value)
        self._save_to_db(user_id)
    
    def get_data(self, user_id: int, key: str, default: Any = None) -> Any:
        """Recupera un dato de un usuario."""
        return self.get_conversation(user_id).get_data(key, default)
    
    def clear_user_data(self, user_id: int) -> None:
        """Limpia todos los datos de un usuario."""
        if user_id in self.conversations:
            self.conversations[user_id].clear_data()
            self._save_to_db(user_id)
    
    def reset_user(self, user_id: int) -> None:
        """Reinicia completamente el estado de un usuario."""
        if user_id in self.conversations:
            del self.conversations[user_id]
            
            # Eliminar de la base de datos
            try:
                conn, cur = get_db()
                cur.execute('DELETE FROM user_states WHERE telegram_id = ?', (user_id,))
                conn.commit()
                logger.info(f"Estado del usuario {user_id} eliminado de la base de datos")
            except Exception as e:
                logger.error(f"Error al eliminar estado de la base de datos: {e}")
    
    def clear_state(self, user_id: int) -> None:
        """Reinicia el estado de la conversación pero mantiene los datos."""
        if user_id in self.conversations:
            self.conversations[user_id].update_state(State.IDLE)
            self._save_to_db(user_id)

# Instancia global del gestor de estados
state_manager = StateManager() 