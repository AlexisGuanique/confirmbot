from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tkinter import messagebox
import sys
from app.confirmabot.hostinger_actions import perform_hostinger_actions

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
        driver.get("https://mail.hostinger.com/?_task=mail&_mbox=INBOX.Confirmar")

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "rcmloginuser"))
        )

        user_input = driver.find_element(By.ID, "rcmloginuser")
        pass_input = driver.find_element(By.ID, "rcmloginpwd")
        login_button = driver.find_element(By.ID, "rcmloginsubmit")

        user_input.clear()
        user_input.send_keys(email)

        pass_input.clear()
        pass_input.send_keys(password)

        login_button.click()
        print("✅ Login automático completado.")

        # 🔽 Ejecutar acciones de búsqueda de código después del login
        success = perform_hostinger_actions(driver)
        if success:
            print("✅ Acción completada después del login.")
        else:
            print("⚠️ No se pudo completar la acción después del login.")

        return success  # ✅ Devolver resultado de verificación

    except Exception as e:
        print(f"❌ Error durante el login: {e}")
        return False  # ⚠️ En caso de error también devolvemos False

