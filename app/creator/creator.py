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
    timeout_seconds = 120  # 2 minutos
    
    # Contadores para evitar bucles infinitos
    numero_count = 0
    captcha_count = 0
    ciclos_sin_imagen = 0
    
    while True:
        # Verificar si ha pasado el timeout
        elapsed_time = time.time() - start_time
        if elapsed_time > timeout_seconds:
            print("⏰ Timeout de 120 segundos - no se encontraron imágenes, cerrando ventana")
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
            ciclos_sin_imagen = 0  # Resetear contador
            print(f"✅ Número encontrado (vez #{numero_count}) - cerrando")
            
            if numero_count >= 2:
                print("🔄 Segundo número detectado - cerrando ventana directamente")
                # Desactivar proxy antes de cerrar por segundo número
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
            ciclos_sin_imagen = 0  # Resetear contador
            print(f"✅ Captcha encontrado (vez #{captcha_count}) - cerrando")
            
            if captcha_count >= 2:
                print("🔄 Segundo captcha detectado - cerrando ventana directamente")
                # Desactivar proxy antes de cerrar por segundo captcha
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
            "imagen_de_confirmacion_de_codigo"
        ]
        
        # Buscar cualquiera de las imágenes de éxito
        for image_name in exito_images:
            if wait_for_creator_image(image_name, max_attempts=1, delay_between_attempts=0.5, silent=True):
                exito_found = True
                exito_image_name = image_name
                break
        
        if exito_found:
            ciclos_sin_imagen = 0  # Resetear contador
            print(f"✅ Imagen de éxito encontrada ({exito_image_name}) - guardando información")
            
            # Desactivar proxy después del éxito
            _desactivar_proxy()
            
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
                        
                        # Agregar al archivo existente (modo append)
                        try:
                            with open(filepath, 'a', encoding='utf-8') as f:
                                f.write(contenido + "\n")
                            return True
                        except Exception as e:
                            return False
                    else:
                        print("❌ No se encontró user agent en la base de datos")
                        return False
        
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


def _click_brave(coordinates):
    """Hace clic en Brave"""
    from app.creator.computer_actions import click_coordinates
    import time
    
    brave_coords = coordinates.get("brave_click")
    if not brave_coords:
        return False
    
    click_coordinates(brave_coords, double_click=True)
    time.sleep(0.5)
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


def _llenar_formulario_registro(coordinates, email):
    """Llena el formulario de registro de LinkedIn"""
    from app.creator.computer_actions import click_coordinates, type_text, press_key, generate_random_password, generate_random_name, generate_random_lastname, wait_for_creator_image
    import time
    
    # Click en email_input_click
    email_coords = coordinates.get("email_input_click")
    if not email_coords:
        return False
    
    click_coordinates(email_coords)
    time.sleep(0.5)
    
    # Escribir email
    type_text(email)
    time.sleep(0.5)
    
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
    if not settings or not settings.get('scheduled_time') or not settings.get('timezone'):
        return True  # No hay hora programada, continuar inmediatamente
    
    scheduled_time = settings.get('scheduled_time')
    timezone_str = settings.get('timezone')
    
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


def execute_creator():
    """
    Función principal del creator que ejecuta todas las acciones
    """
    from app.database.database import get_creator_coordinates, get_all_creator_email_ids
    import time
    
    # Variable global para almacenar el password usado
    global _password_usado
    _password_usado = ""
    
    # Verificar hora programada
    if not _verificar_hora_programada():
        return

    # Obtener emails de la base de datos
    email_ids = get_all_creator_email_ids()
    if not email_ids:
        print("❌ No se encontraron emails en la base de datos")
        return
    
    print(f"🔄 Procesando {len(email_ids)} emails")
    
    # Obtener coordenadas
    coordinates = get_creator_coordinates()
    if not coordinates:
        print("❌ No se encontraron coordenadas configuradas")
        return
    
    # Inicializar archivo de salida
    filepath = _inicializar_archivo_salida(len(email_ids))
    if not filepath:
        return
    
    # BUCLE PRINCIPAL - Procesar cada email
    emails_exitosos = 0
    
    for i, email_id in enumerate(email_ids, 1):
        # Ejecutar modo avión
        _ejecutar_modo_avion()
        print(f"📧 Email {i}/{len(email_ids)}")
        
        # Procesar email individual
        exito = procesar_email_individual(email_id, coordinates, filepath, i, len(email_ids))
        
        if exito:
            emails_exitosos += 1
            print(f"✅ Completado")
        else:
            print(f"❌ Falló")
        
        # Pausa entre emails (excepto en el último)
        if i < len(email_ids):
            time.sleep(5)
    
    # Finalizar proceso
    print(f"🎉 Proceso completado: {emails_exitosos}/{len(email_ids)} exitosos")
    _actualizar_encabezado_con_exitos(filepath, len(email_ids), emails_exitosos)
