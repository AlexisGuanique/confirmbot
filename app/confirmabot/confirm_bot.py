from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from app.database.database import get_email_by_id, get_email_count, get_bot_settings, get_all_emails, get_creator_setting, get_user_data
import sys
import os
import tempfile
import uuid
import shutil

import os, uuid, tempfile, time, shutil, subprocess
from datetime import datetime
from selenium.webdriver.chrome.service import Service

import subprocess

from app.confirmabot.hostinger_login import login_to_hostinger
from app.confirmabot.hostinger_actions import send_email_with_file
from app.confirmabot.mail_actions import mail_actions
import time  # ⏱️ Asegúrate de tener esta importación al inicio del archivo

stop_checker = False




sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


def stop_bot():
    global stop_checker
    stop_checker = True
    print("🛑 Señal de detención enviada al bot.")



BRAVE_EXE = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"

def open_temp_chrome_profile(profile_name="Default", kill_residual=True, chromedriver_exe=None):
    # Configurar variables de entorno para silenciar logs de Chrome
    import os
    os.environ['CHROME_LOG_FILE'] = os.devnull
    os.environ['CHROME_LOG_LEVEL'] = '3'
    
    if kill_residual:
        for exe in ("brave.exe", "BraveCrashHandler.exe"):
            try:
                subprocess.run(["taskkill", "/IM", exe, "/F"], capture_output=True, text=True)
            except Exception:
                pass

    user_data_dir = os.path.join(
        os.environ["LOCALAPPDATA"],
        r"BraveSoftware\Brave-Browser\User Data"
    )

    options = Options()
    options.binary_location = BRAVE_EXE
    options.add_argument(f'--user-data-dir={user_data_dir}')
    options.add_argument(f'--profile-directory={profile_name}')

    # ✅ Importante: no bloquear extensiones
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--remote-debugging-port=0")
    options.add_argument("--disable-remote-debugging")
    options.add_argument("--disable-dev-tools")
    
    # 🔧 Opciones para evitar error DevToolsActivePort
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-tools")
    options.add_argument("--disable-extensions-file-access-check")
    options.add_argument("--disable-extensions-http-throttling")
    options.add_argument("--disable-logging")
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--disable-features=VizDisplayCompositor")
    
    # 🔇 Silenciar logs molestos de Chrome
    options.add_argument("--log-level=3")  # Solo errores fatales
    options.add_argument("--silent")  # Modo silencioso
    options.add_argument("--disable-logging")  # Deshabilitar logging
    options.add_argument("--disable-dev-tools")  # Deshabilitar DevTools
    options.add_argument("--disable-remote-debugging")  # Deshabilitar debugging remoto
    options.add_argument("--disable-background-networking")  # Deshabilitar networking en background
    options.add_argument("--disable-default-apps")  # Deshabilitar apps por defecto
    options.add_argument("--disable-hang-monitor")  # Deshabilitar monitor de cuelgues
    options.add_argument("--disable-sync")  # Deshabilitar sincronización
    options.add_argument("--disable-translate")  # Deshabilitar traducción
    options.add_argument("--mute-audio")  # Silenciar audio
    options.add_argument("--safebrowsing-disable-auto-update")  # Deshabilitar actualización de safebrowsing
    options.add_argument("--disable-component-update")  # Deshabilitar actualización de componentes
    options.add_argument("--disable-domain-reliability")  # Deshabilitar domain reliability
    options.add_argument("--disable-features=TranslateUI,BlinkGenPropertyTrees")  # Deshabilitar más features
    options.add_argument("--disable-ipc-flooding-protection")  # Deshabilitar protección contra flooding IPC
    
    # ✅ Permitir extensiones (se cargarán automáticamente)
    
    # 🧹 Opciones para ventana limpia
    options.add_argument("--incognito")  # Modo incógnito para no cargar pestañas anteriores
    options.add_argument("--disable-session-crashed-bubble")  # Evitar diálogos de sesión
    options.add_argument("--disable-infobars")  # Deshabilitar barras de información
    options.add_argument("--disable-plugins-discovery")  # Deshabilitar descubrimiento de plugins
    options.add_argument("--disable-background-timer-throttling")  # Evitar throttling de timers
    options.add_argument("--disable-backgrounding-occluded-windows")  # Evitar backgrounding
    options.add_argument("--disable-renderer-backgrounding")  # Evitar backgrounding del renderer
    options.add_argument("--disable-features=TranslateUI")  # Deshabilitar traducción automática
    options.add_argument("--disable-ipc-flooding-protection")  # Deshabilitar protección contra flooding IPC

    # 👉 Cargar todas las extensiones disponibles automáticamente
    extensions_dir = os.path.join(user_data_dir, profile_name, "Extensions")
    if os.path.exists(extensions_dir):
        extension_paths = []
        for ext_id in os.listdir(extensions_dir):
            ext_path = os.path.join(extensions_dir, ext_id)
            if os.path.isdir(ext_path):
                # Buscar la versión más reciente de cada extensión
                versions = os.listdir(ext_path)
                if versions:
                    # Ordenar versiones y tomar la más reciente
                    latest_version = sorted(versions)[-1]
                    full_ext_path = os.path.join(ext_path, latest_version)
                    manifest_path = os.path.join(full_ext_path, "manifest.json")
                    if os.path.exists(manifest_path):
                        extension_paths.append(full_ext_path)
                        #print(f"✅ Extensión cargada: {ext_id} v{latest_version}")
        
        # Cargar todas las extensiones válidas
        if extension_paths:
            options.add_argument(f"--load-extension={','.join(extension_paths)}")
        else:
            print("⚠️ No se encontraron extensiones válidas para cargar")

    try:
        if chromedriver_exe and os.path.exists(chromedriver_exe):
            service = Service(chromedriver_exe)
            # Redirigir logs de Chrome al vacío
            service.log_path = os.devnull
            # Configurar ChromeDriver para no mostrar logs
            service.start_error_message = ""
            driver = webdriver.Chrome(service=service, options=options)
        else:
            # Configurar ChromeDriver para no mostrar logs
            service = Service()
            service.log_path = os.devnull
            service.start_error_message = ""
            driver = webdriver.Chrome(service=service, options=options)
        
        # Esperar un momento para que el navegador se inicialice completamente
        time.sleep(2)
        return driver
        
    except Exception as e:
        print(f"❌ Error al inicializar el navegador: {e}")
        print("🔄 Intentando con opciones adicionales...")
        
        # Intentar con opciones más restrictivas
        options.add_argument("--headless")  # Modo sin interfaz gráfica
        options.add_argument("--disable-images")  # Deshabilitar imágenes
        options.add_argument("--disable-javascript")  # Deshabilitar JavaScript temporalmente
        
        try:
            # Configurar ChromeDriver para no mostrar logs
            service = Service()
            service.log_path = os.devnull
            service.start_error_message = ""
            driver = webdriver.Chrome(service=service, options=options)
            time.sleep(2)
            return driver
        except Exception as e2:
            print(f"❌ Error crítico al inicializar el navegador: {e2}")
            raise e2


