#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Módulo de conexión a SQLite
"""

import os
import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

# Conexión global a SQLite
connection = None
cursor = None

def setup_database():
    """Configurar la conexión a SQLite."""
    global connection, cursor
    
    db_path = os.getenv("DATABASE_PATH", "./database/knomad.db")
    
    # Asegurarse de que el directorio existe
    db_dir = os.path.dirname(db_path)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    
    try:
        # Conectar a SQLite
        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row  # Para acceder a columnas por nombre
        cursor = connection.cursor()
        
        logger.info("✅ Conexión a SQLite establecida correctamente")
        
        # Configurar tablas necesarias
        _setup_tables()
        
        return True
    except sqlite3.Error as e:
        logger.error(f"❌ No se pudo conectar a SQLite: {e}")
        return False

def _setup_tables():
    """Configurar tablas e índices."""
    global connection, cursor
    
    # Tabla de usuarios
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id TEXT UNIQUE,
        name TEXT,
        email TEXT UNIQUE,
        status TEXT,
        role TEXT DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Tabla de sitios
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        domain TEXT,
        sftp_config TEXT,
        template TEXT,
        status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        UNIQUE (user_id, domain)
    )
    ''')
    
    # Tabla de contenidos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS contents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        site_id INTEGER,
        title TEXT,
        slug TEXT,
        html_content TEXT,
        feature_image TEXT,
        category TEXT,
        status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (site_id) REFERENCES sites (id),
        UNIQUE (site_id, slug)
    )
    ''')
    
    # Tabla de placeholders personalizados
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS custom_placeholders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        site_id INTEGER,
        placeholder_name TEXT,
        display_name TEXT,
        placeholder_type TEXT DEFAULT 'texto',
        options TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (site_id) REFERENCES sites (id),
        UNIQUE (site_id, placeholder_name)
    )
    ''')
    
    connection.commit()
    logger.info("✅ Tablas e índices configurados correctamente")

def get_db():
    """Obtener la conexión a la base de datos."""
    global connection, cursor
    if connection is None:
        setup_database()
    return connection, cursor

def close_connection():
    """Cerrar la conexión a SQLite."""
    global connection
    if connection:
        connection.close()
        logger.info("Conexión a SQLite cerrada") 