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

def open_temp_chrome_profile():

    chromeOptions = Options()

    # ✅ Crear perfil temporal limpio de Chrome para evitar conflictos
    unique_profile = os.path.join(tempfile.gettempdir(), f"selenium-profile-{uuid.uuid4()}")
    chromeOptions.add_argument(f"--user-data-dir={unique_profile}")

    # ✅ Ruta a la extensión de Captcha en Chrome
    chrome_user_data_path = os.path.join(os.getenv("LOCALAPPDATA", ""), "Google", "Chrome", "User Data")
    extension_id = "dknlfmjaanfblgfdfebhijalfmhmjjjo"

    perfiles_a_buscar = [d for d in os.listdir(chrome_user_data_path)
                         if os.path.isdir(os.path.join(chrome_user_data_path, d)) and (d == "Default" or d.startswith("Profile"))]

    base_extension_dir = None
    for perfil in perfiles_a_buscar:
        posible_dir = os.path.join(chrome_user_data_path, perfil, "Extensions", extension_id)
        if os.path.isdir(posible_dir):
            base_extension_dir = posible_dir
            break

    if base_extension_dir is None:
        raise FileNotFoundError(f"❌ La extensión con ID {extension_id} no se encontró en ningún perfil de Chrome dentro de {chrome_user_data_path}.")

    versiones = sorted([d for d in os.listdir(base_extension_dir) if os.path.isdir(os.path.join(base_extension_dir, d))], reverse=True)

    if not versiones:
        raise FileNotFoundError(f"❌ No se encontraron versiones dentro de {base_extension_dir}")

    extension_path = os.path.join(base_extension_dir, versiones[0])

    manifest_path = os.path.join(extension_path, "manifest.json")
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"❌ No se encontró manifest.json en {extension_path}")

    # Cargar únicamente la extensión necesaria y deshabilitar las demás.
    chromeOptions.add_argument(f"--load-extension={extension_path}")
    chromeOptions.add_argument(f"--disable-extensions-except={extension_path}")

    # 🚫 Desactivar Brave Shields (bloqueador nativo de anuncios) para evitar bloqueo de recursos
    chromeOptions.add_argument("--disable-brave-shields-backend")
    chromeOptions.add_argument("--brave.disable_shields=true")
    # Otras características internas que pueden interferir
    chromeOptions.add_argument("--disable-features=BraveAds,BraveRewards")

    # ⚙️ Opciones de rendimiento
    # chromeOptions.add_argument("--incognito")
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
                for i in range(iteraciones):
                    if stop_checker:
                        print("🛑 Iteración interrumpida por el usuario.")
                        return at_least_one_verified

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
                        else:
                            f.write(f"{final_email.strip()} <-- no verificado\n")
                            f.flush()
                            os.fsync(f.fileno())
                            print(f"⚠️ Email no verificado: {final_email.strip()}")

                    except Exception as e:
                        print(f"❌ Error durante la iteración: {e}")

                    finally:
                        driver.quit()

                    elapsed = time.time() - start_time
                    print(f"⏱️ Tiempo de ejecución de la iteración: {elapsed:.2f} segundos")

        return at_least_one_verified

    except Exception as e:
        print(f"❌ Error al ejecutar el checker: {e}")
        return False


if __name__ == "__main__":
    run_checker()