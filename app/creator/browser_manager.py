def create_browser_manager_window(parent_root):
    """
    Crea una ventana para gestionar navegadores (crear, editar, configurar, eliminar).
    """
    import customtkinter as ctk
    from tkinter import messagebox
    import os
    import shutil
    from app.database.database import (
        get_all_browsers, create_browser, update_browser, 
        delete_browser, get_default_browser, get_browser_by_id,
        get_global_time_config,
    )
    from app.creator.ui_creator import create_new_window
    from app.utils.path_utils import get_browser_images_path, ensure_directory_exists

    def _push_browser_catalog_to_server():
        """Notifica al servidor la lista actual de navegadores (mismo evento que al conectar)."""
        try:
            from app.auth.auth import sync_available_browsers_to_server, sio
            if getattr(sio, "connected", False):
                sync_available_browsers_to_server(force=True)
        except Exception as e:
            print(f"⚠️ No se pudo sincronizar navegadores con el servidor: {e}")
    
    # Crear la ventana
    manager_window = ctk.CTkToplevel(parent_root)
    manager_window.title("Gestión de Navegadores")
    manager_window.geometry("600x600")
    manager_window.configure(fg_color="#FFFFFF")
    
    # Centrar la ventana y hacerla modal
    manager_window.transient(parent_root)
    manager_window.grab_set()
    
    # Crear frame principal con scroll
    main_scroll_frame = ctk.CTkScrollableFrame(manager_window, fg_color="transparent")
    main_scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Título de la ventana
    title_label = ctk.CTkLabel(
        main_scroll_frame,
        text="🌐 Gestión de Navegadores",
        font=("Arial", 18, "bold"),
        text_color="black"
    )
    title_label.pack(pady=(20, 10))

    current_global_config = get_global_time_config() or {}

    # ================= CICLO Y HORA (SERVIDOR — SOLO LECTURA) =================
    time_config_frame = ctk.CTkFrame(main_scroll_frame, fg_color="white", corner_radius=5, border_width=2, border_color="black")
    time_config_frame.pack(fill="x", padx=20, pady=(0, 20))

    time_config_title = ctk.CTkLabel(
        time_config_frame,
        text="Ciclo y hora programada",
        font=("Arial", 14, "bold"),
        text_color="black"
    )
    time_config_title.pack(pady=(15, 5))

    time_config_subtitle = ctk.CTkLabel(
        time_config_frame,
        text="Se configura en el servidor (panel web, configuración global de bots). Al ejecutar el creator desde la web se aplica en esta PC.",
        font=("Arial", 10),
        text_color="gray",
        wraplength=520,
        justify="left",
    )
    time_config_subtitle.pack(pady=(0, 10), padx=20, anchor="w")

    tct = current_global_config.get("time_config_type") or "manual"
    ctm = current_global_config.get("cycle_time_minutes")
    apc = current_global_config.get("accounts_per_cycle")
    st = current_global_config.get("scheduled_time") or "—"
    tz = current_global_config.get("timezone") or "—"
    time_info = (
        "Valores locales (última sincronización / ejecución remota):\n\n"
        f"Modo: {tct}\n"
        f"Minutos entre ciclos: {ctm if ctm is not None else '—'}\n"
        f"Cuentas por ciclo: {apc if apc is not None else '—'}\n"
        f"Hora programada: {st}\n"
        f"Zona: {tz}"
    )
    time_info_label = ctk.CTkLabel(
        time_config_frame,
        text=time_info,
        font=("Arial", 11),
        text_color="black",
        justify="left",
        anchor="w",
    )
    time_info_label.pack(fill="x", padx=20, pady=(0, 15))

    # ================= DOMINIOS (SOLO LECTURA - GESTIONADOS EN SERVIDOR) =================
    domain_config_frame = ctk.CTkFrame(
        main_scroll_frame, fg_color="white", corner_radius=5, border_width=2, border_color="black"
    )
    domain_config_frame.pack(fill="x", padx=20, pady=(0, 20))

    domain_config_title = ctk.CTkLabel(
        domain_config_frame,
        text="📧 Gestión de Dominios",
        font=("Arial", 14, "bold"),
        text_color="black"
    )
    domain_config_title.pack(pady=(15, 5))

    domain_config_subtitle = ctk.CTkLabel(
        domain_config_frame,
        text="🌐 Esta configuración ahora se administra desde el servidor",
        font=("Arial", 10),
        text_color="gray"
    )
    domain_config_subtitle.pack(pady=(0, 10))

    is33mail = bool(current_global_config.get("is33mail", True))
    random_domains = bool(current_global_config.get("random_domains", False))
    fill_domain = bool(current_global_config.get("fill_domain", False))
    mode_text = "33mail" if is33mail else ("Dominios aleatorios" if random_domains else "Dominios personalizados")

    server_info = (
        "La edición local de dominios fue deshabilitada.\n"
        "Actualiza esta configuración desde 'Config Bots' en el servidor.\n\n"
        f"Modo actual (última config aplicada): {mode_text}\n"
        f"Rellenar subdominio: {'Sí' if fill_domain else 'No'}"
    )
    domain_info_label = ctk.CTkLabel(
        domain_config_frame,
        text=server_info,
        font=("Arial", 11),
        text_color="black",
        justify="left",
        anchor="w"
    )
    domain_info_label.pack(fill="x", padx=20, pady=(0, 8))

    server_hint_label = ctk.CTkLabel(
        domain_config_frame,
        text="Tip: inicia ejecución desde el servidor para sincronizar y aplicar cambios al bot.",
        font=("Arial", 10),
        text_color="gray",
        justify="left",
        anchor="w"
    )
    server_hint_label.pack(fill="x", padx=20, pady=(0, 15))
    
    # ================= SECCIÓN CREAR NUEVO NAVEGADOR =================
    
    # Frame para crear nuevo navegador
    create_frame = ctk.CTkFrame(main_scroll_frame, fg_color="white", corner_radius=5, border_width=2, border_color="black")
    create_frame.pack(fill="x", padx=20, pady=(0, 20))
    
    create_title = ctk.CTkLabel(
        create_frame,
        text="➕ Crear Nuevo Navegador",
        font=("Arial", 14, "bold"),
        text_color="black"
    )
    create_title.pack(pady=(15, 10))
    
    # Frame para inputs
    create_inputs_frame = ctk.CTkFrame(create_frame, fg_color="transparent")
    create_inputs_frame.pack(fill="x", padx=20, pady=(0, 15))
    
    # Input para nombre del navegador
    name_label = ctk.CTkLabel(
        create_inputs_frame,
        text="Nombre del Navegador:",
        font=("Arial", 12),
        text_color="black"
    )
    name_label.pack(anchor="w", pady=(0, 5))
    
    name_entry = ctk.CTkEntry(
        create_inputs_frame,
        placeholder_text="Ejemplo: Chrome, Firefox, Brave...",
        font=("Arial", 11),
        height=35
    )
    name_entry.pack(fill="x", pady=(0, 10))
    
    # Función para crear navegador
    def create_new_browser():
        name = name_entry.get().strip()
        if not name:
            messagebox.showwarning("Advertencia", "Por favor ingresa un nombre para el navegador.")
            return
        
        # La selección del navegador de ejecución se controla desde el servidor.
        # Los navegadores nuevos se crean inactivos por defecto.
        browser_id = create_browser(name, False)
        
        if browser_id:
            # Crear directorio de imágenes para el navegador
            from app.utils.path_utils import get_browser_images_path, ensure_directory_exists
            browser_images_path = get_browser_images_path(name)
            if ensure_directory_exists(browser_images_path):
                print(f"✅ Directorio de imágenes creado: {browser_images_path}")
            else:
                print(f"⚠️ No se pudo crear el directorio de imágenes: {browser_images_path}")
            
            messagebox.showinfo("Éxito", f"✅ Navegador '{name}' creado correctamente.\n\n📁 Directorio de imágenes creado: {os.path.basename(browser_images_path)}")
            name_entry.delete(0, 'end')
            refresh_browsers_table()
            _push_browser_catalog_to_server()
        else:
            messagebox.showerror("Error", f"❌ No se pudo crear el navegador. Verifica que el nombre no esté duplicado.")
    
    # Botón para crear navegador
    create_button = ctk.CTkButton(
        create_inputs_frame,
        text="➕ Crear Navegador",
        command=create_new_browser,
        fg_color="#28a745",
        text_color="white",
        font=("Arial", 12, "bold"),
        height=35
    )
    create_button.pack(pady=(0, 15))
    
    # ================= TABLA DE NAVEGADORES =================
    
    # Título de la tabla
    table_title = ctk.CTkLabel(
        main_scroll_frame,
        text="📋 Lista de Navegadores",
        font=("Arial", 16, "bold"),
        text_color="black"
    )
    table_title.pack(pady=(0, 15))
    
    # Contenedor de la tabla
    table_container = ctk.CTkFrame(main_scroll_frame, fg_color="white", corner_radius=5, border_width=2, border_color="black")
    table_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
    
    # Crear encabezados de la tabla
    header_frame = ctk.CTkFrame(table_container, fg_color="#f0f0f0", corner_radius=0)
    header_frame.pack(fill="x")
    
    # Encabezados
    headers = ["Nombre", "Acciones"]
    header_widths = [140, 320]
    header_alignments = ["w", "center"]
    
    for i, (header, width, alignment) in enumerate(zip(headers, header_widths, header_alignments)):
        header_label = ctk.CTkLabel(
            header_frame,
            text=header,
            font=("Arial", 11, "bold"),
            text_color="black",
            width=width,
            anchor=alignment
        )
        sticky_value = "w" if alignment == "w" else "ew"
        header_label.grid(row=0, column=i, padx=3, pady=5, sticky=sticky_value)
    
    # Configurar columnas del header
    for i in range(2):
        header_frame.grid_columnconfigure(i, weight=1)
    
    # Frame para las filas de navegadores (contenedor scrollable)
    browsers_rows_frame = ctk.CTkFrame(table_container, fg_color="transparent")
    browsers_rows_frame.pack(fill="both", expand=True)
    
    # Función para refrescar la tabla de navegadores
    def refresh_browsers_table():
        # Limpiar filas existentes
        for widget in browsers_rows_frame.winfo_children():
            widget.destroy()
        
        # Obtener todos los navegadores
        browsers = get_all_browsers()
        
        if not browsers:
            # Mostrar mensaje si no hay navegadores
            no_browsers_label = ctk.CTkLabel(
                browsers_rows_frame,
                text="No hay navegadores registrados. Crea uno nuevo arriba.",
                font=("Arial", 12),
                text_color="gray"
            )
            no_browsers_label.pack(pady=20)
            return
        
        # Crear fila para cada navegador
        for browser in browsers:
            row_frame = ctk.CTkFrame(browsers_rows_frame, fg_color="white", corner_radius=0)
            row_frame.pack(fill="x")
            
            # Frame para el nombre (permite edición)
            name_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            name_frame.grid(row=0, column=0, padx=3, pady=4, sticky="w")
            
            # Nombre del navegador (label inicial)
            name_label = ctk.CTkLabel(
                name_frame,
                text=browser['name'],
                font=("Arial", 10),
                text_color="black",
                width=100,
                anchor="w"
            )
            name_label.pack(side="left")
            
            # Entry para editar (inicialmente oculto)
            name_entry = ctk.CTkEntry(
                name_frame,
                font=("Arial", 10),
                width=100,
                height=25
            )
            name_entry.insert(0, browser['name'])
            # name_entry no se muestra inicialmente
            
            # Variable para rastrear si estamos editando
            is_editing = {"value": False}
            
            # Frame para botones de acciones
            actions_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            actions_frame.grid(row=0, column=1, padx=3, pady=4)
            
            # Botón de guardar (inicialmente oculto)
            save_button = ctk.CTkButton(
                actions_frame,
                text="💾 Guardar",
                fg_color="#28a745",
                text_color="white",
                font=("Arial", 9),
                width=70,
                height=25
            )
            # No se muestra inicialmente
            
            # Botón de cancelar (inicialmente oculto)
            cancel_button = ctk.CTkButton(
                actions_frame,
                text="❌ Cancelar",
                fg_color="#6c757d",
                text_color="white",
                font=("Arial", 9),
                width=70,
                height=25
            )
            # No se muestra inicialmente
            
            # Función para editar nombre
            def create_edit_name_function(browser_id, old_name, name_label_ref, name_entry_ref, is_editing_ref, edit_btn_ref, save_btn_ref, cancel_btn_ref):
                def start_edit():
                    if is_editing_ref["value"]:
                        return  # Ya está editando
                    
                    is_editing_ref["value"] = True
                    name_label_ref.pack_forget()
                    name_entry_ref.pack(side="left")
                    name_entry_ref.focus()
                    name_entry_ref.select_range(0, 'end')
                    
                    # Cambiar botón Editar por Guardar/Cancelar
                    edit_btn_ref.pack_forget()
                    save_btn_ref.pack(side="left", padx=(0, 3))
                    cancel_btn_ref.pack(side="left", padx=(0, 3))
                
                def save_edit():
                    new_name = name_entry_ref.get().strip()
                    
                    if not new_name:
                        messagebox.showwarning("Advertencia", "El nombre no puede estar vacío.")
                        return
                    
                    if new_name == old_name:
                        # No hay cambios, solo cancelar edición
                        cancel_edit()
                        return
                    
                    # Verificar si ya existe un navegador con ese nombre
                    all_browsers = get_all_browsers()
                    for b in all_browsers:
                        if b['id'] != browser_id and b['name'].lower() == new_name.lower():
                            messagebox.showerror("Error", f"❌ Ya existe un navegador con el nombre '{new_name}'.")
                            return
                    
                    # Obtener el nombre actual del navegador desde la base de datos
                    # para asegurarnos de tener el nombre correcto antes de renombrar
                    current_browser = get_browser_by_id(browser_id)
                    if not current_browser:
                        messagebox.showerror("Error", f"❌ No se pudo encontrar el navegador en la base de datos.")
                        cancel_edit()
                        return
                    
                    # Usar el nombre actual de la base de datos para construir la ruta antigua
                    actual_old_name = current_browser['name']
                    
                    # Obtener rutas de directorios
                    old_path = get_browser_images_path(actual_old_name)
                    new_path = get_browser_images_path(new_name)
                    
                    # Actualizar en la base de datos
                    if update_browser(browser_id, name=new_name):
                        # Renombrar directorio si existe
                        if os.path.exists(old_path) and os.path.isdir(old_path):
                            try:
                                if os.path.exists(new_path):
                                    # Si el nuevo directorio ya existe, preguntar qué hacer
                                    result = messagebox.askyesno(
                                        "Directorio Existente",
                                        f"El directorio '{os.path.basename(new_path)}' ya existe.\n\n"
                                        f"¿Deseas fusionar el contenido del directorio antiguo con el nuevo?"
                                    )
                                    if result:
                                        # Fusionar contenido
                                        for item in os.listdir(old_path):
                                            src = os.path.join(old_path, item)
                                            dst = os.path.join(new_path, item)
                                            if os.path.isdir(src):
                                                if os.path.exists(dst):
                                                    shutil.copytree(src, dst, dirs_exist_ok=True)
                                                else:
                                                    shutil.copytree(src, dst)
                                                shutil.rmtree(src)
                                            else:
                                                if os.path.exists(dst):
                                                    os.remove(dst)
                                                shutil.move(src, dst)
                                        os.rmdir(old_path)
                                    else:
                                        # Solo eliminar el antiguo
                                        shutil.rmtree(old_path)
                                else:
                                    # Renombrar directorio
                                    shutil.move(old_path, new_path)
                                print(f"✅ Directorio renombrado: {old_path} -> {new_path}")
                            except Exception as e:
                                print(f"⚠️ Error al renombrar directorio: {e}")
                                print(f"   Ruta antigua: {old_path}")
                                print(f"   Ruta nueva: {new_path}")
                                print(f"   ¿Existe ruta antigua?: {os.path.exists(old_path)}")
                                messagebox.showwarning(
                                    "Advertencia",
                                    f"✅ El nombre se actualizó en la base de datos, pero hubo un problema al renombrar el directorio:\n\n{e}\n\n"
                                    f"Ruta antigua: {old_path}\n"
                                    f"Ruta nueva: {new_path}"
                                )
                        else:
                            # Si el directorio antiguo no existe, crear el nuevo
                            if not os.path.exists(new_path):
                                ensure_directory_exists(new_path)
                                print(f"✅ Nuevo directorio creado: {new_path}")
                            else:
                                print(f"ℹ️ El directorio nuevo ya existe: {new_path}")
                        
                        messagebox.showinfo("Éxito", f"✅ Nombre del navegador actualizado correctamente.\n\n📁 Directorio: {os.path.basename(new_path)}")
                        refresh_browsers_table()
                        _push_browser_catalog_to_server()
                    else:
                        messagebox.showerror("Error", f"❌ No se pudo actualizar el nombre del navegador.")
                
                def cancel_edit():
                    is_editing_ref["value"] = False
                    name_entry_ref.pack_forget()
                    name_label_ref.pack(side="left")
                    name_entry_ref.delete(0, 'end')
                    name_entry_ref.insert(0, old_name)
                    
                    # Restaurar botón Editar
                    save_btn_ref.pack_forget()
                    cancel_btn_ref.pack_forget()
                    edit_btn_ref.pack(side="left", padx=(0, 3))
                
                def on_entry_return(event):
                    save_edit()
                
                name_entry_ref.bind("<Return>", on_entry_return)
                name_entry_ref.bind("<Escape>", lambda e: cancel_edit())
                
                return start_edit, save_edit, cancel_edit
            
            # Botón de editar nombre (se crea primero para poder pasarlo a la función)
            edit_button = ctk.CTkButton(
                actions_frame,
                text="✏️ Editar",
                fg_color="#ffc107",
                text_color="black",
                font=("Arial", 11),
                width=30,
                height=25
            )
            edit_button.pack(side="left", padx=(0, 3))
            
            # Crear funciones de edición con todas las referencias
            start_edit_func, save_edit_func, cancel_edit_func = create_edit_name_function(
                browser['id'], browser['name'], name_label, name_entry, is_editing, 
                edit_button, save_button, cancel_button
            )
            
            # Asignar comandos a los botones
            edit_button.configure(command=start_edit_func)
            save_button.configure(command=save_edit_func)
            cancel_button.configure(command=cancel_edit_func)
            
            # Botón de configuraciones
            def create_config_function(browser_id):
                def open_config():
                    create_new_window(parent_root, browser_id=browser_id)
                return open_config
            
            config_button = ctk.CTkButton(
                actions_frame,
                text="⚙️ Config",
                command=create_config_function(browser['id']),
                fg_color="#007ACC",
                text_color="white",
                font=("Arial", 9),
                width=70,
                height=25
            )
            config_button.pack(side="left", padx=(0, 3))
            
            # Botón de eliminar
            def create_delete_function(browser_id, browser_name):
                def delete_browser_func():
                    result = messagebox.askyesno(
                        "Confirmar Eliminación",
                        f"¿Estás seguro de que quieres eliminar el navegador '{browser_name}'?\n\n"
                        f"⚠️ Esta acción eliminará también todas sus configuraciones, coordenadas e imágenes.\n\n"
                        f"Esta acción no se puede deshacer."
                    )
                    if result:
                        if delete_browser(browser_id):
                            messagebox.showinfo("Éxito", f"✅ Navegador '{browser_name}' eliminado correctamente.")
                            refresh_browsers_table()
                            _push_browser_catalog_to_server()
                        else:
                            messagebox.showerror("Error", f"❌ No se pudo eliminar el navegador.")
                return delete_browser_func
            
            delete_button = ctk.CTkButton(
                actions_frame,
                text="🗑️",
                command=create_delete_function(browser['id'], browser['name']),
                fg_color="#dc3545",
                text_color="white",
                font=("Arial", 9),
                width=20,
                height=25
            )
            delete_button.pack(side="left", padx=(0, 3))
            
            # Configurar columnas de la fila
            row_frame.grid_columnconfigure(0, weight=1, minsize=140)
            row_frame.grid_columnconfigure(1, weight=1, minsize=220)
    
    # Cargar navegadores inicialmente
    refresh_browsers_table()
    
    # Botón para cerrar
    close_button = ctk.CTkButton(
        main_scroll_frame,
        text="Cerrar",
        command=manager_window.destroy,
        fg_color="#6c757d",
        text_color="white",
        font=("Arial", 12, "bold"),
        height=35,
        width=150
    )
    close_button.pack(pady=(10, 20))
    
    return manager_window

