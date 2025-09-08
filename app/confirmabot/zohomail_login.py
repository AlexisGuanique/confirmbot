import time
import re
from selenium.webdriver.common.by import By
from app.confirmabot.utils.zoho_emails import get_emails_imap, mark_email_as_read

def login_to_zohomail(driver, email_hostinger, password_hostinger):
    """Proceso automático de verificación de cuenta usando el driver proporcionado"""
    print("📬 Iniciando verificación automática...")
    
    # Buscar email de confirmación con reintentos
    for attempt in range(1, 11):  # 10 intentos máximo
        try:
            print(f"📬 Intento {attempt}/10 - Obteniendo emails...")
            emails = get_emails_imap(email_hostinger, password_hostinger)
            
            if emails:
                # Buscar emails de confirmación y ordenarlos por fecha (más nuevo primero)
                confirmation_emails = []
                for email_data in emails:
                    subject = email_data.get('subject', '').lower()
                    content = email_data.get('content', '').lower()
                    
                    if any(keyword in subject for keyword in ['confirm', 'verification', 'activate', 'signup']):
                        confirmation_emails.append(email_data)
                    elif any(keyword in content for keyword in ['confirm', 'verification', 'activate', 'click this link']):
                        confirmation_emails.append(email_data)
                
                if confirmation_emails:
                    # Ordenar por fecha (más nuevo primero) usando el ID del email
                    confirmation_emails.sort(key=lambda x: int(x['id']), reverse=True)
                    newest_email = confirmation_emails[0]
                    
                    print(f"✅ Email encontrado: {newest_email['subject']}")
                    
                    # Procesar el email más nuevo
                    success = process_confirmation_email(driver, newest_email['content'])
                    
                    if success:
                        # Marcar el email como leído después de procesarlo exitosamente
                        mark_success = mark_email_as_read(email_hostinger, password_hostinger, newest_email['id'])
                        if mark_success:
                            print("✅ Email marcado como leído")
                        else:
                            print("⚠️ No se pudo marcar el email como leído")
                        return True
                    else:
                        print("❌ Falló el procesamiento del email")
                        return False
            
            if attempt < 10:
                print("⏳ Esperando 5 segundos...")
                time.sleep(5)
                
        except Exception as e:
            print(f"❌ Error en intento {attempt}: {e}")
            if attempt < 10:
                time.sleep(5)
    
    print("❌ No se encontró email de confirmación")
    return False

def process_confirmation_email(driver, email_content):
    """Procesa el email de confirmación y abre el link automáticamente"""
    # Extraer link de confirmación
    url_pattern = r'https?://[^\s<>"]+'
    urls = re.findall(url_pattern, email_content)
    
    confirmation_link = None
    for url in urls:
        if any(keyword in url.lower() for keyword in ['confirm', 'verify', 'activate', '33mail']):
            confirmation_link = url
            break
    
    if not confirmation_link and urls:
        confirmation_link = urls[0]
    
    if not confirmation_link:
        print("❌ No se encontró link de confirmación")
        return False
    
    print(f"🔗 Abriendo link: {confirmation_link}")
    
    try:
        # Abrir el link en el driver existente
        driver.get(confirmation_link)
        print("✅ Link abierto")
        
        # Esperar confirmación automáticamente
        for attempt in range(1, 31):  # 1 minuto máximo
            try:
                driver.find_element(By.XPATH, "//a[@href='/help']")
                print("🎉 ¡Verificación exitosa!")
                return True
            except:
                pass
            
            time.sleep(2)
        
        print("❌ Timeout esperando confirmación")
        return False
        
    except Exception as e:
        print(f"❌ Error procesando confirmación: {e}")
        return False

