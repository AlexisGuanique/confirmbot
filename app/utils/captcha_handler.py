from selenium.webdriver.common.by import By
import time

def detect_and_handle_captcha(driver):
    """Detecta el captcha de LinkedIn y maneja errores automáticamente"""
    try:
        print("🔍 Buscando modal de verificación...")
        
        # Buscar el modal
        modal = driver.find_element(By.CSS_SELECTOR, "section[aria-modal='true']")
        if not modal.is_displayed():
            return False
        
        print("✅ Modal de verificación encontrado")
        
        # Buscar el iframe
        iframe = modal.find_element(By.CSS_SELECTOR, "iframe.challenge-dialog__iframe")
        print("✅ Iframe del captcha encontrado")
        
        # Cambiar al iframe para poder interactuar
        driver.switch_to.frame(iframe)
        time.sleep(2)
        
        # Verificar y cerrar errores del captcha automáticamente
        print("\n🔍 Verificando errores del captcha...")
        if detect_and_close_captcha_error(driver):
            print("✅ Errores del captcha manejados automáticamente")
            # Volver al contexto principal
            driver.switch_to.default_content()
            return "errors_handled"
        
        # Si no hay errores, analizar tipo de captcha
        captcha_type = analyze_captcha_type(driver)
        print(f"🎯 Tipo de captcha: {captcha_type}")
        
        # Proporcionar instrucciones básicas
        instructions = get_captcha_instructions(captcha_type)
        print(instructions)
        
        # Volver al contexto principal
        driver.switch_to.default_content()
        
        # Si no hay errores, esperar a que el usuario resuelva el captcha
        print("\n⏳ Esperando a que se resuelva el captcha...")
        print("💡 El bot está pausado aquí para que puedas resolver el captcha manualmente.")
        print("🔄 El bot verificará automáticamente cuando el modal desaparezca.")
        
        # Esperar a que el captcha se complete
        if wait_for_completion(driver):
            print("🎉 ¡Captcha completado exitosamente!")
            return "completed"
        else:
            print("⏰ Tiempo de espera agotado para el captcha.")
            return "timeout"
        
    except Exception as e:
        print(f"⚠️ Error al manejar captcha: {e}")
        try:
            driver.switch_to.default_content()
        except:
            pass
        return False

def detect_and_close_captcha_error(driver):
    """Detecta y cierra automáticamente errores del captcha"""
    try:
        print("🔍 Buscando errores del captcha...")
        
        # Buscar el elemento de error específico con más selectores
        error_selectors = [
            "div.body__banner.body__banner--error",
            "div[class*='body__banner'][class*='error']",
            "div[class*='error']",
            "div[role='alert']",
            "div[class*='alert']",
            "div[class*='notification']",
            "div[class*='message'][class*='error']",
            "div[class*='captcha'][class*='error']",
            "div[class*='challenge'][class*='error']",
            "div[class*='verification'][class*='error']",
            "span[class*='error']",
            "p[class*='error']"
        ]
        
        error_found = False
        for selector in error_selectors:
            try:
                error_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in error_elements:
                    if element.is_displayed():
                        # Verificar si contiene el texto de error específico
                        error_text = element.text.lower()
                        if any(keyword in error_text for keyword in [
                            'nocaptcha', 'user response code', 'missing', 'invalid', 'error',
                            'failed', 'incorrect', 'wrong', 'try again', 'verification failed',
                            'challenge failed', 'captcha failed', 'please try again'
                        ]):
                            print(f"✅ Error del captcha detectado: {selector}")
                            print(f"📝 Texto del error: {element.text[:100]}...")
                            
                            # Intentar cerrar el error
                            if close_captcha_error(driver, element):
                                error_found = True
                                break
                
                if error_found:
                    break
                    
            except Exception as e:
                continue
        
        # Si no se encontraron errores con selectores específicos, buscar por texto
        if not error_found:
            try:
                # Buscar elementos que contengan texto de error
                all_elements = driver.find_elements(By.CSS_SELECTOR, "*")
                for element in all_elements:
                    try:
                        if element.is_displayed() and element.text:
                            error_text = element.text.lower()
                            if any(keyword in error_text for keyword in [
                                'nocaptcha', 'user response code', 'missing', 'invalid', 'error',
                                'failed', 'incorrect', 'wrong', 'try again', 'verification failed',
                                'challenge failed', 'captcha failed', 'please try again'
                            ]):
                                print(f"✅ Error del captcha detectado por texto: {element.tag_name}")
                                print(f"📝 Texto del error: {element.text[:100]}...")
                                
                                # Intentar cerrar el error
                                if close_captcha_error(driver, element):
                                    error_found = True
                                    break
                    except:
                        continue
            except:
                pass
        
        # Búsqueda específica para el elemento de LinkedIn
        if not error_found:
            try:
                print("🔍 Búsqueda específica para elemento de LinkedIn...")
                # Buscar específicamente el elemento con la clase exacta
                linkedin_error = driver.find_element(By.CSS_SELECTOR, "div.body__banner.body__banner--error")
                if linkedin_error.is_displayed():
                    print("✅ Elemento de error de LinkedIn detectado específicamente")
                    print(f"📝 Texto: {linkedin_error.text[:100]}...")
                    
                    # Intentar cerrar el error
                    if close_captcha_error(driver, linkedin_error):
                        error_found = True
            except Exception as e:
                print(f"⚠️ No se encontró elemento específico de LinkedIn: {e}")
        
        if not error_found:
            print("✅ No se detectaron errores del captcha")
        
        return error_found
        
    except Exception as e:
        print(f"⚠️ Error al detectar errores del captcha: {e}")
        return False

