def _verificar_cookie_duplicada(filepath, nueva_cookie):
    """
    Verifica si la nueva cookie ya existe en el archivo
    
    Args:
        filepath: Ruta del archivo de cookies
        nueva_cookie: Cookie nueva a verificar
    
    Returns:
        bool: True si la cookie es duplicada, False si es única
    """
    try:
        # Leer las últimas 10 líneas del archivo para verificar duplicados
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Buscar solo en las líneas que contienen datos (saltar encabezados)
        data_lines = []
        for line in lines:
            # Si la línea contiene tabs y no es un encabezado
            if '\t' in line and not line.startswith('CUENTAS') and not line.startswith('=') and not line.startswith('Total') and not line.startswith('Formato'):
                data_lines.append(line.strip())
        
        # Verificar solo las últimas 5 cookies guardadas
        recent_cookies = data_lines[-5:] if len(data_lines) >= 5 else data_lines
        
        for line in recent_cookies:
            parts = line.split('\t')
            if len(parts) >= 4:  # user_agent, email, password, cookie
                existing_cookie = parts[3]
                # Comparar cookies
                if existing_cookie == nueva_cookie:
                    return True
        
        return False
        
    except Exception as e:
        return False  # En caso de error, permitir guardar


def observador_unificado(coordinates, email, password, filepath):
    
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
    timeout_seconds = 60  # 2 minutos
    
    # Contadores para evitar bucles infinitos
    numero_count = 0
    captcha_count = 0
    ciclos_sin_imagen = 0
    # Contador global para cualquier obstáculo (número o captcha)
    obstaculo_count = 0
    
    while True:
        # Verificar si ha pasado el timeout
        elapsed_time = time.time() - start_time
        if elapsed_time > timeout_seconds:
            print("⏰ Timeout de 60 segundos - no se encontraron imágenes, cerrando ventana")
            # Desactivar proxy antes de cerrar por timeout
            _desactivar_proxy()
            close_window_coords = coordinates.get("close_window")
            if close_window_coords:
                click_coordinates(close_window_coords)
                time.sleep(1)
            return False
        
        # Verificar número
        numero_found = wait_for_creator_image("imagen_numero", max_attempts=1, delay_between_attempts=0.5, silent=True)
        
        if numero_found:
            numero_count += 1
            obstaculo_count += 1
            ciclos_sin_imagen = 0  # Resetear contador
            print(f"✅ Número encontrado (vez #{numero_count}) - cerrando")
            
            if obstaculo_count >= 2:
                print("🔄 Segundo obstáculo detectado - cerrando ventana directamente")
                # Desactivar proxy antes de cerrar por segundo obstáculo
                _desactivar_proxy()
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
            obstaculo_count += 1
            ciclos_sin_imagen = 0  # Resetear contador
            print(f"✅ Captcha encontrado (vez #{captcha_count}) - cerrando")
            
            if obstaculo_count >= 2:
                print("🔄 Segundo obstáculo detectado - cerrando ventana directamente")
                # Desactivar proxy antes de cerrar por segundo obstáculo
                _desactivar_proxy()
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
        
        # Verificar imágenes de éxito (cualquiera de las tres)
        exito_found = False
        exito_image_name = None
        
        # Lista de imágenes que indican éxito
        exito_images = [
            "imagen_de_creacion_de_cuenta_con_exito_logo_linkedin",
            "imagen_de_creacion_de_cuenta_con_exito_logo_linkedin_2", 
            "imagen_de_confirmacion_de_codigo",
            "add_location"
        ]
        
        # Buscar cualquiera de las imágenes de éxito
        for image_name in exito_images:
            if wait_for_creator_image(image_name, max_attempts=1, delay_between_attempts=0.5, silent=True):
                exito_found = True
                exito_image_name = image_name
                break
        
        if exito_found:
            ciclos_sin_imagen = 0  # Resetear contador
            print(f"✅ Imagen de éxito encontrada - buscando cookie...")
            
            # Desactivar proxy después del éxito
            _desactivar_proxy()
            
            # Intentar obtener cookie única (máximo 3 intentos)
            max_intentos = 3
            for intento in range(1, max_intentos + 1):
                # Limpiar portapapeles antes de obtener la cookie
                import pyperclip
                pyperclip.copy("")
                time.sleep(0.2)
                
                # Clic en cookie_editor_icon_click
                cookie_editor_coords = coordinates.get("cookie_editor_icon_click")
                if cookie_editor_coords:
                    click_coordinates(cookie_editor_coords)
                    time.sleep(2)
                    
                    # Clic en save_cookie_clipboard_click
                    save_cookie_coords = coordinates.get("save_cookie_clipboard_click")
                    if save_cookie_coords:
                        click_coordinates(save_cookie_coords)
                        time.sleep(1)
                        
                        # Obtener cookie del portapapeles
                        cookie_raw = get_clipboard_content()
                        
                        # Validar que la cookie no esté vacía
                        if not cookie_raw or len(cookie_raw.strip()) < 10:
                            if intento < max_intentos:
                                continue
                            else:
                                return False
                        
                        # Formatear cookie a una sola línea
                        cookie = format_cookie_to_single_line(cookie_raw)
                        
                        # Validar que la cookie formateada sea válida
                        if not cookie or len(cookie.strip()) < 10:
                            if intento < max_intentos:
                                continue
                            else:
                                return False
                        
                        # Verificar que la cookie no sea duplicada
                        if _verificar_cookie_duplicada(filepath, cookie):
                            if intento < max_intentos:
                                print(f"⚠️ Cookie duplicada detectada - intento {intento + 1}/{max_intentos}")
                                time.sleep(1)
                                continue
                            else:
                                print("❌ Cookie duplicada después de todos los intentos")
                                return False
                        
                        # Si llegamos aquí, la cookie es válida y única
                        print("✅ Cookie única guardada")
                        
                        # Obtener user agent desde la base de datos
                        creator_settings = get_creator_setting()
                        if creator_settings and creator_settings.get('user_agent'):
                            user_agent = creator_settings.get('user_agent')
                            
                            # Crear contenido del archivo con formato correcto (separado por tabs)
                            contenido = f"{user_agent}\t{email}\t{password}\t{cookie}"
                            
                            # Agregar al archivo existente (modo append)
                            try:
                                with open(filepath, 'a', encoding='utf-8') as f:
                                    f.write(contenido + "\n")
                                return True
                            except Exception as e:
                                return False
                        else:
                            return False
                    else:
                        return False
                else:
                    return False
            
            return False
        
        # Si no se encontró ninguna imagen, incrementar contador
        if not numero_found and not captcha_found and not exito_found:
            ciclos_sin_imagen += 1
        
        # Pequeña pausa antes del siguiente ciclo
        time.sleep(0.5)


