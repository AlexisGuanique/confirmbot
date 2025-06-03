def setup_ui(logged_in_user, on_login_success):
    import customtkinter as ctk
    from tkinter import filedialog
    from tkinter import messagebox
    from app.auth.auth import logout
    from app.confirmabot.auth_ui import setup_auth_ui
    from app.database.database import save_bot_settings, get_bot_settings, save_emails, get_all_emails, get_email_count, clear_emails

    from app.confirmabot.confirm_bot import run_checker



    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("Confirma Bot")
    root.geometry("600x550")
    root.configure(fg_color="#FFFFFF")  # Fondo blanco

   # 📌 Etiqueta de bienvenida centrada arriba
    welcome_label = ctk.CTkLabel(
        root,
        text=f"Bienvenido a Confirma Bot, {logged_in_user}.",
        font=("Arial", 22, "bold"),
        text_color="black"
    )
    welcome_label.pack(pady=(30, 10))

    # 👉 Contenedor para inputs de Hostinger (lado izquierdo)
    hostinger_frame = ctk.CTkFrame(root, fg_color="transparent")
    hostinger_frame.place(relx=0.0, rely=0.0, anchor="nw", x=20, y=100)


   #! 👉 Input: Cantidad de iteraciones
    iterations_label = ctk.CTkLabel(
        hostinger_frame,
        text="Cantidad de emails creados por dominio:",
        text_color="black",
        font=("Arial", 12, "bold")
    )
    iterations_label.pack(pady=(10, 2), anchor="w")

    iterations_entry = ctk.CTkEntry(
        hostinger_frame,
        width=200,
        placeholder_text="Ej: 5"
    )
    iterations_entry.pack(pady=(0, 10))

    # 🔽 Cargar valor guardado (si existe)
    bot_settings = get_bot_settings()
    if bot_settings:
        iterations_entry.insert(0, str(bot_settings["iterations"]))

    # 👉 Botón para guardar solo el número de iteraciones
    def save_iterations_only():
        iterations = iterations_entry.get()

        if not iterations.isdigit():
            messagebox.showerror("Error", "Ingresa un número válido de iteraciones.")
            return

        success = save_bot_settings(int(iterations))
        if success:
            messagebox.showinfo("Guardado", "✅ Iteraciones guardadas correctamente.")
        else:
            messagebox.showerror("Error", "No se pudieron guardar las iteraciones.")

    save_iterations_button = ctk.CTkButton(
        hostinger_frame,
        text="Guardar Iteraciones",
        command=save_iterations_only,
        fg_color="#0066cc",
        text_color="white"
    )
    save_iterations_button.pack(pady=(0, 15))


    # 👉 Mostrar cantidad de dominios y hacer clic para verlos
    def toggle_domain_view(event=None):
        if domain_view_frame.winfo_ismapped():
            domain_view_frame.pack_forget()
        else:
            update_domain_list()
            domain_view_frame.pack(pady=(0, 10), anchor="ne")

    email_count_label = ctk.CTkLabel(
        hostinger_frame,
        text=f"Dominios cargados: {get_email_count()} (click para ver)",
        text_color="blue",
        font=("Arial", 12, "bold"),
        cursor="hand2"
    )
    email_count_label.pack(pady=(10, 2), anchor="w")
    email_count_label.bind("<Button-1>", toggle_domain_view)

    def load_emails_from_file():
        file_path = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt")],
            title="Seleccionar archivo de emails"
        )

        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]

            if len(lines) % 3 != 0:
                messagebox.showerror("Error", "El archivo debe tener bloques de 3 líneas: email, contraseña y dominio.")
                return

            registros_guardados = 0

            for i in range(0, len(lines), 3):
                email_h = lines[i]
                password_h = lines[i + 1]
                dominio = lines[i + 2]

                if dominio.startswith("@"):
                    success = save_emails([dominio], email_h, password_h)
                    if success:
                        registros_guardados += 1

            if registros_guardados:
                email_count_label.configure(text=f"Dominios cargados: {get_email_count()} (click para ver)")
                messagebox.showinfo("Éxito", f"Se guardaron {registros_guardados} dominios.")
            else:
                messagebox.showwarning("Sin registros", "No se guardó ningún dominio válido.")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer el archivo:\n{e}")


    load_emails_button = ctk.CTkButton(
        hostinger_frame,
        text="Cargar Dominios",
        command=load_emails_from_file,
        fg_color="#4CAF50",
        text_color="white"
    )
    load_emails_button.pack(pady=(0, 15))

   # 👉 Contenedor oculto que mostrará los dominios
    domain_view_frame = ctk.CTkFrame(
        root,
        width=300,
        height=200,
        fg_color="white",
        corner_radius=8,
        border_width=1,
        border_color="black"
    )
    domain_view_frame.place_forget()  # Oculto al inicio

    domain_title = ctk.CTkLabel(
        domain_view_frame,
        text="📬 Dominios guardados",
        text_color="black",
        font=("Arial", 13, "bold")
    )
    domain_title.pack(pady=(10, 5))

    domain_listbox = ctk.CTkTextbox(
        domain_view_frame,
        width=280,   # ⬅️ Aumentado para llenar mejor el frame
        height=110,
        font=("Arial", 11),
        text_color="black",
        fg_color="white"
    )

    domain_listbox.pack(pady=(0, 10), padx=10)

    # 👉 Botón para eliminar todos los dominios
    def clear_domains_ui():
        confirm = messagebox.askyesno("Confirmar", "¿Seguro que quieres eliminar todos los dominios?")
        if confirm:
            if clear_emails():
                update_domain_list()
                email_count_label.configure(text=f"Dominios cargados: {get_email_count()} (click para ver)")
                messagebox.showinfo("Eliminado", "✅ Todos los dominios fueron eliminados.")
            else:
                messagebox.showerror("Error", "No se pudieron eliminar los dominios.")

    clear_button = ctk.CTkButton(
        domain_view_frame,
        text="Eliminar Todos",
        fg_color="tomato",
        text_color="white",
        command=clear_domains_ui
    )
    clear_button.pack(pady=(0, 10))

    def update_domain_list():
        domain_listbox.delete("0.0", "end")
        registros = get_all_emails()

        if registros:
            for reg in registros:
                domain = reg["email"]
                hostinger_email = reg["email_hostinger"]
                domain_listbox.insert("end", f"{domain}  ←  {hostinger_email}\n")
        else:
            domain_listbox.insert("end", "No hay dominios cargados.")

                
    # 👉 Mostrar/ocultar el panel de dominios (ajustado manualmente)
    def toggle_domain_view(event=None):
        if domain_view_frame.winfo_ismapped():
            domain_view_frame.place_forget()
        else:
            update_domain_list()
            # ❗ Probar valores más bajos para ver el cambio real
            domain_view_frame.place(x=250, y=250)  # ⇠ Más a la izquierda y abajo



    
    # 👉 Botón para ejecutar el bot
    def handle_run_checker():
        run_checker()

    run_checker_button = ctk.CTkButton(
        hostinger_frame,
        text="Ejecutar Bot",
        command=handle_run_checker,
        fg_color="#007ACC",   # Azul
        text_color="white"
    )
    run_checker_button.pack(pady=(10, 10))






    # 👉 Función de logout
    def handle_logout():
        if logout():
            messagebox.showinfo("Logout Exitoso", "Has cerrado sesión.")
            root.destroy()
            setup_auth_ui(on_login_success)
        else:
            messagebox.showwarning("Error", "No hay ningún usuario logueado.")

    # 👉 Botón de logout en la esquina inferior derecha
    logout_button = ctk.CTkButton(
        root,
        text="Cerrar Sesión",
        command=handle_logout,
        font=("Arial", 14),
        fg_color="#FFFFFF",
        text_color="black",
        corner_radius=10,
        width=160,
        height=40,
        border_color="black",
        border_width=2,
        hover_color="tomato"
    )
    logout_button.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-20)

    root.mainloop()
