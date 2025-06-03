import os

def log_verified_email(email_hostinger, verified_email):
    try:
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

        logs_dir = os.path.join(root_dir, "verifications")

        safe_filename = email_hostinger.replace("@", "_at_")
        file_path = os.path.join(logs_dir, f"{safe_filename}.txt")

        if not os.path.isfile(file_path):
            print(f"⚠️ El archivo de log {file_path} no existe. No se escribirá el email.")
            return

        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"{verified_email.strip()}\n")

        print(f"📝 Email verificado guardado en {file_path}")

    except Exception as e:
        print(f"❌ Error al registrar email verificado: {e}")
