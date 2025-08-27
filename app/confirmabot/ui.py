def setup_ui(logged_in_user, on_login_success):
    import customtkinter as ctk
    from tkinter import filedialog
    from tkinter import messagebox
    from app.auth.auth import logout
    from app.confirmabot.auth_ui import setup_auth_ui
    from app.database.database import save_bot_settings, get_bot_settings, save_emails, get_all_emails, get_email_count, clear_emails, save_first_three_coordinates, save_fourth_fifth_coordinates, save_nopecha_key, get_nopecha_key, save_user_agent, get_user_agent

    from app.confirmabot.confirm_bot import run_checker, stop_bot, run_creator, open_chrome_profile as openProfileWithExtraExtension
    import threading
    from app.confirmabot.utils.field_reader import parse_email_file  
    from app.confirmabot.utils.mouse_click_coordenates import get_mouse_coordinate_on_keypress

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

    # 👉 Contenedor para inputs de Hostinger (lado izquierdo)
    hostinger_frame = ctk.CTkFrame(root, fg_color="transparent")
    hostinger_frame.place(relx=0.0, rely=0.0, anchor="nw", x=20, y=100)

    # 👉 Contenedor para botones del lado derecho
    right_frame = ctk.CTkFrame(root, fg_color="transparent")
    right_frame.place(relx=1.0, rely=0.0, anchor="ne", x=-20, y=100)

    # 👉 Título del frame derecho
    right_title_label = ctk.CTkLabel(
        right_frame,
        text="🎯 Configuración del creador de cuentas",
        text_color="black",
        font=("Arial", 16, "bold")
    )
    right_title_label.pack(pady=(0, 15), anchor="w")


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

    # 👉 Input: NopeCHA API Key
    nopecha_label = ctk.CTkLabel(
        hostinger_frame,
        text="NopeCHA API Key:",
        text_color="black",
        font=("Arial", 12, "bold")
    )
    nopecha_label.pack(pady=(10, 2), anchor="w")

    nopecha_entry = ctk.CTkEntry(
        hostinger_frame,
        width=200,
        placeholder_text="sub_xxxxxxxxxxxxxxxxxxxxxxxxx"
    )
    nopecha_entry.pack(pady=(0, 5))

    # Cargar clave guardada si existe
    stored_key = get_nopecha_key()
    if stored_key:
        nopecha_entry.insert(0, stored_key)

    def save_nopecha_key_ui():
        key = nopecha_entry.get().strip()
        if not key:
            messagebox.showerror("Error", "La clave NopeCHA no puede estar vacía.")
            return

        if save_nopecha_key(key):
            messagebox.showinfo("Guardado", "✅ NopeCHA key guardada correctamente.")
        else:
            messagebox.showerror("Error", "No se pudo guardar la NopeCHA key.")

    save_nopecha_button = ctk.CTkButton(
        hostinger_frame,
        text="Guardar NopeCHA Key",
        command=save_nopecha_key_ui,
        fg_color="#0066cc",
        text_color="white"
    )
    save_nopecha_button.pack(pady=(0, 15))

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

        if resultado:
            messagebox.showinfo(
                "Verificación completada",
                "✅ Proceso finalizado correctamente.\n\nLos correos verificados fueron guardados en la carpeta:\nverifications/"
            )
        else:
            messagebox.showwarning(
                "Verificación incompleta",
                "⚠️ No se pudo verificar ninguna cuenta.\n\nPor favor revisa errores en consola y verifica credenciales.\nLos resultados (si hay alguno) están en:\nverifications/"
            )


    run_checker_button = ctk.CTkButton(
        hostinger_frame,
        text="Ejecutar Confirmabot",
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

    # ================= Ejecutar Creador =================
    def handle_run_creator():
        resultado = run_creator()
        
        # No mostrar messagebox, solo ejecutar silenciosamente
        if resultado:
            print("✅ Creador ejecutado correctamente")
        else:
            print("❌ Error al ejecutar el creador")

    run_creator_button = ctk.CTkButton(
        right_frame,
        text="🚀 Ejecutar Creador",
        command=handle_run_creator,
        fg_color="#28A745",  # Verde
        text_color="white",
        hover_color="#218838",
        width=220,  # Tamaño reducido
        height=35   # Tamaño reducido
    )
    run_creator_button.pack(pady=(10, 10))

    # ================= Capturar Coordenadas =================
    def add_coordinates_interactively():
        etiquetas = [
            "first_click",
            "second_click",
            "third_click"
        ]

        coordenadas = []

        # Abrir Chrome utilizando la misma configuración del bot en modo incógnito
        driver = openProfileWithExtraExtension()
        driver.maximize_window()
        driver.get("https://www.google.com/")

        def capturar_y_mostrar(index, popup):
            popup.lift()
            popup.focus_force()
            popup.attributes("-topmost", True)

            label = ctk.CTkLabel(
                popup,
                text=f"Presiona la tecla 'c' para capturar la coordenada de:\n{etiquetas[index]}",
                font=("Arial", 14),
                text_color="black"
            )
            label.pack(pady=15)

            coord_label = ctk.CTkLabel(
                popup,
                text="",
                font=("Arial", 14, "bold"),
                text_color="black"
            )
            coord_label.pack(pady=10)

            def capturar():
                coord_raw = get_mouse_coordinate_on_keypress("c")  # formato "123x456"
                # Convertir a "123 x 456"
                if "x" in coord_raw:
                    x, y = coord_raw.split("x")
                    coord = f"{x} x {y}"
                else:
                    coord = coord_raw
                coordenadas.append(coord)
                popup.after(0, lambda: coord_label.configure(text=f"{etiquetas[index]}: {coord}"))

            threading.Thread(target=capturar, daemon=True).start()

            def siguiente():
                popup.destroy()
                if index + 1 < len(etiquetas):
                    mostrar_popup(index + 1)
                else:
                    # Guardar solo las primeras 3 coordenadas en la base de datos
                    if save_first_three_coordinates(coordenadas):
                        messagebox.showinfo("Guardado", "✅ Primeras 3 coordenadas guardadas correctamente.")
                    else:
                        messagebox.showerror("Error", "No se pudieron guardar las coordenadas.")

                    try:
                        driver.quit()
                    except Exception as e:
                        print(f"❌ Error al cerrar Chrome: {e}")

            next_button = ctk.CTkButton(
                popup,
                text="Próxima coordenada" if index + 1 < len(etiquetas) else "Finalizar",
                command=siguiente,
                fg_color="#5C2D91",
                text_color="white",
                hover_color="#472173"
            )
            next_button.pack(pady=15)

        def mostrar_popup(index):
            popup = ctk.CTkToplevel()
            popup.geometry("420x220")
            popup.title("Captura de Coordenada")
            popup.configure(fg_color="#f0f0f0")
            capturar_y_mostrar(index, popup)

        mostrar_popup(0)

    # ================= Capturar Coordenadas 4 y 5 =================
    def add_fourth_fifth_coordinates():
        etiquetas = [
            "fourth_click",
            "fifth_click"
        ]

        coordenadas = []

        # Abrir Chrome utilizando la misma configuración del bot en modo incógnito
        driver = openProfileWithExtraExtension(incognito_mode=True)
        driver.maximize_window()
        driver.get("https://www.linkedin.com/signup?_l=us&trk=guest_homepage-basic_nav-header-join.com/")

        def capturar_y_mostrar(index, popup):
            popup.lift()
            popup.focus_force()
            popup.attributes("-topmost", True)

            label = ctk.CTkLabel(
                popup,
                text=f"Presiona la tecla 'c' para capturar la coordenada de:\n{etiquetas[index]}",
                font=("Arial", 14),
                text_color="black"
            )
            label.pack(pady=15)

            coord_label = ctk.CTkLabel(
                popup,
                text="",
                font=("Arial", 14, "bold"),
                text_color="black"
            )
            coord_label.pack(pady=10)

            def capturar():
                coord_raw = get_mouse_coordinate_on_keypress("c")  # formato "123x456"
                # Convertir a "123 x 456"
                if "x" in coord_raw:
                    x, y = coord_raw.split("x")
                    coord = f"{x} x {y}"
                else:
                    coord = coord_raw
                coordenadas.append(coord)
                popup.after(0, lambda: coord_label.configure(text=f"{etiquetas[index]}: {coord}"))

            threading.Thread(target=capturar, daemon=True).start()

            def siguiente():
                popup.destroy()
                if index + 1 < len(etiquetas):
                    mostrar_popup(index + 1)
                else:
                    # Guardar solo las coordenadas 4 y 5 en la base de datos
                    if save_fourth_fifth_coordinates(coordenadas[0], coordenadas[1]):
                        messagebox.showinfo("Guardado", "✅ Coordenadas 4 y 5 guardadas correctamente.")
                    else:
                        messagebox.showerror("Error", "No se pudieron guardar las coordenadas 4 y 5.")

                    try:
                        driver.quit()
                    except Exception as e:
                        print(f"❌ Error al cerrar Chrome: {e}")

            next_button = ctk.CTkButton(
                popup,
                text="Próxima coordenada" if index + 1 < len(etiquetas) else "Finalizar",
                command=siguiente,
                fg_color="#5C2D91",
                text_color="white",
                hover_color="#472173"
            )
            next_button.pack(pady=15)

        def mostrar_popup(index):
            popup = ctk.CTkToplevel()
            popup.geometry("420x220")
            popup.title("Captura de Coordenadas 4 y 5")
            popup.configure(fg_color="#f0f0f0")
            capturar_y_mostrar(index, popup)

        mostrar_popup(0)

    capture_coords_button = ctk.CTkButton(
        hostinger_frame,
        text="Capturar Coordenadas",
        command=add_coordinates_interactively,
        fg_color="#9C27B0",
        text_color="white"
    )
    capture_coords_button.pack(pady=(5, 10))


    # 👉 Input: User Agent
    user_agent_label = ctk.CTkLabel(
        right_frame,
        text="User Agent:",
        text_color="black",
        font=("Arial", 12, "bold")
    )
    user_agent_label.pack(pady=(10, 2), anchor="center")

    user_agent_entry = ctk.CTkEntry(
        right_frame,
        width=220,  # Mismo ancho que los botones
        placeholder_text="Mozilla/5.0 (Windows NT 10.0; Win64; x64)..."
    )
    user_agent_entry.pack(pady=(0, 5))

    # Cargar User Agent guardado si existe
    stored_user_agent = get_user_agent()
    if stored_user_agent:
        user_agent_entry.insert(0, stored_user_agent)

    def save_user_agent_ui():
        user_agent = user_agent_entry.get().strip()
        if not user_agent:
            messagebox.showerror("Error", "El User Agent no puede estar vacío.")
            return

        if save_user_agent(user_agent):
            messagebox.showinfo("Guardado", "✅ User Agent guardado correctamente.")
        else:
            messagebox.showerror("Error", "No se pudo guardar el User Agent.")

    save_user_agent_button = ctk.CTkButton(
        right_frame,
        text="💾 Guardar User Agent",
        command=save_user_agent_ui,
        fg_color="#0066cc",
        text_color="white",
        hover_color="#0052a3",
        width=220,  # Mismo ancho que los otros botones
        height=35   # Mismo alto que los otros botones
    )
    save_user_agent_button.pack(pady=(0, 15))



    # 👉 Botón para capturar coordenadas 4 y 5
    capture_coords_4_5_button = ctk.CTkButton(
        right_frame,
        text="📱 Capturar Coordenadas LinkedIn",
        command=add_fourth_fifth_coordinates,
        fg_color="#FF9800",  # Naranja
        text_color="white",
        hover_color="#F57C00",
        width=220,  # Tamaño reducido
        height=35   # Tamaño reducido
    )
    capture_coords_4_5_button.pack(pady=(5, 10))

    # ================= Cargar Correos desde .txt =================
    def load_emails_from_txt():
        file_path = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt")],
            title="Seleccionar archivo .txt con correos"
        )

        if not file_path:
            return

        try:
            # Importar la función de detección automática
            from app.confirmabot.utils.field_reader import auto_detect_email_format
            from app.database.database import save_txt_emails, get_txt_emails_count
            
            print(f"📁 Archivo seleccionado: {file_path}")
            
            # Usar detección automática de formato
            registros = auto_detect_email_format(file_path)
            
            if registros:
                print(f"\n📧 Correos leídos del archivo:")
                print("=" * 50)
                for i, (email, email_hostinger, password) in enumerate(registros, 1):
                    print(f"{i:2d}. {email}")
                print("=" * 50)
                print(f"✅ Total de correos procesados: {len(registros)}")
                
                # Extraer solo los emails para guardar en la base de datos
                # Para formato simple: registro[0] es el email
                emails_list = [registro[0] for registro in registros]
                
                # Guardar en la base de datos
                print("\n💾 Guardando correos en la base de datos...")
                if save_txt_emails(emails_list):
                    print("✅ Correos guardados exitosamente en la base de datos")
                    # Actualizar el contador en la UI
                    update_txt_emails_count()
                    # Mostrar mensaje de éxito
                    messagebox.showinfo(
                        "Éxito", 
                        f"✅ Se cargaron {len(registros)} correos exitosamente desde el archivo.\n\nLos correos han sido guardados en la base de datos."
                    )
                else:
                    print("❌ Error al guardar correos en la base de datos")
                    messagebox.showerror(
                        "Error", 
                        "❌ No se pudieron guardar los correos en la base de datos.\n\nPor favor revisa los errores en la consola."
                    )
            else:
                print("❌ No se pudieron leer correos del archivo")
                # Mostrar messagebox informando sobre el formato incorrecto
                messagebox.showerror(
                    "Formato de archivo incorrecto", 
                    "❌ El archivo seleccionado no tiene el formato correcto.\n\n"
                    "📋 Formato requerido: un email por línea\n"
                    "Ejemplo:\n"
                    "dinner174qbda@play387dlbu.33mail.com\n"
                    "just401yfcw@car60gvku.33mail.com\n"
                    "base318qkrp@challenge200duqh.33mail.com\n\n"
                    "⚠️ NO se aceptan archivos con formato de bloques (dominio, email, contraseña).\n"
                    "Corrige el formato del archivo y vuelve a intentar."
                )

        except Exception as e:
            print(f"❌ Error al procesar el archivo: {e}")
            messagebox.showerror(
                "Error", 
                f"❌ Error al procesar el archivo:\n{e}\n\nPor favor verifica que el archivo sea válido."
            )

    def clear_txt_emails_ui():
        """Función para eliminar todos los correos del archivo .txt"""
        try:
            from app.database.database import clear_txt_emails
            
            # Confirmar antes de eliminar
            confirm = messagebox.askyesno(
                "Confirmar eliminación", 
                "¿Estás seguro de que quieres eliminar TODOS los correos del archivo .txt?\n\nEsta acción no se puede deshacer."
            )
            
            if confirm:
                if clear_txt_emails():
                    messagebox.showinfo(
                        "Eliminación exitosa", 
                        "✅ Todos los correos del archivo .txt han sido eliminados."
                    )
                    # Actualizar el contador en la UI
                    update_txt_emails_count()
                else:
                    messagebox.showerror(
                        "Error", 
                        "❌ No se pudieron eliminar los correos."
                    )
        except Exception as e:
            print(f"❌ Error al eliminar correos: {e}")
            messagebox.showerror("Error", f"Error al eliminar correos: {e}")

    def update_txt_emails_count():
        """Función para actualizar el contador de correos en la UI"""
        try:
            from app.database.database import get_txt_emails_count
            count = get_txt_emails_count()
            txt_emails_count_label.configure(text=f"📧 Correos almacenados: {count}")
        except Exception as e:
            print(f"❌ Error al actualizar contador: {e}")
            txt_emails_count_label.configure(text="📧 Correos almacenados: Error")

    # 👉 Botón para cargar correos desde .txt
    load_emails_txt_button = ctk.CTkButton(
        right_frame,
        text="📧 Cargar Correos",
        command=load_emails_from_txt,
        fg_color="#17A2B8",  # Azul claro
        text_color="white",
        hover_color="#138496",
        width=220,  # Tamaño reducido
        height=35   # Tamaño reducido
    )
    load_emails_txt_button.pack(pady=(5, 10))

    # 👉 Botón para eliminar todos los correos del archivo .txt
    clear_txt_emails_button = ctk.CTkButton(
        right_frame,
        text="🗑️ Eliminar Correos",
        command=clear_txt_emails_ui,
        fg_color="#DC3545",  # Rojo
        text_color="white",
        hover_color="#C82333",
        width=220,  # Tamaño reducido
        height=35   # Tamaño reducido
    )
    clear_txt_emails_button.pack(pady=(5, 10))



    # 👉 Etiqueta para mostrar la cantidad de correos en .txt
    txt_emails_count_label = ctk.CTkLabel(
        right_frame,
        text="📧 Correos almacenados: 0",
        text_color="black",
        font=("Arial", 12, "bold")
    )
    txt_emails_count_label.pack(pady=(5, 10), anchor="w")
    update_txt_emails_count() # Inicializar el contador

    #  Función de logout
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
