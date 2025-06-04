from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tkinter import messagebox
import sys
from app.confirmabot.hostinger_actions import perform_hostinger_actions
import time

import concurrent.futures

def login_to_hostinger(driver, email, password):
    try:
        if not email or not password:
            print("⚠️ Credenciales no proporcionadas.")
            messagebox.showerror(
                "Credenciales de Hostinger faltantes",
                "Debes ingresar tu email y contraseña de Hostinger.\n\nHazlo desde la interfaz de configuración y vuelve a ejecutar la aplicación."
            )
            sys.exit()

        print("🌐 Abriendo bandeja de entrada de Hostinger...")

        def open_hostinger():
            driver.get("https://mail.hostinger.com/?_task=mail&_mbox=INBOX.Confirmar")

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(open_hostinger)
            try:
                future.result(timeout=30)
            except concurrent.futures.TimeoutError:
                print("❌ Timeout: la página de Hostinger no respondió a tiempo.")
                return False


        max_retries = 10
        for attempt in range(1, max_retries + 1):
            print(f"⏳ Intento número: {attempt}")

            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, "rcmloginuser"))
                )
                break
            except:
                print(f"⏳ Esperando formulario de login... intento {attempt}/{max_retries}")
                time.sleep(1)
        else:
            print("❌ No se pudo cargar el formulario de login después de varios intentos.")
            return False

        # ✅ Sólo ahora podemos confirmar que el login es posible
        print("✅ Login automático comenzando...")

        user_input = driver.find_element(By.ID, "rcmloginuser")
        pass_input = driver.find_element(By.ID, "rcmloginpwd")
        login_button = driver.find_element(By.ID, "rcmloginsubmit")

        user_input.clear()
        user_input.send_keys(email)
        pass_input.clear()
        pass_input.send_keys(password)
        login_button.click()

        print("✅ Login automático completado.")

        success = perform_hostinger_actions(driver)
        if success:
            print("✅ Acción completada después del login.")
        else:
            print("⚠️ No se pudo completar la acción después del login.")

        return success

    except Exception as e:
        print(f"❌ Error durante el login: {e}")
        return False
