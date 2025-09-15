def handle_imagenes_verificacion(coordinates):
    """
    Maneja la lógica de verificación de número y captcha:
    - Si encuentra número: cierra número → clic continuar → evalúa número nuevamente
    - Si encuentra captcha: cierra captcha → clic continuar → espera resolución → evalúa captcha nuevamente
    """
    from app.creator.computer_actions import click_coordinates, wait_for_creator_image
    import time
    
    # Evaluar número primero
    print("🔍 Evaluando número...")
    numero_found = wait_for_creator_image("imagen_numero", max_attempts=15, delay_between_attempts=3)
    
    if numero_found:
        print("✅ Número encontrado")
        
        # Cerrar número
        close_number_coords = coordinates.get("close_number_click")
        if close_number_coords:
            click_coordinates(close_number_coords)
            time.sleep(1)
            
            # Clic en continuar
            continue2_coords = coordinates.get("continue_button2_click")
            if continue2_coords:
                click_coordinates(continue2_coords)
                time.sleep(3)  # Esperar más tiempo después del clic
                
                # Evaluar número nuevamente
                print("🔍 Evaluando número nuevamente...")
                numero_found_again = wait_for_creator_image("imagen_numero", max_attempts=5, delay_between_attempts=2)
                
                if numero_found_again:
                    print("✅ Número encontrado por segunda vez - retornando True")
                    return True
                else:
                    print("ℹ️ Número no encontrado en segunda evaluación, pasando a evaluar captcha")
                    # No retornar False aquí, continuar con la evaluación de captcha
    
    time.sleep(8)
    # Si no encontró número, evaluar captcha
    print("🔍 Evaluando captcha...")
    captcha_found = wait_for_creator_image("imagen_captcha_rojo", max_attempts=15, delay_between_attempts=3)
    
    if captcha_found:
        print("✅ Captcha encontrado")
        
        # Cerrar captcha
        close_captcha_coords = coordinates.get("close_captcha_click")
        if close_captcha_coords:
            click_coordinates(close_captcha_coords)
            time.sleep(1)
            
            # Clic en continuar
            continue2_coords = coordinates.get("continue_button2_click")
            if continue2_coords:
                click_coordinates(continue2_coords)
                time.sleep(2)
                
                # Esperar tiempo para resolver captcha
                print("⏳ Esperando resolución del captcha...")
                time.sleep(10)  # Esperar 10 segundos para resolver captcha
                
                # Evaluar captcha nuevamente
                print("🔍 Evaluando captcha nuevamente...")
                captcha_found_again = wait_for_creator_image("imagen_captcha_rojo", max_attempts=3, delay_between_attempts=1)
                
                if captcha_found_again:
                    print("✅ Captcha encontrado por segunda vez - retornando True")
                    return True
                else:
                    print("ℹ️ Captcha resuelto exitosamente - retornando False")
                    return False
    
    
    print("ℹ️ No se encontró ni número ni captcha")
    return False

def handle_creacion_exitosa(email="test@test.com", password="test123456"):
    """
    Maneja la lógica cuando se crea la cuenta exitosamente
    """
    from app.creator.computer_actions import click_coordinates, wait_for_creator_image, get_clipboard_content
    from app.database.database import get_creator_setting, get_creator_coordinates
    import time
    import os
    from datetime import datetime


    coordinates = get_creator_coordinates()
    if not coordinates:
        print("❌ No se encontraron coordenadas configuradas")
        return
    
    print("🔍 Buscando imagen de creación exitosa...")
    imagen_exitosa_found = wait_for_creator_image("imagen_de_creacion_de_cuenta_con_exito_logo_linkedin", max_attempts=5, delay_between_attempts=2)
    
    if imagen_exitosa_found:
        print("✅ Cuenta creada exitosamente")
        
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
                cookie = get_clipboard_content()
                
                # Obtener user agent desde la base de datos
                creator_settings = get_creator_setting()
                if creator_settings and creator_settings.get('user_agent'):
                    user_agent = creator_settings.get('user_agent')
                else:
                    print("❌ No se encontró user agent en la base de datos")
                    return False
                
                # Crear contenido del archivo con formato correcto (separado por tabs)
                contenido = f"{user_agent}\t{email}\t{password}\t{cookie}"
                
                # Guardar en archivo .txt
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"cuenta_creada_{timestamp}.txt"
                filepath = os.path.join("linkedin_accounts", filename)
                
                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(contenido)
                    print(f"✅ Información guardada en {filepath}")
                except Exception as e:
                    print(f"❌ Error guardando archivo: {e}")
                
                return True
    return False



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
            type_text("askdjahdkja345435shdsad@mmmmmadasd.com")
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
                time.sleep(1)
                
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
                        
                        # Manejar imágenes de verificación (unificadas)
                        imagen_encontrada_dos_veces = handle_imagenes_verificacion(coordinates)
                        
                        # Si se encontró la imagen por segunda vez, hacer clic en close_window
                        if imagen_encontrada_dos_veces:
                            close_window_coords = coordinates.get("close_window")
                            if close_window_coords:
                                click_coordinates(close_window_coords)
                                time.sleep(1)
                        
                        # Manejar creación exitosa
                        handle_creacion_exitosa("askdjahdkjashdsad@asdadasd.com", random_password)
                    

                    
                else:
                    print("⚠️ No se encontraron coordenadas para name_input_click")
            else:
                print("⚠️ No se encontraron coordenadas para continue_button_click")
        else:
            print("⚠️ No se encontraron coordenadas para email_input_click")
    else:
        print("❌ No se encontró la imagen de verificación de LinkedIn")
