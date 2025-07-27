#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Modelo de datos para el contenido
"""

import logging
from datetime import datetime
from database.connection import get_db

logger = logging.getLogger(__name__)

class Content:
    """Clase para manejar contenidos del sitio web."""

    def __init__(self, id=None, site_id=None, title=None, slug=None, html_content=None, 
                 feature_image=None, category=None, tags=None, status="draft", created_at=None):
        """
        Inicializar un nuevo contenido.

        Args:
            id (int, optional): ID en la base de datos.
            site_id (int): ID del sitio.
            title (str): Título del contenido.
            slug (str): Slug para la URL.
            html_content (str, optional): Contenido HTML.
            feature_image (str, optional): URL de la imagen destacada.
            category (str, optional): Categoría del contenido.
            tags (list, optional): Lista de etiquetas.
            status (str, optional): Estado del contenido (draft, published).
            created_at (datetime, optional): Fecha de creación.
        """
        self.id = id
        self.site_id = site_id
        self.title = title
        self.slug = slug
        self.html_content = html_content
        self.feature_image = feature_image
        self.category = category
        self.tags = tags or []
        self.status = status
        self.created_at = created_at or datetime.now()

    def to_dict(self):
        """Convertir el objeto a un diccionario."""
        return {
            "id": self.id,
            "site_id": self.site_id,
            "title": self.title,
            "slug": self.slug,
            "html_content": self.html_content,
            "feature_image": self.feature_image,
            "category": self.category,
            "tags": self.tags,
            "status": self.status,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data):
        """Crear un objeto de contenido desde un diccionario."""
        return cls(
            id=data.get("id"),
            site_id=data.get("site_id"),
            title=data.get("title"),
            slug=data.get("slug"),
            html_content=data.get("html_content"),
            feature_image=data.get("feature_image"),
            category=data.get("category"),
            tags=data.get("tags", []),
            status=data.get("status", "draft"),
            created_at=data.get("created_at")
        )

    @classmethod
    def from_db_row(cls, row):
        """Crear un objeto de contenido desde una fila de la base de datos."""
        if not row:
            return None
            
        # Convertir el objeto Row a diccionario
        data = {key: row[key] for key in row.keys()}
        
        # Convertir el campo tags de texto a lista
        if data.get("tags"):
            try:
                data["tags"] = data["tags"].split(",")
            except:
                data["tags"] = []
        else:
            data["tags"] = []
                
        return cls.from_dict(data)

    @classmethod
    async def create(cls, data):
        """
        Crear un nuevo contenido en la base de datos.

        Args:
            data (dict): Datos del contenido.

        Returns:
            Content: Objeto de contenido creado.
        """
        conn, cur = get_db()
        
        try:
            # Convertir la lista de tags a texto separado por comas
            tags = ",".join(data.get("tags", [])) if data.get("tags") else None
            
            cur.execute('''
                INSERT INTO contents (site_id, title, slug, html_content, feature_image, category, tags, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get("site_id"),
                data.get("title"),
                data.get("slug"),
                data.get("html_content"),
                data.get("feature_image"),
                data.get("category"),
                tags,
                data.get("status", "draft")
            ))
            
            content_id = cur.lastrowid
            conn.commit()
            
            # Obtener el contenido recién creado
            cur.execute('SELECT * FROM contents WHERE id = ?', (content_id,))
            content_data = cur.fetchone()
            
            if content_data:
                return cls.from_db_row(content_data)
            return None
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al crear contenido: {e}")
            return None

    @classmethod
    def get_by_id(cls, content_id):
        """
        Obtener un contenido por su ID.

        Args:
            content_id (int): ID del contenido.

        Returns:
            Content: Objeto de contenido o None si no existe.
        """
        conn, cur = get_db()
        
        try:
            cur.execute('SELECT * FROM contents WHERE id = ?', (content_id,))
            content_data = cur.fetchone()
            
            if content_data:
                return cls.from_db_row(content_data)
            return None
        except Exception as e:
            logger.error(f"Error al obtener contenido por ID: {e}")
            return None

    @classmethod
    def get_by_site_id(cls, site_id):
        """
        Obtener contenidos de un sitio.

        Args:
            site_id (int): ID del sitio.

        Returns:
            list: Lista de objetos Content.
        """
        conn, cur = get_db()
        
        try:
            cur.execute('SELECT * FROM contents WHERE site_id = ? ORDER BY created_at DESC', (site_id,))
            contents_data = cur.fetchall()
            
            return [cls.from_db_row(content) for content in contents_data]
        except Exception as e:
            logger.error(f"Error al obtener contenidos por site_id: {e}")
            return []

    def save(self):
        """
        Guardar o actualizar el contenido en la base de datos.

        Returns:
            bool: True si tuvo éxito, False en caso contrario.
        """
        conn, cur = get_db()
        
        try:
            # Convertir la lista de tags a texto separado por comas
            tags = ",".join(self.tags) if self.tags else None
            
            if self.id:
                # Actualizar contenido existente
                cur.execute('''
                    UPDATE contents
                    SET site_id = ?, title = ?, slug = ?, html_content = ?, 
                        feature_image = ?, category = ?, tags = ?, status = ?
                    WHERE id = ?
                ''', (
                    self.site_id,
                    self.title,
                    self.slug,
                    self.html_content,
                    self.feature_image,
                    self.category,
                    tags,
                    self.status,
                    self.id
                ))
            else:
                # Insertar nuevo contenido
                cur.execute('''
                    INSERT INTO contents (site_id, title, slug, html_content, feature_image, 
                                          category, tags, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    self.site_id,
                    self.title,
                    self.slug,
                    self.html_content,
                    self.feature_image,
                    self.category,
                    tags,
                    self.status
                ))
                self.id = cur.lastrowid
                
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al guardar contenido: {e}")
            return False

    def delete(self):
        """
        Eliminar el contenido de la base de datos.

        Returns:
            bool: True si tuvo éxito, False en caso contrario.
        """
        if not self.id:
            return False
            
        conn, cur = get_db()
        
        try:
            cur.execute('DELETE FROM contents WHERE id = ?', (self.id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al eliminar contenido: {e}")
            return False

    def publish(self):
        """
        Publicar el contenido.

        Returns:
            bool: True si tuvo éxito, False en caso contrario.
        """
        self.status = "published"
        return self.save() 