def observador_unificado_con_detalle(coordinates, email, password, filepath):
    """
    Versión mejorada del observador que devuelve información detallada sobre el resultado
    Retorna: (exito: bool, motivo_fallo: str, detalles: dict)
    """
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
    timeout_seconds = 60 # 1 minutos
    
    # Contadores para evitar bucles infinitos
    numero_count = 0
    captcha_count = 0
    ciclos_sin_imagen = 0
    # Contador global para cualquier obstáculo (número o captcha)
    obstaculo_count = 0
    
    while True:
        # Verificar si ha pasado el timeout
        elapsed_time = time.time() - start_time
        if elapsed_time > timeout_seconds:
            print("⏰ Timeout de 60 segundos - no se encontraron imágenes, cerrando ventana")
            # Desactivar proxy antes de cerrar por timeout
            _desactivar_proxy()
            close_window_coords = coordinates.get("close_window")
            if close_window_coords:
                click_coordinates(close_window_coords)
                time.sleep(1)
            return False, "timeout", {"tiempo_transcurrido": elapsed_time, "timeout_seconds": timeout_seconds}
        
        # Verificar número
        numero_found = wait_for_creator_image("imagen_numero", max_attempts=1, delay_between_attempts=0.5, silent=True)
        
        if numero_found:
            numero_count += 1
            obstaculo_count += 1
            ciclos_sin_imagen = 0  # Resetear contador
            print(f"✅ Número encontrado (vez #{numero_count}) - cerrando")
            
            if obstaculo_count >= 2:
                print("🔄 Segundo obstáculo detectado - cerrando ventana directamente")
                # Desactivar proxy antes de cerrar por segundo obstáculo
                _desactivar_proxy()
                close_window_coords = coordinates.get("close_window")
                if close_window_coords:
                    click_coordinates(close_window_coords)
                    time.sleep(1)
                return False, "numero_segundo_obstaculo", {"numero_count": numero_count, "obstaculo_count": obstaculo_count}
            
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
            obstaculo_count += 1
            ciclos_sin_imagen = 0  # Resetear contador
            print(f"✅ Captcha encontrado (vez #{captcha_count}) - cerrando")
            
            if obstaculo_count >= 2:
                print("🔄 Segundo obstáculo detectado - cerrando ventana directamente")
                # Desactivar proxy antes de cerrar por segundo obstáculo
                _desactivar_proxy()
                close_window_coords = coordinates.get("close_window")
                if close_window_coords:
                    click_coordinates(close_window_coords)
                    time.sleep(1)
                return False, "captcha_segundo_obstaculo", {"captcha_count": captcha_count, "obstaculo_count": obstaculo_count}
            
            close_captcha_coords = coordinates.get("close_captcha_click")
            if close_captcha_coords:
                click_coordinates(close_captcha_coords)
                time.sleep(1)
                
                continue2_coords = coordinates.get("continue_button2_click")
                if continue2_coords:
                    click_coordinates(continue2_coords)
                    time.sleep(2)
                    continue
        
        # Verificar imágenes de éxito (cualquiera de las tres)
        exito_found = False
        exito_image_name = None
        
        # Lista de imágenes que indican éxito
        exito_images = [
            "imagen_de_creacion_de_cuenta_con_exito_logo_linkedin",
            "imagen_de_creacion_de_cuenta_con_exito_logo_linkedin_2", 
            "imagen_de_confirmacion_de_codigo",
            "add_location"
        ]
        
        # Buscar cualquiera de las imágenes de éxito
        for image_name in exito_images:
            if wait_for_creator_image(image_name, max_attempts=1, delay_between_attempts=0.5, silent=True):
                exito_found = True
                exito_image_name = image_name
                break
        
        if exito_found:
            ciclos_sin_imagen = 0  # Resetear contador
            print(f"✅ Imagen de éxito encontrada - buscando cookie...")
            
            # Desactivar proxy después del éxito
            _desactivar_proxy()
            
            # Intentar obtener cookie única (máximo 3 intentos)
            max_intentos = 3
            for intento in range(1, max_intentos + 1):
                # Limpiar portapapeles antes de obtener la cookie
                import pyperclip
                pyperclip.copy("")
                time.sleep(0.2)
                
                # Clic en cookie_editor_icon_click
                cookie_editor_coords = coordinates.get("cookie_editor_icon_click")
                if cookie_editor_coords:
                    click_coordinates(cookie_editor_coords)
                    time.sleep(2)
                    
                    # Clic en save_cookie_clipboard_click
                    save_cookie_coords = coordinates.get("save_cookie_clipboard_click")
                    if save_cookie_coords:
                        click_coordinates(save_cookie_coords)
                        time.sleep(1)
                        
                        # Obtener cookie del portapapeles
                        cookie_raw = get_clipboard_content()
                        
                        # Validar que la cookie no esté vacía
                        if not cookie_raw or len(cookie_raw.strip()) < 10:
                            if intento < max_intentos:
                                continue
                            else:
                                return False, "cookie_vacia", {"intento": intento, "max_intentos": max_intentos}
                        
                        # Formatear cookie a una sola línea
                        cookie = format_cookie_to_single_line(cookie_raw)
                        
                        # Validar que la cookie formateada sea válida
                        if not cookie or len(cookie.strip()) < 10:
                            if intento < max_intentos:
                                continue
                            else:
                                return False, "cookie_invalida", {"intento": intento, "max_intentos": max_intentos}
                        
                        # Verificar que la cookie no sea duplicada
                        if _verificar_cookie_duplicada(filepath, cookie):
                            if intento < max_intentos:
                                print(f"⚠️ Cookie duplicada detectada - intento {intento + 1}/{max_intentos}")
                                time.sleep(1)
                                continue
                            else:
                                print("❌ Cookie duplicada después de todos los intentos")
                                return False, "cookie_duplicada", {"intento": intento, "max_intentos": max_intentos}
                        
                        # Si llegamos aquí, la cookie es válida y única
                        print("✅ Cookie única guardada")
                        
                        # Obtener user agent desde la base de datos
                        creator_settings = get_creator_setting()
                        if creator_settings and creator_settings.get('user_agent'):
                            user_agent = creator_settings.get('user_agent')
                            
                            # Crear contenido del archivo con formato correcto (separado por tabs)
                            contenido = f"{user_agent}\t{email}\t{password}\t{cookie}"
                            
                            # Agregar al archivo existente (modo append)
                            try:
                                with open(filepath, 'a', encoding='utf-8') as f:
                                    f.write(contenido + "\n")
                                return True, "exito", {"imagen_exito": exito_image_name, "intento": intento}
                            except Exception as e:
                                return False, "error_escritura_archivo", {"error": str(e)}
                        else:
                            return False, "user_agent_no_encontrado", {}
                    else:
                        return False, "coordenadas_save_cookie_no_encontradas", {}
                else:
                    return False, "coordenadas_cookie_editor_no_encontradas", {}
            
            return False, "max_intentos_cookie", {"max_intentos": max_intentos}
        
        # Si no se encontró ninguna imagen, incrementar contador
        if not numero_found and not captcha_found and not exito_found:
            ciclos_sin_imagen += 1
        
        # Pequeña pausa antes del siguiente ciclo
        time.sleep(0.5)


