"""
Módulo para manejar acciones automatizadas en LinkedIn
"""

from app.confirmabot.confirm_bot import open_chrome_profile
from app.database.database import get_txt_email_by_id
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from tkinter import messagebox
from faker import Faker
import time

# Inicializar Faker para generar datos aleatorios
fake = Faker()

def process_linkedin_email(email_id):

    try:
        # Paso 1: Obtener el email de la base de datos
        email_data = get_txt_email_by_id(email_id)
        if not email_data:
            messagebox.showerror(
                "Email no encontrado", 
                f"❌ No se encontró email con ID: {email_id}\n\n"
                "💡 Verifica que el ID sea correcto y que exista en la base de datos"
            )
            return False
        
        email_text = email_data['email']
        
        # Paso 2: Abrir ventana de LinkedIn
        driver = open_chrome_profile(incognito_mode=True)
        driver.maximize_window()
        
        driver.get("https://www.linkedin.com/signup?_l=us&trk=guest_homepage-basic_nav-header-join.com/")
        
        # Paso 3: Esperar a que cargue la página y buscar el input de email
        wait = WebDriverWait(driver, 20)
        email_input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-tracking-control-name='email-address']"))
        )
        
        # Paso 4: Llenar el input con el email
        email_input.clear()
        email_input.send_keys(email_text)
        
        # Esperar un segundo después de pegar el email
        time.sleep(1)
        
        # Paso 5: Buscar y llenar el input de contraseña
        password_input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-tracking-control-name='registration-frontend_join-form-password']"))
        )
        
        # Generar contraseña aleatoria usando Faker
        random_password = fake.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)
        
        # Llenar el input de contraseña
        password_input.clear()
        password_input.send_keys(random_password)
        
        # Esperar un segundo después de pegar la contraseña
        time.sleep(1)
        
        # Paso 6: Buscar y hacer clic en el botón "Agree & Join"
        submit_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-tracking-control-name='registration-frontend_join-form-submit']"))
        )
        
        # Hacer clic en el botón
        submit_button.click()
        
        # Esperar un segundo después de hacer clic
        time.sleep(1)
        
        # Paso 7: Buscar y llenar el input del nombre
        first_name_input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-tracking-control-name='registration-frontend_join-form-name_first-name']"))
        )
        
        # Generar nombre aleatorio realista usando Faker
        random_first_name = fake.first_name()
        
        # Llenar el input del nombre
        first_name_input.clear()
        first_name_input.send_keys(random_first_name)
        
        # Esperar un segundo después de pegar el nombre
        time.sleep(1)
        
        # Paso 8: Buscar y llenar el input del apellido
        last_name_input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-tracking-control-name='registration-frontend_join-form-name_last-name']"))
        )
        
        # Generar apellido aleatorio realista usando Faker
        random_last_name = fake.last_name()
        
        # Llenar el input del apellido
        last_name_input.clear()
        last_name_input.send_keys(random_last_name)
        
        # Esperar un segundo después de pegar el apellido
        time.sleep(1)
        
        # Paso 9: Buscar y hacer clic en el botón "Continue"
        continue_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-tracking-control-name='registration-frontend_join-form-submit']"))
        )
        
        # Hacer clic en el botón Continue
        continue_button.click()
        
        # Esperar un segundo después de hacer clic
        time.sleep(1)
        
        return True
        
    except Exception as e:
        print(f"❌ Error en process_linkedin_email: {e}")
        return False

def close_linkedin_window(driver):
    """
    Cierra la ventana de LinkedIn de forma segura
    """
    try:
        if driver:
            driver.quit()
            print("🔒 Ventana de LinkedIn cerrada")
    except Exception as e:
        print(f"⚠️ Error al cerrar la ventana: {e}")

# Función para testing
if __name__ == "__main__":
    print("🧪 Probando función de LinkedIn...")
    success = process_linkedin_email(1)  # Procesar email con ID 1
    if success:
        print("✅ Prueba exitosa")
    else:
        print("❌ Prueba fallida")
