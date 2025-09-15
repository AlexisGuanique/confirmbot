#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para convertir archivos JSON de cookies de formato multilínea a una sola línea
"""

import json
import os
import sys

def format_cookies_to_single_line(input_file, output_file=None):
    """
    Convierte un archivo JSON de cookies de formato multilínea a una sola línea
    
    Args:
        input_file (str): Ruta del archivo de entrada
        output_file (str): Ruta del archivo de salida (opcional, por defecto sobrescribe el original)
    """
    try:
        # Leer el archivo completo
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Buscar el inicio del JSON (primer '[')
        json_start = content.find('[')
        if json_start == -1:
            print("❌ No se encontró un array JSON válido en el archivo")
            return False
        
        # Extraer solo la parte JSON
        json_content = content[json_start:]
        
        # Parsear el JSON
        data = json.loads(json_content)
        
        # Convertir a JSON compacto (una sola línea)
        json_single_line = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
        
        # Determinar archivo de salida
        if output_file is None:
            output_file = input_file
        
        # Si hay contenido antes del JSON, mantenerlo
        if json_start > 0:
            prefix = content[:json_start]
            final_content = prefix + json_single_line
        else:
            final_content = json_single_line
        
        # Escribir el resultado
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_content)
        
        print(f"✅ Archivo convertido exitosamente: {output_file}")
        print(f"📏 Longitud de la línea JSON: {len(json_single_line)} caracteres")
        
    except json.JSONDecodeError as e:
        print(f"❌ Error al parsear JSON: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ Archivo no encontrado: {input_file}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False
    
    return True

def main():
    """Función principal del script"""
    if len(sys.argv) < 2:
        print("Uso: python format_cookies.py <archivo_entrada> [archivo_salida]")
        print("\nEjemplos:")
        print("  python format_cookies.py cuenta_creada_20250915_005113.txt")
        print("  python format_cookies.py input.txt output.txt")
        return
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Verificar que el archivo existe
    if not os.path.exists(input_file):
        print(f"❌ El archivo {input_file} no existe")
        return
    
    # Convertir el archivo
    success = format_cookies_to_single_line(input_file, output_file)
    
    if success:
        print("\n🎉 ¡Conversión completada!")
    else:
        print("\n💥 Error en la conversión")

if __name__ == "__main__":
    main()