def procesar_email_individual(email_id, coordinates, filepath, contador, total):
    """
    Procesa un email individual en el proceso de creación de cuenta LinkedIn
    """
    from app.database.database import get_creator_email_by_id
    from app.creator.computer_actions import click_coordinates, wait_for_creator_image, type_text, press_key, generate_random_password, generate_random_name, generate_random_lastname
    import time
    
    # Obtener el email por ID
    current_email = get_creator_email_by_id(email_id)
    if not current_email:
        print(f"⚠️ Email ID {email_id} no encontrado")
        return False
    
    # Paso 1: Click en Brave
    if not _click_brave(coordinates):
        return False
    
    # Paso 2: Click en LinkedIn fav
    if not _click_linkedin_fav(coordinates):
        return False
    
    # Paso 3: Verificar carga de LinkedIn
    if not _verificar_carga_linkedin():
        return False
    
    # Paso 4: Llenar formulario de registro
    if not _llenar_formulario_registro(coordinates, current_email):
        return False
    
    # Paso 5: Observar y crear cuenta
    cuenta_creada = observador_unificado(coordinates, current_email, _get_password_usado(), filepath)
    
    # Paso 6: Cerrar ventana si se creó exitosamente
    if cuenta_creada:
        _cerrar_ventana(coordinates)
        return True
    else:
        return False


def procesar_email_individual_con_detalle(email_id, coordinates, filepath, contador, total):
    """
    Procesa un email individual en el proceso de creación de cuenta LinkedIn con información detallada
    Retorna: (exito: bool, motivo_fallo: str, detalles: dict)
    """
    from app.database.database import get_creator_email_by_id
    from app.creator.computer_actions import click_coordinates, wait_for_creator_image, type_text, press_key, generate_random_password, generate_random_name, generate_random_lastname
    import time
    
    # Obtener el email por ID
    current_email = get_creator_email_by_id(email_id)
    if not current_email:
        print(f"⚠️ Email ID {email_id} no encontrado")
        return False, "email_no_encontrado", {"email_id": email_id}
    
    # Paso 1: Click en Brave
    if not _click_brave(coordinates):
        return False, "error_click_brave", {}
    
    # Paso 2: Click en LinkedIn fav
    if not _click_linkedin_fav(coordinates):
        return False, "error_click_linkedin_fav", {}
    
    # Paso 3: Verificar carga de LinkedIn
    if not _verificar_carga_linkedin():
        return False, "error_carga_linkedin", {}
    
    # Paso 4: Llenar formulario de registro
    if not _llenar_formulario_registro(coordinates, current_email):
        return False, "error_llenar_formulario", {}
    
    # Paso 5: Observar y crear cuenta con detalle
    exito, motivo_fallo, detalles = observador_unificado_con_detalle(coordinates, current_email, _get_password_usado(), filepath)
    
    # Paso 6: Cerrar ventana si se creó exitosamente
    if exito:
        _cerrar_ventana(coordinates)
        return True, "exito", detalles
    else:
        return False, motivo_fallo, detalles


def _click_brave(coordinates):
    """Hace clic en Brave"""
    from app.creator.computer_actions import click_coordinates
    import time
    
    brave_coords = coordinates.get("brave_click")
    if not brave_coords:
        return False
    
    click_coordinates(brave_coords, double_click=True)
    time.sleep(1)
    return True


def _click_linkedin_fav(coordinates):
    """Hace clic en el favorito de LinkedIn"""
    from app.creator.computer_actions import click_coordinates
    import time
    
    linkedin_coords = coordinates.get("linkedin_fav_click")
    if not linkedin_coords:
        return False
    
    click_coordinates(linkedin_coords)
    time.sleep(3)
    return True


def _verificar_carga_linkedin():
    """Verifica que LinkedIn haya cargado correctamente"""
    from app.creator.computer_actions import wait_for_creator_image
    
    verification_image = wait_for_creator_image("imagen_de_verificacion_de_exito_carga_linkedin", max_attempts=15, delay_between_attempts=1)
    if not verification_image:
        return False
    return True


def _escribir_y_verificar_email(email, max_intentos=3):
    """
    Escribe el email y verifica que se haya pegado correctamente.
    Reintenta hasta 3 veces si no se pega correctamente.
    """
    from app.creator.computer_actions import type_text
    import time
    import pyperclip
    
    for intento in range(max_intentos):
        print(f"📧 Intentando escribir email (intento {intento + 1}/{max_intentos}): {email}")
        
        # Limpiar el campo primero
        pyperclip.copy("")
        time.sleep(0.1)
        
        # Seleccionar todo el texto en el campo
        import pyautogui
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        
        # Escribir el email
        success = type_text(email)
        if not success:
            print(f"⚠️ Error en type_text, intento {intento + 1}")
            time.sleep(0.5)
            continue
        
        # Esperar un poco más para que se complete la operación
        time.sleep(0.8)
        
        # Verificar que el email se haya pegado correctamente
        if _verificar_email_pegado(email):
            print(f"✅ Email pegado correctamente: {email}")
            return True
        else:
            print(f"⚠️ Email no se pegó correctamente, reintentando...")
            time.sleep(0.5)
    
    print(f"❌ No se pudo pegar el email después de {max_intentos} intentos")
    return False


def _verificar_email_pegado(email_esperado):
    """
    Verifica que el email se haya pegado correctamente en el campo.
    Lee el contenido del portapapeles después de seleccionar todo el texto del campo.
    """
    import pyperclip
    import pyautogui
    import time
    
    try:
        # Seleccionar todo el texto en el campo actual
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        
        # Copiar el texto seleccionado
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.3)
        
        # Leer el contenido del portapapeles
        texto_pegado = pyperclip.paste()
        
        # Verificar si el email está en el texto pegado
        if email_esperado in texto_pegado:
            return True
        else:
            print(f"🔍 Verificación fallida - Esperado: '{email_esperado}', Obtenido: '{texto_pegado}'")
            return False
            
    except Exception as e:
        print(f"⚠️ Error verificando email pegado: {e}")
        return False


