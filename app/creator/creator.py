def observador_unificado(coordinates, email, password):
    
    from app.creator.computer_actions import click_coordinates, wait_for_creator_image, get_clipboard_content
    from app.database.database import get_creator_setting
    import time
    import os
    import json
    from datetime import datetime
    
    def format_cookie_to_single_line(cookie_content):
        """
        Convierte el contenido de cookies del portapapeles a formato de una sola línea
        """
        try:
            # Buscar el inicio del JSON (primer '[')
            json_start = cookie_content.find('[')
            if json_start == -1:
                print("⚠️ No se encontró un array JSON válido en las cookies")
                return cookie_content
            
            # Extraer solo la parte JSON
            json_content = cookie_content[json_start:]
            
            # Parsear el JSON
            data = json.loads(json_content)
            
            # Convertir a JSON compacto (una sola línea)
            json_single_line = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
            
            # Si hay contenido antes del JSON, mantenerlo
            if json_start > 0:
                prefix = cookie_content[:json_start]
                return prefix + json_single_line
            else:
                return json_single_line
                
        except json.JSONDecodeError as e:
            print(f"⚠️ Error al parsear cookies JSON: {e}")
            return cookie_content
        except Exception as e:
            print(f"⚠️ Error inesperado al formatear cookies: {e}")
            return cookie_content
    
    print("👁️ Observando número, captcha rojo o éxito...")
    
    start_time = time.time()
    timeout_seconds = 120  # 2 minutos
    
    # Contadores para evitar bucles infinitos
    numero_count = 0
    captcha_count = 0
    
    while True:
        # Verificar si ha pasado el timeout
        elapsed_time = time.time() - start_time
        if elapsed_time > timeout_seconds:
            print("⏰ Timeout de 120 segundos - cerrando ventana")
            close_window_coords = coordinates.get("close_window")
            if close_window_coords:
                click_coordinates(close_window_coords)
                time.sleep(1)
            return False
        
        # Verificar número
        numero_found = wait_for_creator_image("imagen_numero", max_attempts=1, delay_between_attempts=0.5, silent=True)
        
        if numero_found:
            numero_count += 1
            print(f"✅ Número encontrado (vez #{numero_count}) - cerrando")
            
            if numero_count >= 2:
                print("🔄 Segundo número detectado - cerrando ventana directamente")
                close_window_coords = coordinates.get("close_window")
                if close_window_coords:
                    click_coordinates(close_window_coords)
                    time.sleep(1)
                return False
            
            close_number_coords = coordinates.get("close_number_click")
            if close_number_coords:
                click_coordinates(close_number_coords)
                time.sleep(1)
                
                continue2_coords = coordinates.get("continue_button2_click")
                if continue2_coords:
                    click_coordinates(continue2_coords)
                    time.sleep(2)
                    continue
        
        # Verificar captcha rojo
        captcha_found = wait_for_creator_image("imagen_captcha_rojo", max_attempts=1, delay_between_attempts=0.5, silent=True)
        
        if captcha_found:
            captcha_count += 1
            print(f"✅ Captcha encontrado (vez #{captcha_count}) - cerrando")
            
            if captcha_count >= 2:
                print("🔄 Segundo captcha detectado - cerrando ventana directamente")
                close_window_coords = coordinates.get("close_window")
                if close_window_coords:
                    click_coordinates(close_window_coords)
                    time.sleep(1)
                return False
            
            close_captcha_coords = coordinates.get("close_captcha_click")
            if close_captcha_coords:
                click_coordinates(close_captcha_coords)
                time.sleep(1)
                
                continue2_coords = coordinates.get("continue_button2_click")
                if continue2_coords:
                    click_coordinates(continue2_coords)
                    time.sleep(2)
                    continue
        
        # Verificar imagen de éxito
        exito_found = wait_for_creator_image("imagen_de_creacion_de_cuenta_con_exito_logo_linkedin", max_attempts=1, delay_between_attempts=0.5, silent=True)
        
        if exito_found:
            print("✅ Imagen de éxito encontrada - guardando información")
            
            # Clic en cookie_editor_icon_click
            cookie_editor_coords = coordinates.get("cookie_editor_icon_click")
            if cookie_editor_coords:
                click_coordinates(cookie_editor_coords)
                time.sleep(1)
                
                # Clic en save_cookie_clipboard_click
                save_cookie_coords = coordinates.get("save_cookie_clipboard_click")
                if save_cookie_coords:
                    click_coordinates(save_cookie_coords)
                    time.sleep(1)
                    
                    # Obtener cookie del portapapeles
                    cookie_raw = get_clipboard_content()
                    
                    # Formatear cookie a una sola línea
                    cookie = format_cookie_to_single_line(cookie_raw)
                    print(f"📋 Cookie formateada: {len(cookie)} caracteres")
                    
                    # Obtener user agent desde la base de datos
                    creator_settings = get_creator_setting()
                    if creator_settings and creator_settings.get('user_agent'):
                        user_agent = creator_settings.get('user_agent')
                        
                        # Crear contenido del archivo con formato correcto (separado por tabs)
                        contenido = f"{user_agent}\t{email}\t{password}\t{cookie}"
                        
                        # Crear carpeta linkedin_accounts si no existe
                        folder_path = "linkedin_accounts"
                        if not os.path.exists(folder_path):
                            os.makedirs(folder_path)
                        
                        # Guardar en archivo .txt
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"cuenta_creada_{timestamp}.txt"
                        filepath = os.path.join(folder_path, filename)
                        
                        try:
                            with open(filepath, 'w', encoding='utf-8') as f:
                                f.write(contenido)
                            print(f"✅ Información guardada en {filepath}")
                            return True
                        except Exception as e:
                            print(f"❌ Error guardando archivo: {e}")
                            return False
                    else:
                        print("❌ No se encontró user agent en la base de datos")
                        return False
        
        # Pequeña pausa antes del siguiente ciclo
        time.sleep(0.5)



