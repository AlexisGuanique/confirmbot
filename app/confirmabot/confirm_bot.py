from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from app.database.database import get_email_by_id, get_email_count, get_bot_settings
import sys
import os
import tempfile
import uuid
import shutil

import os, uuid, tempfile, time, shutil, subprocess
from selenium.webdriver.chrome.service import Service

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



BRAVE_EXE = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"

def open_temp_chrome_profile(profile_name="Default", kill_residual=True, chromedriver_exe=None):
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

    # 👉 Ruta a la extensión (ajusta versión)
    extension_path = os.path.join(
        user_data_dir,
        profile_name,
        "Extensions",
        "dknlfmjaanfblgfdfebhijalfmhmjjjo",
        "0.4.13_0"
    )
    options.add_argument(f"--load-extension={extension_path}")

    if chromedriver_exe and os.path.exists(chromedriver_exe):
        service = Service(chromedriver_exe)
        driver = webdriver.Chrome(service=service, options=options)
    else:
        driver = webdriver.Chrome(options=options)

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
        pause_minutes = config.get("pause_minutes", 20)

        # Ruta del ejecutable ADB
        adb_path = r"C:\Adb\adb"
        print("🔄 Modo avión será ejecutado en cada iteración")

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

                    # Ejecutar comandos ADB siempre (con manejo de errores)
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
                        time.sleep(2)  # Pequeña pausa para simular el proceso

                    # Inicializar el navegador
                    driver = open_temp_chrome_profile()

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