def _llenar_formulario_registro(coordinates, email):
    """Llena el formulario de registro de LinkedIn"""
    from app.creator.computer_actions import click_coordinates, type_text, press_key, generate_random_password, generate_random_name, generate_random_lastname, wait_for_creator_image
    import time
    import pyperclip
    
    # Click en email_input_click
    email_coords = coordinates.get("email_input_click")
    if not email_coords:
        return False
    
    click_coordinates(email_coords)
    time.sleep(0.5)
    
    # Limpiar portapapeles antes de escribir email
    pyperclip.copy("")
    time.sleep(0.2)
    
    # Escribir email con verificación
    if not _escribir_y_verificar_email(email):
        print("❌ Error: No se pudo escribir el email correctamente")
        return False
    
    # Ir al campo de contraseña
    press_key("tab")
    time.sleep(0.5)
    
    # Escribir contraseña aleatoria
    password = generate_random_password()
    type_text(password)
    time.sleep(0.5)
    
    checkbox_found = wait_for_creator_image("Checkbox recuerdame", max_attempts=1, delay_between_attempts=0.5, silent=True)
    
    if checkbox_found:
        # Si encuentra el checkbox, usar continue_button_click
        continue_coords = coordinates.get("continue_button_click")
        if not continue_coords:
            return False
        click_coordinates(continue_coords)
    else:
        # Si no encuentra el checkbox, usar continue_button_click_optional
        continue_coords = coordinates.get("continue_button_click_optional")
        if not continue_coords:
            return False
        click_coordinates(continue_coords)
    
    time.sleep(2)
    
    # Click en name_input_click
    name_coords = coordinates.get("name_input_click")
    if not name_coords:
        return False
    
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
    
    # Activar proxy antes de hacer clic en continue_button2_click
    _activar_proxy()
    
    # Click en continue_button2_click
    continue2_coords = coordinates.get("continue_button2_click")
    if not continue2_coords:
        return False
    
    click_coordinates(continue2_coords)
    time.sleep(2)
    
    # Guardar password para uso posterior
    global _password_usado
    _password_usado = password
    return True


def _get_password_usado():
    """Obtiene el password usado en el formulario"""
    global _password_usado
    return _password_usado


def _cerrar_ventana(coordinates):
    """Cierra la ventana después de crear la cuenta exitosamente"""
    from app.creator.computer_actions import click_coordinates
    import time
    
    close_window_coords = coordinates.get("close_window")
    if close_window_coords:
        click_coordinates(close_window_coords)
        time.sleep(2)


def _ejecutar_modo_avion():
    """Ejecuta el modo avión si está disponible"""
    import os
    import subprocess
    import time
    from app.database.database import get_bot_settings
    
    config = get_bot_settings()
    
    # Ruta del ejecutable ADB - verificar si existe
    adb_path = r"C:\Adb\adb.exe"
    adb_available = os.path.exists(adb_path)
    
    if not adb_available:
        return
    
    # Ejecutar comandos ADB solo si está disponible y habilitado
    enable_adb = config.get("enable_adb", True)
    if adb_available and enable_adb:
        try:
            # Ejecutar el comando para activar el modo avión
            subprocess.run([adb_path, "shell", "cmd", "connectivity", "airplane-mode", "enable"], 
                            capture_output=True, text=True, timeout=10)
            print("########################################################")
            print("✈️ Modo avión activado")
            time.sleep(3)

            # Ejecutar el comando para desactivar el modo avión
            subprocess.run([adb_path, "shell", "cmd", "connectivity", "airplane-mode", "disable"], 
                            capture_output=True, text=True, timeout=10)
            print("📶 Modo avión desactivado")
            time.sleep(3)
        except Exception as e:
            pass
    else:
        print("❌ Modo avión no activado")
        time.sleep(2)


def _activar_proxy():
    """Activa el proxy si está habilitado en la configuración"""
    import time
    from app.database.database import get_bot_settings
    from app.confirmabot.utils.proxy_tool import ProxyController
    
    config = get_bot_settings()
    enable_proxy = config.get("enable_proxy", True)
    
    if enable_proxy:
        try:
            print("🌐 Activando proxy...")
            proxy_controller = ProxyController()
            try:
                # Solo activar el proxy sin cambiar la configuración existente
                proxy_controller.enable_proxy_only()
                proxy_controller.refresh_internet_settings()
                
                # Verificar que el proxy esté realmente activo
                print("🔍 Verificando que el proxy esté activado...")
                enabled, server, port = proxy_controller.get_proxy_status()
                if enabled and server:
                    print(f"✅ Proxy confirmado activado: {server}")
                else:
                    print("⚠️ Proxy no se activó correctamente, reintentando...")
                    proxy_controller.enable_proxy_only()
                    proxy_controller.refresh_internet_settings()
                    time.sleep(3)  # Esperar más tiempo en el segundo intento
                    
            finally:
                proxy_controller.close()
        except Exception as e:
            print(f"❌ Error al activar proxy: {e}")
    else:
        print("❌ Proxy no habilitado en configuración")


def _desactivar_proxy():
    """Desactiva el proxy si está habilitado en la configuración"""
    import time
    from app.database.database import get_bot_settings
    from app.confirmabot.utils.proxy_tool import ProxyController
    
    config = get_bot_settings()
    enable_proxy = config.get("enable_proxy", True)
    
    if enable_proxy:
        try:
            print("🌐 Desactivando proxy...")
            proxy_controller = ProxyController()
            try:
                proxy_controller.disable_proxy()
                proxy_controller.refresh_internet_settings()
                print("✅ Proxy desactivado exitosamente")
            finally:
                proxy_controller.close()
            time.sleep(1)  # Esperar un momento para que el proxy se desactive
        except Exception as e:
            print(f"❌ Error al desactivar proxy: {e}")
    else:
        print("❌ Proxy no habilitado en configuración")


def _actualizar_encabezado_con_exitos(filepath, total_emails, emails_exitosos):
    """Actualiza el encabezado del archivo con la información de éxitos"""
    from datetime import datetime
    
    try:
        # Leer el contenido actual del archivo
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Crear nuevo encabezado con información de éxitos
        fecha_hora = datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')
        nuevo_encabezado = [
            f"CUENTAS LINKEDIN CREADAS - {fecha_hora}\n",
            "="*60 + "\n",
            f"Total de emails a procesar: {total_emails}\n",
            f"Emails procesados con éxito: {emails_exitosos}\n",
            f"Emails fallidos: {total_emails - emails_exitosos}\n",
            "Formato: User-Agent | Email | Password | Cookie\n",
            "="*60 + "\n\n"
        ]
        
        # Encontrar donde empiezan las cuentas (después del segundo separador)
        inicio_cuentas = 0
        separadores_encontrados = 0
        for i, line in enumerate(lines):
            if line.strip() == "="*60:
                separadores_encontrados += 1
                if separadores_encontrados == 2:  # Segundo separador
                    inicio_cuentas = i + 2  # Saltar las líneas de separación
                    break
        
        # Escribir el archivo actualizado
        with open(filepath, 'w', encoding='utf-8') as f:
            # Escribir nuevo encabezado
            f.writelines(nuevo_encabezado)
            # Escribir las cuentas existentes
            if inicio_cuentas < len(lines):
                f.writelines(lines[inicio_cuentas:])
                
    except Exception as e:
        pass


