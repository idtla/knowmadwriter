#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utilidades para procesar HTML y manejar placeholders
"""

import re
import logging
from bs4 import BeautifulSoup
import html5lib

logger = logging.getLogger(__name__)

# Placeholders definidos en el sistema
PLACEHOLDERS = {
    "{{TITLE}}": {
        "description": "Título del post",
        "required": True
    },
    "{{SITE_NAME}}": {
        "description": "Nombre del sitio",
        "required": True
    },
    "{{META_DESCRIPTION}}": {
        "description": "Meta descripción del post",
        "required": True
    },
    "{{FEATURE_IMAGE}}": {
        "description": "Imagen principal del post",
        "required": True
    },
    "{{PUBLISHED_TIME}}": {
        "description": "Fecha de publicación",
        "required": True
    },
    "{{CATEGORY}}": {
        "description": "Categoría asignada",
        "required": True
    },
    "{{LAST_MODIFIED}}": {
        "description": "Última fecha de modificación",
        "required": False
    },
    "{{SITE_URL}}": {
        "description": "Dominio del sitio",
        "required": True
    },
    "{{ARTICLE_URL}}": {
        "description": "URL final del artículo (dominio + slug)",
        "required": True
    },
    "{{CONTENT}}": {
        "description": "Contenido en HTML",
        "required": True
    },
    "{{FEATURE_IMAGE_ALT}}": {
        "description": "Texto alternativo de imagen",
        "required": False
    },
    "{{READING_TIME}}": {
        "description": "Tiempo estimado de lectura",
        "required": False
    },
    "{{SOURCE_LIST}}": {
        "description": "Lista de fuentes",
        "required": False
    },
    "{{SLUG}}": {
        "description": "URL amigable generado a partir del título",
        "required": True
    },
    "{{POST_MONTH}}": {
        "description": "Nombre del mes de publicación (Ej: Ene, Feb)",
        "required": False
    }
}

def validate_html(html_content):
    """
    Validar que el HTML esté bien formado.
    
    Args:
        html_content (str): Contenido HTML a validar.
        
    Returns:
        tuple: (bool, str) - (es_válido, mensaje_de_error)
    """
    try:
        # Intentar parsear el HTML
        soup = BeautifulSoup(html_content, 'html5lib')
        return True, "HTML válido"
    except Exception as e:
        logger.error(f"Error validando HTML: {e}")
        return False, f"HTML inválido: {str(e)}"

def extract_images_from_html(html_content):
    """
    Extraer todas las imágenes de un HTML.
    
    Args:
        html_content (str): Contenido HTML.
        
    Returns:
        list: Lista de diccionarios con información de las imágenes.
    """
    images = []
    try:
        soup = BeautifulSoup(html_content, 'html5lib')
        img_tags = soup.find_all('img')
        
        for img in img_tags:
            src = img.get('src', '')
            
            # Ignorar imágenes base64 o URLs externas
            if src.startswith('data:') or src.startswith('http'):
                continue
                
            alt = img.get('alt', '')
            filename = src.split('/')[-1]
            
            images.append({
                'src': src,
                'filename': filename,
                'alt': alt
            })
            
        return images
    except Exception as e:
        logger.error(f"Error extrayendo imágenes del HTML: {e}")
        return []

def find_placeholders_in_template(template):
    """
    Encontrar placeholders en una plantilla HTML.
    
    Args:
        template (str): Plantilla HTML.
        
    Returns:
        dict: Diccionario con información sobre placeholders encontrados.
    """
    result = {
        "required": [],
        "optional": [],
        "missing": [],
        "unknown": []
    }
    
    # Buscar todos los placeholders usando regex
    pattern = r"{{[A-Z_]+}}"
    found_placeholders = set(re.findall(pattern, template))
    
    # Clasificar los placeholders
    for placeholder in PLACEHOLDERS:
        if placeholder in found_placeholders:
            if PLACEHOLDERS[placeholder]["required"]:
                result["required"].append(placeholder)
            else:
                result["optional"].append(placeholder)
        else:
            result["missing"].append(placeholder)
    
    # Identificar placeholders desconocidos
    for found in found_placeholders:
        if found not in PLACEHOLDERS:
            result["unknown"].append(found)
    
    return result

def replace_placeholders(template, values):
    """
    Reemplazar placeholders en una plantilla con valores.
    
    Args:
        template (str): Plantilla HTML.
        values (dict): Diccionario con valores para reemplazar.
        
    Returns:
        str: HTML con placeholders reemplazados.
    """
    result = template
    
    for placeholder, value in values.items():
        if not placeholder.startswith("{{"):
            placeholder = "{{" + placeholder + "}}"
        result = result.replace(placeholder, str(value) if value is not None else "")
    
    return result

def estimate_reading_time(html_content):
    """
    Estimar el tiempo de lectura de un contenido HTML.
    
    Args:
        html_content (str): Contenido HTML.
        
    Returns:
        int: Tiempo estimado de lectura en minutos.
    """
    try:
        soup = BeautifulSoup(html_content, 'html5lib')
        text = soup.get_text()
        
        # Contar palabras
        words = len(text.split())
        
        # Estimar tiempo (promedio de 200 palabras por minuto)
        minutes = max(1, round(words / 200))
        
        return minutes
    except Exception as e:
        logger.error(f"Error estimando tiempo de lectura: {e}")
        return 1  # Valor por defecto

def get_all_placeholders(site_id=None):
    """
    Obtener todos los placeholders disponibles, incluyendo los personalizados.
    
    Args:
        site_id (int, optional): ID del sitio para obtener placeholders personalizados.
        
    Returns:
        dict: Diccionario con todos los placeholders y sus propiedades.
    """
    # Copia de los placeholders estándar
    all_placeholders = PLACEHOLDERS.copy()
    
    # Si hay un site_id, buscar placeholders personalizados
    if site_id:
        try:
            from models.placeholder import CustomPlaceholder
            custom_placeholders = CustomPlaceholder.get_by_site_id(site_id)
            
            # Añadir cada placeholder personalizado
            for ph in custom_placeholders:
                placeholder_name = f"{{{{{ph.placeholder_name}}}}}"
                all_placeholders[placeholder_name] = {
                    "description": ph.display_name,
                    "required": False,
                    "type": ph.placeholder_type,
                    "options": ph.options,
                    "custom": True
                }
        except Exception as e:
            logger.error(f"Error al obtener placeholders personalizados: {e}")
    
    return all_placeholders

def get_custom_placeholders_from_site(site):
    """
    Obtener los placeholders personalizados de un sitio.
    
    Args:
        site: Objeto Site.
        
    Returns:
        dict: Diccionario con los placeholders personalizados y sus propiedades.
    """
    custom_placeholders = {}
    
    if not site:
        return custom_placeholders
    
    try:
        placeholders = site.get_custom_placeholders()
        for ph in placeholders:
            placeholder_name = f"{{{{{ph.placeholder_name}}}}}"
            custom_placeholders[placeholder_name] = {
                "description": ph.display_name,
                "required": False,
                "type": ph.placeholder_type,
                "options": ph.options,
                "custom": True,
                "placeholder_obj": ph
            }
    except Exception as e:
        logger.error(f"Error al obtener placeholders personalizados del sitio: {e}")
    
    return custom_placeholders

def validate_placeholder_value(placeholder_type, value, options=None):
    """
    Validar un valor de acuerdo al tipo de placeholder.
    
    Args:
        placeholder_type (str): Tipo de placeholder (texto, numero, url, desplegable).
        value: Valor a validar.
        options (str, optional): Opciones para tipos desplegables.
        
    Returns:
        bool: True si el valor es válido, False en caso contrario.
    """
    if not value:
        return True  # Permitir valores vacíos
        
    if placeholder_type == "numero":
        try:
            float(value)
            return True
        except ValueError:
            return False
    elif placeholder_type == "url":
        # Validación básica de URL
        return value.startswith(('http://', 'https://'))
    elif placeholder_type == "desplegable":
        if not options:
            return True
        options_list = [opt.strip() for opt in options.split(',')]
        return value in options_list
    else:  # texto
        return True 