#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Modelo de datos para los sitios web
"""

import logging
import json
from datetime import datetime
from database.connection import get_db

logger = logging.getLogger(__name__)

class Site:
    """Clase para manejar sitios web de los usuarios."""

    def __init__(self, id=None, user_id=None, name=None, domain=None, sftp_config=None, 
                 template="default", status="active", created_at=None):
        """
        Inicializar un nuevo sitio web.

        Args:
            id (int, optional): ID en la base de datos.
            user_id (int): ID del usuario propietario.
            name (str): Nombre del sitio.
            domain (str): Dominio del sitio.
            sftp_config (dict, optional): Configuración SFTP.
            template (str, optional): Plantilla del sitio.
            status (str, optional): Estado del sitio (active, inactive).
            created_at (datetime, optional): Fecha de creación.
        """
        self.id = id
        self.user_id = user_id
        self.name = name
        self.domain = domain
        self.sftp_config = sftp_config
        self.template = template
        self.status = status
        self.created_at = created_at or datetime.now()
        self._custom_placeholders = None  # Caché de placeholders

    def to_dict(self):
        """Convertir el objeto a un diccionario."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "domain": self.domain,
            "sftp_config": self.sftp_config,
            "template": self.template,
            "status": self.status,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data):
        """Crear un objeto de sitio desde un diccionario."""
        return cls(
            id=data.get("id"),
            user_id=data.get("user_id"),
            name=data.get("name"),
            domain=data.get("domain"),
            sftp_config=data.get("sftp_config"),
            template=data.get("template", "default"),
            status=data.get("status", "active"),
            created_at=data.get("created_at")
        )

    @classmethod
    def from_db_row(cls, row):
        """Crear un objeto de sitio desde una fila de la base de datos."""
        if not row:
            return None
            
        # Convertir el objeto Row a diccionario
        data = {key: row[key] for key in row.keys()}
        
        # Convertir el campo sftp_config de JSON a diccionario
        if data.get("sftp_config"):
            try:
                data["sftp_config"] = json.loads(data["sftp_config"])
            except json.JSONDecodeError:
                data["sftp_config"] = {}
                
        return cls.from_dict(data)

    @classmethod
    async def create(cls, data):
        """
        Crear un nuevo sitio en la base de datos.

        Args:
            data (dict): Datos del sitio.

        Returns:
            Site: Objeto de sitio creado.
        """
        conn, cur = get_db()
        
        try:
            # Convertir la configuración SFTP a JSON
            sftp_config = json.dumps(data.get("sftp_config", {})) if data.get("sftp_config") else None
            
            cur.execute('''
                INSERT INTO sites (user_id, name, domain, sftp_config, template, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                data.get("user_id"),
                data.get("name"),
                data.get("domain"),
                sftp_config,
                data.get("template", "default"),
                data.get("status", "active")
            ))
            
            site_id = cur.lastrowid
            conn.commit()
            
            # Obtener el sitio recién creado
            cur.execute('SELECT * FROM sites WHERE id = ?', (site_id,))
            site_data = cur.fetchone()
            
            if site_data:
                return cls.from_db_row(site_data)
            return None
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al crear sitio: {e}")
            return None

    @classmethod
    def get_by_id(cls, site_id):
        """
        Obtener un sitio por su ID.

        Args:
            site_id (int): ID del sitio.

        Returns:
            Site: Objeto de sitio o None si no existe.
        """
        conn, cur = get_db()
        
        try:
            cur.execute('SELECT * FROM sites WHERE id = ?', (site_id,))
            site_data = cur.fetchone()
            
            if site_data:
                return cls.from_db_row(site_data)
            return None
        except Exception as e:
            logger.error(f"Error al obtener sitio por ID: {e}")
            return None

    @classmethod
    def get_by_user_id(cls, user_id):
        """
        Obtener sitios de un usuario.

        Args:
            user_id (int): ID del usuario.

        Returns:
            list: Lista de objetos Site.
        """
        conn, cur = get_db()
        
        try:
            cur.execute('SELECT * FROM sites WHERE user_id = ?', (user_id,))
            sites_data = cur.fetchall()
            
            return [cls.from_db_row(site) for site in sites_data]
        except Exception as e:
            logger.error(f"Error al obtener sitios por user_id: {e}")
            return []

    def save(self):
        """
        Guardar o actualizar el sitio en la base de datos.

        Returns:
            bool: True si tuvo éxito, False en caso contrario.
        """
        conn, cur = get_db()
        
        try:
            # Convertir la configuración SFTP a JSON
            sftp_config = json.dumps(self.sftp_config) if self.sftp_config else None
            
            if self.id:
                # Actualizar sitio existente
                cur.execute('''
                    UPDATE sites
                    SET user_id = ?, name = ?, domain = ?, sftp_config = ?, template = ?, status = ?
                    WHERE id = ?
                ''', (
                    self.user_id,
                    self.name,
                    self.domain,
                    sftp_config,
                    self.template,
                    self.status,
                    self.id
                ))
            else:
                # Insertar nuevo sitio
                cur.execute('''
                    INSERT INTO sites (user_id, name, domain, sftp_config, template, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    self.user_id,
                    self.name,
                    self.domain,
                    sftp_config,
                    self.template,
                    self.status
                ))
                self.id = cur.lastrowid
                
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al guardar sitio: {e}")
            return False

    def delete(self):
        """
        Eliminar el sitio de la base de datos.

        Returns:
            bool: True si tuvo éxito, False en caso contrario.
        """
        if not self.id:
            return False
            
        conn, cur = get_db()
        
        try:
            cur.execute('DELETE FROM sites WHERE id = ?', (self.id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al eliminar sitio: {e}")
            return False

    def get_custom_placeholders(self, force_refresh=False):
        """
        Obtener todos los placeholders personalizados del sitio.
        
        Args:
            force_refresh (bool, optional): Forzar recarga desde la base de datos.
            
        Returns:
            list: Lista de objetos CustomPlaceholder.
        """
        if self._custom_placeholders is None or force_refresh:
            from models.placeholder import CustomPlaceholder
            self._custom_placeholders = CustomPlaceholder.get_by_site_id(self.id)
        return self._custom_placeholders
        
    def get_custom_placeholder_by_name(self, placeholder_name):
        """
        Obtener un placeholder personalizado por su nombre.
        
        Args:
            placeholder_name (str): Nombre del placeholder (sin {{}}).
            
        Returns:
            CustomPlaceholder: Objeto placeholder o None si no existe.
        """
        from models.placeholder import CustomPlaceholder
        
        # Eliminar llaves si están presentes
        if placeholder_name.startswith('{{') and placeholder_name.endswith('}}'):
            placeholder_name = placeholder_name[2:-2]
            
        return CustomPlaceholder.get_by_placeholder_name(self.id, placeholder_name)
        
    def add_custom_placeholder(self, placeholder_name, display_name, placeholder_type="texto", options=None):
        """
        Añadir un nuevo placeholder personalizado.
        
        Args:
            placeholder_name (str): Nombre del placeholder (sin {{}}).
            display_name (str): Nombre para mostrar en formularios.
            placeholder_type (str, optional): Tipo de dato (texto, numero, url, desplegable).
            options (str, optional): Opciones para tipo desplegable (separadas por coma).
            
        Returns:
            CustomPlaceholder: El nuevo placeholder creado o None en caso de error.
        """
        from models.placeholder import CustomPlaceholder
        
        # Eliminar llaves si están presentes
        if placeholder_name.startswith('{{') and placeholder_name.endswith('}}'):
            placeholder_name = placeholder_name[2:-2]
            
        # Crear el nuevo placeholder
        placeholder_data = {
            "site_id": self.id,
            "placeholder_name": placeholder_name,
            "display_name": display_name,
            "placeholder_type": placeholder_type,
            "options": options
        }
        
        new_placeholder = CustomPlaceholder.create(placeholder_data)
        
        # Actualizar caché
        if new_placeholder and self._custom_placeholders is not None:
            self._custom_placeholders.append(new_placeholder)
            
        return new_placeholder
        
    def update_custom_placeholder(self, placeholder_id, **kwargs):
        """
        Actualizar un placeholder personalizado existente.
        
        Args:
            placeholder_id (int): ID del placeholder a actualizar.
            **kwargs: Campos a actualizar (display_name, placeholder_type, options).
            
        Returns:
            bool: True si se actualizó correctamente, False en caso contrario.
        """
        from models.placeholder import CustomPlaceholder
        
        placeholder = CustomPlaceholder.get_by_id(placeholder_id)
        if not placeholder or placeholder.site_id != self.id:
            return False
            
        # Actualizar campos
        for key, value in kwargs.items():
            if hasattr(placeholder, key):
                setattr(placeholder, key, value)
                
        success = placeholder.save()
        
        # Actualizar caché
        if success and self._custom_placeholders is not None:
            for i, p in enumerate(self._custom_placeholders):
                if p.id == placeholder_id:
                    self._custom_placeholders[i] = placeholder
                    break
                    
        return success
        
    def delete_custom_placeholder(self, placeholder_id):
        """
        Eliminar un placeholder personalizado.
        
        Args:
            placeholder_id (int): ID del placeholder a eliminar.
            
        Returns:
            bool: True si se eliminó correctamente, False en caso contrario.
        """
        from models.placeholder import CustomPlaceholder
        
        placeholder = CustomPlaceholder.get_by_id(placeholder_id)
        if not placeholder or placeholder.site_id != self.id:
            return False
            
        success = placeholder.delete()
        
        # Actualizar caché
        if success and self._custom_placeholders is not None:
            self._custom_placeholders = [p for p in self._custom_placeholders if p.id != placeholder_id]
            
        return success 