def _inicializar_archivo_salida(total_emails):
    """Inicializa el archivo de salida para el bucle"""
    import os
    from datetime import datetime
    from app.utils.path_utils import get_linkedin_accounts_path, ensure_directory_exists
    
    # Crear carpeta linkedin_accounts si no existe (al lado del ejecutable)
    folder_path = get_linkedin_accounts_path()
    ensure_directory_exists(folder_path)
    
    # Crear un solo archivo para todo el bucle
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"cuentas_creadas_bucle_{timestamp}.txt"
    filepath = os.path.join(folder_path, filename)
    
    # Escribir encabezado del archivo
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            fecha_hora = datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')
            f.write(f"CUENTAS LINKEDIN CREADAS - {fecha_hora}\n")
            f.write("="*60 + "\n")
            f.write(f"Total de emails a procesar: {total_emails}\n")
            f.write("Formato: User-Agent | Email | Password | Cookie\n")
            f.write("="*60 + "\n\n")
        return filepath
    except Exception as e:
        return None


def _verificar_hora_programada():
    """
    Verifica si hay una hora programada y espera hasta esa hora si es necesario.
    
    Returns:
        bool: True si debe continuar con el proceso, False si debe detenerse
    """
    from app.database.database import get_creator_setting
    import time
    import datetime
    import pytz
    import re
    
    settings = get_creator_setting()
    if not settings:
        print("⚡ No hay configuración de tiempo, ejecutando inmediatamente")
        return True  # No hay configuración, continuar inmediatamente
    
    # Solo verificar hora programada si el tipo de configuración es 'scheduled' o 'both'
    time_config_type = settings.get('time_config_type')
    if time_config_type not in ['scheduled', 'both']:
        print("⚡ Configuración de ciclo de tiempo, ejecutando inmediatamente")
        return True  # No es configuración programada, continuar inmediatamente
    
    # Verificar si hay hora programada configurada
    if not settings.get('scheduled_time') or not settings.get('timezone'):
        print("⚡ No hay hora programada configurada, ejecutando inmediatamente")
        return True  # No hay hora programada, continuar inmediatamente
    
    scheduled_time = settings.get('scheduled_time')
    timezone_str = settings.get('timezone')
    
    print(f"🕐 Hora programada configurada: {scheduled_time} ({timezone_str})")
    
    try:
        # Extraer el offset GMT del string del país
        offset_match = re.search(r'GMT([+-]\d{1,2}(?::\d{2})?)', timezone_str)
        if not offset_match:
            return True  # No se pudo parsear, continuar inmediatamente
        
        offset_str = offset_match.group(1)
        
        # Manejar formato GMT+5:30 (India)
        if ':' in offset_str:
            hours, minutes = offset_str.split(':')
            offset_hours = int(hours) + (int(minutes) / 60)
        else:
            offset_hours = int(offset_str)
        
        # Crear zona horaria personalizada
        custom_tz = pytz.FixedOffset(offset_hours * 60)
        
        # Obtener hora actual y objetivo
        now = datetime.datetime.now(custom_tz)
        target_hour, target_minute = map(int, scheduled_time.split(':'))
        target_datetime = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
        
        # Si la hora ya pasó hoy, programar para mañana
        if target_datetime <= now:
            target_datetime += datetime.timedelta(days=1)
        
        # Calcular tiempo de espera
        wait_seconds = (target_datetime - now).total_seconds()
        
        if wait_seconds > 0:
            wait_hours = wait_seconds / 3600
            print(f"⏳ Esperando {wait_hours:.1f}h para iniciar...")
            
            # Esperar hasta la hora programada
            time.sleep(wait_seconds)
            print("🚀 ¡Iniciando proceso!")
        
        return True
        
    except Exception as e:
        print(f"⚠️ Error en hora programada: {e}")
        return True  # En caso de error, continuar inmediatamente


def _enviar_archivo_por_correo(filepath, total_emails, emails_exitosos, cuentas_fallidas=None, es_ciclo=False, ciclo_minutes=None):
    try:
        from app.confirmabot.hostinger_actions import send_email_with_file
        from app.database.database import get_creator_setting, get_all_emails, get_user_data
        from app.utils.http_utils import post
        import os
        from datetime import datetime, timedelta
        import json
        
        # Obtener credenciales de correo
        emails_data = get_all_emails()
        if not emails_data:
            return False
        
        # Buscar email con credenciales de Hostinger
        email_address = None
        email_password = None
        for email_data in emails_data:
            if email_data.get('email_hostinger') and email_data.get('password_hostinger'):
                email_address = email_data['email_hostinger']
                email_password = email_data['password_hostinger']
                break
        
        if not email_address or not email_password:
            return False
        
        # Verificar archivo
        if not os.path.exists(filepath):
            return False
        
        # Obtener email de destino
        settings = get_creator_setting()
        email_destino = settings.get('notification_email') if settings else None
        
        if not email_destino:
            return True  # No hay email configurado, continuar
        
        # Guardar cuentas en base de datos del servidor primero
        cuentas_guardadas = _guardar_cuentas_en_servidor(filepath)
        
        # Obtener conteo total de cuentas en el servidor
        total_cuentas_servidor = _obtener_conteo_cuentas_servidor()
        
        # Preparar correo
        fecha_hora = datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')
        asunto = f"Reporte LinkedIn Creator - {fecha_hora}"
        
        # Calcular estadísticas reales
        emails_fallidos = len(cuentas_fallidas) if cuentas_fallidas else 0
        total_emails_solicitados = emails_exitosos + emails_fallidos
        tasa_exito_real = (emails_exitosos / total_emails_solicitados * 100) if total_emails_solicitados > 0 else 0
        
        # Calcular próxima ejecución si es ciclo
        proxima_ejecucion = ""
        if es_ciclo and ciclo_minutes:
            proxima = datetime.now() + timedelta(minutes=ciclo_minutes)
            proxima_ejecucion = f"\n            ⏰ PRÓXIMO CICLO:\n            - Iniciará a las: {proxima.strftime('%H:%M:%S')}\n"
        
        cuerpo = f"""Hola,

            El proceso de creación de cuentas LinkedIn ha finalizado.

            📊 RESUMEN DEL PROCESO:
            - Total de emails solicitados del servidor: {total_emails_solicitados}
            - Cuentas creadas exitosamente: {emails_exitosos}
            - Cuentas que fallaron: {emails_fallidos}
            - Tasa de éxito real: {tasa_exito_real:.1f}%
            
            {proxima_ejecucion}
            Saludos,
            ConfirmaBot
        """
        
        # Enviar correo sin archivo adjunto
        exito = _enviar_correo_sin_adjunto(
            email_address=email_address,
            password=email_password,
            to_email=email_destino,
            subject=asunto,
            body=cuerpo
        )
        
        if exito:
            print(f"📧 Reporte enviado: {emails_exitosos}/{total_emails_solicitados} cuentas")
        
        return exito
            
    except Exception as e:
        return False


def _enviar_correo_sin_adjunto(email_address: str, password: str, to_email: str, 
                               subject: str, body: str) -> bool:
    """
    Envía un correo sin archivo adjunto usando las credenciales de Hostinger
    """
    try:
        from app.confirmabot.hostinger_actions import HostingerEmailClient
        
        # Crear cliente de correo
        email_client = HostingerEmailClient(email_address, password)
        
        # Conectar al servidor
        if not email_client.connect():
            print("❌ Error al conectar con el servidor de correo")
            return False
        
        # Enviar correo
        success = email_client.send_email(to_email, subject, body)
        
        # Desconectar
        email_client.disconnect()
        
        return success
        
    except Exception as e:
        print(f"❌ Error al enviar correo: {e}")
        return False


