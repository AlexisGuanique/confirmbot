def setup_ui(logged_in_user, on_login_success):
    import customtkinter as ctk
    from tkinter import filedialog
    from tkinter import messagebox
    from app.auth.auth import logout
    from app.confirmabot.auth_ui import setup_auth_ui
    from app.database.database import (
        save_bot_settings,
        get_bot_settings,
        save_emails,
        get_all_emails,
        get_email_count,
        clear_emails,
        save_click_coordinates,
        save_nopecha_key,
        get_nopecha_key,
        get_default_browser,
        get_creator_setting,
        save_creator_setting,
        create_browser,
    )

    from app.confirmabot.confirm_bot import run_checker, stop_bot, open_temp_chrome_profile as openProfileWithExtraExtension
    import threading
    import time
    from app.confirmabot.utils.field_reader import parse_email_file  
    from app.confirmabot.utils.mouse_click_coordenates import get_mouse_coordinate_on_keypress
    from app.creator.ui_creator import create_new_window, open_proxy_rotation_config_modal

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("Confirma Bot")
    root.geometry("600x720")
    root.minsize(520, 480)
    root.configure(fg_color="#FFFFFF")  # Fondo blanco

    welcome_label = ctk.CTkLabel(
        root,
        text=f"Bienvenido a Confirma Bot, {logged_in_user}.",
        font=("Arial", 22, "bold"),
        text_color="black",
    )
    welcome_label.pack(pady=(16, 6))

    scroll_outer = ctk.CTkFrame(root, fg_color="#FFFFFF")
    # Espacio inferior para el botón «Cerrar sesión» fijo
    scroll_outer.pack(fill="both", expand=True, padx=0, pady=(0, 56))

    main_scroll = ctk.CTkScrollableFrame(scroll_outer, fg_color="#FFFFFF")
    main_scroll.pack(fill="both", expand=True, padx=6, pady=4)

    titles_row = ctk.CTkFrame(main_scroll, fg_color="transparent")
    titles_row.pack(fill="x", pady=(0, 8))
    ctk.CTkLabel(
        titles_row,
        text="ConfirmaBot",
        text_color="black",
        font=("Arial", 16, "bold"),
    ).pack(side="left", anchor="w")
    ctk.CTkLabel(
        titles_row,
        text="Linkedin Creator",
        text_color="black",
        font=("Arial", 16, "bold"),
    ).pack(side="right", anchor="e")

    columns_row = ctk.CTkFrame(main_scroll, fg_color="transparent")
    columns_row.pack(fill="both", expand=True)

    hostinger_frame = ctk.CTkFrame(columns_row, fg_color="transparent")
    hostinger_frame.pack(side="left", anchor="nw", fill="both", expand=True, padx=(0, 10))

    options_frame = ctk.CTkFrame(columns_row, fg_color="transparent")
    options_frame.pack(side="right", anchor="ne", fill="both", expand=True, padx=(10, 0))


    # Los inputs de configuración del bot se movieron a una ventana separada



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


    # 👉 Mostrar cantidad de dominios y hacer clic para verlos
    email_count_label = ctk.CTkLabel(
        hostinger_frame,
        text=f"Dominios cargados: {get_email_count()} (click para ver)",
        text_color="blue",
        font=("Arial", 12, "bold"),
        cursor="hand2",
    )
    email_count_label.pack(pady=(10, 2), anchor="w")



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

   # 👉 Contenedor oculto que mostrará los dominios (se empaqueta al expandir; dentro del scroll)
    domain_view_frame = ctk.CTkFrame(
        hostinger_frame,
        fg_color="white",
        corner_radius=8,
        border_width=1,
        border_color="black",
    )

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

    def toggle_domain_view(event=None):
        if domain_view_frame.winfo_ismapped():
            domain_view_frame.pack_forget()
        else:
            update_domain_list()
            domain_view_frame.pack(fill="x", pady=(0, 10), after=load_emails_button)

    email_count_label.bind("<Button-1>", toggle_domain_view)

                
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

        #! 👉 Botón para abrir ventana de gestión de navegadores
    def open_browser_manager():
        from app.creator.browser_manager import create_browser_manager_window
        create_browser_manager_window(root)

    new_window_button = ctk.CTkButton(
        options_frame,
        text="Configuración del creator",
        command=open_browser_manager,
        fg_color="#28a745",
        text_color="white",
        font=("Arial", 12)
    )
    new_window_button.pack(pady=(0, 10), anchor="w")

    # 👉 Función para abrir ventana de configuración del bot
    def open_config_window():
        """Abre la ventana de configuración del bot"""
        config_window = ctk.CTkToplevel(root)
        config_window.title("Configuración del Bot")
        config_window.geometry("400x400")
        config_window.resizable(False, False)
        config_window.configure(fg_color="white")
        
        # Centrar la ventana
        config_window.transient(root)
        config_window.grab_set()
        
        # Frame principal con scroll
        main_frame = ctk.CTkScrollableFrame(config_window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        title_label = ctk.CTkLabel(
            main_frame,
            text="Configuración del Bot",
            font=("Arial", 18, "bold"),
            text_color="black"
        )
        title_label.pack(pady=(0, 20))
        
        # Input: Cantidad de iteraciones
        iterations_label = ctk.CTkLabel(
            main_frame,
            text="Cantidad de emails creados por dominio:",
            text_color="black",
            font=("Arial", 12, "bold")
        )
        iterations_label.pack(pady=(10, 2), anchor="w")
        
        iterations_entry = ctk.CTkEntry(
            main_frame,
            width=300,
            placeholder_text="Ej: 5"
        )
        iterations_entry.pack(pady=(0, 10))
        
        # Input: Tiempo de pausa
        pause_label = ctk.CTkLabel(
            main_frame,
            text="Tiempo de pausa (minutos) cada 10 iteraciones:",
            text_color="black",
            font=("Arial", 12, "bold")
        )
        pause_label.pack(pady=(10, 2), anchor="w")
        
        pause_entry = ctk.CTkEntry(
            main_frame,
            width=300,
            placeholder_text="Ej: 20"
        )
        pause_entry.pack(pady=(0, 10))
        
        # Input: Emails por corte
        emails_batch_label = ctk.CTkLabel(
            main_frame,
            text="Emails por corte (para envío de reportes):",
            text_color="black",
            font=("Arial", 12, "bold")
        )
        emails_batch_label.pack(pady=(10, 2), anchor="w")
        
        emails_batch_entry = ctk.CTkEntry(
            main_frame,
            width=300,
            placeholder_text="Ej: 5"
        )
        emails_batch_entry.pack(pady=(0, 20))
        
        # Cargar valores guardados
        bot_settings = get_bot_settings()
        if bot_settings:
            iterations_entry.insert(0, str(bot_settings["iterations"]))
            pause_entry.insert(0, str(bot_settings.get("pause_minutes", 20)))
            emails_batch_entry.insert(0, str(bot_settings.get("emails_per_batch", 5)))
        
        def save_config():
            """Guarda la configuración del bot"""
            try:
                iterations = int(iterations_entry.get())
                pause_minutes = int(pause_entry.get())
                emails_per_batch = int(emails_batch_entry.get())
                
                if iterations <= 0 or pause_minutes < 0 or emails_per_batch <= 0:
                    messagebox.showerror("Error", "Los valores deben ser números positivos.")
                    return
                
                # Obtener valores actuales de los checkboxes para no sobrescribirlos
                current_settings = get_bot_settings()
                enable_adb = current_settings.get("enable_adb", True) if current_settings else True
                pc = current_settings.get("proxy_via_coordinates", False) if current_settings else False
                pw = current_settings.get("proxy_via_windows", True) if current_settings else True
                enable_creator_ua = (
                    current_settings.get("enable_creator_user_agent_actions", False) if current_settings else False
                )

                save_bot_settings(
                    iterations,
                    pause_minutes,
                    enable_adb,
                    emails_per_batch,
                    proxy_via_coordinates=pc,
                    proxy_via_windows=pw,
                    enable_creator_user_agent_actions=enable_creator_ua,
                )
                
                messagebox.showinfo("Éxito", "Configuración guardada correctamente.")
                config_window.destroy()
                
            except ValueError:
                messagebox.showerror("Error", "Por favor ingresa números válidos.")
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar: {e}")
        
        # Botones
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(10, 0))
        
        save_button = ctk.CTkButton(
            buttons_frame,
            text="Guardar",
            command=save_config,
            fg_color="#007ACC",
            hover_color="#005A9E",
            width=120,
            height=40
        )
        save_button.pack(side="left", padx=(0, 10))
        
        cancel_button = ctk.CTkButton(
            buttons_frame,
            text="Cancelar",
            command=config_window.destroy,
            fg_color="#6C757D",
            hover_color="#5A6268",
            width=120,
            height=40
        )
        cancel_button.pack(side="left")


    # 👉 Botón para abrir configuración del bot
    config_bot_button = ctk.CTkButton(
        hostinger_frame,
        text="Configuración del Bot",
        command=open_config_window,
        fg_color="#FF6B35",
        text_color="white",
        font=("Arial", 12)
    )
    config_bot_button.pack(pady=(0, 15))

    # 👉 Función para abrir ventana de configuración del nombre del bot
    def open_bot_name_config():
        """Abre un modal para configurar el nombre del bot"""
        from app.database.database import get_bot_connection_config, save_bot_connection_config
        from app.auth.auth import connect_bot, sio
        
        name_window = ctk.CTkToplevel(root)
        name_window.title("Configurar Nombre del Bot")
        name_window.geometry("500x280")
        name_window.resizable(False, False)
        name_window.configure(fg_color="white")
        
        # Centrar la ventana
        name_window.transient(root)
        name_window.grab_set()
        
        # Frame principal
        main_frame = ctk.CTkFrame(name_window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=40, pady=30)
        
        # Título
        title_label = ctk.CTkLabel(
            main_frame,
            text="Configurar Nombre del Bot",
            font=("Arial", 18, "bold"),
            text_color="black"
        )
        title_label.pack(pady=(0, 25))
        
        # Input: Nombre del bot
        name_label = ctk.CTkLabel(
            main_frame,
            text="Nombre del bot:",
            text_color="black",
            font=("Arial", 12, "bold")
        )
        name_label.pack(pady=(0, 8), anchor="w")
        
        name_entry = ctk.CTkEntry(
            main_frame,
            width=400,
            height=40,
            font=("Arial", 12),
            placeholder_text="Ej: ConfirmaBot-MiPC"
        )
        name_entry.pack(pady=(0, 30))
        
        # Cargar nombre actual
        bot_config = get_bot_connection_config()
        if bot_config and bot_config.get("bot_name"):
            name_entry.insert(0, bot_config["bot_name"])
        
        def save_bot_name():
            """Guarda el nombre del bot y reconecta al WebSocket"""
            new_name = name_entry.get().strip()
            
            if not new_name:
                messagebox.showerror("Error", "El nombre del bot no puede estar vacío.")
                return
            
            try:
                # Guardar el nuevo nombre en la base de datos
                bot_type = bot_config.get("bot_type", "creador") if bot_config else "creador"
                success = save_bot_connection_config(new_name, bot_type)
                
                if success:
                    # Desconectar WebSocket actual si está conectado
                    if sio.connected:
                        try:
                            sio.emit('status_update', {'status': 'offline'})
                            time.sleep(0.3)
                            sio.disconnect()
                            print("🔌 WebSocket desconectado para reconectar con nuevo nombre")
                        except Exception as e:
                            print(f"⚠️  Error al desconectar: {e}")
                    
                    # Reconectar con el nuevo nombre
                    print(f"🔄 Reconectando con nuevo nombre: {new_name}")
                    if connect_bot():
                        messagebox.showinfo("Éxito", f"Nombre del bot actualizado a '{new_name}'.\n\nBot reconectado exitosamente.")
                        name_window.destroy()
                    else:
                        messagebox.showwarning("Advertencia", f"Nombre guardado como '{new_name}', pero no se pudo reconectar al servidor.\n\nIntenta reconectar manualmente.")
                        name_window.destroy()
                else:
                    messagebox.showerror("Error", "No se pudo guardar el nombre del bot.")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar: {e}")
        
        # Botones
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(20, 0))
        
        save_button = ctk.CTkButton(
            buttons_frame,
            text="Guardar",
            command=save_bot_name,
            fg_color="#007ACC",
            hover_color="#005A9E",
            width=140,
            height=40,
            font=("Arial", 13, "bold")
        )
        save_button.pack(side="left", padx=(0, 15))
        
        cancel_button = ctk.CTkButton(
            buttons_frame,
            text="Cancelar",
            command=name_window.destroy,
            fg_color="#6C757D",
            hover_color="#5A6268",
            width=140,
            height=40,
            font=("Arial", 13)
        )
        cancel_button.pack(side="left")
        
        # Permitir guardar con Enter
        name_entry.bind("<Return>", lambda e: save_bot_name())
        name_entry.focus()

    # 👉 Botón para configurar nombre del bot
    bot_name_button = ctk.CTkButton(
        hostinger_frame,
        text="Configurar Nombre del Bot",
        command=open_bot_name_config,
        fg_color="#9B59B6",
        text_color="white",
        font=("Arial", 12)
    )
    bot_name_button.pack(pady=(0, 15))


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

    ctk.CTkLabel(
        hostinger_frame,
        text="Proxy (elige un modo):",
        text_color="black",
        font=("Arial", 12, "bold"),
    ).pack(pady=(0, 4), anchor="center")

    proxy_coord_checkbox = ctk.CTkCheckBox(
        hostinger_frame,
        text="Proxy por coordenadas (clics / extensión)",
        text_color="black",
        font=("Arial", 12),
        checkbox_width=20,
        checkbox_height=20,
    )
    proxy_coord_checkbox.pack(pady=(0, 6), anchor="center")

    proxy_win_checkbox = ctk.CTkCheckBox(
        hostinger_frame,
        text="Proxy de Windows (registro del sistema)",
        text_color="black",
        font=("Arial", 12),
        checkbox_width=20,
        checkbox_height=20,
    )
    proxy_win_checkbox.pack(pady=(0, 10), anchor="center")

    def _on_proxy_coord_toggle():
        if proxy_coord_checkbox.get() == 1:
            proxy_win_checkbox.deselect()
        auto_save_checkboxes()

    def _on_proxy_win_toggle():
        if proxy_win_checkbox.get() == 1:
            proxy_coord_checkbox.deselect()
        auto_save_checkboxes()

    # Rotación proxy (creator): debajo de los modos de proxy; solo aparece el botón al marcar el checkbox
    def resolve_main_creator_browser():
        b = get_default_browser()
        if not b:
            bid_new = create_browser("Navegador Principal", True)
            if bid_new:
                b = get_default_browser()
        if b:
            return b["id"], b["name"]
        return None, None

    bid_rot, bname_rot = resolve_main_creator_browser()
    cs_rot = (get_creator_setting(bid_rot) or {}) if bid_rot else {}

    creator_proxy_outer = ctk.CTkFrame(hostinger_frame, fg_color="transparent")
    creator_proxy_outer.pack(fill="x", pady=(0, 12), anchor="w")

    ctk.CTkLabel(
        creator_proxy_outer,
        text="🌐 Creator — URL de proxy",
        font=("Arial", 11, "bold"),
        text_color="black",
    ).pack(anchor="w")
    ctk.CTkLabel(
        creator_proxy_outer,
        text=(
            f"Navegador predeterminado: {bname_rot}"
            if bid_rot
            else "Sin navegador: abre «Configuración del creator» y crea uno."
        ),
        font=("Arial", 10),
        text_color="gray",
        wraplength=320,
        justify="left",
    ).pack(anchor="w", pady=(2, 6))

    main_proxy_url_enabled_var = ctk.IntVar(
        value=1 if cs_rot.get("proxy_url_enabled") else 0
    )
    main_proxy_url_chk = ctk.CTkCheckBox(
        creator_proxy_outer,
        text="Usar URL de proxy configurada",
        text_color="black",
        font=("Arial", 11),
        checkbox_width=20,
        checkbox_height=20,
        variable=main_proxy_url_enabled_var,
    )
    main_proxy_url_chk.pack(anchor="w", pady=(0, 4))

    main_proxy_url_entry = ctk.CTkEntry(
        creator_proxy_outer,
        placeholder_text="https://usuario:pass@host:puerto o http://host:puerto",
        font=("Arial", 11),
        height=32,
    )
    main_proxy_url_entry.pack(fill="x", pady=(0, 8))
    if cs_rot.get("proxy_url"):
        main_proxy_url_entry.insert(0, str(cs_rot["proxy_url"]))

    def save_creator_proxy_url_settings(silent: bool = False):
        bid, _ = resolve_main_creator_browser()
        if not bid:
            if not silent:
                messagebox.showwarning(
                    "Aviso",
                    "No hay navegador en la base de datos.\nAbre «Configuración del creator».",
                )
            return
        cs_m = get_creator_setting(bid) or {}
        pu = main_proxy_url_entry.get().strip()
        en = main_proxy_url_enabled_var.get() == 1
        ok = save_creator_setting(
            browser_id=bid,
            user_agent=cs_m.get("user_agent") or "",
            accounts_to_create=cs_m.get("accounts_to_create") or 1,
            notification_email=cs_m.get("notification_email"),
            isInVps=cs_m.get("isInVps"),
            proxy_rotation_enabled=None,
            proxy_rotation_link=None,
            proxy_url=pu,
            proxy_url_enabled=en,
        )
        if ok:
            if not silent:
                messagebox.showinfo("Éxito", "URL de proxy del Creator guardada.")
            else:
                print(f"✅ Creator proxy URL: checkbox={'sí' if en else 'no'} guardado en BD")
        else:
            if not silent:
                messagebox.showerror("Error", "No se pudo guardar la URL de proxy.")
            else:
                print("❌ No se pudo guardar URL de proxy / checkbox")

    main_proxy_url_chk.configure(
        command=lambda: save_creator_proxy_url_settings(silent=True),
    )

    ctk.CTkButton(
        creator_proxy_outer,
        text="💾 Guardar URL de proxy",
        command=lambda: save_creator_proxy_url_settings(silent=False),
        fg_color="#28a745",
        text_color="white",
        font=("Arial", 11, "bold"),
        width=200,
        height=30,
    ).pack(anchor="w")

    rot_proxy_outer = ctk.CTkFrame(hostinger_frame, fg_color="transparent")
    rot_proxy_outer.pack(fill="x", pady=(0, 14), anchor="w")

    ctk.CTkLabel(
        rot_proxy_outer,
        text="🔄 Creator — rotación proxy",
        font=("Arial", 11, "bold"),
        text_color="black",
    ).pack(anchor="w")
    ctk.CTkLabel(
        rot_proxy_outer,
        text=(
            f"Navegador predeterminado: {bname_rot}"
            if bid_rot
            else "Sin navegador: abre «Configuración del creator» y crea uno."
        ),
        font=("Arial", 10),
        text_color="gray",
        wraplength=320,
        justify="left",
    ).pack(anchor="w", pady=(2, 6))

    main_proxy_rot_var = ctk.IntVar(value=1 if cs_rot.get("proxy_rotation_enabled") else 0)

    def sync_rot_proxy_config_btn():
        bid, _ = resolve_main_creator_browser()
        if main_proxy_rot_var.get() == 1 and bid:
            main_rot_proxy_config_btn.pack(anchor="w", pady=(6, 0))
        else:
            main_rot_proxy_config_btn.pack_forget()

    def on_creator_rot_proxy_toggle():
        bid, _ = resolve_main_creator_browser()
        sync_rot_proxy_config_btn()
        if not bid:
            return
        cs_m = get_creator_setting(bid) or {}
        save_creator_setting(
            browser_id=bid,
            user_agent=cs_m.get("user_agent") or "",
            accounts_to_create=cs_m.get("accounts_to_create") or 1,
            notification_email=cs_m.get("notification_email"),
            isInVps=cs_m.get("isInVps"),
            proxy_rotation_enabled=(main_proxy_rot_var.get() == 1),
            proxy_rotation_link=None,
            proxy_url=cs_m.get("proxy_url"),
            proxy_url_enabled=cs_m.get("proxy_url_enabled"),
        )

    def open_creator_rot_proxy_modal():
        bid, _ = resolve_main_creator_browser()
        if not bid:
            messagebox.showwarning(
                "Aviso",
                "No hay navegador en la base de datos.\nAbre «Configuración del creator».",
            )
            return
        open_proxy_rotation_config_modal(root, bid, include_link_section=True)

    main_rot_proxy_config_btn = ctk.CTkButton(
        rot_proxy_outer,
        text="Configurar rotación proxy",
        fg_color="#6f42c1",
        text_color="white",
        font=("Arial", 11, "bold"),
        width=210,
        height=32,
        command=open_creator_rot_proxy_modal,
    )

    ctk.CTkCheckBox(
        rot_proxy_outer,
        text="Habilitar enlace de rotación de proxy",
        text_color="black",
        font=("Arial", 11),
        checkbox_width=20,
        checkbox_height=20,
        variable=main_proxy_rot_var,
        command=on_creator_rot_proxy_toggle,
    ).pack(anchor="w", pady=(0, 2))

    sync_rot_proxy_config_btn()

    # 🔽 Función para guardar automáticamente cuando cambien los checkboxes
    def auto_save_checkboxes():
        try:
            # Obtener configuración actual para mantener TODOS los campos existentes
            current_settings = get_bot_settings()
            if not current_settings:
                # Si no hay configuración, usar valores por defecto
                iterations_val = 5
                pause_minutes_val = 20
                emails_per_batch_val = 5
            else:
                # Mantener todos los valores existentes
                iterations_val = current_settings.get("iterations", 5)
                pause_minutes_val = current_settings.get("pause_minutes", 20)
                emails_per_batch_val = current_settings.get("emails_per_batch", 5)

            enable_adb = adb_checkbox.get() == 1
            pc = proxy_coord_checkbox.get() == 1
            pw = proxy_win_checkbox.get() == 1
            enable_creator_ua = (
                current_settings.get("enable_creator_user_agent_actions", False)
                if current_settings
                else False
            )

            success = save_bot_settings(
                iterations_val,
                pause_minutes_val,
                enable_adb,
                emails_per_batch_val,
                proxy_via_coordinates=pc,
                proxy_via_windows=pw,
                enable_creator_user_agent_actions=enable_creator_ua,
            )
            if success:
                print("✅ Configuración de checkboxes guardada automáticamente")
            else:
                print("❌ Error al guardar configuración automáticamente")
        except Exception as e:
            print(f"❌ Error en auto-guardado: {e}")

    # 🔽 Cargar valores guardados de los checkboxes
    bot_settings = get_bot_settings()
    if bot_settings:
        adb_checkbox.select() if bot_settings.get("enable_adb", True) else adb_checkbox.deselect()
        pc = bot_settings.get("proxy_via_coordinates", False)
        pw = bot_settings.get("proxy_via_windows", False)
        if pc:
            proxy_coord_checkbox.select()
            proxy_win_checkbox.deselect()
        elif pw:
            proxy_win_checkbox.select()
            proxy_coord_checkbox.deselect()
        elif bot_settings.get("enable_proxy", False):
            proxy_win_checkbox.select()
            proxy_coord_checkbox.deselect()
        else:
            proxy_coord_checkbox.deselect()
            proxy_win_checkbox.deselect()
    else:
        adb_checkbox.select()
        proxy_coord_checkbox.deselect()
        proxy_win_checkbox.select()

    adb_checkbox.configure(command=auto_save_checkboxes)
    proxy_coord_checkbox.configure(command=_on_proxy_coord_toggle)
    proxy_win_checkbox.configure(command=_on_proxy_win_toggle)

   

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
