#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para cargar emails desde un archivo .txt a la base de datos remota
Uso: python cargar_emails.py archivo.txt
"""

import sys
import os
from pathlib import Path

# Agregar el directorio app al path para importar módulos
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from utils.http_utils import post
from database.database import get_user_data

# =============================================================================
# CONFIGURACIÓN - MODIFICA ESTOS VALORES SEGÚN TUS NECESIDADES
# =============================================================================

# ID del usuario en la base de datos remota
USER_ID = 3 # Cambia este valor por tu ID de usuario

# Token de acceso para la API
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwiZXhwIjoxNzYxOTM3MDkzfQ.bJIMvIOd-774KfZPLfb6HI6nzuxpt86pjaoKmUuJ_f0"

# =============================================================================


def cargar_emails_desde_archivo(archivo_txt, user_id=None, access_token=None):
    """
    Carga emails desde un archivo .txt a la base de datos remota
    
    Args:
        archivo_txt (str): Ruta del archivo .txt con los emails
        user_id (int, optional): ID del usuario (si no se proporciona, se obtiene de la BD)
        access_token (str, optional): Token de acceso (si no se proporciona, se obtiene de la BD)
        
    Returns:
        bool: True si la carga fue exitosa, False en caso contrario
    """
    try:
        # Verificar que el archivo existe
        if not os.path.exists(archivo_txt):
            print(f"❌ Error: El archivo {archivo_txt} no existe")
            return False
        
        # Obtener datos del usuario
        if not user_id or not access_token:
            print("🔍 Obteniendo datos de usuario desde la base de datos local...")
            user_data = get_user_data()
            if not user_data:
                print("❌ Error: No se encontraron datos de usuario en la base de datos local")
                print("💡 Asegúrate de tener configurado un usuario con access_token")
                return False
            
            access_token = access_token or user_data.get('access_token')
            user_id = user_id or user_data.get('id')
        
        if not access_token or not user_id:
            print("❌ Error: No se encontró access_token o ID de usuario")
            return False
        
        # Leer emails del archivo
        emails = []
        try:
            with open(archivo_txt, 'r', encoding='utf-8') as f:
                for line in f:
                    email = line.strip()
                    if email and not email.startswith('#') and '@' in email:
                        emails.append(email)
        except Exception as e:
            print(f"❌ Error al leer el archivo: {e}")
            return False
        
        if not emails:
            print("❌ Error: No se encontraron emails válidos en el archivo")
            return False
        
        print(f"📁 Archivo: {archivo_txt}")
        print(f"📧 Emails encontrados: {len(emails)}")
        print(f"👤 Usuario ID: {user_id}")
        print(f"🌐 Enviando a la base de datos...")
        
        # Preparar datos para la API
        url = f"http://34.29.59.97/api/emails/save/{user_id}"
        headers = {
            'Content-Type': 'application/json'
        }
        
        data = {
            "access_token": access_token,
            "emails": emails
        }
        
        # Realizar petición POST
        response = post(url, body=data, headers=headers)
        
        if response and response.status_code in [200, 201]:
            try:
                response_data = response.json()
                saved_count = response_data.get('saved_count', len(emails))
                duplicate_count = response_data.get('duplicate_count', 0)
                invalid_count = response_data.get('invalid_format_count', 0)
                
                print(f"✅ ¡Carga exitosa!")
                print(f"📊 Emails guardados: {saved_count}")
                if duplicate_count > 0:
                    print(f"⚠️ Emails duplicados (omitidos): {duplicate_count}")
                if invalid_count > 0:
                    print(f"⚠️ Emails con formato inválido: {invalid_count}")
                
                return True
            except Exception as e:
                print(f"✅ Emails enviados exitosamente: {len(emails)}")
                print(f"⚠️ No se pudo procesar la respuesta detallada: {e}")
                return True
        else:
            print(f"❌ Error al enviar emails a la base de datos")
            if response:
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False


def mostrar_ayuda():
    """Muestra la ayuda del script"""
    print("""
📧 Cargador de Emails a Base de Datos
=====================================

Uso:
    python cargar_emails.py archivo.txt

Ejemplos:
    python cargar_emails.py emails.txt
    python cargar_emails.py "C:\\ruta\\a\\mis\\emails.txt"

Formato del archivo:
    - Un email por línea
    - Líneas que empiecen con # se ignoran
    - Líneas vacías se ignoran
    - Solo se procesan emails con formato válido (contienen @)

Ejemplo de archivo:
    reason177jkid@word323gawj.33mail.com
    black218vugv@investment546awfr.33mail.com
    # Este es un comentario
    imagine396cmqu@party31ljkj.33mail.com

Configuración:
    - Edita USER_ID y ACCESS_TOKEN en el archivo cargar_emails.py
    - O deja que use los valores de la base de datos local

Requisitos:
    - Debe tener configurado un usuario en la base de datos local (opcional)
    - El usuario debe tener un access_token válido
    - Conexión a internet para acceder a la API remota
""")


def main():
    """Función principal del script"""
    if len(sys.argv) != 2:
        mostrar_ayuda()
        return
    
    archivo = sys.argv[1]
    
    # Verificar si es una petición de ayuda
    if archivo in ['-h', '--help', 'help']:
        mostrar_ayuda()
        return
    
    print("🚀 Iniciando carga de emails...")
    print("=" * 50)
    print(f"👤 Usuario ID: {USER_ID}")
    print(f"🔑 Token: {ACCESS_TOKEN[:20]}...")
    print("=" * 50)
    
    # Cargar emails usando los valores hardcodeados
    exito = cargar_emails_desde_archivo(archivo, USER_ID, ACCESS_TOKEN)
    
    print("=" * 50)
    if exito:
        print("🎉 ¡Proceso completado exitosamente!")
    else:
        print("💥 El proceso falló. Revisa los errores arriba.")
        sys.exit(1)


if __name__ == "__main__":
    main()