def _enviar_notificacion_inicio_ciclo(ciclo_numero: int, objetivo_cuentas: int, ciclo_minutes: int):
    """
    Envía una notificación por email al inicio de cada ciclo
    """
    try:
        from app.database.database import get_creator_setting, get_all_emails
        from datetime import datetime, timedelta
        
        # Obtener credenciales de correo
        emails_data = get_all_emails()
        if not emails_data:
            return False
        
        # Buscar email con credenciales de Hostinger
        email_address = None
        email_password = None
        for email_data in emails_data:
            if email_data.get('email_hostinger') and email_data.get('password_hostinger'):
                email_address = email_data['email_hostinger']
                email_password = email_data['password_hostinger']
                break
        
        if not email_address or not email_password:
            return False
        
        # Obtener email de destino
        settings = get_creator_setting()
        email_destino = settings.get('notification_email') if settings else None
        
        if not email_destino:
            return True  # No hay email configurado, continuar
        
        # Preparar correo
        fecha_hora = datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')
        asunto = f"Inicio Ciclo #{ciclo_numero} - LinkedIn Creator"
        
        # Calcular hora estimada de finalización
        hora_finalizacion = datetime.now() + timedelta(minutes=ciclo_minutes)
        hora_fin = hora_finalizacion.strftime('%H:%M:%S')
        
        cuerpo = f"""Hola,

            🔄 CICLO #{ciclo_numero} INICIADO

            📊 INFORMACIÓN DEL CICLO:
            - Hora de inicio: {fecha_hora}
            - Objetivo: {objetivo_cuentas} cuentas

            🎯 El bot está procesando las cuentas...
            Te notificaremos cuando termine este ciclo.

            Saludos,
            ConfirmaBot
            """
        
        # Enviar correo
        exito = _enviar_correo_sin_adjunto(
            email_address=email_address,
            password=email_password,
            to_email=email_destino,
            subject=asunto,
            body=cuerpo
        )
        
        if exito:
            print(f"📧 Notificación de inicio de ciclo #{ciclo_numero} enviada")
        
        return exito
            
    except Exception as e:
        print(f"❌ Error al enviar notificación de inicio de ciclo: {e}")
        return False


def _obtener_conteo_cuentas_servidor():
    """
    Obtiene el conteo total de cuentas en la base de datos del servidor
    """
    try:
        from app.database.database import get_user_data
        from app.utils.http_utils import post
        import json
        
        # Obtener datos del usuario logueado
        user_data = get_user_data()
        if not user_data:
            print("❌ No se encontraron datos del usuario logueado")
            return 0
        
        user_id = user_data.get('id')
        access_token = user_data.get('access_token')
        
        if not user_id or not access_token:
            print("❌ Faltan datos del usuario (ID o access_token)")
            return 0
        
        # Preparar datos para el servidor
        payload = {
            "access_token": access_token
        }
        
        # URL del servidor
        url = f"http://35.209.237.44/api/accounts/count/{user_id}"
        
        # Headers
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Enviar petición al servidor
        response = post(url, body=payload, headers=headers)
        
        if response:
            try:
                response_data = response.json()
                account_count = response_data.get('account_count', 0)
                print(f"📊 Total de cuentas en servidor: {account_count}")
                return account_count
            except json.JSONDecodeError:
                print("❌ Error al procesar respuesta del servidor")
                return 0
        else:
            print("❌ Error al conectar con el servidor")
            return 0
            
    except Exception as e:
        print(f"❌ Error al obtener conteo de cuentas: {e}")
        return 0


def _guardar_cuentas_en_servidor(filepath):
    """
    Guarda las cuentas creadas en la base de datos del servidor
    """
    try:
        from app.database.database import get_user_data
        from app.utils.http_utils import post
        import json
        
        # Obtener datos del usuario logueado
        user_data = get_user_data()
        if not user_data:
            print("❌ No se encontraron datos del usuario logueado")
            return False
        
        user_id = user_data.get('id')
        access_token = user_data.get('access_token')
        
        if not user_id or not access_token:
            print("❌ Faltan datos del usuario (ID o access_token)")
            return False
        
        # Leer y parsear el archivo de cuentas
        accounts = _leer_cuentas_del_archivo(filepath)
        if not accounts:
            print("❌ No se encontraron cuentas en el archivo")
            return False
        
        # Preparar datos para el servidor
        payload = {
            "access_token": access_token,
            "accounts": accounts
        }
        
        # URL del servidor
        url = f"http://35.209.237.44/api/accounts/save/{user_id}"
        
        # Headers
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Enviar petición al servidor
        response = post(url, body=payload, headers=headers)
        
        if response:
            try:
                response_data = response.json()
                saved_count = response_data.get('saved_count', 0)
                duplicate_count = response_data.get('duplicate_count', 0)
                total_processed = response_data.get('total_processed', 0)
                
                print(f"💾 Cuentas guardadas en servidor: {saved_count} nuevas, {duplicate_count} duplicadas")
                return True
            except json.JSONDecodeError:
                print("❌ Error al procesar respuesta del servidor")
                return False
        else:
            print("❌ Error al conectar con el servidor")
            return False
            
    except Exception as e:
        print(f"❌ Error al guardar cuentas en servidor: {e}")
        return False


def _guardar_cuentas_fallidas_en_servidor(cuentas_fallidas):
    """
    Guarda las cuentas fallidas en la base de datos del servidor
    """
    try:
        from app.database.database import get_user_data
        from app.utils.http_utils import post
        import json
        
        if not cuentas_fallidas:
            print("📝 No hay cuentas fallidas para guardar")
            return True
        
        # Obtener datos del usuario logueado
        user_data = get_user_data()
        if not user_data:
            print("❌ No se encontraron datos del usuario logueado")
            return False
        
        user_id = user_data.get('id')
        access_token = user_data.get('access_token')
        
        if not user_id or not access_token:
            print("❌ Faltan datos del usuario (ID o access_token)")
            return False
        
        # Extraer solo los emails de las cuentas fallidas
        emails_fallidos = [cuenta['email'] for cuenta in cuentas_fallidas]
        
        # Preparar datos para el servidor (formato correcto)
        payload = {
            "access_token": access_token,
            "emails": emails_fallidos
        }
        
        # URL del servidor para emails fallidos
        url = f"http://35.209.237.44/api/emails/save/{user_id}"
        
        # Headers
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Enviar petición al servidor
        response = post(url, body=payload, headers=headers)
        
        if response:
            try:
                response_data = response.json()
                saved_count = response_data.get('saved_count', 0)
                total_processed = response_data.get('total_processed', 0)
                
                print(f"💾 Emails fallidos guardados en servidor: {saved_count}")
                return True
            except json.JSONDecodeError:
                print("❌ Error al procesar respuesta del servidor")
                return False
        else:
            print("❌ Error al conectar con el servidor")
            return False
            
    except Exception as e:
        print(f"❌ Error al guardar emails fallidos en servidor: {e}")
        return False


