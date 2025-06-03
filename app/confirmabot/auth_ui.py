from tkinter import messagebox
from app.auth.auth import login
import customtkinter as ctk


def setup_auth_ui(on_login_success):

    def handle_login():
        username = username_entry.get()
        password = password_entry.get()

        # Recibe el JSON con los datos del usuario
        login_data = login(username, password)

        if login_data and login_data.get("access_token"):
            messagebox.showinfo(
                "Login Exitoso", f"Bienvenido, {login_data.get('name')} {login_data.get('lastname')}!")
            root.destroy()
            # Pasa el JSON completo con la información del usuario
            on_login_success(login_data)
        else:
            error_message = login_data.get(
                "error", "Usuario o contraseña incorrectos.") if login_data else "Error desconocido."

            if "El token ha expirado" in error_message:
                error_message = "Usuario expirado. Contacte a los desarrolladores."

            messagebox.showerror("Login Fallido", error_message)

    def on_enter_key(event):
        handle_login()

    # Configurar apariencia
    ctk.set_appearance_mode("light")  # Modo claro
    ctk.set_default_color_theme("blue")  # Color primario

    # Crear ventana principal
    root = ctk.CTk()
    root.title("Login - Ultra Bot")
    root.geometry("600x300")
    root.configure(fg_color="#FFFFFF")

    # Título principal centrado
    title_label = ctk.CTkLabel(
        root,
        text="Bienvenido al Ultra Bot",
        font=("Arial", 24, "bold"),
        text_color="black"
    )
    title_label.pack(pady=20)  # Espaciado arriba y centrado automáticamente

    # Función para manejar placeholders
    def add_placeholder(entry, placeholder_text, is_password=False):
        """Añade placeholder dinámico en los inputs. En contraseña, maneja visibilidad."""
        entry.insert(0, placeholder_text)
        entry.configure(text_color="gray")

        if is_password:
            entry.configure(show="")  # Mostrar texto normal en inicio

        def on_focus_in(event):
            if entry.get() == placeholder_text:
                entry.delete(0, "end")
                entry.configure(text_color="black")
                if is_password:
                    entry.configure(show="*")  # Cambiar a oculto al escribir

        def on_focus_out(event):
            if entry.get() == "":
                entry.insert(0, placeholder_text)
                entry.configure(text_color="gray")
                if is_password:
                    entry.configure(show="")  # Mostrar texto normal si está vacío

        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

    # 🔹 Input de usuario con placeholder
    username_entry = ctk.CTkEntry(root, font=("Arial", 12), corner_radius=10, width=350, height=40)
    username_entry.pack(pady=10)
    add_placeholder(username_entry, "Usuario")

    # 🔹 Contenedor de contraseña centrado en la ventana
    password_frame = ctk.CTkFrame(root, fg_color="transparent", width=350, height=50)
    password_frame.pack(pady=10)  # Agrega espaciado debajo del input de usuario

    # 🔹 Input de contraseña centrado dentro del contenedor principal
    password_entry = ctk.CTkEntry(
        password_frame, font=("Arial", 12), corner_radius=10, width=350, height=40
    )
    password_entry.pack(fill="both", expand=True, padx=10)  # Se mantiene centrado dentro del frame

    add_placeholder(password_entry, "Contraseña", is_password=True)



    # Función para alternar la visibilidad de la contraseña
    def toggle_password():
        if password_entry.cget("show") == "*":
            password_entry.configure(show="")
            eye_button.configure(text="👁")  # Ícono de ojo abierto
        else:
            password_entry.configure(show="*")
            eye_button.configure(text="🙈")  # Ícono de ojo cerrado

    # 🔹 Botón de ojo SIN fondo ni hover visible, completamente blanco
    eye_button = ctk.CTkButton(
        password_frame, text="👁", width=20, height=30, command=toggle_password,
        fg_color="white", text_color="black", corner_radius=10, 
        hover_color="white", border_width=0  # Asegurar sin bordes grises
    )

    # ⬅ Moviendo el icono más a la izquierda
    eye_button.place(relx=0.89, rely=0.5, anchor="center")  # Ajusta la posición

    # Detectar "Enter" en la contraseña también
    password_entry.bind("<Return>", on_enter_key)  

    # 🔹 Botón de login con borde negro
    login_button = ctk.CTkButton(
        root, 
        text="Iniciar Sesión", 
        command=handle_login, 
        font=("Arial", 14), 
        fg_color="#2644d9",  # Color de fondo azul oscuro
        text_color="white",  # Texto blanco
        corner_radius=10, 
        width=200, 
        height=40,
        border_color="black",  # Borde negro
        border_width=2  # Grosor del borde
    )

    login_button.pack(pady=20)


    # Etiqueta de firma en la esquina inferior izquierda
    signature_label = ctk.CTkLabel(
        root,
        text="Desarrollado por A. G.",
        font=("Arial", 10),  # Fuente más pequeña
        text_color="black"  # Texto negro
    )

    # Ubicarlo bien pegado al borde inferior
    signature_label.place(relx=0.0, rely=1.0, anchor="sw", x=10, y=-5)  # Reduciendo margen inferior

    # Ejecutar la UI
    root.mainloop()