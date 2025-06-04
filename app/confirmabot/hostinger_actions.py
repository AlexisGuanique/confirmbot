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
        wait = WebDriverWait(driver, 15)
        try:
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "tbody")))
        except:
            print("❌ Timeout: No se pudo cargar la bandeja de entrada.")
            return False

        max_attempts = 10
        for attempt in range(1, max_attempts + 1):
            print(f"🔄 Intento {attempt} de {max_attempts}")

            try:
                refresh_btn = driver.find_element(By.ID, "rcmbtn113")
                refresh_btn.click()
                time.sleep(2)

                unread_emails = driver.find_elements(By.CSS_SELECTOR, "tr.message.unread a")

                if not unread_emails and attempt in [3, 6]:
                    print("🔍 Verificando si hay contador de mensajes...")
                    try:
                        driver.find_element(By.XPATH, "//span[contains(@class, 'unreadcount') and contains(@class, 'skip-content')]")
                        print("📬 Contador encontrado. Refrescando la página...")
                        driver.refresh()
                        time.sleep(5)
                        unread_emails = driver.find_elements(By.CSS_SELECTOR, "tr.message.unread a")
                    except:
                        print("⚠️ Contador no encontrado.")


                if not unread_emails:
                    print("🕐 No hay correos no leídos aún.")
                    time.sleep(2)
                    continue

                unread_emails[0].click()

                try:
                    WebDriverWait(driver, 15).until(
                        EC.frame_to_be_available_and_switch_to_it((By.ID, "messagecontframe"))
                    )
                except:
                    print("❌ Timeout: No se cargó el contenido del mensaje.")
                    return False

                try:
                    confirmation_link = WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/user/confirm/')]"))
                    )
                    link_url = confirmation_link.get_attribute("href")
                    print(f"🔗 Enlace encontrado: {link_url}")
                    confirmation_link.click()

                    driver.switch_to.default_content()
                    driver.switch_to.window(driver.window_handles[-1])

                    # 🟡 Intentar encontrar el elemento directamente varias veces sin esperar carga completa
                    for attempt in range(1, 11):
                        all_links = driver.find_elements(By.XPATH, "//a[@href='/help']")
                        if all_links:
                            print("🎉 Confirmación completada.")
                            return True
                        print(f"⏳ Buscando <a href='/help'>... intento {attempt}/10")
                        time.sleep(2)

                    print("❌ No se encontró el enlace '/help' tras varios intentos.")
                    return False


                except Exception as e:
                    print(f"⚠️ No se encontró el enlace de confirmación: {e}")

                finally:
                    driver.switch_to.default_content()

            except Exception as e:
                print(f"⚠️ Error en intento {attempt}: {e}")
                driver.switch_to.default_content()
                time.sleep(3)

    except Exception as e:
        print(f"❌ Error inesperado en bandeja de entrada: {e}")

    print("❌ No se pudo obtener el código de verificación tras múltiples intentos.")
    return False
