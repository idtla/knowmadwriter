"""
Modelo para las etiquetas del sitio.

Este módulo define la estructura y métodos para trabajar con etiquetas
que se utilizarán en los contenidos del sitio.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from utils.file_operations import read_json_file, write_json_file

# Logger
logger = logging.getLogger(__name__)

# Ruta al archivo de etiquetas
DATA_DIR = Path('data')
TAGS_FILE = DATA_DIR / 'tags.json'

class Tag:
    """
    Clase que representa una etiqueta del sitio.
    """
    
    def __init__(self, name: str, post_count: int = 0, tag_id: Optional[str] = None):
        """
        Inicializa una nueva etiqueta.
        
        Args:
            name: Nombre de la etiqueta
            post_count: Contador de posts con esta etiqueta (por defecto: 0)
            tag_id: Identificador único (opcional)
        """
        self.name = name
        self.post_count = post_count
        self.id = tag_id or self._generate_id()
    
    def _generate_id(self) -> str:
        """
        Genera un ID único para la etiqueta.
        
        Returns:
            ID único basado en el nombre de la etiqueta
        """
        import hashlib
        import time
        
        # Generar un hash basado en el nombre y la hora actual
        unique_string = f"{self.name}_{time.time()}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:8]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte la etiqueta a un diccionario.
        
        Returns:
            Diccionario con los datos de la etiqueta
        """
        return {
            "id": self.id,
            "name": self.name,
            "post_count": self.post_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Tag':
        """
        Crea una instancia de Tag a partir de un diccionario.
        
        Args:
            data: Diccionario con los datos de la etiqueta
            
        Returns:
            Instancia de Tag
        """
        return cls(
            name=data.get("name", ""),
            post_count=data.get("post_count", 0),
            tag_id=data.get("id")
        )
    
    @staticmethod
    def ensure_file_exists() -> None:
        """
        Asegura que el archivo de etiquetas exista.
        Si no existe, crea uno con etiquetas predeterminadas.
        """
        # Asegurar que el directorio existe
        DATA_DIR.mkdir(exist_ok=True)
        
        if not TAGS_FILE.exists():
            # Crear etiquetas por defecto
            default_tags = {
                "tags": [
                    {"id": "web001", "name": "Web", "post_count": 0},
                    {"id": "dev001", "name": "Desarrollo", "post_count": 0},
                    {"id": "mar001", "name": "Marketing", "post_count": 0}
                ]
            }
            
            write_json_file(TAGS_FILE, default_tags)
            logger.info("Archivo de etiquetas creado con valores predeterminados")
    
    @staticmethod
    def get_all() -> List['Tag']:
        """
        Obtiene todas las etiquetas disponibles.
        
        Returns:
            Lista de objetos Tag
        """
        Tag.ensure_file_exists()
        
        try:
            data = read_json_file(TAGS_FILE)
            tags = data.get("tags", [])
            return [Tag.from_dict(tag) for tag in tags]
        except Exception as e:
            logger.error(f"Error al cargar etiquetas: {e}")
            return []
    
    @staticmethod
    def get_by_name(name: str) -> Optional['Tag']:
        """
        Busca una etiqueta por su nombre.
        
        Args:
            name: Nombre de la etiqueta a buscar
            
        Returns:
            Objeto Tag si se encuentra, None en caso contrario
        """
        tags = Tag.get_all()
        for tag in tags:
            if tag.name.lower() == name.lower():
                return tag
        return None
    
    @staticmethod
    def get_by_id(tag_id: str) -> Optional['Tag']:
        """
        Busca una etiqueta por su ID.
        
        Args:
            tag_id: ID de la etiqueta a buscar
            
        Returns:
            Objeto Tag si se encuentra, None en caso contrario
        """
        tags = Tag.get_all()
        for tag in tags:
            if tag.id == tag_id:
                return tag
        return None
    
    @staticmethod
    def save(tag: 'Tag') -> bool:
        """
        Guarda una etiqueta en el archivo.
        Si la etiqueta ya existe (mismo ID), la actualiza.
        Si no existe, la añade.
        
        Args:
            tag: Objeto Tag a guardar
            
        Returns:
            True si se guardó correctamente, False en caso contrario
        """
        Tag.ensure_file_exists()
        
        try:
            data = read_json_file(TAGS_FILE)
            tags = data.get("tags", [])
            
            # Buscar si ya existe la etiqueta por ID
            for i, t in enumerate(tags):
                if t.get("id") == tag.id:
                    # Actualizar la etiqueta existente
                    tags[i] = tag.to_dict()
                    break
            else:
                # Si no se encontró, añadir la nueva etiqueta
                tags.append(tag.to_dict())
            
            data["tags"] = tags
            write_json_file(TAGS_FILE, data)
            logger.info(f"Etiqueta '{tag.name}' guardada correctamente")
            return True
        except Exception as e:
            logger.error(f"Error al guardar etiqueta '{tag.name}': {e}")
            return False
    
    @staticmethod
    def delete(tag_id: str) -> bool:
        """
        Elimina una etiqueta del archivo.
        
        Args:
            tag_id: ID de la etiqueta a eliminar
            
        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        Tag.ensure_file_exists()
        
        try:
            data = read_json_file(TAGS_FILE)
            tags = data.get("tags", [])
            
            # Filtrar la etiqueta a eliminar
            new_tags = [t for t in tags if t.get("id") != tag_id]
            
            # Si no se eliminó ninguna etiqueta, retornar False
            if len(new_tags) == len(tags):
                logger.warning(f"No se encontró la etiqueta con ID '{tag_id}' para eliminar")
                return False
            
            data["tags"] = new_tags
            write_json_file(TAGS_FILE, data)
            logger.info(f"Etiqueta con ID '{tag_id}' eliminada correctamente")
            return True
        except Exception as e:
            logger.error(f"Error al eliminar etiqueta con ID '{tag_id}': {e}")
            return False
    
    @staticmethod
    def increment_post_count(tag_name: str) -> bool:
        """
        Incrementa el contador de posts para una etiqueta específica.
        
        Args:
            tag_name: Nombre de la etiqueta
            
        Returns:
            True si se incrementó correctamente, False en caso contrario
        """
        tag = Tag.get_by_name(tag_name)
        if not tag:
            # Si no existe, la creamos con contador 1
            tag = Tag(name=tag_name, post_count=1)
            return Tag.save(tag)
        
        # Si existe, incrementamos el contador
        tag.post_count += 1
        return Tag.save(tag)
    
    @staticmethod
    def decrement_post_count(tag_name: str) -> bool:
        """
        Decrementa el contador de posts para una etiqueta específica.
        
        Args:
            tag_name: Nombre de la etiqueta
            
        Returns:
            True si se decrementó correctamente, False en caso contrario
        """
        tag = Tag.get_by_name(tag_name)
        if not tag:
            logger.warning(f"No se encontró la etiqueta '{tag_name}' para decrementar")
            return False
        
        # Decrementar el contador (mínimo 0)
        tag.post_count = max(0, tag.post_count - 1)
        return Tag.save(tag)
    
    @staticmethod
    def update_post_counts_from_posts() -> bool:
        """
        Actualiza los contadores de todas las etiquetas basándose en los posts existentes.
        Útil para mantener la consistencia de los datos.
        
        Returns:
            True si se actualizaron correctamente, False en caso contrario
        """
        try:
            from utils.file_operations import read_json_file
            from pathlib import Path
            
            # Cargar los posts
            posts_file = Path('data/posts.json')
            if not posts_file.exists():
                logger.warning("No se encontró el archivo de posts para actualizar contadores")
                return False
            
            posts_data = read_json_file(posts_file)
            posts = posts_data.get("posts", [])
            
            # Reiniciar todos los contadores
            tags = Tag.get_all()
            tag_counts = {tag.name.lower(): 0 for tag in tags}
            
            # Contar posts por etiqueta
            for post in posts:
                post_tags = post.get("tags", [])
                if isinstance(post_tags, list):
                    for tag_name in post_tags:
                        tag_name_lower = tag_name.lower()
                        if tag_name_lower in tag_counts:
                            tag_counts[tag_name_lower] += 1
                        else:
                            tag_counts[tag_name_lower] = 1
            
            # Actualizar etiquetas existentes y crear nuevas si es necesario
            for tag_name, count in tag_counts.items():
                tag = Tag.get_by_name(tag_name)
                if tag:
                    tag.post_count = count
                    Tag.save(tag)
                else:
                    # Si la etiqueta no existe pero hay posts con ella, la creamos
                    if count > 0:
                        new_tag = Tag(name=tag_name, post_count=count)
                        Tag.save(new_tag)
            
            logger.info("Contadores de etiquetas actualizados correctamente")
            return True
        except Exception as e:
            logger.error(f"Error al actualizar contadores de etiquetas: {e}")
            return False 