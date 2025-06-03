from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from app.database.database import get_email_by_id

import sys
import os

# Agrega la raíz del proyecto al sys.path para poder importar 'app'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.confirmabot.hostinger_login import login_to_hostinger
from app.confirmabot.hostinger_actions import perform_hostinger_actions
from app.confirmabot.mail_actions import mail_actions



def open_temp_chrome_profile():
    chrome_options = Options()

    # Crear un perfil temporal (no requiere que cierres el Chrome real)
    chrome_options.add_argument("--user-data-dir=C:/temp/selenium-profile")
    chrome_options.add_argument("--profile-directory=Profile 1")

    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=chrome_options)
    return driver




def run_checker():
    print("🟢 Ejecutando checker con el primer registro de la base de datos...")

    try:
        registro = get_email_by_id(1)
        if not registro:
            print("❌ No se encontró ningún registro con ID 1.")
            return

        email_hostinger = registro["email_hostinger"]
        password_hostinger = registro["password_hostinger"]
        domain = registro["email"]

        driver = open_temp_chrome_profile()

        mail_ok, generated_email = mail_actions(driver, domain)
        if not mail_ok:
            print("❌ Falló la creación del correo en 33mail.")
            driver.quit()
            return

        login_to_hostinger(driver, email_hostinger, password_hostinger)

    except Exception as e:
        print(f"❌ Error al ejecutar el checker: {e}")







if __name__ == "__main__":
    run_checker()