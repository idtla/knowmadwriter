"""
Operaciones de archivo para el bot de Telegram.

Este módulo proporciona funciones para operaciones comunes con archivos,
como leer y escribir archivos JSON, copiar archivos, etc.
"""

import json
import os
import logging
from pathlib import Path
from typing import Any, Dict, Union, List

# Logger
logger = logging.getLogger(__name__)

def ensure_dir_exists(directory: Union[str, Path]) -> None:
    """
    Asegura que un directorio exista, creándolo si no existe.
    
    Args:
        directory: Ruta del directorio a verificar/crear
    """
    if isinstance(directory, str):
        directory = Path(directory)
    
    try:
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Directorio asegurado: {directory}")
    except Exception as e:
        logger.error(f"Error al crear directorio {directory}: {e}")
        raise

def read_json_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Lee un archivo JSON y devuelve su contenido.
    
    Args:
        file_path: Ruta al archivo JSON
        
    Returns:
        Contenido del archivo JSON como diccionario
        
    Raises:
        FileNotFoundError: Si el archivo no existe
        json.JSONDecodeError: Si el archivo no es un JSON válido
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            logger.debug(f"Archivo JSON leído: {file_path}")
            return data
    except FileNotFoundError:
        logger.error(f"Archivo no encontrado: {file_path}")
        raise
    except json.JSONDecodeError:
        logger.error(f"Error al decodificar JSON en archivo: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error al leer archivo {file_path}: {e}")
        raise

def write_json_file(file_path: Union[str, Path], data: Dict[str, Any], indent: int = 2) -> None:
    """
    Escribe datos en un archivo JSON.
    
    Args:
        file_path: Ruta donde guardar el archivo JSON
        data: Datos a escribir en el archivo
        indent: Número de espacios para indentar el JSON (por defecto 2)
    
    Raises:
        IOError: Si hay un error al escribir el archivo
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)
    
    # Asegurar que el directorio existe
    ensure_dir_exists(file_path.parent)
    
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=indent, ensure_ascii=False)
            logger.debug(f"Archivo JSON escrito: {file_path}")
    except Exception as e:
        logger.error(f"Error al escribir archivo JSON {file_path}: {e}")
        raise

def backup_file(file_path: Union[str, Path], backup_dir: Union[str, Path] = None) -> Path:
    """
    Crea una copia de seguridad de un archivo.
    
    Args:
        file_path: Ruta al archivo a respaldar
        backup_dir: Directorio donde guardar la copia (opcional)
        
    Returns:
        Ruta al archivo de copia de seguridad
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)
    
    # Si no se especifica directorio de backup, usamos el mismo directorio
    if backup_dir is None:
        backup_dir = file_path.parent
    elif isinstance(backup_dir, str):
        backup_dir = Path(backup_dir)
    
    # Asegurar que el directorio de backup existe
    ensure_dir_exists(backup_dir)
    
    # Generar nombre para el archivo de backup
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"{file_path.stem}_{timestamp}{file_path.suffix}"
    backup_path = backup_dir / backup_filename
    
    try:
        import shutil
        shutil.copy2(file_path, backup_path)
        logger.info(f"Backup creado: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Error al crear backup de {file_path}: {e}")
        raise

def file_exists(file_path: Union[str, Path]) -> bool:
    """
    Verifica si un archivo existe.
    
    Args:
        file_path: Ruta al archivo a verificar
        
    Returns:
        True si el archivo existe, False en caso contrario
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)
    
    return file_path.exists() and file_path.is_file() 