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
