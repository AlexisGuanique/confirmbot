import tkinter as tk
from tkinter import messagebox
from app.confirmabot.auth_ui import setup_auth_ui
from app.confirmabot.ui import setup_ui
from app.database.database import create_database, get_logged_in_user
from app.auth.auth import logout, verify_token, connect_bot


def on_login_success(login_data):
    create_database()

    name = login_data.get("name")
    lastname = login_data.get("lastname")

    if name and lastname:
        full_name = f"{name} {lastname}"
        
        # Conectar el bot al servidor WebSocket después del login
        print("🔌 Intentando conectar bot al servidor WebSocket...")
        if connect_bot():
            print("✅ Bot conectado al servidor WebSocket")
        else:
            print("⚠️  No se pudo conectar el bot al servidor WebSocket. Continuando sin conexión...")
        
        setup_ui(full_name, on_login_success)
    else:
        print("Error: No se pudo obtener el nombre o apellido del usuario")

def main():
    create_database()

    logged_in_user = get_logged_in_user()

    if logged_in_user:

        token_status = verify_token() or {"is_valid": False}

        if not token_status.get("is_valid"):
            messagebox.showerror("Token Expirado", "Usuario expirado. Contacte a los desarrolladores.")
            logout()
            setup_auth_ui(on_login_success)
            return

        root = tk.Tk()
        root.withdraw() 

        name = logged_in_user.get("name")
        lastname = logged_in_user.get("lastname")
        full_name = f"{name} {lastname}"

        result = messagebox.askyesno(
            "Usuario Logueado",
            f"El usuario {full_name} está actualmente logueado. ¿Deseas continuar logueado?"
        )

        if result:
            root.destroy()
            # Conectar el bot al servidor WebSocket si no está conectado
            from app.auth.auth import sio
            if not sio.connected:
                print("🔌 Intentando conectar bot al servidor WebSocket...")
                if connect_bot():
                    print("✅ Bot conectado al servidor WebSocket")
                else:
                    print("⚠️  No se pudo conectar el bot al servidor WebSocket. Continuando sin conexión...")
            setup_ui(full_name, on_login_success)
        else:
            logout()
            messagebox.showinfo("Logout Exitoso", "Has cerrado sesión.")
            root.destroy()
            setup_auth_ui(on_login_success)
    else:
        setup_auth_ui(on_login_success)


if __name__ == "__main__":
    main()