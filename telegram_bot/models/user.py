#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Modelo de datos para los usuarios
"""

import logging
from datetime import datetime
from database.connection import get_db

logger = logging.getLogger(__name__)

class User:
    """Clase para manejar usuarios del bot."""

    # Posibles estados para un usuario
    STATUS_ACTIVE = "active"
    STATUS_BLOCKED = "blocked"
    
    # Posibles roles
    ROLE_USER = "user"
    ROLE_ADMIN = "admin"

    def __init__(self, id=None, telegram_id=None, name=None, email=None, status="pre_registered", role="user", created_at=None):
        """
        Inicializar un nuevo usuario.

        Args:
            id (int, optional): ID en la base de datos.
            telegram_id (str): ID único de Telegram.
            name (str): Nombre del usuario.
            email (str, optional): Email del usuario.
            status (str, optional): Estado del usuario (pre_registered, active, inactive).
            role (str, optional): Rol del usuario (user, admin).
            created_at (datetime, optional): Fecha de creación.
        """
        self.id = id
        self.telegram_id = telegram_id
        self.name = name
        self.email = email
        self.status = status
        self.role = role
        self.created_at = created_at or datetime.now()

    def to_dict(self):
        """Convertir el objeto a un diccionario."""
        return {
            "id": self.id,
            "telegram_id": self.telegram_id,
            "name": self.name,
            "email": self.email,
            "status": self.status,
            "role": self.role,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data):
        """Crear un objeto de usuario desde un diccionario."""
        return cls(
            id=data.get("id"),
            telegram_id=data.get("telegram_id"),
            name=data.get("name"),
            email=data.get("email"),
            status=data.get("status", "pre_registered"),
            role=data.get("role", "user"),
            created_at=data.get("created_at")
        )

    def is_pre_registered(self):
        """Verificar si el usuario está pre-registrado."""
        return self.status == "pre_registered"

    def is_active(self):
        """Verificar si el usuario está activo."""
        return self.status == "active"

    def is_admin(self):
        """Verificar si el usuario es administrador."""
        return self.role == "admin"

    @classmethod
    async def create(cls, data):
        """
        Crear un nuevo usuario en la base de datos.

        Args:
            data (dict): Datos del usuario.

        Returns:
            User: Objeto de usuario creado.
        """
        conn, cur = get_db()
        
        try:
            cur.execute('''
                INSERT INTO users (telegram_id, name, email, status, role)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                data.get("telegram_id"),
                data.get("name"),
                data.get("email"),
                data.get("status", "pre_registered"),
                data.get("role", "user")
            ))
            
            user_id = cur.lastrowid
            conn.commit()
            
            # Obtener el usuario recién creado
            cur.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            user_data = cur.fetchone()
            
            if user_data:
                return cls.from_db_row(user_data)
            return None
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al crear usuario: {e}")
            return None

    @classmethod
    def from_db_row(cls, row):
        """Crear un objeto de usuario desde una fila de la base de datos."""
        if not row:
            return None
            
        # Convertir el objeto Row a diccionario
        data = {key: row[key] for key in row.keys()}
        return cls.from_dict(data)

    @classmethod
    def get_by_telegram_id(cls, telegram_id):
        """
        Obtener un usuario por su ID de Telegram.

        Args:
            telegram_id (str): ID de Telegram.

        Returns:
            User: Objeto de usuario o None si no existe.
        """
        conn, cur = get_db()
        
        try:
            cur.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
            user_data = cur.fetchone()
            
            if user_data:
                return cls.from_db_row(user_data)
            return None
        except Exception as e:
            logger.error(f"Error al obtener usuario por telegram_id: {e}")
            return None

    @classmethod
    def get_by_email(cls, email):
        """
        Obtener un usuario por su email.

        Args:
            email (str): Email del usuario.

        Returns:
            User: Objeto de usuario o None si no existe.
        """
        conn, cur = get_db()
        
        try:
            cur.execute('SELECT * FROM users WHERE email = ?', (email,))
            user_data = cur.fetchone()
            
            if user_data:
                return cls.from_db_row(user_data)
            return None
        except Exception as e:
            logger.error(f"Error al obtener usuario por email: {e}")
            return None

    def save(self):
        """
        Guardar o actualizar el usuario en la base de datos.

        Returns:
            bool: True si tuvo éxito, False en caso contrario.
        """
        conn, cur = get_db()
        
        try:
            if self.id:
                # Actualizar usuario existente
                cur.execute('''
                    UPDATE users
                    SET telegram_id = ?, name = ?, email = ?, status = ?, role = ?
                    WHERE id = ?
                ''', (
                    self.telegram_id,
                    self.name,
                    self.email,
                    self.status,
                    self.role,
                    self.id
                ))
            else:
                # Insertar nuevo usuario
                cur.execute('''
                    INSERT INTO users (telegram_id, name, email, status, role)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    self.telegram_id,
                    self.name,
                    self.email,
                    self.status,
                    self.role
                ))
                self.id = cur.lastrowid
                
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al guardar usuario: {e}")
            return False

    def update_status(self, new_status):
        """Actualizar el estado del usuario."""
        self.status = new_status
        return self.save()

    def update_last_active(self):
        """Actualizar la fecha de última actividad del usuario."""
        conn, cur = get_db()
        
        try:
            cur.execute('''
                UPDATE users 
                SET last_active = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (self.id,))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al actualizar última actividad del usuario: {e}")
            return False

    @staticmethod
    def get_all():
        """Obtiene todos los usuarios registrados."""
        conn, cur = get_db()
        cur.execute("SELECT * FROM users")
        rows = cur.fetchall()
        users = []
        for row in rows:
            user = User()
            user.id = row['id']
            user.telegram_id = row['telegram_id']
            user.name = row['name']
            user.email = row['email']
            user.status = row['status']
            user.role = row['role']
            users.append(user)
        return users

    @staticmethod
    def count_all():
        """Cuenta el número total de usuarios registrados."""
        conn, cur = get_db()
        cur.execute("SELECT COUNT(*) as count FROM users")
        result = cur.fetchone()
        return result['count'] if result else 0

    @staticmethod
    def count_active():
        """Cuenta el número de usuarios activos."""
        conn, cur = get_db()
        cur.execute("SELECT COUNT(*) as count FROM users WHERE status = ?", (User.STATUS_ACTIVE,))
        result = cur.fetchone()
        return result['count'] if result else 0

    @staticmethod
    def is_admin(telegram_id):
        """Verifica si un usuario es administrador."""
        user = User.get_by_telegram_id(telegram_id)
        return user and user.role == User.ROLE_ADMIN 