def _leer_cuentas_del_archivo(filepath):
    """
    Lee las cuentas del archivo y las convierte al formato requerido por el servidor
    """
    try:
        accounts = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Buscar las líneas que contienen datos de cuentas (saltar encabezados)
        for line in lines:
            line = line.strip()
            # Si la línea contiene tabs y no es un encabezado
            if '\t' in line and not line.startswith('CUENTAS') and not line.startswith('=') and not line.startswith('Total') and not line.startswith('Formato'):
                parts = line.split('\t')
                if len(parts) >= 4:  # user_agent, email, password, cookie
                    user_agent = parts[0].strip()
                    email = parts[1].strip()
                    password = parts[2].strip()
                    cookie = parts[3].strip()
                    
                    # Agregar cuenta al array
                    account = {
                        "user_agent": user_agent,
                        "email": email,
                        "password": password,
                        "cookie": cookie
                    }
                    accounts.append(account)
        
        return accounts
        
    except Exception as e:
        print(f"❌ Error al leer archivo de cuentas: {e}")
        return []


def execute_creator():
    """
    Función principal del creator que ejecuta todas las acciones
    """
    from app.database.database import get_creator_setting
    import time
    
    global _password_usado
    _password_usado = ""
    
    settings = get_creator_setting()
    if not settings:
        print("❌ Sin configuración")
        return
    
    time_config_type = settings.get('time_config_type', 'manual')
    scheduled_time = settings.get('scheduled_time')
    cycle_time_minutes = settings.get('cycle_time_minutes', 60)
    
    has_scheduled = scheduled_time and scheduled_time.strip()
    has_cycle = cycle_time_minutes and cycle_time_minutes > 0
    
    # Determinar modo de ejecución
    if has_scheduled and has_cycle:
        print("🔄 Ciclo + Hora programada")
        if not _verificar_hora_programada():
            return
        _ejecutar_creator_en_ciclo()
    elif has_cycle:
        print("🔄 Solo ciclo")
        _ejecutar_creator_en_ciclo()
    elif has_scheduled:
        print("🕐 Solo hora programada")
        if not _verificar_hora_programada():
            return
        _ejecutar_proceso_creator()
    else:
        print("👤 Modo manual")
        _ejecutar_proceso_creator()


def _ejecutar_proceso_creator():
    """
    Ejecuta el proceso de creación de cuentas una sola vez
    """
    from app.database.database import (
        get_creator_coordinates, get_all_available_creator_emails, get_next_creator_emails, 
        get_creator_setting, update_creator_email_progress, fetch_and_save_emails_for_cycle,
        reset_creator_email_progress
    )
    import time
    
    settings = get_creator_setting()
    time_config_type = settings.get('time_config_type', 'manual')
    
    # Obtener emails según configuración
    if time_config_type in ['cycle', 'both']:
        accounts_per_cycle = settings.get('accounts_per_cycle', 1)
        email_ids = get_next_creator_emails(accounts_per_cycle)
        print(f"🔄 Procesando {accounts_per_cycle} cuentas")
    else:
        print("🌐 Obteniendo emails del servidor...")
        resultado = fetch_and_save_emails_for_cycle(100)
        
        if resultado == "NO_EMAILS_AVAILABLE":
            print("📭 No hay más emails disponibles en el servidor")
            # Mostrar messagebox y detener el bot
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showwarning(
                "Sin Emails Disponibles", 
                "Te quedaste sin emails en la base de datos.\n\nEl bot se detendrá."
            )
            root.destroy()
            return False
        elif not resultado:
            print("❌ Error al obtener emails")
            return False
            
        email_ids = get_all_available_creator_emails()
        print(f"🔄 Procesando {len(email_ids)} cuentas")
    
    if not email_ids:
        print("❌ Sin emails disponibles")
        reset_creator_email_progress()
        return False
    
    coordinates = get_creator_coordinates()
    if not coordinates:
        print("❌ Sin coordenadas")
        return
    
    filepath = _inicializar_archivo_salida(len(email_ids))
    if not filepath:
        return
    
    # Procesar emails
    emails_exitosos = 0
    cuentas_fallidas = []
    
    for i, email_id in enumerate(email_ids, 1):
        _ejecutar_modo_avion()
        print(f"📧 {i}/{len(email_ids)}")
        
        exito, motivo_fallo, detalles = procesar_email_individual_con_detalle(email_id, coordinates, filepath, i, len(email_ids))
        
        if exito:
            emails_exitosos += 1
            print(f"✅ Completado")
        else:
            print(f"❌ Falló - {motivo_fallo}")
            # Agregar a la lista de cuentas fallidas
            from app.database.database import get_creator_email_by_id
            from app.database.database import get_creator_setting
            from datetime import datetime
            
            current_email = get_creator_email_by_id(email_id)
            creator_settings = get_creator_setting()
            user_agent = creator_settings.get('user_agent', '') if creator_settings else ''
            
            cuenta_fallida = {
                "email": current_email if current_email else f"email_id_{email_id}",
                "password": _get_password_usado(),
                "user_agent": user_agent,
                "motivo_fallo": motivo_fallo,
                "detalles": detalles,
                "fecha_fallo": datetime.now().isoformat(),
                "contador": i,
                "total": len(email_ids)
            }
            cuentas_fallidas.append(cuenta_fallida)
        
        update_creator_email_progress(email_id, emails_exitosos)
        if i < len(email_ids):
            time.sleep(1)
    
    print(f"🎉 Completado: {emails_exitosos}/{len(email_ids)}")
    _actualizar_encabezado_con_exitos(filepath, len(email_ids), emails_exitosos)
    
    # Guardar cuentas fallidas en el servidor
    if cuentas_fallidas:
        print(f"💾 Guardando {len(cuentas_fallidas)} cuentas fallidas en el servidor...")
        print("📧 EMAILS FALLIDOS:")
        for i, cuenta in enumerate(cuentas_fallidas, 1):
            print(f"  {i}. {cuenta['email']} - {cuenta['motivo_fallo']}")
        _guardar_cuentas_fallidas_en_servidor(cuentas_fallidas)
    
    _enviar_archivo_por_correo(filepath, len(email_ids), emails_exitosos, cuentas_fallidas)
    
    return True