def _enviar_emails_a_base_datos(emails_verificados, total_emails, emails_exitosos, corte_numero=None):
    """
    Envía los emails verificados a la base de datos remota mediante API
    """
    try:
        from app.utils.http_utils import post
        
        # Obtener datos del usuario desde la base de datos
        user_data = get_user_data()
        if not user_data:
            return False
        
        access_token = user_data.get('access_token')
        user_id = user_data.get('id')
        
        if not access_token or not user_id:
            return False
        
        # Preparar datos para la API
        url = f"http://34.29.59.97/api/emails/save/{user_id}"
        headers = {
            'Content-Type': 'application/json'
        }
        
        data = {
            "access_token": access_token,
            "emails": emails_verificados
        }
        
        # Realizar petición POST
        response = post(url, body=data, headers=headers)
        
        if response and response.status_code in [200, 201]:
            print(f"✅ Emails enviados a la base de datos: {len(emails_verificados)}")
            return True
        else:
            print(f"❌ Error al enviar emails a la base de datos")
            return False
            
    except Exception as e:
        print(f"❌ Error al enviar emails a la base de datos: {e}")
        return False


def _obtener_total_emails_base_datos():
    """
    Obtiene el total de emails en la base de datos remota.
    Como la operación es asíncrona, espera un poco antes de consultar.
    
    Returns:
        int: Total de emails en la base de datos o 0 si hay error
    """
    try:
        from app.utils.http_utils import post
        import time
        
        # Obtener datos del usuario desde la base de datos
        user_data = get_user_data()
        if not user_data:
            return 0
        
        access_token = user_data.get('access_token')
        user_id = user_data.get('id')
        
        if not access_token or not user_id:
            return 0
        
        # Preparar datos para la API
        url = f"http://34.29.59.97/api/emails/count/{user_id}"
        headers = {
            'Content-Type': 'application/json'
        }
        
        data = {
            "access_token": access_token
        }
        
        # Intentar obtener el conteo varias veces con delays crecientes
        for attempt in range(3):
            # Esperar tiempo creciente: 3, 5, 7 segundos
            wait_time = 3 + (attempt * 2)
            time.sleep(wait_time)
            
            # Realizar petición POST
            response = post(url, body=data, headers=headers)
            
            if response and response.status_code in [200, 201]:
                try:
                    response_data = response.json()
                    total_emails = response_data.get('email_count', 0)  # Cambiado de 'total' a 'email_count'
                    # Si obtenemos un número mayor a 0, lo consideramos válido
                    if total_emails > 0:
                        return total_emails
                except Exception as e:
                    pass
            
            # Si es el último intento, devolver lo que tengamos (aunque sea 0)
            if attempt == 2:
                try:
                    response_data = response.json()
                    return response_data.get('email_count', 0)  # Cambiado de 'total' a 'email_count'
                except:
                    return 0
        
        return 0
            
    except Exception as e:
        return 0


