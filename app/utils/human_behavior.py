from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from faker import Faker
import time
import random

# Inicializar Faker para generar datos aleatorios
fake = Faker()

# Configuración de delays (30% más rápido)
DELAYS = {
    'typing': (0.035, 0.105),
    'mouse': (0.07, 0.21),
    'action': (0.35, 1.4),
    'wait': (10, 17)
}

def random_delay(min_seconds=None, max_seconds=None):
    """Delay aleatorio configurable"""
    if min_seconds is None:
        min_seconds, max_seconds = DELAYS['action']
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)
    return delay

def human_like_typing(element, text):
    """Escritura humana con delays aleatorios"""
    element.clear()
    min_delay, max_delay = DELAYS['typing']
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(min_delay, max_delay))

def random_mouse_movement(driver, element):
    """Movimiento de mouse seguro y aleatorio"""
    try:
        actions = ActionChains(driver)
        window_size = driver.get_window_size()
        max_x, max_y = window_size['width'] - 50, window_size['height'] - 50
        
        # Movimiento aleatorio antes del elemento
        if random.choice([True, False]):
            offset_x = random.randint(-20, 20)
            offset_y = random.randint(-15, 15)
            actions.move_by_offset(offset_x, offset_y)
            actions.perform()
            time.sleep(random.uniform(*DELAYS['mouse']))
        
        # Mover al elemento objetivo
        actions.move_to_element(element)
        actions.perform()
        
        # Movimiento sutil después
        if random.choice([True, False]):
            actions.move_by_offset(random.randint(-5, 5), random.randint(-3, 3))
            actions.perform()
            time.sleep(random.uniform(0.07, 0.14))
            
    except Exception as e:
        print(f"⚠️ Movimiento de mouse omitido: {e}")

def simulate_error_correction(element, text):
    """Simula corrección de errores de escritura"""
    try:
        if random.random() < 0.3:
            wrong_char = random.choice(['x', 'z', 'q'])
            element.send_keys(wrong_char)
            time.sleep(random.uniform(0.14, 0.35))
            element.send_keys(Keys.BACKSPACE)
            time.sleep(random.uniform(0.07, 0.21))
        
        human_like_typing(element, text)
        return True
        
    except Exception as e:
        print(f"⚠️ Simulación de error omitida: {e}")
        try:
            element.clear()
            element.send_keys(text)
            return True
        except Exception as write_error:
            print(f"❌ Error al escribir texto: {write_error}")
            return False

def random_pause():
    """Pausa aleatoria impredecible"""
    if random.random() < 0.4:
        time.sleep(random.uniform(0.35, 1.4))

def fill_field_safely(driver, element, text, field_name):
    """Llena un campo de forma segura con simulación humana"""
    try:
        random_mouse_movement(driver, element)
    except:
        pass
    
    if not simulate_error_correction(element, text):
        element.clear()
        element.send_keys(text)
    
    print(f"✅ Campo '{field_name}' llenado: {text[:20]}...")
    random_delay(0.7, 1.75)
    random_pause()

def click_button_safely(driver, button, button_name):
    """Hace clic en un botón de forma segura"""
    try:
        random_mouse_movement(driver, button)
    except:
        pass
    
    random_delay(0.56, 1.4)
    button.click()
    print(f"✅ Botón '{button_name}' clickeado")
    random_delay(0.84, 2.1)
    random_pause()

def generate_random_password():
    """Genera una contraseña aleatoria segura"""
    return fake.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)

def generate_random_name():
    """Genera un nombre aleatorio"""
    return fake.first_name()

def generate_random_lastname():
    """Genera un apellido aleatorio"""
    return fake.last_name()