def execute_creator():
    """
    Función principal del creator que ejecuta todas las acciones
    """
    from app.database.database import get_creator_coordinates
    from app.creator.computer_actions import click_coordinates, wait_for_creator_image, type_text, press_key, generate_random_password, generate_random_name, generate_random_lastname
    import time
    import os
    import subprocess

    from app.database.database import get_bot_settings

    config = get_bot_settings()


    # Ruta del ejecutable ADB - verificar si existe
    adb_path = r"C:\Adb\adb.exe"
    adb_available = os.path.exists(adb_path)
    
    if not adb_available:
        print("⚠️ ADB no encontrado en C:\\Adb\\adb.exe")
        print("💡 El modo avión se omitirá, pero el bot continuará funcionando")
    else:
        print("✅ ADB encontrado y disponible")

    # Ejecutar comandos ADB solo si está disponible y habilitado
    enable_adb = config.get("enable_adb", True)
    if adb_available and enable_adb:
        try:
            # Ejecutar el comando para activar el modo avión
            subprocess.run([adb_path, "shell", "cmd", "connectivity", "airplane-mode", "enable"], 
                            capture_output=True, text=True, timeout=10)
            print("✅ Modo avión activado.")
            time.sleep(3)  # Esperar 5 segundos

            # Ejecutar el comando para desactivar el modo avión
            subprocess.run([adb_path, "shell", "cmd", "connectivity", "airplane-mode", "disable"], 
                            capture_output=True, text=True, timeout=10)
            print("✅ Modo avión desactivado.")
            time.sleep(3)  # Esperar 5 segundos
        except Exception as e:
            print(f"⚠️ Error ejecutando comandos ADB: {e}")
            print("🔄 Continuando sin modo avión...")
    elif not enable_adb:
        print("⏭️ Modo avión deshabilitado por configuración")
        time.sleep(2)  # Pequeña pausa para simular el proceso
    else:
        print("⏭️ Omitiendo modo avión (ADB no disponible)")
        time.sleep(2)  # Pequeña pausa para simular el proceso
    
    coordinates = get_creator_coordinates()
    if not coordinates:
        print("❌ No se encontraron coordenadas configuradas")
        return
    
    # Click en Brave
    brave_coords = coordinates.get("brave_click")
    if brave_coords:
        click_coordinates(brave_coords, double_click=True)
    else:
        print("⚠️ No se encontraron coordenadas para Brave")
        return
    
    time.sleep(0.5)
    
    # Click en LinkedIn fav
    linkedin_coords = coordinates.get("linkedin_fav_click")
    if linkedin_coords:
        click_coordinates(linkedin_coords)
    else:
        print("⚠️ No se encontraron coordenadas para LinkedIn fav")
        return
    
    time.sleep(3)
    
    # Buscar imagen de verificación de LinkedIn
    verification_image = wait_for_creator_image("imagen_de_verificacion_de_exito_carga_linkedin", max_attempts=15, delay_between_attempts=1)
    if verification_image:
        # Click en email_input_click
        email_coords = coordinates.get("email_input_click")
        if email_coords:
            click_coordinates(email_coords)
            time.sleep(0.5)
            
            # Escribir email
            type_text("zzzsdfsdfae345445d@mmasdfsdfdasd.com")
            time.sleep(0.5)
            
            # Ir al campo de contraseña
            press_key("tab")
            time.sleep(0.5)
            
            # Escribir contraseña aleatoria
            random_password = generate_random_password()
            type_text(random_password)
            time.sleep(0.5)
            
            # Click en continue_button_click
            continue_coords = coordinates.get("continue_button_click")
            if continue_coords:
                click_coordinates(continue_coords)
                time.sleep(2)
                
                # Click en name_input_click
                name_coords = coordinates.get("name_input_click")
                if name_coords:
                    click_coordinates(name_coords)
                    time.sleep(0.5)
                    
                    # Escribir nombre aleatorio
                    random_name = generate_random_name()
                    type_text(random_name)
                    time.sleep(0.5)
                    
                    # Ir al campo de apellido
                    press_key("tab")
                    time.sleep(0.5)
                    
                    # Escribir apellido aleatorio
                    random_lastname = generate_random_lastname()
                    type_text(random_lastname)
                    time.sleep(0.5)
                    
                    # Click en continue_button2_click
                    continue2_coords = coordinates.get("continue_button2_click")
                    if continue2_coords:
                        click_coordinates(continue2_coords)
                        time.sleep(2)
                        
                        # Iniciar observador unificado
                        observador_unificado(coordinates, "zzzdjaewrwerdk435shdsad@mmadasd.com", random_password)
                    

                    
                else:
                    print("⚠️ No se encontraron coordenadas para name_input_click")
            else:
                print("⚠️ No se encontraron coordenadas para continue_button_click")
        else:
            print("⚠️ No se encontraron coordenadas para email_input_click")
    else:
        print("❌ No se encontró la imagen de verificación de LinkedIn")
