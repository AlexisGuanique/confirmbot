def create_new_window(parent_root):
    """
    Crea una nueva ventana con tabla de coordenadas del creator
    """
    import customtkinter as ctk
    from tkinter import messagebox
    import threading
    from app.database.database import get_creator_coordinates, save_creator_coordinates
    from app.confirmabot.utils.mouse_click_coordenates import get_mouse_coordinate_on_keypress
    
    # Crear la nueva ventana
    new_window = ctk.CTkToplevel(parent_root)
    new_window.title("Configuración del Creator")
    new_window.geometry("800x600")
    new_window.configure(fg_color="#FFFFFF")
    
    # Centrar la ventana y hacerla modal
    new_window.transient(parent_root)
    new_window.grab_set()
    
    # Título de la ventana
    title_label = ctk.CTkLabel(
        new_window,
        text="⚙️ Configuración de Coordenadas del Creator",
        font=("Arial", 18, "bold"),
        text_color="black"
    )
    title_label.pack(pady=(20, 30))
    
    # Crear frame principal para la tabla
    main_frame = ctk.CTkFrame(new_window, fg_color="transparent")
    main_frame.pack(fill="both", expand=True, padx=20, pady=10)
    
    # Definir las coordenadas y sus nombres
    coordinates_list = [
        "Click del Brave",
        "Click del link de LinkedIn en fav",
        "Click input email",
        "Click botón continue",
        "Click input de nombre",
        "Click botón continue (2)",
        "Click cerrar captcha",
        "Click cerrar número",
        "Click icono cookie editor",
        "Click guardar cookie portapapeles"
    ]
    
    # Mapeo de nombres a campos de la base de datos
    field_mapping = {
        "Click del Brave": "brave_click",
        "Click del link de LinkedIn en fav": "linkedin_fav_click",
        "Click input email": "email_input_click",
        "Click botón continue": "continue_button_click",
        "Click input de nombre": "name_input_click",
        "Click botón continue (2)": "continue_button2_click",
        "Click cerrar captcha": "close_captcha_click",
        "Click cerrar número": "close_number_click",
        "Click icono cookie editor": "cookie_editor_icon_click",
        "Click guardar cookie portapapeles": "save_cookie_clipboard_click"
    }
    
    # Obtener coordenadas guardadas
    saved_coordinates = get_creator_coordinates()
    
    # Función para capturar coordenadas (igual que en ui.py)
    def capture_coordinate(coord_name, field_name):
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
            popup.after(0, lambda: coord_label.configure(text=f"{coord_name}: {coordenada_capturada}"))
            
            # Mostrar botones de confirmación después de capturar
            popup.after(0, lambda: mostrar_botones_confirmacion(coordenada_capturada))

        def mostrar_botones_confirmacion(coord):
            # Limpiar widgets anteriores
            for widget in popup.winfo_children():
                if isinstance(widget, ctk.CTkButton):
                    widget.destroy()
            
            def guardar():
                if save_creator_coordinates(**{field_name: coord}):
                    messagebox.showinfo("Guardado", f"✅ Coordenada guardada: {coord}")
                    popup.destroy()
                    refresh_window()
                else:
                    messagebox.showerror("Error", "No se pudo guardar la coordenada.")

            def volver_a_capturar():
                popup.destroy()
                capture_coordinate(coord_name, field_name)

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

        threading.Thread(target=capturar, daemon=True).start()
    
    # Función para refrescar la ventana
    def refresh_window():
        new_window.destroy()
        create_new_window(parent_root)
    
    # Crear encabezados de la tabla
    header_frame = ctk.CTkFrame(main_frame, fg_color="#f0f0f0", corner_radius=5)
    header_frame.pack(fill="x", pady=(0, 5))
    
    # Encabezados
    headers = ["Coordenada", "Valor", "Acción"]
    header_widths = [300, 200, 150]
    
    for i, (header, width) in enumerate(zip(headers, header_widths)):
        header_label = ctk.CTkLabel(
            header_frame,
            text=header,
            font=("Arial", 14, "bold"),
            text_color="black",
            width=width
        )
        header_label.grid(row=0, column=i, padx=5, pady=10, sticky="ew")
    
    # Configurar columnas del header
    for i in range(3):
        header_frame.grid_columnconfigure(i, weight=1)
    
    # Crear filas de datos
    for i, coord_name in enumerate(coordinates_list):
        row_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=5)
        row_frame.pack(fill="x", pady=2)
        
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
        def create_capture_function(coord_name, field_name):
            def capture_coordinates():
                capture_coordinate(coord_name, field_name)
            return capture_coordinates
        
        action_button = ctk.CTkButton(
            row_frame,
            text="Configurar",
            command=create_capture_function(coord_name, field_name),
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
    
    return new_window
