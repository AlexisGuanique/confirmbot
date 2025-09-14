def setup_ui(logged_in_user, on_login_success):
    import customtkinter as ctk
    from tkinter import filedialog
    from tkinter import messagebox
    from app.auth.auth import logout
    from app.confirmabot.auth_ui import setup_auth_ui
    from app.database.database import save_bot_settings, get_bot_settings, save_emails, get_all_emails, get_email_count, clear_emails, save_click_coordinates, save_nopecha_key, get_nopecha_key

    from app.confirmabot.confirm_bot import run_checker, stop_bot, open_temp_chrome_profile as openProfileWithExtraExtension
    import threading
    from app.confirmabot.utils.field_reader import parse_email_file  
    from app.confirmabot.utils.mouse_click_coordenates import get_mouse_coordinate_on_keypress
    from app.creator.ui_creator import create_new_window

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("Confirma Bot")
    root.geometry("600x650")
    root.configure(fg_color="#FFFFFF")  # Fondo blanco

   # 📌 Etiqueta de bienvenida centrada arriba
    welcome_label = ctk.CTkLabel(
        root,
        text=f"Bienvenido a Confirma Bot, {logged_in_user}.",
        font=("Arial", 22, "bold"),
        text_color="black"
    )
    welcome_label.pack(pady=(30, 10))

    # 👉 Título para el lado izquierdo
    left_title = ctk.CTkLabel(
        root,
        text="ConfirmaBot",
        text_color="black",
        font=("Arial", 16, "bold")
    )
    left_title.place(relx=0.0, rely=0.0, anchor="nw", x=20, y=70)

    # 👉 Título para el lado derecho
    right_title = ctk.CTkLabel(
        root,
        text="Linkedin Creator",
        text_color="black",
        font=("Arial", 16, "bold")
    )
    right_title.place(relx=1.0, rely=0.0, anchor="ne", x=-20, y=70)

    # 👉 Contenedor para inputs de Hostinger (lado izquierdo)
    hostinger_frame = ctk.CTkFrame(root, fg_color="transparent")
    hostinger_frame.place(relx=0.0, rely=0.0, anchor="nw", x=20, y=100)

    # 👉 Contenedor para opciones del bot (lado derecho)
    options_frame = ctk.CTkFrame(root, fg_color="transparent")
    options_frame.place(relx=1.0, rely=0.0, anchor="ne", x=-20, y=100)


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

    # 👉 Input: Tiempo de pausa entre cada 10 iteraciones
    pause_label = ctk.CTkLabel(
        hostinger_frame,
        text="Tiempo de pausa (minutos) cada 10 iteraciones:",
        text_color="black",
        font=("Arial", 12, "bold")
    )
    pause_label.pack(pady=(10, 2), anchor="w")

    pause_entry = ctk.CTkEntry(
        hostinger_frame,
        width=200,
        placeholder_text="Ej: 20"
    )
    pause_entry.pack(pady=(0, 10))

    # 🔽 Cargar valor guardado (si existe)
    if bot_settings:
        pause_entry.insert(0, str(bot_settings.get("pause_minutes", 20)))



    # 👉 Botón para ejecutar creator
    from app.creator.creator import execute_creator

    creator_button = ctk.CTkButton(
        options_frame,
        text="Ejecutar Creator",
        command=execute_creator,
        fg_color="#007ACC",
        text_color="white",
        font=("Arial", 12)
    )
    creator_button.pack(pady=(20, 10), anchor="w")

    #! 👉 Botón para abrir ventana nueva
    def open_new_window():
        create_new_window(root)

    new_window_button = ctk.CTkButton(
        options_frame,
        text="Configuración del creator",
        command=open_new_window,
        fg_color="#28a745",
        text_color="white",
        font=("Arial", 12)
    )
    new_window_button.pack(pady=(0, 0), anchor="w")

    # 👉 Botón para guardar configuración completa
    def save_bot_config():
        iterations = iterations_entry.get()
        pause_minutes = pause_entry.get()
        enable_adb = adb_checkbox.get() == 1
        enable_proxy = proxy_checkbox.get() == 1

        if not iterations.isdigit():
            messagebox.showerror("Error", "Ingresa un número válido de iteraciones.")
            return

        if not pause_minutes.isdigit():
            messagebox.showerror("Error", "Ingresa un número válido de minutos para la pausa.")
            return

        success = save_bot_settings(int(iterations), int(pause_minutes), enable_adb, enable_proxy)
        if success:
            messagebox.showinfo("Guardado", "✅ Configuración del bot guardada correctamente.")
        else:
            messagebox.showerror("Error", "No se pudo guardar la configuración.")

    save_config_button = ctk.CTkButton(
        hostinger_frame,
        text="Guardar Configuración",
        command=save_bot_config,
        fg_color="#0066cc",
        text_color="white"
    )
    save_config_button.pack(pady=(0, 15))

    # 👉 Input: NopeCHA API Key
    #nopecha_label = ctk.CTkLabel(
    #    hostinger_frame,
    #    text="NopeCHA API Key:",
    #    text_color="black",
    #    font=("Arial", 12, "bold")
    #)
    #nopecha_label.pack(pady=(10, 2), anchor="w")

    #nopecha_entry = ctk.CTkEntry(
    #    hostinger_frame,
    #    width=200,
    #    placeholder_text="sub_xxxxxxxxxxxxxxxxxxxxxxxxx"
    #)
    #nopecha_entry.pack(pady=(0, 5))

    # Cargar clave guardada si existe
    #stored_key = get_nopecha_key()
    #if stored_key:
    #    nopecha_entry.insert(0, stored_key)

    #def save_nopecha_key_ui():
    #    pass
    #    key = nopecha_entry.get().strip()
    #    if not key:
    #        messagebox.showerror("Error", "La clave NopeCHA no puede estar vacía.")
    #        return

    #    if save_nopecha_key(key):
    #        messagebox.showinfo("Guardado", "✅ NopeCHA key guardada correctamente.")
    #    else:
    #        messagebox.showerror("Error", "No se pudo guardar la NopeCHA key.")

    #save_nopecha_button = ctk.CTkButton(
    #    hostinger_frame,
    #    text="Guardar NopeCHA Key",
    #    command=save_nopecha_key_ui,
    #    fg_color="#0066cc",
    #    text_color="white"
    #)
    #save_nopecha_button.pack(pady=(0, 15))

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
            registros = parse_email_file(file_path)
            registros_guardados = 0

            for email, email_hostinger, password_hostinger in registros:
                print(email, email_hostinger, password_hostinger)
                success = save_emails(email, email_hostinger, password_hostinger)
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
        resultado = run_checker()

        #if resultado:
         #   messagebox.showinfo(
         #       "Verificación completada",
         #       "✅ Proceso finalizado correctamente.\n\nLos correos verificados fueron guardados en la carpeta:\nverifications/"
         #   )
        #else:
        #    messagebox.showwarning(
        #        "Verificación incompleta",
        #        "⚠️ No se pudo verificar ninguna cuenta.\n\nPor favor revisa errores en consola y verifica credenciales.\nLos resultados (si hay alguno) están en:\nverifications/"
        #    )


    run_checker_button = ctk.CTkButton(
        hostinger_frame,
        text="Ejecutar Bot",
        command=handle_run_checker,
        fg_color="#007ACC",   # Azul
        text_color="white"
    )
    run_checker_button.pack(pady=(10, 10))


    stop_button = ctk.CTkButton(
        hostinger_frame,
        text="Detener Bot",
        command=stop_bot,
        fg_color="red",
        text_color="white"
    )
    stop_button.pack(pady=(5, 10))

    # 👉 Checkboxes para opciones del bot (lado izquierdo - al final)
    options_title = ctk.CTkLabel(
        hostinger_frame,
        text="⚙️ Opciones del Bot",
        text_color="black",
        font=("Arial", 14, "bold")
    )
    options_title.pack(pady=(20, 15), anchor="center")

    # Checkbox para ADB (modo avión)
    adb_checkbox = ctk.CTkCheckBox(
        hostinger_frame,
        text="Activar modo avión (ADB)",
        text_color="black",
        font=("Arial", 12),
        checkbox_width=20,
        checkbox_height=20
    )
    adb_checkbox.pack(pady=(0, 10), anchor="center")

    # Checkbox para Proxy
    proxy_checkbox = ctk.CTkCheckBox(
        hostinger_frame,
        text="Activar proxy",
        text_color="black",
        font=("Arial", 12),
        checkbox_width=20,
        checkbox_height=20
    )
    proxy_checkbox.pack(pady=(0, 15), anchor="center")

    # 🔽 Función para guardar automáticamente cuando cambien los checkboxes
    def auto_save_checkboxes():
        try:
            iterations = iterations_entry.get() or "5"  # Valor por defecto si está vacío
            pause_minutes = pause_entry.get() or "20"  # Valor por defecto si está vacío
            
            # Convertir a enteros con valores por defecto
            iterations_val = int(iterations) if iterations.isdigit() else 5
            pause_minutes_val = int(pause_minutes) if pause_minutes.isdigit() else 20
            
            enable_adb = adb_checkbox.get() == 1
            enable_proxy = proxy_checkbox.get() == 1
            
            success = save_bot_settings(iterations_val, pause_minutes_val, enable_adb, enable_proxy)
            if success:
                print("✅ Configuración de checkboxes guardada automáticamente")
            else:
                print("❌ Error al guardar configuración automáticamente")
        except Exception as e:
            print(f"❌ Error en auto-guardado: {e}")

    # 🔽 Cargar valores guardados de los checkboxes
    if bot_settings:
        adb_checkbox.select() if bot_settings.get("enable_adb", True) else adb_checkbox.deselect()
        proxy_checkbox.select() if bot_settings.get("enable_proxy", True) else proxy_checkbox.deselect()
    else:
        # Valores por defecto si no hay configuración
        adb_checkbox.select()
        proxy_checkbox.select()

    # 🔽 Conectar eventos de cambio a los checkboxes
    adb_checkbox.configure(command=auto_save_checkboxes)
    proxy_checkbox.configure(command=auto_save_checkboxes)

    # ================= Capturar Coordenadas =================
    #def add_coordinates_interactively():
    #    etiquetas = [
    #        "first_click",
    #        "second_click",
    #        "third_click",
    #        "fourth_click"
    #    ]

    #    coordenadas = []

        # Abrir Chrome utilizando la misma configuración del bot
    #    driver = openProfileWithExtraExtension()
    #    driver.maximize_window()
    #    driver.get("https://www.google.com/")

    #    def capturar_y_mostrar(index, popup):
    #        popup.lift()
    #        popup.focus_force()
    #        popup.attributes("-topmost", True)

    #        label = ctk.CTkLabel(
    #            popup,
    #            text=f"Presiona la tecla 'c' para capturar la coordenada de:\n{etiquetas[index]}",
    #            font=("Arial", 14),
    #            text_color="black"
    #        )
    #        label.pack(pady=15)

    #        coord_label = ctk.CTkLabel(
    #            popup,
    #            text="",
    #            font=("Arial", 14, "bold"),
    #            text_color="black"
    #        )
    #        coord_label.pack(pady=10)

    #        def capturar():
    #            coord_raw = get_mouse_coordinate_on_keypress("c")  # formato "123x456"
    #            # Convertir a "123 x 456"
    #            if "x" in coord_raw:
    #                x, y = coord_raw.split("x")
    #                coord = f"{x} x {y}"
    #            else:
    #                coord = coord_raw
    #            coordenadas.append(coord)
    #            popup.after(0, lambda: coord_label.configure(text=f"{etiquetas[index]}: {coord}"))

    #        threading.Thread(target=capturar, daemon=True).start()

    #        def siguiente():
    #            popup.destroy()
    #            if index + 1 < len(etiquetas):
    #                mostrar_popup(index + 1)
    #            else:
    #                # Guardar coordenadas en la base de datos
    #                if save_click_coordinates(coordenadas):
    #                    messagebox.showinfo("Guardado", "✅ Coordenadas guardadas correctamente.")
    #                else:
    #                    messagebox.showerror("Error", "No se pudieron guardar las coordenadas.")

    #            try:
    #                driver.quit()
    #            except Exception as e:
    #                print(f"❌ Error al cerrar Chrome: {e}")

    #        next_button = ctk.CTkButton(
    #            popup,
    #            text="Próxima coordenada" if index + 1 < len(etiquetas) else "Finalizar",
    #            command=siguiente,
    #            fg_color="#5C2D91",
    #            text_color="white",
    #            hover_color="#472173"
    #        )
    #        next_button.pack(pady=15)

    #    def mostrar_popup(index):
    #        popup = ctk.CTkToplevel()
    #        popup.geometry("420x220")
    #        popup.title("Captura de Coordenada")
    #        popup.configure(fg_color="#f0f0f0")
    #        capturar_y_mostrar(index, popup)

    #    mostrar_popup(0)

    #capture_coords_button = ctk.CTkButton(
    #    hostinger_frame,
    #    text="Capturar Coordenadas",
    #    command=add_coordinates_interactively,
    #    fg_color="#9C27B0",
    #    text_color="white"
    #)
    #capture_coords_button.pack(pady=(5, 10))

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
