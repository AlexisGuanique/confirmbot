def parse_email_file(file_path):

    registros = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        if len(lines) % 3 != 0:
            raise ValueError("El archivo debe tener bloques de 3 líneas: dominio, email de Hostinger y contraseña.")

        for i in range(0, len(lines), 3):
            email = lines[i]                 # dominio (ej: @facilrecordar.com)
            email_hostinger = lines[i + 1]   # ej: alexisguanique@facilrecordar.com
            password_hostinger = lines[i + 2] # ej: Alexis4321.
            registros.append((email, email_hostinger, password_hostinger))

        return registros

    except Exception as e:
        print(f"❌ Error al procesar archivo: {e}")
        return []


def parse_simple_emails_file(file_path):

    registros = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        if not lines:
            print("❌ El archivo está vacío o no contiene correos válidos.")
            return []

        print(f"📧 Procesando {len(lines)} líneas del archivo...")

        for i, line in enumerate(lines, 1):
            # Validación más estricta de correo electrónico
            if line.startswith('@'):
                print(f"⚠️ Línea {i} ignorada (empieza con @): {line}")
                continue
            elif '@' not in line or '.' not in line:
                print(f"⚠️ Línea {i} ignorada (formato de correo inválido): {line}")
                continue
            elif line.count('@') > 1:
                print(f"⚠️ Línea {i} ignorada (múltiples @): {line}")
                continue
            elif len(line) < 5:  # Correo muy corto
                print(f"⚠️ Línea {i} ignorada (muy corto): {line}")
                continue
            else:
                # Validar estructura básica: usuario@dominio.com
                parts = line.split('@')
                if len(parts) == 2:
                    username, domain = parts
                    if len(username) > 0 and len(domain) > 0 and '.' in domain:
                        registros.append((line, line, ""))
                        print(f"✅ Línea {i} procesada: {line}")
                    else:
                        print(f"⚠️ Línea {i} ignorada (estructura inválida): {line}")
                else:
                    print(f"⚠️ Línea {i} ignorada (formato inválido): {line}")

        print(f"✅ Se procesaron {len(registros)} correos válidos de {len(lines)} líneas")
        return registros

    except Exception as e:
        print(f"❌ Error al procesar archivo de correos simples: {e}")
        return []


def auto_detect_email_format(file_path):
    """
    Función que detecta el formato del archivo y SOLO acepta formato simple de correos.
    Rechaza archivos con formato de bloques de 3 líneas.
    
    Args:
        file_path (str): Ruta al archivo .txt
    
    Returns:
        list: Lista de registros procesados (solo formato simple)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        if not lines:
            print("❌ El archivo está vacío")
            return []

        print(f"📊 Analizando archivo con {len(lines)} líneas...")
        
        # Verificar si hay líneas que empiecen con @ (formato de bloques)
        has_domain_format = any(line.startswith('@') for line in lines)
        
        if has_domain_format:
            print("❌ Formato de archivo NO válido detectado!")
            print("⚠️ El archivo contiene líneas que empiezan con @ (formato de bloques)")
            print("📋 Formato requerido: un email por línea, ejemplo:")
            print("   dinner174qbda@play387dlbu.33mail.com")
            print("   just401yfcw@car60gvku.33mail.com")
            print("   base318qkrp@challenge200duqh.33mail.com")
            print("")
            print("❌ NO se procesará el archivo. Corrige el formato y vuelve a intentar.")
            return []
        
        # Si no hay líneas que empiecen con @, es formato simple válido
        print("✅ Formato válido detectado: un email por línea")
        return parse_simple_emails_file(file_path)

    except Exception as e:
        print(f"❌ Error al detectar formato del archivo: {e}")
        return []
