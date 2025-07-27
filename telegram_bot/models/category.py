"""
Modelo para las categorías del sitio.

Este módulo define la estructura y métodos para trabajar con categorías
que se utilizarán en los contenidos del sitio.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from utils.file_operations import read_json_file, write_json_file

# Logger
logger = logging.getLogger(__name__)

# Ruta al archivo de categorías
DATA_DIR = Path('data')
CATEGORIES_FILE = DATA_DIR / 'categories.json'

class Category:
    """
    Clase que representa una categoría del sitio.
    """
    
    def __init__(self, name: str, color: str = "#007BFF", category_id: Optional[str] = None):
        """
        Inicializa una nueva categoría.
        
        Args:
            name: Nombre de la categoría
            color: Color en formato hexadecimal (por defecto: azul)
            category_id: Identificador único (opcional)
        """
        self.name = name
        self.color = color
        self.id = category_id or self._generate_id()
    
    def _generate_id(self) -> str:
        """
        Genera un ID único para la categoría.
        
        Returns:
            ID único basado en el nombre de la categoría
        """
        import hashlib
        import time
        
        # Generar un hash basado en el nombre y la hora actual
        unique_string = f"{self.name}_{time.time()}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:8]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte la categoría a un diccionario.
        
        Returns:
            Diccionario con los datos de la categoría
        """
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Category':
        """
        Crea una instancia de Category a partir de un diccionario.
        
        Args:
            data: Diccionario con los datos de la categoría
            
        Returns:
            Instancia de Category
        """
        return cls(
            name=data.get("name", ""),
            color=data.get("color", "#007BFF"),
            category_id=data.get("id")
        )
    
    @staticmethod
    def ensure_file_exists() -> None:
        """
        Asegura que el archivo de categorías exista.
        Si no existe, crea uno con categorías predeterminadas.
        """
        # Asegurar que el directorio existe
        DATA_DIR.mkdir(exist_ok=True)
        
        if not CATEGORIES_FILE.exists():
            # Crear categorías por defecto
            default_categories = {
                "categories": [
                    {"id": "gen001", "name": "General", "color": "#007BFF"},
                    {"id": "tech01", "name": "Tecnología", "color": "#28A745"},
                    {"id": "biz001", "name": "Negocios", "color": "#DC3545"}
                ]
            }
            
            write_json_file(CATEGORIES_FILE, default_categories)
            logger.info("Archivo de categorías creado con valores predeterminados")
    
    @staticmethod
    def get_all() -> List['Category']:
        """
        Obtiene todas las categorías disponibles.
        
        Returns:
            Lista de objetos Category
        """
        Category.ensure_file_exists()
        
        try:
            data = read_json_file(CATEGORIES_FILE)
            categories = data.get("categories", [])
            return [Category.from_dict(cat) for cat in categories]
        except Exception as e:
            logger.error(f"Error al cargar categorías: {e}")
            return []
    
    @staticmethod
    def get_by_name(name: str) -> Optional['Category']:
        """
        Busca una categoría por su nombre.
        
        Args:
            name: Nombre de la categoría a buscar
            
        Returns:
            Objeto Category si se encuentra, None en caso contrario
        """
        categories = Category.get_all()
        for category in categories:
            if category.name.lower() == name.lower():
                return category
        return None
    
    @staticmethod
    def get_by_id(category_id: str) -> Optional['Category']:
        """
        Busca una categoría por su ID.
        
        Args:
            category_id: ID de la categoría a buscar
            
        Returns:
            Objeto Category si se encuentra, None en caso contrario
        """
        categories = Category.get_all()
        for category in categories:
            if category.id == category_id:
                return category
        return None
    
    @staticmethod
    def save(category: 'Category') -> bool:
        """
        Guarda una categoría en el archivo.
        Si la categoría ya existe (mismo ID), la actualiza.
        Si no existe, la añade.
        
        Args:
            category: Objeto Category a guardar
            
        Returns:
            True si se guardó correctamente, False en caso contrario
        """
        Category.ensure_file_exists()
        
        try:
            data = read_json_file(CATEGORIES_FILE)
            categories = data.get("categories", [])
            
            # Buscar si ya existe la categoría por ID
            for i, cat in enumerate(categories):
                if cat.get("id") == category.id:
                    # Actualizar la categoría existente
                    categories[i] = category.to_dict()
                    break
            else:
                # Si no se encontró, añadir la nueva categoría
                categories.append(category.to_dict())
            
            data["categories"] = categories
            write_json_file(CATEGORIES_FILE, data)
            logger.info(f"Categoría '{category.name}' guardada correctamente")
            return True
        except Exception as e:
            logger.error(f"Error al guardar categoría '{category.name}': {e}")
            return False
    
    @staticmethod
    def delete(category_id: str) -> bool:
        """
        Elimina una categoría del archivo.
        
        Args:
            category_id: ID de la categoría a eliminar
            
        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        Category.ensure_file_exists()
        
        try:
            data = read_json_file(CATEGORIES_FILE)
            categories = data.get("categories", [])
            
            # Filtrar la categoría a eliminar
            new_categories = [cat for cat in categories if cat.get("id") != category_id]
            
            # Si no se eliminó ninguna categoría, retornar False
            if len(new_categories) == len(categories):
                logger.warning(f"No se encontró la categoría con ID '{category_id}' para eliminar")
                return False
            
            data["categories"] = new_categories
            write_json_file(CATEGORIES_FILE, data)
            logger.info(f"Categoría con ID '{category_id}' eliminada correctamente")
            return True
        except Exception as e:
            logger.error(f"Error al eliminar categoría con ID '{category_id}': {e}")
            return False 