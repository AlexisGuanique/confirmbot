from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pyperclip
import re
import time

def extract_code_from_text(text):
    match = re.search(r'\b\d{6}\b', text)
    return match.group(0) if match else None



def perform_hostinger_actions(driver):
    try:
        wait = WebDriverWait(driver, 30)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "tbody")))

        max_attempts = 10
        for attempt in range(1, max_attempts + 1):
            print(f"🔄 Intento {attempt} de {max_attempts}")

            try:
                # 🔄 Refresh inbox
                refresh_btn = driver.find_element(By.ID, "rcmbtn113")
                refresh_btn.click()
                time.sleep(2)

                # 📥 Check for unread emails
                unread_emails = driver.find_elements(By.CSS_SELECTOR, "tr.message.unread a")

                # 🔍 Check if 'Confirmar' folder has unread email
                if not unread_emails and attempt in [3, 6]:
                    print("🔍 Verificando si el contador '1' está visible en la carpeta Confirmar...")
                    try:
                        driver.find_element(By.XPATH, "//span[@class='unreadcount skip-content' and text()='1']")
                        print("📬 Correo no leído detectado en la carpeta. Refrescando página completa...")
                        driver.refresh()
                        time.sleep(5)
                        unread_emails = driver.find_elements(By.CSS_SELECTOR, "tr.message.unread a")
                    except:
                        print("⚠️ No se encontró el contador de correo no leído (span con '1').")

                # ⏳ No unread emails
                if not unread_emails:
                    print("🕐 No hay correos no leídos aún.")
                    time.sleep(2)
                    continue

                # 🖱️ Open first unread email
                unread_emails[0].click()

                WebDriverWait(driver, 20).until(
                    EC.frame_to_be_available_and_switch_to_it((By.ID, "messagecontframe"))
                )
                time.sleep(1.5)

                try:
                    # 🔗 Look for confirmation link
                    confirmation_link = WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/user/confirm/')]"))
                    )

                    link_url = confirmation_link.get_attribute("href")
                    print(f"🔗 Enlace de confirmación encontrado: {link_url}")
                    confirmation_link.click()
                    print("✅ Enlace de confirmación clickeado.")

                    # 🧭 Switch to confirmation tab
                    driver.switch_to.default_content()
                    driver.switch_to.window(driver.window_handles[-1])

                    # ✅ Confirm successful final page load
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.XPATH, "//a[@href='/help']"))
                    )

                    print("🎉 Confirmación detectada en nueva pestaña. Proceso finalizado.")
                    return True  # ✅ Verification success

                except Exception as e:
                    print(f"⚠️ No se pudo encontrar el enlace de confirmación: {e}")

                finally:
                    driver.switch_to.default_content()

            except Exception as e:
                print(f"⚠️ Error en intento {attempt}: {e}")
                driver.switch_to.default_content()
                time.sleep(3)

    except Exception as e:
        print(f"❌ Error inesperado: {e}")

    # ❌ If all attempts fail
    print("❌ No se pudo obtener el código de verificación tras múltiples intentos.")
    return False
