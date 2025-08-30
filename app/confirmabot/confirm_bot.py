from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from app.database.database import get_email_by_id, get_email_count, get_bot_settings
import sys
import os
import tempfile
import uuid

from contextlib import contextmanager

import subprocess

from app.confirmabot.hostinger_login import login_to_hostinger
from app.confirmabot.mail_actions import mail_actions
import time  # ⏱️ Asegúrate de tener esta importación al inicio del archivo

stop_checker = False




sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


def stop_bot():
    global stop_checker
    stop_checker = True
    print("🛑 Señal de detención enviada al bot.")

@contextmanager
def suppress_stderr():
    """Oculta errores en consola temporalmente."""
    with open(os.devnull, 'w') as fnull:
        old_stderr = sys.stderr
        sys.stderr = fnull
        try:
            yield
        finally:
            sys.stderr = old_stderr

def open_temp_chrome_profile(incognito_mode=False):

    chromeOptions = Options()

    # ✅ Usar el perfil por defecto de Chrome para mantener configuraciones y extensiones
    chrome_user_data_path = os.path.join(os.getenv("LOCALAPPDATA", ""), "Google", "Chrome", "User Data")
    chromeOptions.add_argument(f"--user-data-dir={chrome_user_data_path}")
    chromeOptions.add_argument("--profile-directory=Default")

    # ✅ Rutas a las extensiones en Chrome
    # Extensión de Captcha (existente)
    extension_id_captcha = "dknlfmjaanfblgfdfebhijalfmhmjjjo"
    # Nueva extensión a agregar
    extension_id_new = "hlkenndednhfkekhgcdicdfddnkalmdm"
    
    perfiles_a_buscar = [d for d in os.listdir(chrome_user_data_path)
                         if os.path.isdir(os.path.join(chrome_user_data_path, d)) and (d == "Default" or d.startswith("Profile"))]

    # Buscar la extensión de Captcha
    base_extension_dir_captcha = None
    for perfil in perfiles_a_buscar:
        posible_dir = os.path.join(chrome_user_data_path, perfil, "Extensions", extension_id_captcha)
        if os.path.isdir(posible_dir):
            base_extension_dir_captcha = posible_dir
            break

    if base_extension_dir_captcha is None:
        raise FileNotFoundError(f"❌ La extensión de Captcha con ID {extension_id_captcha} no se encontró en ningún perfil de Chrome dentro de {chrome_user_data_path}.")

    # Buscar la nueva extensión
    base_extension_dir_new = None
    for perfil in perfiles_a_buscar:
        posible_dir = os.path.join(chrome_user_data_path, perfil, "Extensions", extension_id_new)
        if os.path.isdir(posible_dir):
            base_extension_dir_new = posible_dir
            break

    if base_extension_dir_new is None:
        raise FileNotFoundError(f"❌ La nueva extensión con ID {extension_id_new} no se encontró en ningún perfil de Chrome dentro de {chrome_user_data_path}.")

    # Obtener la versión más reciente de la extensión de Captcha
    versiones_captcha = sorted([d for d in os.listdir(base_extension_dir_captcha) if os.path.isdir(os.path.join(base_extension_dir_captcha, d))], reverse=True)
    if not versiones_captcha:
        raise FileNotFoundError(f"❌ No se encontraron versiones dentro de {base_extension_dir_captcha}")
    extension_path_captcha = os.path.join(base_extension_dir_captcha, versiones_captcha[0])

    # Obtener la versión más reciente de la nueva extensión
    versiones_new = sorted([d for d in os.listdir(base_extension_dir_new) if os.path.isdir(os.path.join(base_extension_dir_new, d))], reverse=True)
    if not versiones_new:
        raise FileNotFoundError(f"❌ No se encontraron versiones dentro de {base_extension_dir_new}")
    extension_path_new = os.path.join(base_extension_dir_new, versiones_new[0])

    # Verificar que existan los manifest.json
    manifest_path_captcha = os.path.join(extension_path_captcha, "manifest.json")
    manifest_path_new = os.path.join(extension_path_new, "manifest.json")
    
    if not os.path.exists(manifest_path_captcha):
        raise FileNotFoundError(f"❌ No se encontró manifest.json en {extension_path_captcha}")
    if not os.path.exists(manifest_path_new):
        raise FileNotFoundError(f"❌ No se encontró manifest.json en {extension_path_new}")

    # Cargar ambas extensiones
    chromeOptions.add_argument(f"--load-extension={extension_path_captcha},{extension_path_new}")
    chromeOptions.add_argument(f"--disable-extensions-except={extension_path_captcha},{extension_path_new}")

    # 🚫 Desactivar Brave Shields (bloqueador nativo de anuncios) para evitar bloqueo de recursos
    chromeOptions.add_argument("--disable-brave-shields-backend")
    chromeOptions.add_argument("--brave.disable_shields=true")
    # Otras características internas que pueden interferir
    chromeOptions.add_argument("--disable-features=BraveAds,BraveRewards")

    # ⚙️ Opciones de rendimiento
    # Activar modo incógnito si se solicita
    if incognito_mode:
        chromeOptions.add_argument("--incognito")
    
    chromeOptions.add_argument("--disable-gpu")
    chromeOptions.add_argument("--disable-software-rasterizer")
    chromeOptions.add_argument("--disable-features=VizDisplayCompositor")
    chromeOptions.add_argument("--disable-accelerated-2d-canvas")
    chromeOptions.add_argument("--disable-accelerated-video-decode")
    chromeOptions.add_argument("--disable-accelerated-mjpeg-decode")

    # 🕵️ Evitar detección de Selenium
    chromeOptions.add_experimental_option("excludeSwitches", ["enable-automation"])
    chromeOptions.add_experimental_option("useAutomationExtension", False)

    # 🚀 Crear driver (Chrome predeterminado)
    with suppress_stderr():
        driver = webdriver.Chrome(options=chromeOptions)
    

    return driver




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

        # Ruta del ejecutable
        adb_path = r"C:\Adb\adb"

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

            with open(file_path, "a", encoding="utf-8") as f:
                successful_iterations = 0
                failed_iterations = 0
                timeout_errors = 0
                other_errors = 0

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

                    # Ejecutar el comando para activar el modo avión
                    # subprocess.run([adb_path, "shell", "cmd", "connectivity", "airplane-mode", "enable"])
                    # print("✅ Modo avión activado.")
                    # time.sleep(5)  # Esperar 3 segundos

                    # Ejecutar el comando para desactivar el modo avión
                    # subprocess.run([adb_path, "shell", "cmd", "connectivity", "airplane-mode", "disable"])
                    # print("✅ Modo avión desactivado.")
                    # time.sleep(5)  # Esperar 5 segundos

                    # Inicializar el navegador
                    driver = open_temp_chrome_profile(incognito_mode=True)

                    try:
                        mail_ok, final_email = mail_actions(driver, domain)
                        if not mail_ok:
                            print("❌ Falló la creación del correo en 33mail.")
                            continue

                        is_verified = login_to_hostinger(driver, email_hostinger, password_hostinger)

                        if is_verified:
                            f.write(f"{final_email.strip()}\n")
                            f.flush()
                            os.fsync(f.fileno())
                            print(f"📝 Email verificado guardado: {final_email.strip()}")
                            at_least_one_verified = True
                            successful_iterations += 1
                        else:
                            f.write(f"{final_email.strip()} <-- no verificado\n")
                            f.flush()
                            os.fsync(f.fileno())
                            print(f"⚠️ Email no verificado: {final_email.strip()}")
                            failed_iterations += 1

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
                            driver.quit()
                        except Exception as e:
                            print(f"⚠️ Error al cerrar el navegador: {e}")
                            # Continuar aunque falle el cierre del navegador

                    elapsed = time.time() - start_time
                    print(f"⏱️ Tiempo de ejecución de la iteración: {elapsed:.2f} segundos")

            # Resumen de estadísticas para este ID
            print(f"\n📊 Resumen para ID {id}:")
            print(f"  ✅ Iteraciones exitosas: {successful_iterations}")
            print(f"  ❌ Iteraciones fallidas: {failed_iterations}")
            if timeout_errors > 0:
                print(f"  ⏰ Errores de timeout: {timeout_errors}")
            if other_errors > 0:
                print(f"  ⚠️ Otros errores: {other_errors}")
            print(f"  📈 Tasa de éxito: {(successful_iterations/iteraciones)*100:.1f}%")
            print("-" * 50)

        return at_least_one_verified

    except Exception as e:
        print(f"❌ Error al ejecutar el checker: {e}")
        return False


if __name__ == "__main__":
    run_checker()