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
    timeout_seconds = 180  # 3 minutos
    
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


def _enviar_archivo_por_correo(filepath, total_emails, emails_exitosos):
    try:
        from app.confirmabot.hostinger_actions import send_email_with_file
        from app.database.database import get_creator_setting, get_all_emails
        import os
        from datetime import datetime
        
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
        
        # Preparar correo
        fecha_hora = datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')
        asunto = f"Reporte LinkedIn Creator - {fecha_hora}"
        
        cuerpo = f"""Hola,

            El proceso de creación de cuentas LinkedIn ha finalizado.

            📊 RESUMEN:
            - Total de emails procesados: {total_emails}
            - Cuentas creadas exitosamente: {emails_exitosos}
            - Tasa de éxito: {(emails_exitosos/total_emails*100):.1f}%

            📎 Adjunto encontrarás el archivo con todas de las cuentas creadas.

            Saludos,
            ConfirmaBot
        """
        
        # Enviar correo
        exito = send_email_with_file(
            email_address=email_address,
            password=email_password,
            to_email=email_destino,
            subject=asunto,
            body=cuerpo,
            attachment_path=filepath
        )
        
        if exito:
            print(f"📧 Reporte enviado: {emails_exitosos}/{total_emails} cuentas")
        
        return exito
            
    except Exception as e:
        return False


def execute_creator():
    """
    Función principal del creator que ejecuta todas las acciones
    """
    from app.database.database import get_creator_coordinates, get_all_creator_email_ids, get_creator_setting
    import time
    
    # Variable global para almacenar el password usado
    global _password_usado
    _password_usado = ""
    
    # Obtener configuración para determinar el tipo de ejecución
    settings = get_creator_setting()
    if not settings:
        print("❌ No se encontró configuración del creator")
        return
    
    time_config_type = settings.get('time_config_type', 'manual')
    scheduled_time = settings.get('scheduled_time')
    cycle_time_minutes = settings.get('cycle_time_minutes', 60)
    
    # Determinar el modo de ejecución
    has_scheduled = scheduled_time and scheduled_time.strip()
    has_cycle = cycle_time_minutes and cycle_time_minutes > 0
    
    if has_scheduled and has_cycle:
        # Ambos configurados: verificar hora y ejecutar en ciclo
        print("🔄 Modo: Ciclo + Hora programada - Verificando hora...")
        if not _verificar_hora_programada():
            return
        print("✅ Hora programada verificada - Ejecutando en ciclo")
        _ejecutar_creator_en_ciclo()
    elif has_cycle:
        # Solo ciclo configurado
        print("🔄 Modo: Solo ciclo - Ejecutando en ciclo")
        _ejecutar_creator_en_ciclo()
    elif has_scheduled:
        # Solo hora programada configurada - PROCESAR TODAS LAS CUENTAS
        print("🕐 Modo: Solo hora programada - Verificando hora...")
        if not _verificar_hora_programada():
            return
        print("✅ Hora programada verificada - Procesando TODAS las cuentas disponibles")
        _ejecutar_proceso_creator()
    else:
        # Ninguno configurado: modo manual (ejecutar una vez) - PROCESAR TODAS LAS CUENTAS
        print("👤 Modo: Manual - Procesando TODAS las cuentas disponibles")
        _ejecutar_proceso_creator()


def _ejecutar_proceso_creator():
    """
    Ejecuta el proceso de creación de cuentas una sola vez
    """
    from app.database.database import get_creator_coordinates, get_all_available_creator_emails, get_next_creator_emails, get_creator_setting, update_creator_email_progress, get_creator_email_count
    import time
    
    # Obtener configuración para determinar cuántas cuentas crear
    settings = get_creator_setting()
    time_config_type = settings.get('time_config_type', 'manual')
    
    # Obtener emails según el tipo de configuración
    if time_config_type in ['cycle', 'both']:
        # Modo ciclo o both: procesar solo las cuentas especificadas por ciclo
        accounts_per_cycle = settings.get('accounts_per_cycle', 1)
        email_ids = get_next_creator_emails(accounts_per_cycle)
        print(f"🔄 Modo ciclo: procesando {accounts_per_cycle} cuentas por ciclo")
    else:
        # Para modo manual, scheduled, o cualquier otro: procesar TODAS las cuentas disponibles
        email_ids = get_all_available_creator_emails()
        print(f"🔄 Modo programado/manual: procesando TODAS las cuentas disponibles ({len(email_ids)} cuentas)")
    
    if not email_ids:
        print("❌ No hay emails disponibles para procesar")
        # Reiniciar progreso cuando no hay emails
        from app.database.database import reset_creator_email_progress
        reset_creator_email_progress()
        return False  # Retornar False para indicar que no hay más emails
    
    print(f"📧 Total de emails a procesar: {len(email_ids)}")
    
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
        print(f"📧 Procesando email {i}/{len(email_ids)}")
        
        # Procesar email individual
        exito = procesar_email_individual(email_id, coordinates, filepath, i, len(email_ids))
        
        if exito:
            emails_exitosos += 1
            print(f"✅ Email {i} completado")
        else:
            print(f"❌ Email {i} falló")
        
        # Actualizar progreso después de cada email
        update_creator_email_progress(email_id, emails_exitosos)
        
        # Pausa entre emails (excepto en el último)
        if i < len(email_ids):
            time.sleep(1)
    
    # Finalizar proceso
    print(f"🎉 Completado: {emails_exitosos}/{len(email_ids)} exitosos")
    _actualizar_encabezado_con_exitos(filepath, len(email_ids), emails_exitosos)
    _enviar_archivo_por_correo(filepath, len(email_ids), emails_exitosos)
    
    return True  # Retornar True para indicar que se procesaron emails


def _ejecutar_creator_en_ciclo():
    """
    Ejecuta el proceso de creación de cuentas en ciclo continuo
    """
    from app.database.database import get_creator_setting, get_creator_email_count
    import time
    import datetime
    
    settings = get_creator_setting()
    cycle_minutes = settings.get('cycle_time_minutes', 60)
    accounts_per_cycle = settings.get('accounts_per_cycle', 1)
    
    print(f"🔄 Ciclo cada {cycle_minutes}min - {accounts_per_cycle} cuentas por ciclo")
    print("💡 Ctrl+C para detener")
    
    ciclo_numero = 1
    
    try:
        while True:
            print(f"\n🔄 CICLO #{ciclo_numero}")
            
            # Verificar si hay emails disponibles
            total_emails = get_creator_email_count()
            if total_emails == 0:
                print("❌ No hay emails en la base de datos")
                break
            
            # Ejecutar el proceso de creación
            resultado = _ejecutar_proceso_creator()
            
            # Si no hay más emails disponibles, detener el ciclo
            if resultado == False:
                print("🎉 ¡Todos los emails procesados!")
                break
            
            print(f"⏰ Esperando {cycle_minutes}min...")
            
            # Esperar el tiempo del ciclo
            time.sleep(cycle_minutes * 60)
            
            ciclo_numero += 1
            
    except KeyboardInterrupt:
        print(f"\n🛑 Ciclo detenido - {ciclo_numero - 1} ciclos completados")
    except Exception as e:
        print(f"\n❌ Error: {e}")
