def create_new_window(parent_root):
    """
    Crea una nueva ventana con tabla de coordenadas del creator
    """
    import customtkinter as ctk
    from tkinter import messagebox
    import threading
    import datetime
    import pytz
    from app.database.database import get_creator_coordinates, save_creator_coordinates, save_creator_setting, get_creator_setting, load_emails_from_file, get_creator_email_count, clear_scheduled_time
    from app.confirmabot.utils.mouse_click_coordenates import get_mouse_coordinate_on_keypress
    from app.creator.image_config import view_image, load_image, get_image_path
    from tkinter import filedialog
    
    # Crear la nueva ventana
    new_window = ctk.CTkToplevel(parent_root)
    new_window.title("Configuración del Creator")
    new_window.geometry("650x600")
    new_window.configure(fg_color="#FFFFFF")
    
    # Centrar la ventana y hacerla modal
    new_window.transient(parent_root)
    new_window.grab_set()
    
    # Crear frame principal con scroll
    main_scroll_frame = ctk.CTkScrollableFrame(new_window, fg_color="transparent")
    main_scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Título de la ventana
    title_label = ctk.CTkLabel(
        main_scroll_frame,
        text="⚙️ Configuración de Coordenadas del Creator",
        font=("Arial", 18, "bold"),
        text_color="black"
    )
    title_label.pack(pady=(20, 30))
    
    # ================= SECCIÓN USER AGENT =================
    
    # Título de la sección User Agent
    user_agent_title = ctk.CTkLabel(
        main_scroll_frame,
        text="🌐 Configuración de User Agent",
        font=("Arial", 16, "bold"),
        text_color="black"
    )
    user_agent_title.pack(pady=(0, 15))
    
    # Frame para el User Agent
    user_agent_frame = ctk.CTkFrame(main_scroll_frame, fg_color="white", corner_radius=5, border_width=2, border_color="black")
    user_agent_frame.pack(fill="x", padx=20, pady=(0, 20))
    
    # Obtener configuración actual
    current_settings = get_creator_setting()
    current_user_agent = current_settings.get('user_agent', '') if current_settings else ''
    
    # Frame para los inputs (User Agent y Hora Programada)
    inputs_frame = ctk.CTkFrame(user_agent_frame, fg_color="transparent")
    inputs_frame.pack(fill="x", padx=20, pady=(15, 10))
    
    # === USER AGENT ===
    # Label para el User Agent
    user_agent_label = ctk.CTkLabel(
        inputs_frame,
        text="User Agent:",
        font=("Arial", 12, "bold"),
        text_color="black"
    )
    user_agent_label.pack(anchor="w")
    
    # Input para el User Agent
    user_agent_entry = ctk.CTkEntry(
        inputs_frame,
        placeholder_text="Ingresa tu User Agent aquí...",
        font=("Arial", 11),
        height=35
    )
    user_agent_entry.pack(fill="x", pady=(5, 15))
    
    # Insertar el valor actual si existe
    if current_user_agent:
        user_agent_entry.insert(0, current_user_agent)
    
    # === EMAIL DE NOTIFICACIÓN ===
    # Label para el Email de Notificación
    notification_email_label = ctk.CTkLabel(
        inputs_frame,
        text="📧 Email de Notificación:",
        font=("Arial", 12, "bold"),
        text_color="black"
    )
    notification_email_label.pack(anchor="w")
    
    # Input para el Email de Notificación
    notification_email_entry = ctk.CTkEntry(
        inputs_frame,
        placeholder_text="ejemplo@gmail.com",
        font=("Arial", 11),
        height=35
    )
    notification_email_entry.pack(fill="x", pady=(5, 15))
    
    # Insertar el valor actual si existe
    current_settings = get_creator_setting()
    if current_settings and current_settings.get('notification_email'):
        notification_email_entry.insert(0, current_settings['notification_email'])
    
    # ================= CONFIGURACIÓN DE TIEMPO =================
    
    def open_time_config_window():
        """Abre la ventana de configuración de tiempo"""
        create_time_config_window(new_window)
    
    # Botón para abrir configuración de tiempo
    time_config_button = ctk.CTkButton(
        inputs_frame,
        text="⏰ Configurar Tiempo",
        command=open_time_config_window,
        fg_color="#007bff",
        text_color="white",
        font=("Arial", 11),
        height=35,
        width=150
    )
    time_config_button.pack(side="left", padx=(0, 10), pady=(5, 15))
    
    
    # Función para guardar configuración completa
    def save_creator_settings():
        user_agent = user_agent_entry.get().strip()
        notification_email = notification_email_entry.get().strip()
        
        if not user_agent:
            messagebox.showwarning("Advertencia", "Por favor ingresa un User Agent válido.")
            return
        
        # Validar email de notificación si se proporciona
        if notification_email:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, notification_email):
                messagebox.showwarning("Advertencia", "Por favor ingresa un email válido para las notificaciones.")
                return
        
        # Obtener configuración actual para preservar configuración de tiempo
        current_settings = get_creator_setting()
        
        # Guardar configuración (preservar configuración de tiempo existente)
        if save_creator_setting(
            user_agent=user_agent, 
            accounts_to_create=1, 
            scheduled_time=current_settings.get('scheduled_time') if current_settings else None,
            timezone=current_settings.get('timezone') if current_settings else None,
            notification_email=notification_email if notification_email else None,
            cycle_time_minutes=current_settings.get('cycle_time_minutes') if current_settings else 60,
            time_config_type=current_settings.get('time_config_type') if current_settings else 'scheduled',
            accounts_per_cycle=current_settings.get('accounts_per_cycle') if current_settings else 1
        ):
            success_msg = f"✅ Configuración guardada correctamente.\n\nUser Agent: {user_agent}"
            if notification_email:
                success_msg += f"\nEmail de notificación: {notification_email}"
            success_msg += f"\n\n💡 Para configurar el tiempo de ejecución, usa el botón '⏰ Configurar Tiempo'"
            messagebox.showinfo("Éxito", success_msg)
        else:
            messagebox.showerror("Error", "❌ No se pudo guardar la configuración.")
    
    # Botón para guardar configuración
    save_settings_button = ctk.CTkButton(
        user_agent_frame,
        text="💾 Guardar Configuración",
        command=save_creator_settings,
        fg_color="#28a745",
        text_color="white",
        font=("Arial", 12, "bold"),
        height=35,
        width=250
    )
    save_settings_button.pack(pady=(0, 15), padx=20)
    
    # ================= SECCIÓN GESTIÓN DE EMAILS =================
    
    # Título de la sección de emails
    emails_title = ctk.CTkLabel(
        main_scroll_frame,
        text="📧 Gestión de Emails del Creator",
        font=("Arial", 16, "bold"),
        text_color="black"
    )
    emails_title.pack(pady=(0, 15))
    
    # Frame para la gestión de emails
    emails_frame = ctk.CTkFrame(main_scroll_frame, fg_color="white", corner_radius=5, border_width=2, border_color="black")
    emails_frame.pack(fill="x", padx=20, pady=(0, 20))
    
    # Obtener cantidad actual de emails
    current_email_count = get_creator_email_count()
    
    # Label con información de emails
    emails_info_label = ctk.CTkLabel(
        emails_frame,
        text=f"📊 Emails actuales en la base de datos: {current_email_count}",
        font=("Arial", 12, "bold"),
        text_color="black"
    )
    emails_info_label.pack(pady=(15, 10), padx=20, anchor="w")
    
    # Función para cargar emails desde archivo
    def load_emails_from_file_ui():
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo de emails",
            filetypes=[
                ("Archivos de texto", "*.txt"),
                ("Todos los archivos", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        # Mostrar mensaje de procesamiento
        messagebox.showinfo("Procesando", "📧 Procesando archivo de emails...")
        
        # Cargar emails usando la función de la base de datos
        result = load_emails_from_file(file_path)
        
        # Mostrar resultado
        if result['success']:
            message = f"""✅ Carga completada exitosamente!

            📊 Estadísticas:
            • Total de líneas: {result['total_lines']}
            • Emails válidos: {result['valid_emails']}
            • Emails guardados: {result['saved_emails']}
            • Emails duplicados: {result['duplicate_emails']}
            • Emails inválidos: {result['invalid_emails']}

            📧 Total de emails en la base de datos: {get_creator_email_count()}"""
            messagebox.showinfo("Éxito", message)
            
            # Actualizar el contador
            emails_info_label.configure(text=f"📊 Emails actuales en la base de datos: {get_creator_email_count()}")
        else:
            messagebox.showerror("Error", f"❌ {result['message']}")
    
    # Función para eliminar todos los emails
    def delete_all_emails():
        from app.database.database import delete_all_creator_emails, reset_creator_email_progress
        
        result = messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Estás seguro de que quieres eliminar TODOS los emails?\n\n📧 Emails actuales: {current_email_count}\n\nEsta acción no se puede deshacer."
        )
        
        if result:
            if delete_all_creator_emails():
                # Reiniciar el progreso de emails
                reset_creator_email_progress()
                messagebox.showinfo("Éxito", "✅ Todos los emails han sido eliminados y el progreso reiniciado.")
                # Actualizar el contador
                emails_info_label.configure(text=f"📊 Emails actuales en la base de datos: {get_creator_email_count()}")
            else:
                messagebox.showerror("Error", "❌ No se pudieron eliminar los emails.")
    
    # Frame para los botones
    buttons_frame = ctk.CTkFrame(emails_frame, fg_color="transparent")
    buttons_frame.pack(fill="x", padx=20, pady=(0, 15))
    
    # Botón para cargar emails
    load_emails_button = ctk.CTkButton(
        buttons_frame,
        text="📁 Cargar Emails desde Archivo",
        command=load_emails_from_file_ui,
        fg_color="#007ACC",
        text_color="white",
        font=("Arial", 12, "bold"),
        height=35,
        width=250
    )
    load_emails_button.pack(side="left", padx=(0, 10))
    
    # Botón para eliminar todos los emails
    delete_emails_button = ctk.CTkButton(
        buttons_frame,
        text="🗑️ Eliminar Todos los Emails",
        command=delete_all_emails,
        fg_color="#dc3545",
        text_color="white",
        font=("Arial", 12, "bold"),
        height=35,
        width=250
    )
    delete_emails_button.pack(side="left", padx=(10, 0))
    
    # Función para reiniciar progreso
    def reset_email_progress():
        from app.database.database import reset_creator_email_progress
        
        result = messagebox.askyesno(
            "Confirmar Reinicio",
            "¿Estás seguro de que quieres reiniciar el progreso de emails?\n\nEsto hará que el sistema vuelva a empezar desde el primer email en el siguiente ciclo."
        )
        
        if result:
            if reset_creator_email_progress():
                messagebox.showinfo("Éxito", "✅ Progreso de emails reiniciado correctamente.")
            else:
                messagebox.showerror("Error", "❌ No se pudo reiniciar el progreso.")
    
    # Botón para reiniciar progreso
    reset_progress_button = ctk.CTkButton(
        buttons_frame,
        text="🔄 Reiniciar Progreso",
        command=reset_email_progress,
        fg_color="#ffc107",
        text_color="black",
        font=("Arial", 12, "bold"),
        height=35,
        width=200
    )
    reset_progress_button.pack(side="left", padx=(10, 0))
    
    # Crear frame principal para la tabla de coordenadas
    main_frame = ctk.CTkFrame(main_scroll_frame, fg_color="transparent")
    main_frame.pack(fill="x", padx=20, pady=10)
    
    # Definir las coordenadas y sus nombres
    coordinates_list = [
        "Click del Brave",
        "Click del link de LinkedIn en fav",
        "Click input email",
        "Click botón Agree",
        "Click botón Agree opcional",
        "Click input de nombre",
        "Click botón continue",
        "Click cerrar captcha",
        "Click cerrar número",
        "Click icono cookie editor",
        "Click guardar cookie portapapeles",
        "Click cerrar ventana"
    ]
    
    # Mapeo de nombres a campos de la base de datos
    field_mapping = {
        "Click del Brave": "brave_click",
        "Click del link de LinkedIn en fav": "linkedin_fav_click",
        "Click input email": "email_input_click",
        "Click botón Agree": "continue_button_click",
        "Click botón Agree opcional": "continue_button_click_optional",
        "Click input de nombre": "name_input_click",
        "Click botón continue": "continue_button2_click",
        "Click cerrar captcha": "close_captcha_click",
        "Click cerrar número": "close_number_click",
        "Click icono cookie editor": "cookie_editor_icon_click",
        "Click guardar cookie portapapeles": "save_cookie_clipboard_click",
        "Click cerrar ventana": "close_window"
    }
    
    # Obtener coordenadas guardadas
    saved_coordinates = get_creator_coordinates()
    
    # Función para capturar coordenadas (igual que en ui.py)
    def capture_coordinate(coord_name, field_name, value_label_ref):
        # Crear popup para capturar coordenada
        popup = ctk.CTkToplevel(new_window)
        popup.geometry("420x220")
        popup.title("Captura de Coordenada")
        popup.configure(fg_color="#f0f0f0")
        popup.lift()
        popup.focus_force()
        popup.attributes("-topmost", True)

        label = ctk.CTkLabel(
            popup,
            text=f"Presiona la tecla 'c' para capturar la coordenada de:\n{coord_name}",
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
            coordenada_capturada = coord_raw
            
            # Verificar que el popup aún existe antes de actualizar
            try:
                if popup.winfo_exists():
                    coord_label.configure(text=f"{coord_name}: {coordenada_capturada}")
                    mostrar_botones_confirmacion(coordenada_capturada)
            except:
                pass  # El popup ya no existe, ignorar

        def mostrar_botones_confirmacion(coord):
            try:
                # Verificar que el popup aún existe
                if not popup.winfo_exists():
                    return
                
                # Limpiar widgets anteriores
                for widget in popup.winfo_children():
                    if isinstance(widget, ctk.CTkButton):
                        widget.destroy()
                
                def guardar():
                    if save_creator_coordinates(**{field_name: coord}):
                        messagebox.showinfo("Guardado", f"✅ Coordenada guardada: {coord}")
                        popup.destroy()
                        # Actualizar solo el label de valor sin refrescar toda la ventana
                        value_label_ref.configure(text=coord, text_color="black")
                    else:
                        messagebox.showerror("Error", "No se pudo guardar la coordenada.")

                def volver_a_capturar():
                    popup.destroy()
                    capture_coordinate(coord_name, field_name, value_label_ref)

                guardar_button = ctk.CTkButton(
                    popup,
                    text="Guardar",
                    command=guardar,
                    fg_color="#28a745",
                    text_color="white"
                )
                guardar_button.pack(pady=5)

                volver_button = ctk.CTkButton(
                    popup,
                    text="Volver a Capturar",
                    command=volver_a_capturar,
                    fg_color="#dc3545",
                    text_color="white"
                )
                volver_button.pack(pady=5)
            except:
                pass  # El popup ya no existe, ignorar

        threading.Thread(target=capturar, daemon=True).start()
    
    # Función para refrescar la ventana
    def refresh_window():
        new_window.destroy()
        create_new_window(parent_root)
    
    # Crear contenedor de la tabla de coordenadas con borde
    table_container = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=5, border_width=2, border_color="black")
    table_container.pack(fill="x", pady=(0, 20))
    
    # Crear encabezados de la tabla de coordenadas
    header_frame = ctk.CTkFrame(table_container, fg_color="#f0f0f0", corner_radius=0)
    header_frame.pack(fill="x")
    
    # Encabezados
    headers = ["Coordenada", "Valor", "Acción"]
    header_widths = [300, 200, 150]
    header_alignments = ["w", "w", "center"]  # Solo "Acción" centrado
    
    for i, (header, width, alignment) in enumerate(zip(headers, header_widths, header_alignments)):
        header_label = ctk.CTkLabel(
            header_frame,
            text=header,
            font=("Arial", 14, "bold"),
            text_color="black",
            width=width,
            anchor=alignment
        )
        sticky_value = "w" if alignment == "w" else "ew"
        header_label.grid(row=0, column=i, padx=5, pady=10, sticky=sticky_value)
    
    # Configurar columnas del header
    for i in range(3):
        header_frame.grid_columnconfigure(i, weight=1)
    
    # Crear filas de datos de coordenadas
    for i, coord_name in enumerate(coordinates_list):
        row_frame = ctk.CTkFrame(table_container, fg_color="white", corner_radius=0)
        row_frame.pack(fill="x")
        
        # Nombre de la coordenada
        name_label = ctk.CTkLabel(
            row_frame,
            text=coord_name,
            font=("Arial", 12),
            text_color="black",
            width=300,
            anchor="w"
        )
        name_label.grid(row=0, column=0, padx=5, pady=8, sticky="w")
        
        # Valor de la coordenada
        field_name = field_mapping[coord_name]
        coord_value = saved_coordinates.get(field_name, "") if saved_coordinates else ""
        
        value_label = ctk.CTkLabel(
            row_frame,
            text=coord_value if coord_value else "No configurado",
            font=("Arial", 11),
            text_color="gray" if not coord_value else "black",
            width=200,
            anchor="w"
        )
        value_label.grid(row=0, column=1, padx=5, pady=8, sticky="w")
        
        # Botón de acción
        def create_capture_function(coord_name, field_name, value_label_ref):
            def capture_coordinates():
                capture_coordinate(coord_name, field_name, value_label_ref)
            return capture_coordinates
        
        action_button = ctk.CTkButton(
            row_frame,
            text="Configurar",
            command=create_capture_function(coord_name, field_name, value_label),
            fg_color="#007ACC",
            text_color="white",
            font=("Arial", 11),
            width=120,
            height=30
        )
        action_button.grid(row=0, column=2, padx=5, pady=8)
        
        # Configurar columnas de la fila
        for j in range(3):
            row_frame.grid_columnconfigure(j, weight=1)
    
    # ================= TABLA DE IMÁGENES =================
    
    # Título de la tabla de imágenes
    images_title = ctk.CTkLabel(
        main_scroll_frame,
        text="🖼️ Configuración de Imágenes del Creator",
        font=("Arial", 16, "bold"),
        text_color="black"
    )
    images_title.pack(pady=(30, 15))
    
    # Crear contenedor de la tabla de imágenes con borde
    images_table_container = ctk.CTkFrame(main_scroll_frame, fg_color="white", corner_radius=5, border_width=2, border_color="black")
    images_table_container.pack(fill="x", padx=20, pady=10)
    
    # Crear frame para la tabla de imágenes
    images_frame = ctk.CTkFrame(images_table_container, fg_color="transparent")
    images_frame.pack(fill="x")
    
    # Definir las imágenes
    images_list = [
        "Imagen de verificación de éxito carga LinkedIn",
        "Checkbox recuerdame",
        "Imagen captcha rojo",
        "Imagen número",
        "Imagen de creación de cuenta con éxito (logo LinkedIn)",
        "Imagen de creación de cuenta con éxito (logo LinkedIn) 2",
        "Imagen de confirmación de código",
        "add_location",
    ]
    
    # Crear encabezados de la tabla de imágenes
    images_header_frame = ctk.CTkFrame(images_frame, fg_color="#f0f0f0", corner_radius=0)
    images_header_frame.pack(fill="x")
    
    # Encabezados de imágenes
    images_headers = ["Imagen", "Vista Previa", "Acción"]
    images_header_widths = [400, 150, 150]
    images_header_alignments = ["w", "center", "center"]  # Solo "Vista Previa" y "Acción" centrados
    
    for i, (header, width, alignment) in enumerate(zip(images_headers, images_header_widths, images_header_alignments)):
        header_label = ctk.CTkLabel(
            images_header_frame,
            text=header,
            font=("Arial", 14, "bold"),
            text_color="black",
            width=width,
            anchor=alignment
        )
        sticky_value = "w" if alignment == "w" else "ew"
        header_label.grid(row=0, column=i, padx=5, pady=10, sticky=sticky_value)
    
    # Configurar columnas del header de imágenes
    for i in range(3):
        images_header_frame.grid_columnconfigure(i, weight=1)
    
    # Crear filas de datos de imágenes
    for i, image_name in enumerate(images_list):
        row_frame = ctk.CTkFrame(images_frame, fg_color="white", corner_radius=0)
        row_frame.pack(fill="x")
        
        # Nombre de la imagen
        name_label = ctk.CTkLabel(
            row_frame,
            text=image_name,
            font=("Arial", 12),
            text_color="black",
            width=400,
            anchor="w"
        )
        name_label.grid(row=0, column=0, padx=5, pady=8, sticky="w")
        
        # Verificar si existe la imagen
        image_path = get_image_path(image_name)
        has_image = image_path is not None
        
        # Crear botón para ver imagen
        view_button = ctk.CTkButton(
            row_frame,
            text="Ver Imagen",
            fg_color="#17a2b8" if has_image else "#6c757d",
            text_color="white",
            font=("Arial", 11),
            width=120,
            height=30,
            state="normal" if has_image else "disabled"
        )
        view_button.grid(row=0, column=1, padx=5, pady=8)
        
        # Función para ver imagen con referencia correcta al botón
        def create_view_function(img_name, button_ref):
            def view_image_func():
                image_path = get_image_path(img_name)
                if image_path:
                    # Callback para actualizar el botón cuando se elimine la imagen
                    def update_button_after_delete():
                        button_ref.configure(
                            fg_color="#6c757d",
                            state="disabled"
                        )
                    view_image(image_path, update_button_after_delete)
                else:
                    messagebox.showwarning("Imagen no encontrada", f"No se encontró la imagen: {img_name}\n\nPrimero carga la imagen usando el botón 'Cargar Imagen'.")
            return view_image_func
        
        # Función para cargar imagen con referencia correcta al botón
        def create_load_function(img_name, button_ref):
            def load_image_func():
                result = load_image(img_name)
                if result:
                    # Actualizar solo el botón "Ver Imagen" sin refrescar toda la ventana
                    button_ref.configure(
                        fg_color="#17a2b8",
                        state="normal"
                    )
            return load_image_func
        
        # Asignar comandos a los botones con las referencias correctas
        view_button.configure(command=create_view_function(image_name, view_button))
        
        load_button = ctk.CTkButton(
            row_frame,
            text="Cargar Imagen",
            command=create_load_function(image_name, view_button),
            fg_color="#007ACC",
            text_color="white",
            font=("Arial", 11),
            width=120,
            height=30
        )
        load_button.grid(row=0, column=2, padx=5, pady=8)
        
        # Configurar columnas de la fila de imágenes
        for j in range(3):
            row_frame.grid_columnconfigure(j, weight=1)
    
    return new_window


def create_time_config_window(parent_root):
    """
    Crea una nueva ventana para configurar el tiempo (hora programada o ciclo)
    """
    import customtkinter as ctk
    from tkinter import messagebox
    import datetime
    import pytz
    from app.database.database import get_creator_setting, save_creator_setting, clear_scheduled_time
    
    # Crear la nueva ventana
    time_window = ctk.CTkToplevel(parent_root)
    time_window.title("Configuración de Tiempo")
    time_window.geometry("600x500")
    time_window.configure(fg_color="#FFFFFF")
    
    # Centrar la ventana y hacerla modal
    time_window.transient(parent_root)
    time_window.grab_set()
    
    # Crear frame principal con scroll
    main_scroll_frame = ctk.CTkScrollableFrame(time_window, fg_color="transparent")
    main_scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Crear frame principal dentro del scroll
    main_frame = ctk.CTkFrame(main_scroll_frame, fg_color="transparent")
    main_frame.pack(fill="both", expand=True)
    
    # Título de la ventana
    title_label = ctk.CTkLabel(
        main_frame,
        text="⏰ Configuración de Tiempo",
        font=("Arial", 18, "bold"),
        text_color="black"
    )
    title_label.pack(pady=(0, 30))
    
    # Obtener configuración actual
    current_settings = get_creator_setting()
    if not current_settings:
        current_settings = {
            'time_config_type': 'scheduled',
            'scheduled_time': '',
            'timezone': 'Argentina (GMT-3)',
            'cycle_time_minutes': 60,
            'accounts_per_cycle': 1
        }
    
    # Debug: mostrar configuración cargada
    print(f"🔍 Configuración cargada en ventana de tiempo:")
    print(f"   - Tipo: {current_settings.get('time_config_type')}")
    print(f"   - Hora programada: {current_settings.get('scheduled_time')}")
    print(f"   - Zona horaria: {current_settings.get('timezone')}")
    print(f"   - Ciclo minutos: {current_settings.get('cycle_time_minutes')}")
    print(f"   - Cuentas por ciclo: {current_settings.get('accounts_per_cycle')}")
    
    # ================= SELECCIÓN DE TIPO DE CONFIGURACIÓN =================
    
    config_type_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=5, border_width=2, border_color="black")
    config_type_frame.pack(fill="x", pady=(0, 20))
    
    config_type_label = ctk.CTkLabel(
        config_type_frame,
        text="📋 Tipo de Configuración",
        font=("Arial", 14, "bold"),
        text_color="black"
    )
    config_type_label.pack(pady=(15, 10))
    
    # Radio buttons para seleccionar tipo
    config_type_var = ctk.StringVar(value=current_settings.get('time_config_type', 'scheduled'))
    
    scheduled_radio = ctk.CTkRadioButton(
        config_type_frame,
        text="🕐 Hora Programada (ejecutar a una hora específica)",
        variable=config_type_var,
        value="scheduled",
        font=("Arial", 12),
        text_color="black"
    )
    scheduled_radio.pack(pady=5, padx=20, anchor="w")
    
    cycle_radio = ctk.CTkRadioButton(
        config_type_frame,
        text="🔄 Ciclo de Tiempo (ejecutar cada X minutos)",
        variable=config_type_var,
        value="cycle",
        font=("Arial", 12),
        text_color="black"
    )
    cycle_radio.pack(pady=5, padx=20, anchor="w")
    
    # ================= CONFIGURACIÓN DE HORA PROGRAMADA =================
    
    scheduled_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=5, border_width=2, border_color="black")
    scheduled_frame.pack(fill="x", pady=(0, 20))
    
    scheduled_label = ctk.CTkLabel(
        scheduled_frame,
        text="🕐 Hora Programada",
        font=("Arial", 14, "bold"),
        text_color="black"
    )
    scheduled_label.pack(pady=(15, 10))
    
    # Frame para inputs de hora programada
    scheduled_inputs_frame = ctk.CTkFrame(scheduled_frame, fg_color="transparent")
    scheduled_inputs_frame.pack(pady=(0, 15))
    
    # Lista de países con sus zonas horarias
    countries = [
        "Argentina (GMT-3)",
        "Brasil (GMT-3)",
        "Chile (GMT-3)",
        "Uruguay (GMT-3)",
        "Paraguay (GMT-3)",
        "Estados Unidos - Este (GMT-5)",
        "Estados Unidos - Central (GMT-6)",
        "Estados Unidos - Montaña (GMT-7)",
        "Estados Unidos - Pacífico (GMT-8)",
        "México (GMT-6)",
        "Colombia (GMT-5)",
        "Perú (GMT-5)",
        "Venezuela (GMT-4)",
        "Ecuador (GMT-5)",
        "Bolivia (GMT-4)",
        "España (GMT+1)",
        "Francia (GMT+1)",
        "Alemania (GMT+1)",
        "Italia (GMT+1)",
        "Reino Unido (GMT+0)",
        "Portugal (GMT+0)",
        "Rusia - Moscú (GMT+3)",
        "China (GMT+8)",
        "Japón (GMT+9)",
        "India (GMT+5:30)",
        "Australia - Sydney (GMT+10)",
        "Nueva Zelanda (GMT+12)",
        "Canadá - Este (GMT-5)",
        "Canadá - Central (GMT-6)",
        "Canadá - Montaña (GMT-7)",
        "Canadá - Pacífico (GMT-8)"
    ]
    
    # Detectar país automáticamente
    def get_user_country():
        """Detecta automáticamente el país del usuario basado en la zona horaria"""
        try:
            local_tz = datetime.datetime.now().astimezone().tzinfo
            
            if hasattr(local_tz, 'zone'):
                zone_name = local_tz.zone
                try:
                    tz = pytz.timezone(zone_name)
                    utc_offset = tz.utcoffset(datetime.datetime.now())
                    offset_hours = int(utc_offset.total_seconds() / 3600)
                    
                    if offset_hours == -3:
                        if 'Argentina' in zone_name or 'Buenos_Aires' in zone_name:
                            return "Argentina (GMT-3)"
                        else:
                            return "Brasil (GMT-3)"
                    elif offset_hours == -5:
                        return "Estados Unidos - Este (GMT-5)"
                    elif offset_hours == -6:
                        return "Estados Unidos - Central (GMT-6)"
                    elif offset_hours == -7:
                        return "Estados Unidos - Montaña (GMT-7)"
                    elif offset_hours == -8:
                        return "Estados Unidos - Pacífico (GMT-8)"
                    elif offset_hours == 0:
                        return "Reino Unido (GMT+0)"
                    elif offset_hours == 1:
                        return "España (GMT+1)"
                    elif offset_hours == 3:
                        return "Rusia - Moscú (GMT+3)"
                    elif offset_hours == 8:
                        return "China (GMT+8)"
                    elif offset_hours == 9:
                        return "Japón (GMT+9)"
                    else:
                        for country in countries:
                            if f"GMT{offset_hours:+d}" in country:
                                return country
                        return "Argentina (GMT-3)"
                    
                except:
                    return "Argentina (GMT-3)"
            else:
                return "Argentina (GMT-3)"
                
        except Exception as e:
            print(f"Error detectando país: {e}")
            return "Argentina (GMT-3)"
    
    # Input para hora
    time_entry = ctk.CTkEntry(
        scheduled_inputs_frame,
        placeholder_text="HH:MM",
        font=("Arial", 11),
        height=35,
        width=80
    )
    time_entry.pack(side="left", padx=(0, 10), pady=(5, 15))
    
    # Función para validar formato de hora
    def validate_time_format(event=None):
        """Valida que el formato de hora sea correcto (HH:MM)"""
        value = time_entry.get()
        if value:
            if not all(c.isdigit() or c == ':' for c in value):
                time_entry.delete(len(value)-1, 'end')
                return
            
            if len(value) > 5:
                time_entry.delete(5, 'end')
                return
            
            if len(value) == 2 and ':' not in value:
                time_entry.insert(2, ':')
    
    time_entry.bind('<KeyRelease>', validate_time_format)
    
    # Selector de país
    country_dropdown = ctk.CTkComboBox(
        scheduled_inputs_frame,
        values=countries,
        font=("Arial", 11),
        height=35,
        width=200
    )
    country_dropdown.pack(side="left", padx=(0, 10), pady=(5, 15))
    
    # Detectar y establecer país automáticamente
    detected_country = get_user_country()
    country_dropdown.set(detected_country)
    
    # Insertar valores actuales si existen
    if current_settings.get('scheduled_time'):
        time_entry.insert(0, current_settings.get('scheduled_time'))
    if current_settings.get('timezone'):
        country_dropdown.set(current_settings.get('timezone'))
    
    # ================= CONFIGURACIÓN DE CICLO DE TIEMPO =================
    
    cycle_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=5, border_width=2, border_color="black")
    cycle_frame.pack(fill="x", pady=(0, 20))
    
    cycle_label = ctk.CTkLabel(
        cycle_frame,
        text="🔄 Ciclo de Tiempo",
        font=("Arial", 14, "bold"),
        text_color="black"
    )
    cycle_label.pack(pady=(15, 10))
    
    # Explicación del comportamiento del ciclo
    cycle_explanation = ctk.CTkLabel(
        cycle_frame,
        text="💡 El bot procesará emails secuencialmente sin reiniciar.\nCada ciclo procesará exactamente la cantidad configurada.",
        font=("Arial", 10),
        text_color="gray"
    )
    cycle_explanation.pack(pady=(0, 10), padx=20, anchor="w")
    
    # Frame para inputs de ciclo
    cycle_inputs_frame = ctk.CTkFrame(cycle_frame, fg_color="transparent")
    cycle_inputs_frame.pack(pady=(0, 15))
    
    # Input para minutos del ciclo
    cycle_minutes_entry = ctk.CTkEntry(
        cycle_inputs_frame,
        placeholder_text="Minutos",
        font=("Arial", 11),
        height=35,
        width=100
    )
    cycle_minutes_entry.pack(side="left", padx=(0, 10), pady=(5, 15))
    
    # Insertar valor actual si existe
    if current_settings.get('cycle_time_minutes'):
        cycle_minutes_entry.insert(0, str(current_settings.get('cycle_time_minutes')))
    
    # Label explicativo para minutos
    cycle_explanation = ctk.CTkLabel(
        cycle_inputs_frame,
        text="minutos entre cada ejecución",
        font=("Arial", 11),
        text_color="black"
    )
    cycle_explanation.pack(side="left", padx=(0, 10), pady=(5, 15))
    
    # Input para cuentas por ciclo
    accounts_per_cycle_entry = ctk.CTkEntry(
        cycle_inputs_frame,
        placeholder_text="Cuentas",
        font=("Arial", 11),
        height=35,
        width=80
    )
    accounts_per_cycle_entry.pack(side="left", padx=(0, 10), pady=(5, 15))
    
    # Insertar valor actual si existe
    if current_settings.get('accounts_per_cycle'):
        accounts_per_cycle_entry.insert(0, str(current_settings.get('accounts_per_cycle')))
    
    # Label explicativo para cuentas
    accounts_explanation = ctk.CTkLabel(
        cycle_inputs_frame,
        text="cuentas por ciclo",
        font=("Arial", 11),
        text_color="black"
    )
    accounts_explanation.pack(side="left", padx=(0, 10), pady=(5, 15))
    
    # ================= BOTONES DE ACCIÓN =================
    
    buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    buttons_frame.pack(fill="x", pady=(20, 0))
    
    # Función para guardar configuración
    def save_time_config():
        config_type = config_type_var.get()
        scheduled_time = time_entry.get().strip()
        timezone = country_dropdown.get().strip()
        cycle_minutes = cycle_minutes_entry.get().strip()
        accounts_per_cycle = accounts_per_cycle_entry.get().strip()
        
        # Validaciones
        if config_type == 'scheduled' and scheduled_time:
            # Validar formato de hora
            try:
                datetime.datetime.strptime(scheduled_time, '%H:%M')
            except ValueError:
                messagebox.showerror("Error", "❌ Formato de hora inválido. Use HH:MM")
                return
        
        if config_type == 'cycle':
            if not cycle_minutes:
                messagebox.showerror("Error", "❌ Debe ingresar el tiempo del ciclo en minutos")
                return
            try:
                minutes = int(cycle_minutes)
                if minutes < 1 or minutes > 1440:  # Entre 1 minuto y 24 horas
                    messagebox.showerror("Error", "❌ El tiempo del ciclo debe estar entre 1 y 1440 minutos")
                    return
            except ValueError:
                messagebox.showerror("Error", "❌ Ingrese un número válido de minutos")
                return
            
            # Validar cuentas por ciclo
            if not accounts_per_cycle:
                messagebox.showerror("Error", "❌ Debe ingresar la cantidad de cuentas por ciclo")
                return
            try:
                accounts = int(accounts_per_cycle)
                if accounts < 1 or accounts > 100:  # Entre 1 y 100 cuentas
                    messagebox.showerror("Error", "❌ La cantidad de cuentas por ciclo debe estar entre 1 y 100")
                    return
            except ValueError:
                messagebox.showerror("Error", "❌ Ingrese un número válido de cuentas")
                return
        
        # Guardar configuración (preservar ambos tipos de configuración)
        success = save_creator_setting(
            user_agent=current_settings.get('user_agent', ''),
            accounts_to_create=current_settings.get('accounts_to_create', 1),
            scheduled_time=scheduled_time if config_type == 'scheduled' else current_settings.get('scheduled_time'),
            timezone=timezone if config_type == 'scheduled' else current_settings.get('timezone'),
            notification_email=current_settings.get('notification_email', ''),
            cycle_time_minutes=int(cycle_minutes) if config_type == 'cycle' and cycle_minutes else current_settings.get('cycle_time_minutes', 60),
            time_config_type=config_type,
            accounts_per_cycle=int(accounts_per_cycle) if config_type == 'cycle' and accounts_per_cycle else current_settings.get('accounts_per_cycle', 1)
        )
        
        if success:
            messagebox.showinfo("Éxito", f"✅ Configuración de tiempo guardada correctamente\n\nTipo: {'Hora Programada' if config_type == 'scheduled' else 'Ciclo de Tiempo'}")
            time_window.destroy()
        else:
            messagebox.showerror("Error", "❌ No se pudo guardar la configuración")
    
    # Función para limpiar configuración
    def clear_time_config():
        # Limpiar solo los campos del tipo de configuración actual
        config_type = config_type_var.get()
        
        if config_type == 'scheduled':
            # Limpiar solo configuración de hora programada
            time_entry.delete(0, 'end')
            country_dropdown.set(detected_country)
            # Guardar configuración con hora programada vacía
            success = save_creator_setting(
                user_agent=current_settings.get('user_agent', ''),
                accounts_to_create=current_settings.get('accounts_to_create', 1),
                scheduled_time=None,
                timezone=None,
                notification_email=current_settings.get('notification_email', ''),
                cycle_time_minutes=current_settings.get('cycle_time_minutes', 60),
                time_config_type='scheduled',
                accounts_per_cycle=current_settings.get('accounts_per_cycle', 1)
            )
        else:
            # Limpiar solo configuración de ciclo
            cycle_minutes_entry.delete(0, 'end')
            accounts_per_cycle_entry.delete(0, 'end')
            # Guardar configuración con ciclo vacío
            success = save_creator_setting(
                user_agent=current_settings.get('user_agent', ''),
                accounts_to_create=current_settings.get('accounts_to_create', 1),
                scheduled_time=current_settings.get('scheduled_time'),
                timezone=current_settings.get('timezone'),
                notification_email=current_settings.get('notification_email', ''),
                cycle_time_minutes=60,
                time_config_type='cycle',
                accounts_per_cycle=1
            )
        
        if success:
            messagebox.showinfo("Éxito", f"✅ Configuración de {'hora programada' if config_type == 'scheduled' else 'ciclo'} eliminada correctamente")
        else:
            messagebox.showerror("Error", "❌ No se pudo eliminar la configuración")
    
    # Botón Guardar
    save_button = ctk.CTkButton(
        buttons_frame,
        text="💾 Guardar",
        command=save_time_config,
        fg_color="#28a745",
        text_color="white",
        font=("Arial", 12, "bold"),
        height=40,
        width=120
    )
    save_button.pack(side="left", padx=(0, 10))
    
    # Botón Limpiar
    clear_button = ctk.CTkButton(
        buttons_frame,
        text="🗑️ Limpiar",
        command=clear_time_config,
        fg_color="#dc3545",
        text_color="white",
        font=("Arial", 12, "bold"),
        height=40,
        width=120
    )
    clear_button.pack(side="left", padx=(0, 10))
    
    # Botón Cancelar
    cancel_button = ctk.CTkButton(
        buttons_frame,
        text="❌ Cancelar",
        command=time_window.destroy,
        fg_color="#6c757d",
        text_color="white",
        font=("Arial", 12, "bold"),
        height=40,
        width=120
    )
    cancel_button.pack(side="right")