def close_captcha_error(driver, error_element):
    """Cierra el error del captcha"""
    try:
        print("🔒 Intentando cerrar el error del captcha...")
        
        # Primero, volver al contexto principal para cerrar el modal
        try:
            print("🔄 Volviendo al contexto principal para cerrar el modal...")
            driver.switch_to.default_content()
            
            # Buscar el modal
            modal = driver.find_element(By.CSS_SELECTOR, "section[aria-modal='true']")
            
            # Buscar el botón específico de LinkedIn que cierra el modal
            try:
                close_button = modal.find_element(
                    By.CSS_SELECTOR, 
                    "button[data-tracking-control-name='registration-frontend_modal_dismiss']"
                )
                if close_button.is_displayed():
                    close_button.click()
                    print("✅ Modal cerrado con botón específico de LinkedIn")
                    time.sleep(1)
                    return True
            except:
                pass
            
            # Si no se encontró el botón específico, buscar el icon dismiss
            try:
                dismiss_icon = modal.find_element(By.CSS_SELECTOR, "icon.modal__dismiss-icon")
                if dismiss_icon.is_displayed():
                    dismiss_icon.click()
                    print("✅ Modal cerrado con icon dismiss específico")
                    time.sleep(1)
                    return True
            except:
                pass
            
            # Buscar otros botones de cerrar en el modal
            close_selectors = [
                "button[aria-label*='close']",
                "button[aria-label*='dismiss']",
                "button[class*='close']",
                "button[class*='dismiss']",
                "button[class*='modal__dismiss']",
                "button.modal__dismiss"
            ]
            
            for selector in close_selectors:
                try:
                    close_buttons = modal.find_elements(By.CSS_SELECTOR, selector)
                    for button in close_buttons:
                        if button.is_displayed():
                            print(f"✅ Botón de cerrar encontrado en modal: {selector}")
                            button.click()
                            print("✅ Modal cerrado exitosamente")
                            time.sleep(1)
                            return True
                except:
                    continue
                    
        except Exception as e:
            print(f"⚠️ Error al buscar en modal principal: {e}")
        
        print("⚠️ No se pudo cerrar el error del captcha automáticamente")
        return False
        
    except Exception as e:
        print(f"❌ Error al cerrar el error del captcha: {e}")
        return False

def interact_with_iframe_elements(driver):
    """Permite interactuar con elementos dentro del iframe del captcha"""
    try:
        print("🔄 Entrando al iframe para interactuar...")
        
        # Buscar el modal nuevamente
        modal = driver.find_element(By.CSS_SELECTOR, "section[aria-modal='true']")
        iframe = modal.find_element(By.CSS_SELECTOR, "iframe.challenge-dialog__iframe")
        
        # Cambiar al iframe
        driver.switch_to.frame(iframe)
        time.sleep(2)
        
        print("✅ Dentro del iframe. Puedes interactuar manualmente con los elementos.")
        print("💡 El bot está pausado aquí para que puedas hacer lo que necesites.")
        
        # Verificar y cerrar errores del captcha automáticamente
        print("\n🔍 Verificando errores del captcha...")
        if detect_and_close_captcha_error(driver):
            print("✅ Errores del captcha manejados automáticamente")
        
        # Mostrar elementos disponibles
        print("\n🔍 Elementos detectados en el iframe:")
        show_iframe_elements(driver)
        
        # Preguntar si quiere cerrar el modal después de interactuar
        input("\n⏸️ Presiona Enter cuando hayas terminado de interactuar...")
        
        # Volver al contexto principal
        driver.switch_to.default_content()
        
        # Preguntar si cerrar el modal
        close_choice = input("¿Quieres cerrar el modal ahora? (s/n): ").strip().lower()
        if close_choice in ['s', 'si', 'y', 'yes']:
            if close_modal(driver):
                return "closed"
        
        return "interacted"
        
    except Exception as e:
        print(f"⚠️ Error al interactuar con iframe: {e}")
        try:
            driver.switch_to.default_content()
        except:
            pass
        return False