def _enviar_correo_sin_adjunto(email_address: str, password: str, to_email: str, 
                               subject: str, body: str) -> bool:
    """
    Envía un correo electrónico sin archivo adjunto.
    
    Args:
        email_address: Dirección de correo del remitente
        password: Contraseña de la cuenta
        to_email: Dirección de correo del destinatario
        subject: Asunto del correo
        body: Cuerpo del correo
        
    Returns:
        bool: True si el envío fue exitoso, False en caso contrario
    """
    try:
        from app.confirmabot.hostinger_actions import HostingerEmailClient
        
        email_client = HostingerEmailClient(email_address, password)
        
        if email_client.connect_smtp():
            success = email_client.send_email(to_email, subject, body)
            email_client.disconnect_smtp()
            return success
        else:
            return False
            
    except Exception as e:
        return False


def _enviar_archivo_por_correo(filepath, total_emails, emails_exitosos, corte_numero=None):
    """
    Envía un informe por correo sin archivo adjunto, incluyendo el total de emails en la base de datos remota
    """
    try:
        # Obtener credenciales de correo
        emails_data = get_all_emails()
        if not emails_data:
            print("❌ No hay credenciales de correo disponibles")
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
            print("❌ No se encontraron credenciales de Hostinger")
            return False
        
        # Obtener email de destino
        settings = get_creator_setting()
        email_destino = settings.get('notification_email') if settings else None
        
        if not email_destino:
            print("❌ No hay email de notificación configurado")
            return False
        
        # Obtener total de emails de la base de datos remota (opcional, puede fallar)
        try:
            total_emails_base_datos = _obtener_total_emails_base_datos()
        except Exception as e:
            total_emails_base_datos = "N/A"
        
        # Contar emails en el archivo local
        emails_en_archivo = 0
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                emails_en_archivo = len([line for line in f if line.strip()])
        except:
            emails_en_archivo = emails_exitosos
        
        # Preparar correo
        fecha_hora = datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')
        asunto = f"Reporte ConfirmaBot - Corte {corte_numero or 'N/A'} - {fecha_hora}"
        
        cuerpo = f"""Hola,

            El proceso de verificación de emails ha completado un nuevo corte.

            📊 RESUMEN:
            - Emails guardados en este corte: {emails_exitosos}
            - Total de emails en base de datos: {total_emails_base_datos}

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
            print(f"✅ Reporte enviado por correo")
        else:
            print("❌ Error al enviar el reporte")
        
        return exito
            
    except Exception as e:
        print(f"❌ Error enviando archivo por correo: {e}")
        return False


def run_checker():
    global stop_checker
    print("🟢 Ejecutando checker para todos los registros...")
    at_least_one_verified = False  
    stop_checker = False

    try:
        total_registros = get_email_count()
        config = get_bot_settings()

        if total_registros == 0 or not config:
            print("❌ No hay registros válidos o configuración faltante.")
            return False

        iteraciones = config["iterations"]
        pause_minutes = config.get("pause_minutes", 20)  # Valor por defecto: 20 minutos

        # Ruta del ejecutable ADB - verificar si existe
        adb_path = r"C:\Adb\adb.exe"
        adb_available = os.path.exists(adb_path)
        
        if not adb_available:
            print("⚠️ ADB no encontrado en C:\\Adb\\adb.exe")
            print("💡 El modo avión se omitirá, pero el bot continuará funcionando")
        else:
            print("✅ ADB encontrado y disponible")

        for id in range(1, total_registros + 1):
            if stop_checker:
                print("🛑 Ejecución interrumpida por el usuario.")
                return at_least_one_verified

            print(f"📂 Procesando registro ID {id}")
            registro = get_email_by_id(id)
            if not registro:
                print(f"❌ No se encontró el registro con ID {id}. Saltando...")
                continue

            email_hostinger = registro["email_hostinger"]
            password_hostinger = registro["password_hostinger"]
            domain = registro["email"]

            safe_filename = email_hostinger.replace("@", "_at_")
            os.makedirs("verifications", exist_ok=True)
            file_path = os.path.join("verifications", f"{safe_filename}.txt")

            # ✅ Limpiar el archivo solo una vez al comenzar este ID
            with open(file_path, "w", encoding="utf-8"):
                pass
            
            # Crear archivo para emails no verificados
            unverified_file_path = file_path.replace('.txt', '_no_verificados.txt')
            with open(unverified_file_path, "w", encoding="utf-8") as f_unverified:
                f_unverified.write("# Emails no verificados - No se pudo extraer URL de confirmación\n")
                f_unverified.write(f"# Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f_unverified.write("# ================================================\n\n")
            
            print(f"📁 Archivo principal: {file_path}")
            print(f"📁 Archivo de no verificados: {unverified_file_path}")

            with open(file_path, "a", encoding="utf-8") as f:
                successful_iterations = 0
                failed_iterations = 0
                timeout_errors = 0
                other_errors = 0
                emails_sent_count = 0  # Contador de emails ya enviados por correo
                emails_verificados_totales = []  # Lista de todos los emails verificados

                for i in range(iteraciones):
                    if stop_checker:
                        print("🛑 Iteración interrumpida por el usuario.")
                        return at_least_one_verified

                    # ⏸️ Pausa cada 10 iteraciones (excepto en la primera)
                    if i > 0 and i % 10 == 0:
                        print(f"⏸️ Pausa programada: {i} iteraciones completadas")
                        print(f"⏰ Pausando por {pause_minutes} minutos...")
                        
                        # Convertir minutos a segundos
                        pause_seconds = pause_minutes * 60
                        
                        # Mostrar progreso de la pausa cada minuto
                        for remaining in range(pause_seconds, 0, -60):
                            minutes_left = remaining // 60
                            print(f"⏳ Tiempo restante: {minutes_left} minutos")
                            time.sleep(60)  # Esperar 1 minuto
                        
                        # Esperar los segundos restantes
                        remaining_seconds = pause_seconds % 60
                        if remaining_seconds > 0:
                            time.sleep(remaining_seconds)
                        
                        print("✅ Pausa completada. Continuando con las iteraciones...")

                    print(f"🔁 Iteración {i + 1} de {iteraciones} para ID {id}")
                    start_time = time.time()

                    # Ejecutar comandos ADB solo si está disponible y habilitado
                    enable_adb = config.get("enable_adb", True)
                    if adb_available and enable_adb:
                        try:
                            # Ejecutar el comando para activar el modo avión
                            subprocess.run([adb_path, "shell", "cmd", "connectivity", "airplane-mode", "enable"], 
                                         capture_output=True, text=True, timeout=10)
                            print("✅ Modo avión activado.")
                            time.sleep(5)  # Esperar 5 segundos

                            # Ejecutar el comando para desactivar el modo avión
                            subprocess.run([adb_path, "shell", "cmd", "connectivity", "airplane-mode", "disable"], 
                                         capture_output=True, text=True, timeout=10)
                            print("✅ Modo avión desactivado.")
                            time.sleep(5)  # Esperar 5 segundos
                        except Exception as e:
                            print(f"⚠️ Error ejecutando comandos ADB: {e}")
                            print("🔄 Continuando sin modo avión...")
                    elif not enable_adb:
                        print("⏭️ Modo avión deshabilitado por configuración")
                        time.sleep(2)  # Pequeña pausa para simular el proceso
                    else:
                        print("⏭️ Omitiendo modo avión (ADB no disponible)")
                        time.sleep(2)  # Pequeña pausa para simular el proceso

                    # Inicializar el navegador
                    driver = open_temp_chrome_profile()

                    try:
                        enable_proxy = config.get("enable_proxy", True)
                        mail_ok, final_email, generated_email = mail_actions(driver, domain, enable_proxy)
                        if not mail_ok:
                            print("❌ Falló la creación del correo en 33mail.")
                            continue

                        is_verified = login_to_hostinger(driver, email_hostinger, password_hostinger, generated_email)

                        if is_verified:
                            # Extraer solo el dominio del email completo
                            domain_only = f"@{final_email.split('@')[1]}" if '@' in final_email else final_email
                            
                            f.write(f"{domain_only.strip()}\n")
                            f.flush()
                            os.fsync(f.fileno())
                            print(f"📝 Dominio verificado guardado: {domain_only.strip()}")
                            at_least_one_verified = True
                            successful_iterations += 1
                            
                            # Agregar dominio a la lista de verificados
                            emails_verificados_totales.append(domain_only.strip())
                            
                            # Mostrar progreso hacia el próximo corte
                            config = get_bot_settings()
                            emails_per_batch = config.get("emails_per_batch", 5) if config else 5
                            cuentas_actuales = (successful_iterations % emails_per_batch)
                            if cuentas_actuales == 0:
                                cuentas_actuales = emails_per_batch
                            print(f"🎯 {cuentas_actuales}/{emails_per_batch} cuentas para el corte.")
                            
                            # 📧 Enviar emails a base de datos periódicamente basado en la configuración
                            config = get_bot_settings()
                            emails_per_batch = config.get("emails_per_batch", 5) if config else 5
                            
                            # Enviar cada vez que se alcance un múltiplo del número configurado
                            if successful_iterations % emails_per_batch == 0:
                                print(f"🎉 ¡Alcanzado {successful_iterations} emails confirmados! Enviando a base de datos...")
                                
                                # Obtener solo los emails nuevos del lote actual (los últimos emails_per_batch)
                                emails_nuevos = emails_verificados_totales[-emails_per_batch:]
                                
                                # Enviar los emails nuevos a la base de datos
                                if emails_nuevos:
                                    total_emails_procesados = successful_iterations + failed_iterations
                                    corte_numero = successful_iterations // emails_per_batch
                                    
                                    print(f"🎉 Corte #{corte_numero} realizado - Enviando {len(emails_nuevos)} dominios nuevos a la base de datos...")
                                    
                                    # Enviar a base de datos remota
                                    db_success = _enviar_emails_a_base_datos(emails_nuevos, total_emails_procesados, len(emails_nuevos), corte_numero)
                                    
                                    # Enviar reporte por correo (independiente del éxito de la BD)
                                    email_success = _enviar_archivo_por_correo(file_path, total_emails_procesados, len(emails_nuevos), corte_numero)
                                
                                emails_sent_count = successful_iterations
                        else:
                            # Guardar dominio no verificado en archivo separado
                            domain_only = f"@{final_email.split('@')[1]}" if '@' in final_email else final_email
                            unverified_file_path = file_path.replace('.txt', '_no_verificados.txt')
                            with open(unverified_file_path, 'a', encoding='utf-8') as f_unverified:
                                f_unverified.write(f"{domain_only.strip()}\n")
                                f_unverified.flush()
                                os.fsync(f_unverified.fileno())
                            
                            print(f"⚠️ Dominio no verificado guardado en archivo separado: {domain_only.strip()}")
                            failed_iterations += 1

                        # ✅ Guardar email generado sin verificar en Hostinger
                        #f.write(f"{final_email.strip()}\n")
                        #f.flush()
                        #os.fsync(f.fileno())
                        #print(f"📝 Email generado guardado: {final_email.strip()}")
                        #at_least_one_verified = True
                        #successful_iterations += 1

                    except Exception as e:
                        error_msg = str(e)
                        print(f"❌ Error durante la iteración: {error_msg}")
                        
                        # Manejo específico para diferentes tipos de errores
                        if "Timeout esperando confirmación de registro" in error_msg:
                            print("⏰ Timeout en confirmación de registro - Error temporal, continuando...")
                            print("💡 Este error suele ser temporal y se resuelve en siguientes intentos")
                            timeout_errors += 1
                        elif "ElementClickInterceptedException" in error_msg:
                            print("🖱️ Error de clic interceptado - Elemento no disponible, continuando...")
                            other_errors += 1
                        elif "NoSuchElementException" in error_msg:
                            print("🔍 Elemento no encontrado - Página puede haber cambiado, continuando...")
                            other_errors += 1
                        elif "WebDriverException" in error_msg:
                            print("🌐 Error del navegador - Problema de conexión, continuando...")
                            other_errors += 1
                        else:
                            print("❓ Error desconocido - Continuando con el proceso...")
                            other_errors += 1
                        
                        failed_iterations += 1
                        print("🔄 Continuando con la siguiente iteración...")

                    finally:
                        try:
                            # Limpiar directorio temporal antes de cerrar el driver
                            if hasattr(driver, 'cleanup_temp_dir'):
                                driver.cleanup_temp_dir()
                            
                            driver.quit()
                        except Exception as e:
                            print(f"⚠️ Error al cerrar el navegador: {e}")
                            # Continuar aunque falle el cierre del navegador

                    elapsed = time.time() - start_time
                    print(f"⏱️ Tiempo de ejecución de la iteración: {elapsed:.2f} segundos")
                    print("########################################################")
                

            # Enviar emails restantes si los hay (no enviados en cortes anteriores)
            emails_restantes = []
            try:
                # Calcular cuántos emails se enviaron en cortes anteriores
                emails_enviados_en_cortes = emails_sent_count
                
                # Obtener emails restantes (los que no se enviaron en cortes)
                if len(emails_verificados_totales) > emails_enviados_en_cortes:
                    emails_restantes = emails_verificados_totales[emails_enviados_en_cortes:]
                    
                    if emails_restantes:
                        print(f"📤 Enviando {len(emails_restantes)} dominios restantes al finalizar...")
                        
                        # Enviar emails restantes a la base de datos
                        total_emails_procesados = successful_iterations + failed_iterations
                        corte_numero = "FINAL"
                        db_success = _enviar_emails_a_base_datos(emails_restantes, total_emails_procesados, len(emails_restantes), corte_numero)
                        
                        # Enviar reporte final por correo
                        email_success = _enviar_archivo_por_correo(file_path, total_emails_procesados, len(emails_restantes), corte_numero)
                        
                        if db_success and email_success:
                            print(f"✅ Reporte final enviado: {len(emails_restantes)} emails restantes")
                        elif db_success:
                            print(f"⚠️ Reporte final: BD OK, Email falló")
                        elif email_success:
                            print(f"⚠️ Reporte final: Email OK, BD falló")
                        else:
                            print(f"❌ Reporte final: Ambos fallaron")
                            
            except Exception as e:
                print(f"⚠️ Error al procesar emails restantes: {e}")

            # Resumen de estadísticas para este ID
            print(f"\n📊 Resumen para ID {id}:")
            print(f"  ✅ Iteraciones exitosas: {successful_iterations}")
            print(f"  ❌ Iteraciones fallidas: {failed_iterations}")
            if timeout_errors > 0:
                print(f"  ⏰ Errores de timeout: {timeout_errors}")
            if other_errors > 0:
                print(f"  ⚠️ Otros errores: {other_errors}")
            print(f"  📈 Tasa de éxito: {(successful_iterations/iteraciones)*100:.1f}%")
            if emails_restantes:
                print(f"  📤 Emails restantes enviados: {len(emails_restantes)}")
            
            # Mostrar información de archivos generados
            print(f"  📧 Emails verificados guardados en: {file_path}")
            print(f"  ⚠️ Emails no verificados guardados en: {unverified_file_path}")
            
            # Mostrar estadísticas de archivos
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    verified_count = len([line for line in f if line.strip() and not line.startswith('#')])
                with open(unverified_file_path, 'r', encoding='utf-8') as f:
                    unverified_count = len([line for line in f if line.strip() and not line.startswith('#')])
                print(f"  📊 Emails verificados en archivo: {verified_count}")
                print(f"  📊 Emails no verificados en archivo: {unverified_count}")
            except Exception as e:
                print(f"  ⚠️ Error al contar emails en archivos: {e}")
            
            print("-" * 50)

        return at_least_one_verified

    except Exception as e:
        print(f"❌ Error al ejecutar el checker: {e}")
        return False


if __name__ == "__main__":
    run_checker()