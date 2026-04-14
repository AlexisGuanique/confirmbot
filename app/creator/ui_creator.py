def create_new_window(parent_root, browser_id=None):
    """
    Crea una nueva ventana con tabla de coordenadas del creator para un navegador específico
    
    Args:
        parent_root: Ventana padre
        browser_id (int, optional): ID del navegador. Si es None, usa el navegador por defecto o crea uno nuevo.
    """
    import customtkinter as ctk
    from tkinter import messagebox
    import threading
    import datetime
    import pytz
    from app.database.database import (
        get_creator_coordinates, save_creator_coordinates, save_creator_setting, 
        get_creator_setting, load_emails_from_file, get_creator_email_count, 
        clear_scheduled_time, get_user_data, get_default_browser, get_browser_by_id,
        create_browser
    )
    from app.confirmabot.utils.mouse_click_coordenates import get_mouse_coordinate_on_keypress
    from app.creator.image_config import view_image, load_image, get_image_path
    from app.creator.computer_actions import find_creator_image, wait_for_spinner
    from app.utils.http_utils import post
    from tkinter import filedialog
    
    # Función para dibujar un borde rojo alrededor de la imagen encontrada
    def draw_red_border_around_image(box, duration=3000):
        """
        Dibuja un borde rojo alrededor de una imagen encontrada en la pantalla.
        
        Args:
            box: Objeto Box de pyautogui con (left, top, width, height)
            duration: Duración en milisegundos que se mostrará el borde (default: 3000ms)
        """
        try:
            import tkinter as tk
            
            # Obtener la ventana raíz de tkinter (necesario para Toplevel)
            root = tk._default_root
            if root is None:
                # Si no hay raíz, crear una temporal
                root = tk.Tk()
                root.withdraw()  # Ocultar la ventana raíz
            
            # Crear ventana transparente
            overlay = tk.Toplevel(root)
            overlay.overrideredirect(True)  # Sin barra de título
            overlay.attributes('-topmost', True)  # Siempre al frente
            
            # Configurar posición y tamaño
            border_width = 4  # Grosor del borde en píxeles
            x = box.left - border_width
            y = box.top - border_width
            width = box.width + (border_width * 2)
            height = box.height + (border_width * 2)
            
            overlay.geometry(f"{width}x{height}+{x}+{y}")
            
            # Intentar hacer la ventana transparente (puede no funcionar en todos los sistemas)
            try:
                # En Windows, usar colorkey para transparencia
                overlay.attributes('-transparentcolor', 'black')
                overlay.configure(bg='black')
            except:
                try:
                    # Intentar con alpha
                    overlay.attributes('-alpha', 0.0)
                    overlay.configure(bg='black')
                except:
                    overlay.configure(bg='black')
            
            # Crear canvas para dibujar el borde
            canvas = tk.Canvas(
                overlay,
                width=width,
                height=height,
                highlightthickness=0,
                bg='black'
            )
            canvas.pack(fill=tk.BOTH, expand=True)
            
            # Dibujar rectángulo rojo (borde) - dibujar 4 líneas para crear un borde visible
            # Línea superior
            canvas.create_line(
                border_width, border_width,
                width - border_width, border_width,
                fill='red', width=border_width
            )
            # Línea inferior
            canvas.create_line(
                border_width, height - border_width,
                width - border_width, height - border_width,
                fill='red', width=border_width
            )
            # Línea izquierda
            canvas.create_line(
                border_width, border_width,
                border_width, height - border_width,
                fill='red', width=border_width
            )
            # Línea derecha
            canvas.create_line(
                width - border_width, border_width,
                width - border_width, height - border_width,
                fill='red', width=border_width
            )
            
            # Actualizar la ventana para asegurar que se muestre
            overlay.update()
            
            # Cerrar la ventana después de la duración especificada
            def close_overlay():
                try:
                    overlay.destroy()
                except:
                    pass
            
            overlay.after(duration, close_overlay)
            
            # Cerrar al hacer clic
            def on_click(event):
                close_overlay()
            
            canvas.bind('<Button-1>', on_click)
            overlay.bind('<Button-1>', on_click)
            
            # Actualizar periódicamente para mantener la ventana visible
            def keep_alive():
                try:
                    overlay.update()
                    if overlay.winfo_exists():
                        overlay.after(100, keep_alive)
                except:
                    pass
            
            keep_alive()
            
        except Exception as e:
            print(f"Error al dibujar borde: {e}")
    
    # Función para obtener el conteo de emails globales del servidor
    def get_global_email_count():
        try:
            from app.utils.server_config import build_api_url
            user_data = get_user_data()
            if not user_data:
                return None
                
            url = build_api_url(f"/api/emails/count/{user_data['id']}")
            headers = {"Content-Type": "application/json"}
            body = {"access_token": user_data['access_token']}
            
            response = post(url, body=body, headers=headers)
            if response and response.status_code == 200:
                data = response.json()
                return data  # Devolver toda la información del servidor
            return None
        except Exception as e:
            print(f"❌ Error al obtener conteo global: {e}")
            return None
    
    # Obtener o crear navegador
    if browser_id is None:
        default_browser = get_default_browser()
        if default_browser:
            browser_id = default_browser['id']
        else:
            # Crear navegador por defecto si no existe ninguno
            browser_id = create_browser("Navegador Principal", True)
            if not browser_id:
                messagebox.showerror("Error", "❌ No se pudo crear un navegador por defecto.")
                return None
    
    # Verificar que el navegador existe
    browser = get_browser_by_id(browser_id)
    if not browser:
        messagebox.showerror("Error", f"❌ El navegador con ID {browser_id} no existe.")
        return None
    
    # Obtener nombre del navegador para las imágenes
    browser_name = browser['name']
    
    # Crear la nueva ventana
    new_window = ctk.CTkToplevel(parent_root)
    new_window.title(f"Configuración del Creator - {browser_name}")
    new_window.geometry("650x600")
    new_window.configure(fg_color="#FFFFFF")
    
    # Centrar la ventana y hacerla modal
    new_window.transient(parent_root)
    new_window.grab_set()
    
    # Crear frame principal con scroll
    main_scroll_frame = ctk.CTkScrollableFrame(new_window, fg_color="transparent")
    main_scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Título de la ventana con nombre del navegador
    title_label = ctk.CTkLabel(
        main_scroll_frame,
        text=f"⚙️ Configuración del Creator - {browser['name']}",
        font=("Arial", 18, "bold"),
        text_color="black"
    )
    title_label.pack(pady=(20, 30))
    
    # ================= SECCIÓN CONFIG LOCAL DEL CREATOR =================
    
    # Título de la sección local (sin User-Agent)
    user_agent_title = ctk.CTkLabel(
        main_scroll_frame,
        text="⚙️ Configuración local del Creator",
        font=("Arial", 16, "bold"),
        text_color="black"
    )
    user_agent_title.pack(pady=(0, 15))
    
    # Frame para configuración local
    user_agent_frame = ctk.CTkFrame(main_scroll_frame, fg_color="white", corner_radius=5, border_width=2, border_color="black")
    user_agent_frame.pack(fill="x", padx=20, pady=(0, 20))
    
    # Obtener configuración actual para este navegador
    current_settings = get_creator_setting(browser_id)
    
    # Frame para los inputs locales
    inputs_frame = ctk.CTkFrame(user_agent_frame, fg_color="transparent")
    inputs_frame.pack(fill="x", padx=20, pady=(15, 10))

    user_agent_info = ctk.CTkLabel(
        inputs_frame,
        text="El User-Agent ahora se configura desde el servidor (Config Bots) por navegador.",
        font=("Arial", 11),
        text_color="gray",
        wraplength=540,
        justify="left",
    )
    user_agent_info.pack(anchor="w", pady=(0, 10))
    
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
    
    # Insertar el valor actual si existe (ya obtenido arriba)
    if current_settings and current_settings.get('notification_email'):
        notification_email_entry.insert(0, current_settings['notification_email'])
    
    # === CHECKBOXES DE TIPO DE MÁQUINA ===
    # Frame para los checkboxes
    machine_type_frame = ctk.CTkFrame(inputs_frame, fg_color="transparent")
    machine_type_frame.pack(fill="x", pady=(5, 15))
    
    # Label para la sección
    machine_type_label = ctk.CTkLabel(
        machine_type_frame,
        text="🖥️ Tipo de Máquina:",
        font=("Arial", 12, "bold"),
        text_color="black"
    )
    machine_type_label.pack(anchor="w", pady=(0, 10))
    
    # Frame para los checkboxes lado a lado
    checkboxes_container = ctk.CTkFrame(machine_type_frame, fg_color="transparent")
    checkboxes_container.pack(fill="x")
    
    # Variables para los checkboxes (mutuamente exclusivos)
    vps_var = ctk.IntVar(value=0)
    fisica_var = ctk.IntVar(value=0)
    
    # Obtener valor actual de isInVps
    current_isInVps = current_settings.get('isInVps') if current_settings else None
    if current_isInVps is True:
        vps_var.set(1)
    elif current_isInVps is False:
        fisica_var.set(1)
    
    # Función para manejar la exclusividad de los checkboxes
    def on_vps_checkbox_change():
        """Hace que los checkboxes sean mutuamente exclusivos - VPS"""
        if vps_var.get() == 1:
            # Si se selecciona VPS, deseleccionar Máquina Física
            fisica_var.set(0)
    
    def on_fisica_checkbox_change():
        """Hace que los checkboxes sean mutuamente exclusivos - Máquina Física"""
        if fisica_var.get() == 1:
            # Si se selecciona Máquina Física, deseleccionar VPS
            vps_var.set(0)
    
    # Checkbox "Es en VPS"
    vps_checkbox = ctk.CTkCheckBox(
        checkboxes_container,
        text="Es en VPS",
        font=("Arial", 11),
        text_color="black",
        variable=vps_var,
        command=on_vps_checkbox_change
    )
    vps_checkbox.pack(side="left", padx=(0, 20))
    
    # Checkbox "Es en Máquina Física"
    fisica_checkbox = ctk.CTkCheckBox(
        checkboxes_container,
        text="Es en Máquina Física",
        font=("Arial", 11),
        text_color="black",
        variable=fisica_var,
        command=on_fisica_checkbox_change
    )
    fisica_checkbox.pack(side="left")
    
    # Función para guardar configuración completa
    def save_creator_settings():
        notification_email = notification_email_entry.get().strip()
        
        # Obtener valor de tipo de máquina
        isInVps = None
        if vps_var.get() == 1:
            isInVps = True
        elif fisica_var.get() == 1:
            isInVps = False
        
        # Validar email de notificación si se proporciona
        if notification_email:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, notification_email):
                messagebox.showwarning("Advertencia", "Por favor ingresa un email válido para las notificaciones.")
                return
        
        # Obtener configuración actual para preservar configuración de tiempo (ya obtenida arriba)
        
        # Guardar configuración (preservar configuración de tiempo existente)
        # NOTA: is33mail y domain ahora se configuran globalmente en "Gestión de Navegadores"
        user_agent_to_keep = current_settings.get('user_agent', '') if current_settings else ''
        if save_creator_setting(
            browser_id=browser_id,
            user_agent=user_agent_to_keep,
            accounts_to_create=1, 
            scheduled_time=current_settings.get('scheduled_time') if current_settings else None,
            timezone=current_settings.get('timezone') if current_settings else None,
            notification_email=notification_email if notification_email else None,
            cycle_time_minutes=current_settings.get('cycle_time_minutes') if current_settings else None,
            time_config_type=current_settings.get('time_config_type') if current_settings else None,
            accounts_per_cycle=current_settings.get('accounts_per_cycle') if current_settings else None,
            isInVps=isInVps
        ):
            success_msg = "✅ Configuración guardada correctamente."
            if notification_email:
                success_msg += f"\nEmail de notificación: {notification_email}"
            if isInVps is not None:
                machine_type_text = "VPS" if isInVps else "Máquina Física"
                success_msg += f"\nTipo de Máquina: {machine_type_text}"
            success_msg += "\n\n💡 Para configurar User-Agent por navegador, usa 'Config Bots' en el servidor."
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
    
    # Obtener cantidad actual de emails locales
    current_email_count = get_creator_email_count()
    
    # Obtener información detallada de emails globales del servidor
    global_email_data = get_global_email_count()
    
    # Label con información de emails locales
    emails_info_label = ctk.CTkLabel(
        emails_frame,
        text=f"📊 Emails locales en la base de datos: {current_email_count}",
        font=("Arial", 12, "bold"),
        text_color="black"
    )
    emails_info_label.pack(pady=(15, 5), padx=20, anchor="w")
    
    # Información detallada de emails del servidor
    if global_email_data:
        breakdown = global_email_data.get('breakdown', {})
        disponibles = breakdown.get('disponibles', 0)
        usados_una_vez = breakdown.get('usados_una_vez', 0)
        usados_dos_veces = breakdown.get('usados_dos_veces', 0)
        completados = breakdown.get('completados', 0)
        
        # Total de emails que puedes usar (disponibles + usados 1 vez + usados 2 veces)
        total_utilizables = disponibles + usados_una_vez + usados_dos_veces
        
        # Label principal con total de emails utilizables
        total_utilizables_label = ctk.CTkLabel(
            emails_frame,
            text=f"📊 Total de emails utilizables: {total_utilizables}",
            font=("Arial", 12, "bold"),
            text_color="black"
        )
        total_utilizables_label.pack(pady=(5, 5), padx=20, anchor="w")
        
        # Desglose detallado
        breakdown_text = f"📋 Desglose: {disponibles} disponibles | {usados_una_vez} usados 1 vez | {usados_dos_veces} usados 2 veces"
        breakdown_label = ctk.CTkLabel(
            emails_frame,
            text=breakdown_text,
            font=("Arial", 10),
            text_color="gray"
        )
        breakdown_label.pack(pady=(0, 5), padx=20, anchor="w")
        
        # Información de completados (solo para referencia)
        completados_label = ctk.CTkLabel(
            emails_frame,
            text=f"⚠️ Completados (no utilizables): {completados}",
            font=("Arial", 10),
            text_color="red"
        )
        completados_label.pack(pady=(0, 10), padx=20, anchor="w")
    else:
        # Si no se pudo obtener la información
        global_emails_info_label = ctk.CTkLabel(
            emails_frame,
            text="🌐 Emails globales en el servidor: Error al obtener 🔄",
            font=("Arial", 12, "bold"),
            text_color="black"
        )
        global_emails_info_label.pack(pady=(5, 10), padx=20, anchor="w")
    
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
                emails_info_label.configure(text=f"📊 Emails locales en la base de datos: {get_creator_email_count()}")
            else:
                messagebox.showerror("Error", "❌ No se pudieron eliminar los emails.")
    
    # Frame para el botón
    button_frame = ctk.CTkFrame(emails_frame, fg_color="transparent")
    button_frame.pack(fill="x", padx=20, pady=(0, 15))
    
    # Botón para eliminar todos los emails
    delete_emails_button = ctk.CTkButton(
        button_frame,
        text="🗑️ Eliminar Todos los Emails",
        command=delete_all_emails,
        fg_color="#dc3545",
        text_color="white",
        font=("Arial", 12, "bold"),
        height=35,
        width=300
    )
    delete_emails_button.pack(pady=10)
    
    # Crear frame principal para la tabla de coordenadas
    main_frame = ctk.CTkFrame(main_scroll_frame, fg_color="transparent")
    main_frame.pack(fill="x", padx=20, pady=10)
    
    # Definir las coordenadas y sus nombres
    coordinates_list = [
        "Click del Navegador",
        "Click del link de LinkedIn en fav",
        "Click input email",
        "Click botón Agree",
        "Click input de nombre",
        "Click botón continue",
        "Click cerrar captcha",
        "Click cerrar número",
        "Click icono cookie editor",
        "Click guardar cookie portapapeles",
        "Click cerrar ventana",
        "Click botón Agree opcional",
        "Click captcha blanco",
        "Click cerrar captcha error",
        "Click cerrar proxy error"
    ]
    
    # Mapeo de nombres a campos de la base de datos
    field_mapping = {
        "Click del Navegador": "brave_click",
        "Click del link de LinkedIn en fav": "linkedin_fav_click",
        "Click input email": "email_input_click",
        "Click botón Agree": "continue_button_click",
        "Click botón Agree opcional": "continue_button_click_optional",
        "Click input de nombre": "name_input_click",
        "Click botón continue": "continue_button2_click",
        "Click cerrar captcha": "close_captcha_click",
        "Click captcha blanco": "white_captcha_click",
        "Click cerrar número": "close_number_click",
        "Click icono cookie editor": "cookie_editor_icon_click",
        "Click guardar cookie portapapeles": "save_cookie_clipboard_click",
        "Click cerrar ventana": "close_window",
        "Click cerrar captcha error": "close_captcha_error_click",
        "Click cerrar proxy error": "close_proxy_error_click"
    }
    
    # Obtener coordenadas guardadas para este navegador
    saved_coordinates = get_creator_coordinates(browser_id)
    
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
            import pyautogui
            import keyboard
            import threading
            import time
            
            # Bandera para controlar el loop
            capturando = [True]
            
            # Función para actualizar coordenadas en tiempo real
            def actualizar_coordenadas():
                try:
                    while capturando[0]:
                        x, y = pyautogui.position()
                        coord_text = f"X: {x}, Y: {y}"
                        try:
                            if popup.winfo_exists():
                                coord_label.configure(text=f"Movimiento detectado: {coord_text}")
                        except:
                            pass
                        time.sleep(0.1)  # Actualizar cada 0.1 segundos
                except:
                    pass
            
            # Iniciar thread para actualizar coordenadas
            update_thread = threading.Thread(target=actualizar_coordenadas, daemon=True)
            update_thread.start()
            
            # Esperar a que presionen la tecla 'c'
            keyboard.wait('c')
            capturando[0] = False  # Detener actualización
            
            # Obtener coordenada final
            x, y = pyautogui.position()
            coordenada_capturada = f"{x}x{y}"
            
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
                    if save_creator_coordinates(browser_id, **{field_name: coord}):
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
        create_new_window(parent_root, browser_id=browser_id)
    
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
        "Imagen de verificación de éxito carga LinkedIn 2",
        "Imagen de verificación de éxito carga LinkedIn 3",
        "Checkbox recuerdame",
        "Imagen de verificación de carga email y contraseña",
        "Imagen captcha rojo",
        "Imagen captcha blanco",
        "Imagen número",
        "Imagen de creación de cuenta con éxito (logo LinkedIn)",
        "Imagen de creación de cuenta con éxito (logo LinkedIn) 2",
        "Imagen de confirmación de código",
        "add_location",
        "captcha_imposible",
        "captcha_imposible_2",
        "captcha_imposible_3",
        "captcha_verification",
        "captcha_bueno",
        "captcha_bueno_2",
        "captcha_bueno_4",
        "captcha_blanco_2",
        "brave_image",
        "captcha_error",
        "proxy_error",
        "linkedin_error",
    ]
    
    # Crear encabezados de la tabla de imágenes
    images_header_frame = ctk.CTkFrame(images_frame, fg_color="#f0f0f0", corner_radius=0)
    images_header_frame.pack(fill="x")
    
    # Encabezados de imágenes
    images_headers = ["Imagen", "Vista Previa", "Cargar", "Observar"]
    images_header_widths = [350, 120, 120, 120]
    images_header_alignments = ["w", "center", "center", "center"]  # Solo "Vista Previa" y acciones centrados
    
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
    for i in range(4):
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
            width=350,
            anchor="w"
        )
        name_label.grid(row=0, column=0, padx=5, pady=8, sticky="w")
        
        # Verificar si existe la imagen (en el directorio del navegador)
        image_path = get_image_path(image_name, browser_name=browser_name)
        has_image = image_path is not None
        
        # Crear botón para ver imagen
        view_button = ctk.CTkButton(
            row_frame,
            text="Ver Imagen",
            fg_color="#17a2b8" if has_image else "#6c757d",
            text_color="white",
            font=("Arial", 11),
            width=100,
            height=30,
            state="normal" if has_image else "disabled"
        )
        view_button.grid(row=0, column=1, padx=5, pady=8)
        
        # Función para ver imagen con referencia correcta al botón
        def create_view_function(img_name, view_button_ref, observe_button_ref, browser_name_ref):
            def view_image_func():
                image_path = get_image_path(img_name, browser_name=browser_name_ref)
                if image_path:
                    # Callback para actualizar los botones cuando se elimine la imagen
                    def update_buttons_after_delete():
                        view_button_ref.configure(
                            fg_color="#6c757d",
                            state="disabled"
                        )
                        observe_button_ref.configure(
                            fg_color="#6c757d",
                            state="disabled"
                        )
                    view_image(image_path, update_buttons_after_delete)
                else:
                    messagebox.showwarning("Imagen no encontrada", f"No se encontró la imagen: {img_name}\n\nPrimero carga la imagen usando el botón 'Cargar Imagen'.")
            return view_image_func
        
        # Función para cargar imagen con referencia correcta al botón
        def create_load_function(img_name, view_button_ref, observe_button_ref, browser_name_ref):
            def load_image_func():
                result = load_image(img_name, browser_name=browser_name_ref)
                if result:
                    # Actualizar los botones "Ver Imagen" y "Observar" sin refrescar toda la ventana
                    view_button_ref.configure(
                        fg_color="#17a2b8",
                        state="normal"
                    )
                    observe_button_ref.configure(
                        fg_color="#28a745",
                        state="normal"
                    )
            return load_image_func
        
        # Función para observar imagen (verificar si está visible en pantalla)
        def create_observe_function(img_name, browser_name_ref):
            def observe_image_func():
                # Verificar primero si la imagen existe
                image_path = get_image_path(img_name, browser_name=browser_name_ref)
                if not image_path:
                    messagebox.showwarning(
                        "Imagen no encontrada", 
                        f"No se encontró la imagen: {img_name}\n\nPrimero carga la imagen usando el botón 'Cargar Imagen'."
                    )
                    return
                
                # Detectar si es un captcha_imposible (tiene spinner rotando)
                is_spinner_image = (
                    img_name.lower() == "captcha_imposible" or 
                    img_name.lower() == "captcha_imposible_2" or 
                    img_name.lower() == "captcha_imposible_3"
                )
                
                if is_spinner_image:
                    # Usar wait_for_spinner para imágenes con spinner
                    # Probar diferentes niveles de confidence para spinners
                    spinner_configs = [
                        {"confidence": 0.5, "name": "Confianza 0.5 (Recomendado para spinners)"},
                        {"confidence": 0.4, "name": "Confianza 0.4 (Más permisivo)"},
                        {"confidence": 0.6, "name": "Confianza 0.6 (Más estricto)"},
                    ]
                    
                    results = []
                    location = None
                    successful_config = None
                    
                    for config in spinner_configs:
                        test_location = wait_for_spinner(
                            img_name,
                            max_attempts=3,  # Pocos intentos para prueba rápida
                            delay_between_attempts=0.1,
                            confidence=config["confidence"],
                            silent=True,
                            browser_name=browser_name_ref
                        )
                        if test_location:
                            location = test_location
                            successful_config = config
                            results.append(f"✅ {config['name']}: SPINNER ENCONTRADO")
                            break
                        else:
                            results.append(f"❌ {config['name']}: Spinner no encontrado")
                    
                    if location:
                        # Obtener el box para dibujar el borde
                        box = find_creator_image(img_name, confidence=0.5, return_box=True, grayscale=True, browser_name=browser_name_ref)
                        if box:
                            # Dibujar borde rojo alrededor del spinner
                            new_window.after(100, lambda: draw_red_border_around_image(box, duration=3000))
                        
                        all_results = "\n".join(results)
                        messagebox.showinfo(
                            "✅ Spinner Detectado",
                            f"El spinner de '{img_name}' está visible en la pantalla.\n\n"
                            f"Ubicación encontrada: ({location.x}, {location.y})\n"
                            f"{'Área: ' + str(box.width) + 'x' + str(box.height) + ' píxeles' if box else ''}\n\n"
                            f"Configuración exitosa: {successful_config['name']}\n\n"
                            f"Resultados de todas las pruebas:\n{all_results}\n\n"
                            f"💡 Se ha dibujado un borde rojo alrededor del spinner.\n"
                            f"🔄 El spinner está rotando, por eso se usa confidence bajo (0.5)."
                        )
                    else:
                        all_results = "\n".join(results)
                        messagebox.showwarning(
                            "❌ Spinner No Visible",
                            f"El spinner de '{img_name}' NO está visible en la pantalla actualmente.\n\n"
                            f"Se probaron {len(spinner_configs)} configuraciones diferentes:\n\n"
                            f"{all_results}\n\n"
                            f"💡 Recordatorio: Esta imagen tiene un spinner rotando.\n"
                            f"Posibles soluciones:\n"
                            f"• Asegúrate de que el spinner esté visible y rotando\n"
                            f"• Verifica que no esté oculta por otras ventanas\n"
                            f"• El confidence bajo (0.5) permite detectar el spinner en diferentes posiciones\n"
                            f"• Si no se detecta, intenta reducir aún más el confidence (0.4 o 0.3)"
                        )
                else:
                    # Usar método normal para imágenes sin spinner
                    # Usar confidence muy alto para determinar con precisión si la imagen está en pantalla
                    # Especialmente importante para imágenes críticas como verificación de carga
                    is_critical_image = (
                        "verificación" in img_name.lower() or 
                        "verificacion" in img_name.lower() or
                        "carga" in img_name.lower()
                    )
                    
                    if is_critical_image:
                        # Para imágenes críticas, usar confidence muy alto (0.98) para evitar falsos positivos
                        configs_to_try = [
                            {"confidence": 0.98, "grayscale": True, "name": "Confianza 0.98, Escala de grises (Alta precisión)"},
                            {"confidence": 0.97, "grayscale": True, "name": "Confianza 0.97, Escala de grises"},
                            {"confidence": 0.98, "grayscale": False, "name": "Confianza 0.98, Color completo (Alta precisión)"},
                            {"confidence": 0.97, "grayscale": False, "name": "Confianza 0.97, Color completo"},
                        ]
                    else:
                        # Para otras imágenes, usar confidence alto pero no tan extremo
                        configs_to_try = [
                            {"confidence": 0.95, "grayscale": True, "name": "Confianza 0.95, Escala de grises"},
                            {"confidence": 0.9, "grayscale": True, "name": "Confianza 0.9, Escala de grises"},
                            {"confidence": 0.95, "grayscale": False, "name": "Confianza 0.95, Color completo"},
                            {"confidence": 0.9, "grayscale": False, "name": "Confianza 0.9, Color completo"},
                        ]
                    
                    results = []
                    box = None
                    location = None
                    successful_config = None
                    
                    for config in configs_to_try:
                        test_box = find_creator_image(
                            img_name, 
                            confidence=config["confidence"], 
                            return_box=True,
                            grayscale=config["grayscale"],
                            browser_name=browser_name_ref
                        )
                        if test_box:
                            box = test_box
                            location = find_creator_image(
                                img_name, 
                                confidence=config["confidence"], 
                                return_box=False,
                                grayscale=config["grayscale"],
                                browser_name=browser_name_ref
                            )
                            successful_config = config
                            results.append(f"✅ {config['name']}: ENCONTRADA")
                            break
                        else:
                            results.append(f"❌ {config['name']}: No encontrada")
                    
                    if box and location:
                        # Dibujar borde rojo alrededor de la imagen
                        # Usar after para ejecutar después de mostrar el mensaje
                        new_window.after(100, lambda: draw_red_border_around_image(box, duration=3000))
                        
                        # Crear mensaje con información detallada
                        config_info = f"\n\nConfiguración exitosa: {successful_config['name']}"
                        all_results = "\n".join(results)
                        
                        messagebox.showinfo(
                            "✅ Imagen Visible",
                            f"La imagen '{img_name}' está visible en la pantalla.\n\n"
                            f"Ubicación encontrada: ({location.x}, {location.y})\n"
                            f"Área: {box.width}x{box.height} píxeles"
                            f"{config_info}\n\n"
                            f"Resultados de todas las pruebas:\n{all_results}\n\n"
                            f"Se ha dibujado un borde rojo alrededor de la imagen.\n"
                            f"La aplicación puede detectar correctamente esta imagen."
                        )
                    else:
                        # Mostrar resultados de todas las pruebas fallidas
                        all_results = "\n".join(results)
                        messagebox.showwarning(
                            "❌ Imagen No Visible",
                            f"La imagen '{img_name}' NO está visible en la pantalla actualmente.\n\n"
                            f"Se probaron {len(configs_to_try)} configuraciones diferentes:\n\n"
                            f"{all_results}\n\n"
                            f"Posibles soluciones:\n"
                            f"• Asegúrate de que la imagen esté completamente visible\n"
                            f"• Verifica que no esté oculta por otras ventanas\n"
                            f"• La imagen debe coincidir exactamente con la que cargaste\n"
                            f"• En VPS, puede haber diferencias de renderizado - intenta capturar la imagen directamente desde el VPS\n"
                            f"• Considera reducir el confidence o desactivar grayscale en el código"
                        )
            return observe_image_func
        
        # Botón para observar imagen
        observe_button = ctk.CTkButton(
            row_frame,
            text="Observar",
            command=create_observe_function(image_name, browser_name),
            fg_color="#28a745" if has_image else "#6c757d",
            text_color="white",
            font=("Arial", 11),
            width=100,
            height=30,
            state="normal" if has_image else "disabled"
        )
        observe_button.grid(row=0, column=3, padx=5, pady=8)
        
        # Asignar comandos a los botones con las referencias correctas
        view_button.configure(command=create_view_function(image_name, view_button, observe_button, browser_name))
        
        load_button = ctk.CTkButton(
            row_frame,
            text="Cargar Imagen",
            command=create_load_function(image_name, view_button, observe_button, browser_name),
            fg_color="#007ACC",
            text_color="white",
            font=("Arial", 11),
            width=100,
            height=30
        )
        load_button.grid(row=0, column=2, padx=5, pady=8)
        
        # Configurar columnas de la fila de imágenes
        for j in range(4):
            row_frame.grid_columnconfigure(j, weight=1)
    
    return new_window

