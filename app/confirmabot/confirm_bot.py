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



sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))



def open_temp_chrome_profile():
    chrome_options = Options()

    # ✅ Desactivar headless
    # chrome_options.add_argument("--headless")  ← asegurate de que esto esté desactivado

    # ✅ Perfil temporal único para evitar conflictos
    unique_profile = os.path.join(tempfile.gettempdir(), f"selenium-profile-{uuid.uuid4()}")
    chrome_options.add_argument(f"--user-data-dir={unique_profile}")

    # ✅ Evitar automatización visual (opcional)
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    # ✅ Forzar ventanas visibles (descomentar si hiciste pruebas con headless)
    chrome_options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=chrome_options)
    return driver



def run_checker():
    print("🟢 Ejecutando checker para todos los registros...")
    at_least_one_verified = False  # 🟢 Bandera de éxito

    try:
        total_registros = get_email_count()
        config = get_bot_settings()

        if total_registros == 0 or not config:
            print("❌ No hay registros válidos o configuración faltante.")
            return False

        iteraciones = config["iterations"]

        for id in range(1, total_registros + 1):
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

            # 🧹 Limpiar archivo al iniciar el ciclo para este ID
            open(file_path, "w", encoding="utf-8").close()

            with open(file_path, "a", encoding="utf-8") as f:
                for i in range(iteraciones):
                    print(f"🔁 Iteración {i + 1} de {iteraciones} para ID {id}")
                    start_time = time.time()

                    driver = open_temp_chrome_profile()

                    try:
                        mail_ok, final_email = mail_actions(driver, domain)
                        if not mail_ok:
                            print("❌ Falló la creación del correo en 33mail.")
                            continue
                        print(final_email)
                        is_verified = login_to_hostinger(driver, email_hostinger, password_hostinger)

                        if is_verified:
                            f.write(f"{final_email.strip()}\n")
                            print(f"📝 Email verificado guardado: {final_email.strip()}")
                            at_least_one_verified = True  # ✅ Marcamos éxito
                        else:
                            f.write(f"{final_email.strip()} <-- no verificado\n")
                            print(f"⚠️ Email no verificado: {final_email.strip()}")

                    except Exception as e:
                        print(f"❌ Error durante la iteración: {e}")

                    finally:
                        driver.quit()

                    elapsed = time.time() - start_time
                    print(f"⏱️ Tiempo de ejecución de la iteración: {elapsed:.2f} segundos")

        return at_least_one_verified  # ✅ Retornamos si fue exitoso

    except Exception as e:
        print(f"❌ Error al ejecutar el checker: {e}")
        return False



if __name__ == "__main__":
    run_checker()