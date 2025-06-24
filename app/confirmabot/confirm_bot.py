from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from app.database.database import get_email_by_id, get_email_count, get_bot_settings
import sys
import os
import tempfile
import uuid


from app.confirmabot.hostinger_login import login_to_hostinger
from app.confirmabot.mail_actions import mail_actions
import time  # ⏱️ Asegúrate de tener esta importación al inicio del archivo

stop_checker = False




sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


def stop_bot():
    global stop_checker
    stop_checker = True
    print("🛑 Señal de detención enviada al bot.")


def open_temp_chrome_profile():
    chrome_options = Options()

    # ✅ Crear perfil temporal único
    unique_profile = os.path.join(tempfile.gettempdir(), f"selenium-profile-{uuid.uuid4()}")
    chrome_options.add_argument(f"--user-data-dir={unique_profile}")

    # ✅ Evitar mensajes molestos y automatización detectada
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    # ✅ Forzar ventana visible
    chrome_options.add_argument("--start-maximized")

    # ✅ Desactivar caché para evitar errores por espacio
    chrome_options.add_argument("--disable-application-cache")
    chrome_options.add_argument("--disk-cache-size=0")

    # ✅ Evitar problemas en sistemas limitados
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")

    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        print(f"❌ Error al iniciar el navegador: {e}")
        return None  # Devolvemos None si no se puede iniciar el driver


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

                    # Inicializamos el driver
                    driver = open_temp_chrome_profile()

                    # Si el driver es None, terminamos la iteración
                    if not driver:
                        print("❌ Error al crear el navegador, saltando esta iteración.")
                        continue  # Saltamos a la siguiente iteración

                    # Usamos un ciclo para reintentar en caso de error
                    retries = 3
                    while retries > 0:
                        try:
                            mail_ok, final_email = mail_actions(driver, domain)
                            if not mail_ok:
                                print("❌ Falló la creación del correo en 33mail.")
                                retries -= 1  # Reintentar
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
                            break  # Si no hubo error, salimos del ciclo

                        except Exception as e:
                            print(f"❌ Error durante la iteración: {e}")
                            retries -= 1  # Reintentar

                        if retries == 0:
                            print(f"❌ Se alcanzaron los intentos máximos para el registro ID {id}. Saltando...")

                    # Intentar cerrar el driver con seguridad
                    try:
                        driver.quit()
                    except Exception as e:
                        print(f"⚠️ Error al cerrar el driver: {e}")

                    elapsed = time.time() - start_time
                    print(f"⏱️ Tiempo de ejecución de la iteración: {elapsed:.2f} segundos")

        return at_least_one_verified

    except Exception as e:
        print(f"❌ Error al ejecutar el checker: {e}")
        return False



if __name__ == "__main__":
    run_checker()