def show_iframe_elements(driver):
    """Muestra los elementos disponibles dentro del iframe"""
    try:
        # Buscar elementos comunes
        element_types = {
            'Botones': "button",
            'Inputs': "input",
            'Imágenes': "img",
            'Divs': "div",
            'Iframes': "iframe",
            'Formularios': "form"
        }
        
        for element_name, selector in element_types.items():
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"  📱 {element_name}: {len(elements)} encontrados")
                    # Mostrar algunos detalles de los primeros elementos
                    for i, element in enumerate(elements[:3]):  # Solo los primeros 3
                        try:
                            if element.is_displayed():
                                text = element.text[:30] if element.text else "Sin texto"
                                class_name = element.get_attribute("class")[:30] if element.get_attribute("class") else "Sin clase"
                                print(f"    {i+1}. Texto: '{text}' | Clase: '{class_name}'")
                        except:
                            continue
            except:
                continue
                
    except Exception as e:
        print(f"⚠️ Error al mostrar elementos: {e}")

def analyze_captcha_type(driver):
    """Analiza el tipo de captcha"""
    captcha_types = {
        'recaptcha': ["div[class*='recaptcha']", "iframe[src*='recaptcha']"],
        'hcaptcha': ["div[class*='h-captcha']", "iframe[src*='hcaptcha']"],
        'turnstile': ["div[class*='turnstile']", "iframe[src*='turnstile']"],
        'puzzle': ["div[class*='puzzle']", "div[class*='challenge']"],
        'image': ["img[alt*='captcha']", "div[class*='image-captcha']"],
        'text': ["input[class*='captcha']", "div[class*='text-captcha']"]
    }
    
    for captcha_type, selectors in captcha_types.items():
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if any(e.is_displayed() for e in elements):
                    return captcha_type
            except:
                continue
    
    return 'unknown'

def get_captcha_instructions(captcha_type):
    """Obtiene instrucciones básicas según el tipo de captcha"""
    instructions = {
        'recaptcha': "✅ Captcha reCAPTCHA detectado",
        'hcaptcha': "✅ Captcha hCaptcha detectado",
        'turnstile': "✅ Captcha Turnstile detectado",
        'puzzle': "✅ Captcha tipo Puzzle detectado",
        'image': "✅ Captcha de imagen detectado",
        'text': "✅ Captcha de texto detectado",
        'unknown': "✅ Captcha detectado (tipo no identificado)"
    }
    return instructions.get(captcha_type, instructions['unknown'])

def close_modal(driver):
    """Cierra el modal de verificación"""
    try:
        print("🔒 Cerrando modal de verificación...")
        
        # Buscar el botón de cerrar
        close_button = driver.find_element(
            By.CSS_SELECTOR, 
            "button[data-tracking-control-name='registration-frontend_modal_dismiss']"
        )
        
        if close_button.is_displayed():
            close_button.click()
            print("✅ Modal cerrado exitosamente")
            time.sleep(1)
            return True
        else:
            print("❌ Botón de cerrar no visible")
            return False
            
    except Exception as e:
        print(f"❌ Error al cerrar modal: {e}")
        return False

def wait_for_completion(driver, max_wait=300):
    """Espera a que el captcha se complete verificando si el modal desapareció"""
    print("⏳ Verificando si el modal desapareció...")
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            # Verificar si el modal desapareció
            try:
                modal = driver.find_element(By.CSS_SELECTOR, "section[aria-modal='true']")
                if not modal.is_displayed():
                    print("🎉 ¡Modal desapareció!")
                    return True
            except:
                print("🎉 Modal no encontrado - puede haberse cerrado")
                return True
            
            # Verificar si hay algún mensaje de éxito o redirección
            try:
                # Buscar indicadores de éxito
                success_indicators = [
                    "div[class*='success']",
                    "div[class*='completed']",
                    "div[class*='verified']",
                    "div[class*='passed']"
                ]
                
                for selector in success_indicators:
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            if element.is_displayed():
                                print(f"🎉 Indicador de éxito detectado: {selector}")
                                return True
                    except:
                        continue
                        
            except:
                pass
            
            # Mostrar progreso cada 30 segundos
            elapsed = int(time.time() - start_time)
            if elapsed % 30 == 0 and elapsed > 0:
                print(f"⏳ Esperando... ({elapsed}s transcurridos)")
            
            time.sleep(3)
            
        except Exception as e:
            print(f"⚠️ Error durante la verificación: {e}")
            time.sleep(3)
    
    print("⏰ Tiempo de espera agotado.")
    return False