def _ejecutar_proceso_creator_con_objetivo(objetivo_cuentas: int, es_ciclo: bool = False, ciclo_minutes: int = None) -> int:
    """
    Ejecuta el proceso de creación de cuentas con un objetivo específico
    """
    from app.database.database import (
        get_creator_coordinates, get_all_available_creator_emails_for_objective,
        update_creator_email_progress, fetch_and_append_emails_for_cycle
    )
    import time
    import tkinter as tk
    from tkinter import messagebox
    
    print(f"🎯 Objetivo: {objetivo_cuentas} cuentas")
    
    coordinates = get_creator_coordinates()
    if not coordinates:
        print("❌ Sin coordenadas")
        return 0
    
    filepath = _inicializar_archivo_salida(objetivo_cuentas)
    if not filepath:
        return 0
    
    cuentas_creadas = 0
    cuentas_fallidas = []
    intento = 1
    
    while cuentas_creadas < objetivo_cuentas and intento <= 10:
        print(f"📧 Intento {intento} - {cuentas_creadas}/{objetivo_cuentas}")
        
        # Obtener emails disponibles
        email_ids = get_all_available_creator_emails_for_objective()
        
        # Si no hay emails, solicitar más
        if not email_ids:
            faltantes = objetivo_cuentas - cuentas_creadas
            print(f"📭 Solicitando {faltantes} emails...")
            resultado = fetch_and_append_emails_for_cycle(faltantes)
            
            if resultado == "NO_EMAILS_AVAILABLE":
                print("📭 No hay más emails disponibles en el servidor")
                # Mostrar messagebox y detener el bot
                root = tk.Tk()
                root.withdraw()  # Ocultar ventana principal
                messagebox.showwarning(
                    "Sin Emails Disponibles", 
                    "Te quedaste sin emails en la base de datos.\n\nEl bot se detendrá."
                )
                root.destroy()
                break
            elif not resultado:
                print("❌ Error al obtener emails")
                break
                
            email_ids = get_all_available_creator_emails_for_objective()
            if not email_ids:
                break
        
        # Procesar emails
        for i, email_id in enumerate(email_ids, 1):
            if cuentas_creadas >= objetivo_cuentas:
                break
                
            _ejecutar_modo_avion()
            print(f"📧 {cuentas_creadas + 1}/{objetivo_cuentas}")
            
            exito, motivo_fallo, detalles = procesar_email_individual_con_detalle(email_id, coordinates, filepath, cuentas_creadas + 1, objetivo_cuentas)
            
            if exito:
                cuentas_creadas += 1
                print(f"✅ Cuenta {cuentas_creadas}")
            else:
                print(f"❌ Falló - {motivo_fallo}")
                # Agregar a la lista de cuentas fallidas
                from app.database.database import get_creator_email_by_id
                from app.database.database import get_creator_setting
                from datetime import datetime
                
                current_email = get_creator_email_by_id(email_id)
                creator_settings = get_creator_setting()
                user_agent = creator_settings.get('user_agent', '') if creator_settings else ''
                
                cuenta_fallida = {
                    "email": current_email if current_email else f"email_id_{email_id}",
                    "password": _get_password_usado(),
                    "user_agent": user_agent,
                    "motivo_fallo": motivo_fallo,
                    "detalles": detalles,
                    "fecha_fallo": datetime.now().isoformat(),
                    "contador": cuentas_creadas + 1,
                    "total": objetivo_cuentas,
                    "intento": intento
                }
                cuentas_fallidas.append(cuenta_fallida)
            
            update_creator_email_progress(email_id, cuentas_creadas)
            if i < len(email_ids):
                time.sleep(1)
        
        intento += 1
    
    print(f"🎉 Completado: {cuentas_creadas}/{objetivo_cuentas}")
    _actualizar_encabezado_con_exitos(filepath, objetivo_cuentas, cuentas_creadas)
    
    # Guardar cuentas fallidas en el servidor
    if cuentas_fallidas:
        print(f"💾 Guardando {len(cuentas_fallidas)} cuentas fallidas en el servidor...")
        print("📧 EMAILS FALLIDOS:")
        for i, cuenta in enumerate(cuentas_fallidas, 1):
            print(f"  {i}. {cuenta['email']} - {cuenta['motivo_fallo']}")
        _guardar_cuentas_fallidas_en_servidor(cuentas_fallidas)
    
    _enviar_archivo_por_correo(filepath, objetivo_cuentas, cuentas_creadas, cuentas_fallidas, es_ciclo, ciclo_minutes)
    
    return cuentas_creadas


def _ejecutar_creator_en_ciclo():
    """
    Ejecuta el proceso de creación de cuentas en ciclo continuo
    """
    from app.database.database import (
        get_creator_setting, fetch_and_save_emails_for_cycle, 
        delete_all_creator_emails, reset_creator_email_progress
    )
    import time
    
    settings = get_creator_setting()
    cycle_minutes = settings.get('cycle_time_minutes', 60)
    accounts_per_cycle = settings.get('accounts_per_cycle', 1)
    
    print(f"🔄 Ciclo: {cycle_minutes}min - Objetivo: {accounts_per_cycle} cuentas")
    print("💡 Ctrl+C para detener")
    
    ciclo = 1
    
    try:
        while True:
            print(f"\n🔄 CICLO #{ciclo}")
            
            # Enviar notificación de inicio de ciclo
            _enviar_notificacion_inicio_ciclo(ciclo, accounts_per_cycle, cycle_minutes)
            
            # Limpiar emails del ciclo anterior
            if ciclo > 1:
                print("🧹 Limpiando emails...")
                delete_all_creator_emails()
                reset_creator_email_progress()
            
            # Obtener emails del servidor
            print(f"🌐 Obteniendo {accounts_per_cycle} emails...")
            resultado = fetch_and_save_emails_for_cycle(accounts_per_cycle)
            
            if resultado == "NO_EMAILS_AVAILABLE":
                print("📭 No hay más emails disponibles en el servidor")
                # Mostrar messagebox y detener el bot
                import tkinter as tk
                from tkinter import messagebox
                root = tk.Tk()
                root.withdraw()
                messagebox.showwarning(
                    "Sin Emails Disponibles", 
                    "Te quedaste sin emails en la base de datos.\n\nEl bot se detendrá."
                )
                root.destroy()
                break
            elif not resultado:
                print(f"❌ Error - Esperando {cycle_minutes}min...")
                time.sleep(cycle_minutes * 60)
                ciclo += 1
                continue
            
            # Ejecutar proceso de creación
            cuentas_creadas = _ejecutar_proceso_creator_con_objetivo(accounts_per_cycle, es_ciclo=True, ciclo_minutes=cycle_minutes)
            
            # Mostrar resultado
            if cuentas_creadas >= accounts_per_cycle:
                print(f"🎉 Objetivo completado: {cuentas_creadas}/{accounts_per_cycle}")
            else:
                print(f"⚠️ Objetivo parcial: {cuentas_creadas}/{accounts_per_cycle}")
            
            print(f"⏰ Esperando {cycle_minutes}min...")
            time.sleep(cycle_minutes * 60)
            ciclo += 1
            
    except KeyboardInterrupt:
        print(f"\n🛑 Detenido - {ciclo - 1} ciclos completados")
    except Exception as e:
        print(f"\n❌ Error: {e}")