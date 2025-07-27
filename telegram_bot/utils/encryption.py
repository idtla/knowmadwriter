#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utilidad para cifrado y descifrado de información sensible
"""

import os
import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

# Obtener la clave de cifrado desde variables de entorno
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "default_key_for_development_only")

# Salt fija (no es ideal para producción, pero simplifica la implementación)
SALT = b'telegram_bot_salt_fixed'

def _get_fernet_key():
    """Obtener una clave Fernet derivada de la clave de entorno."""
    try:
        # Derivar clave usando PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=SALT,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(ENCRYPTION_KEY.encode()))
        return Fernet(key)
    except Exception as e:
        logger.error(f"Error generando clave de cifrado: {e}")
        # Fallback a una clave básica (no recomendado para producción)
        base_key = ENCRYPTION_KEY.ljust(32)[:32].encode()
        key = base64.urlsafe_b64encode(base_key)
        return Fernet(key)

def encrypt_data(data):
    """
    Cifrar datos sensibles.
    
    Args:
        data (str): Datos a cifrar.
        
    Returns:
        str: Datos cifrados en formato base64.
    """
    if not data:
        return None
        
    try:
        f = _get_fernet_key()
        encrypted_data = f.encrypt(data.encode()).decode()
        return encrypted_data
    except Exception as e:
        logger.error(f"Error al cifrar datos: {e}")
        return None

def decrypt_data(encrypted_data):
    """
    Descifrar datos sensibles.
    
    Args:
        encrypted_data (str): Datos cifrados en formato base64.
        
    Returns:
        str: Datos descifrados.
    """
    if not encrypted_data:
        return None
        
    try:
        f = _get_fernet_key()
        decrypted_data = f.decrypt(encrypted_data.encode()).decode()
        return decrypted_data
    except Exception as e:
        logger.error(f"Error al descifrar datos: {e}")
        return None 