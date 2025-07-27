#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Modelo de datos para los placeholders personalizados
"""

import logging
import json
from datetime import datetime
from database.connection import get_db

logger = logging.getLogger(__name__)

class CustomPlaceholder:
    """Clase para manejar placeholders personalizados de las plantillas."""

    def __init__(self, id=None, site_id=None, placeholder_name=None, display_name=None, 
                 placeholder_type="texto", options=None, created_at=None, updated_at=None):
        """
        Inicializar un nuevo placeholder personalizado.

        Args:
            id (int, optional): ID en la base de datos.
            site_id (int): ID del sitio al que pertenece el placeholder.
            placeholder_name (str): Nombre del placeholder como aparece en la plantilla (ej: {{CUSTOM_FIELD}}).
            display_name (str): Nombre para mostrar en el formulario.
            placeholder_type (str, optional): Tipo de dato (texto, numero, url, desplegable).
            options (str, optional): Opciones separadas por coma para tipo desplegable.
            created_at (datetime, optional): Fecha de creación.
            updated_at (datetime, optional): Fecha de última actualización.
        """
        self.id = id
        self.site_id = site_id
        self.placeholder_name = placeholder_name
        self.display_name = display_name
        self.placeholder_type = placeholder_type
        self.options = options
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()

    def to_dict(self):
        """Convertir el objeto a un diccionario."""
        return {
            "id": self.id,
            "site_id": self.site_id,
            "placeholder_name": self.placeholder_name,
            "display_name": self.display_name,
            "placeholder_type": self.placeholder_type,
            "options": self.options,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @classmethod
    def from_dict(cls, data):
        """Crear un objeto de placeholder desde un diccionario."""
        return cls(
            id=data.get("id"),
            site_id=data.get("site_id"),
            placeholder_name=data.get("placeholder_name"),
            display_name=data.get("display_name"),
            placeholder_type=data.get("placeholder_type", "texto"),
            options=data.get("options"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )

    @classmethod
    def from_db_row(cls, row):
        """Crear un objeto de placeholder desde una fila de la base de datos."""
        if not row:
            return None
            
        # Convertir el objeto Row a diccionario
        data = {key: row[key] for key in row.keys()}
                
        return cls.from_dict(data)

    @classmethod
    def create(cls, data):
        """
        Crear un nuevo placeholder en la base de datos.

        Args:
            data (dict): Datos del placeholder.

        Returns:
            CustomPlaceholder: Objeto de placeholder creado.
        """
        conn, cur = get_db()
        
        try:
            cur.execute('''
                INSERT INTO custom_placeholders (site_id, placeholder_name, display_name, placeholder_type, options)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                data.get("site_id"),
                data.get("placeholder_name"),
                data.get("display_name"),
                data.get("placeholder_type", "texto"),
                data.get("options")
            ))
            
            placeholder_id = cur.lastrowid
            conn.commit()
            
            # Obtener el placeholder recién creado
            cur.execute('SELECT * FROM custom_placeholders WHERE id = ?', (placeholder_id,))
            placeholder_data = cur.fetchone()
            
            if placeholder_data:
                return cls.from_db_row(placeholder_data)
            return None
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al crear placeholder personalizado: {e}")
            return None

    @classmethod
    def get_by_id(cls, placeholder_id):
        """
        Obtener un placeholder por su ID.

        Args:
            placeholder_id (int): ID del placeholder.

        Returns:
            CustomPlaceholder: Objeto de placeholder o None si no existe.
        """
        conn, cur = get_db()
        
        try:
            cur.execute('SELECT * FROM custom_placeholders WHERE id = ?', (placeholder_id,))
            placeholder_data = cur.fetchone()
            
            if placeholder_data:
                return cls.from_db_row(placeholder_data)
            return None
        except Exception as e:
            logger.error(f"Error al obtener placeholder por ID: {e}")
            return None

    @classmethod
    def get_by_site_id(cls, site_id):
        """
        Obtener placeholders de un sitio.

        Args:
            site_id (int): ID del sitio.

        Returns:
            list: Lista de objetos CustomPlaceholder.
        """
        conn, cur = get_db()
        
        try:
            cur.execute('SELECT * FROM custom_placeholders WHERE site_id = ?', (site_id,))
            placeholders_data = cur.fetchall()
            
            return [cls.from_db_row(placeholder) for placeholder in placeholders_data]
        except Exception as e:
            logger.error(f"Error al obtener placeholders por site_id: {e}")
            return []

    @classmethod
    def get_by_placeholder_name(cls, site_id, placeholder_name):
        """
        Obtener un placeholder por su nombre.

        Args:
            site_id (int): ID del sitio.
            placeholder_name (str): Nombre del placeholder.

        Returns:
            CustomPlaceholder: Objeto de placeholder o None si no existe.
        """
        conn, cur = get_db()
        
        try:
            cur.execute('SELECT * FROM custom_placeholders WHERE site_id = ? AND placeholder_name = ?', 
                      (site_id, placeholder_name))
            placeholder_data = cur.fetchone()
            
            if placeholder_data:
                return cls.from_db_row(placeholder_data)
            return None
        except Exception as e:
            logger.error(f"Error al obtener placeholder por nombre: {e}")
            return None

    def save(self):
        """
        Guardar o actualizar el placeholder en la base de datos.

        Returns:
            bool: True si tuvo éxito, False en caso contrario.
        """
        conn, cur = get_db()
        
        try:
            # Actualizar la fecha de modificación
            self.updated_at = datetime.now()
            
            if self.id:
                # Actualizar placeholder existente
                cur.execute('''
                    UPDATE custom_placeholders
                    SET site_id = ?, placeholder_name = ?, display_name = ?, 
                        placeholder_type = ?, options = ?, updated_at = ?
                    WHERE id = ?
                ''', (
                    self.site_id,
                    self.placeholder_name,
                    self.display_name,
                    self.placeholder_type,
                    self.options,
                    self.updated_at,
                    self.id
                ))
            else:
                # Insertar nuevo placeholder
                cur.execute('''
                    INSERT INTO custom_placeholders 
                    (site_id, placeholder_name, display_name, placeholder_type, options, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    self.site_id,
                    self.placeholder_name,
                    self.display_name,
                    self.placeholder_type,
                    self.options,
                    self.created_at,
                    self.updated_at
                ))
                self.id = cur.lastrowid
                
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al guardar placeholder: {e}")
            return False

    def delete(self):
        """
        Eliminar el placeholder de la base de datos.

        Returns:
            bool: True si tuvo éxito, False en caso contrario.
        """
        if not self.id:
            return False
            
        conn, cur = get_db()
        
        try:
            cur.execute('DELETE FROM custom_placeholders WHERE id = ?', (self.id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al eliminar placeholder: {e}")
            return False
            
    def validate_value(self, value):
        """
        Valida un valor según el tipo de placeholder.
        
        Args:
            value: Valor a validar.
            
        Returns:
            bool: True si el valor es válido, False en caso contrario.
        """
        if not value:
            return True  # Permitir valores vacíos
            
        if self.placeholder_type == "numero":
            try:
                float(value)
                return True
            except ValueError:
                return False
        elif self.placeholder_type == "url":
            # Validación básica de URL
            return value.startswith(('http://', 'https://'))
        elif self.placeholder_type == "desplegable":
            options_list = [opt.strip() for opt in self.options.split(',')] if self.options else []
            return value in options_list
        else:  # texto
            return True 