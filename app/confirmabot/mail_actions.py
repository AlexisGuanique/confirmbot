from faker import Faker
import time
import random
import string
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

fake = Faker()

def generate_custom_username():

    word = fake.word().lower()
    number = random.randint(0, 600)
    letters = ''.join(random.choices(string.ascii_lowercase, k=4))
    return f"{word}{number}{letters}"

def generate_secure_password(length=10):

    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))


def mail_actions(driver, domain):
    try:
        print("🌐 Abriendo 33mail para crear cuenta...")
        driver.get("https://www.33mail.com/signup")
        print("📨 Iniciando acciones en la página de 33mail...")

        # 👉 Generar datos
        username = generate_custom_username()
        generated_email = f"{username}{domain}"
        password = generate_secure_password()

        wait = WebDriverWait(driver, 30)

        # 👉 Email destino
        input_email = wait.until(EC.presence_of_element_located((By.ID, "lbl-13")))
        input_email.clear()
        input_email.send_keys(generated_email)

        # 👉 Username
        input_username = wait.until(EC.presence_of_element_located((By.ID, "lbl-14")))
        input_username.clear()
        input_username.send_keys(username)

        # 👉 Contraseña
        input_password = wait.until(EC.presence_of_element_located((By.ID, "lbl-15")))
        input_password.clear()
        input_password.send_keys(password)

        # 👉 Confirmar contraseña
        input_password_confirm = wait.until(EC.presence_of_element_located((By.ID, "lbl-16")))
        input_password_confirm.clear()
        input_password_confirm.send_keys(password)

        print(f"📧 Email generado: {generated_email}")
        print(f"👤 Username: {username}")
        print(f"🔒 Password: {password}")

        # 👉 Botón de registro
        submit_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, '//input[@type="submit" and @value="Continue signup"]'))
        )
        submit_button.click()
        print("🚀 Formulario enviado. Esperando confirmación final...")

        # ✅ Esperar a que se cargue el header con enlace a dashboard
        wait.until(EC.presence_of_element_located((By.XPATH, '//a[@href="/dashboard"]')))
        print("✅ Registro completado y página final cargada.")

        return True, generated_email

    except Exception as e:
        print(f"❌ Error durante las acciones en mail: {e}")
        return False, None
