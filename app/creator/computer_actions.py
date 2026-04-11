import os
import re
import sys
import pyautogui
import time
import random
import string
import pyperclip
from faker import Faker
from app.creator.image_config import get_image_path
from app.utils.path_utils import get_base_path

def get_resource_path(relative_path):
    """
    Obtiene la ruta de un recurso tanto en desarrollo como en ejecutable.
    Esta función es específica para recursos que van dentro del ejecutable.
    Para archivos de usuario (imágenes, cuentas), usar get_base_path().
    """
    if getattr(sys, 'frozen', False):
        # Si estamos ejecutando desde un ejecutable (PyInstaller)
        base_path = sys._MEIPASS
    else:
        # Si estamos en desarrollo, usar el directorio raíz del proyecto
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def find_image(image_path, confidence=0.7, silent=False):
    """Busca una imagen en la pantalla y devuelve su ubicación si la encuentra."""
    image_path = get_resource_path(image_path)
    try:
        if not os.path.exists(image_path):
            #if not silent:
            #    print(f"⚠️ La imagen no existe: {image_path}")
            return None

        location = pyautogui.locateCenterOnScreen(
            image_path, confidence=confidence, grayscale=True)
        
        if location:
            #if not silent:
            #    print(f"✅ Imagen detectada: {image_path} en {location}")
            return location
        else:
            #if not silent:
            #    print(f"❌ Imagen no encontrada: {image_path}")
            pass

    except Exception as e:
        #if not silent:
        #    print(f"⚠️ Error detectando {image_path}: {e}")
        pass
    return None

def find_creator_image(image_name, confidence=0.8, return_box=False, grayscale=True, region=None, browser_name=None):
    """
    Busca una imagen del creator por su nombre.
    
    Args:
        image_name: Nombre de la imagen
        confidence: Nivel de confianza (0-1). Valores más altos = más estricto (default: 0.8)
        return_box: Si es True, devuelve el Box completo en lugar del centro
        grayscale: Si es True, convierte a escala de grises antes de comparar (default: True)
        region: Tupla (left, top, width, height) para limitar la búsqueda a una región específica
        browser_name: Nombre del navegador. Si se proporciona, busca en su directorio específico.
    
    Returns:
        Point (x, y) si return_box=False, o Box (left, top, width, height) si return_box=True
    """
    image_path = get_image_path(image_name, browser_name=browser_name)
    if not image_path:
        return None
    
    # Usar la ruta absoluta directamente sin get_resource_path
    try:
        if not os.path.exists(image_path):
            return None

        # Asegurar que confidence esté en un rango válido y sea razonable
        confidence = max(0.5, min(0.99, confidence))  # Entre 0.5 y 0.99

        # Preparar parámetros para pyautogui
        kwargs = {
            'confidence': confidence,
            'grayscale': grayscale
        }
        
        # Agregar región si se especifica
        if region:
            kwargs['region'] = region

        if return_box:
            # Devolver el área completa de la imagen
            box = pyautogui.locateOnScreen(image_path, **kwargs)
            return box
        else:
            # Devolver solo el centro
            location = pyautogui.locateCenterOnScreen(image_path, **kwargs)
            return location
    except pyautogui.ImageNotFoundException:
        # Imagen no encontrada - esto es normal, no es un error
        return None
    except Exception as e:
        # Log del error para debugging (solo si es un error real)
        error_type = type(e).__name__
        error_msg = str(e)
        # No mostrar errores de archivo faltante o problemas de codificación (son normales)
        # Estos errores son esperados y no necesitan mostrarse en consola
        if "ImageNotFoundException" not in error_type and "NotFound" not in error_type:
            # Filtrar errores comunes de codificación o archivo faltante
            if "can't open/read file" not in error_msg.lower() and "file is missing" not in error_msg.lower():
                # Solo mostrar errores realmente inesperados (muy raros)
                pass
        return None

def image_exists(image_path, confidence=0.7):
    """Verifica si una imagen existe en la pantalla."""
    location = find_image(image_path, confidence)
    return location is not None

def creator_image_exists(image_name, confidence=0.8):
    """Verifica si una imagen del creator existe en la pantalla."""
    location = find_creator_image(image_name, confidence=confidence)
    return location is not None

def click_coordinates(coordinates, double_click=False, button='left'):
    """
    Hace click o doble click en coordenadas específicas
    """
    try:
        # Parsear las coordenadas del formato "EjeXxEjeY"
        if 'x' not in coordinates:
            print(f"⚠️ Formato de coordenadas inválido: {coordinates}")
            return False
        
        x_str, y_str = coordinates.split('x')
        x = int(x_str)
        y = int(y_str)
        
        # Configurar pyautogui
        pyautogui.PAUSE = 0.01
        pyautogui.FAILSAFE = False
        
        # Mover mouse a la posición
        #print(f"🖱️ Moviendo mouse a coordenadas: {x}, {y}")
        pyautogui.moveTo(x, y, duration=0.5)  # Movimiento más lento
        time.sleep(0.3)  # Esperar más tiempo a que llegue
        
        # Verificar que el mouse llegó a la posición correcta
        current_pos = pyautogui.position()
        #print(f"📍 Posición actual del mouse: {current_pos}")
        
        # Verificar si está cerca de la posición objetivo (tolerancia de 5 píxeles)
        if abs(current_pos.x - x) <= 5 and abs(current_pos.y - y) <= 5:
            #print("✅ Mouse en posición correcta, haciendo click")
            if double_click:
                # Doble click
                pyautogui.click(button=button)
                time.sleep(0.15)  # Delay entre clicks
                pyautogui.click(button=button)
            else:
                # Click simple
                pyautogui.click(button=button)
        else:
            #print(f"⚠️ Mouse no llegó a la posición correcta. Objetivo: ({x}, {y}), Actual: ({current_pos.x}, {current_pos.y})")
            return False
        
        return True
        
    except ValueError as e:
        print(f"⚠️ Error parseando coordenadas '{coordinates}': {e}")
        return False
    except Exception as e:
        print(f"⚠️ Error haciendo click en coordenadas '{coordinates}': {e}")
        return False

def type_text(text):
    """
    Escribe texto usando el portapapeles (copiar y pegar)
    """
    try:
        # Guardar el contenido actual del portapapeles
        original_clipboard = pyperclip.paste()
        
        # Copiar el texto al portapapeles
        pyperclip.copy(text)
        time.sleep(0.1)  # Pequeña pausa para asegurar que se copió
        
        # Pegar usando Ctrl+V
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.1)  # Pequeña pausa después de pegar
        
        # Restaurar el contenido original del portapapeles
        pyperclip.copy(original_clipboard)
        
        #print(f"✅ Texto pegado: {text}")
        return True
    except Exception as e:
        print(f"⚠️ Error pegando texto '{text}': {e}")
        return False

def press_key(key):
    """
    Presiona una tecla específica
    """
    try:
        pyautogui.press(key)
        #print(f"✅ Tecla presionada: {key}")
        return True
    except Exception as e:
        print(f"⚠️ Error presionando tecla '{key}': {e}")
        return False

def generate_random_password(length=12):
    """
    Genera una contraseña aleatoria
    """
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(random.choice(characters) for _ in range(length))
    return password

def wait_for_image(image_path, max_attempts=90, delay_between_attempts=1, confidence=0.7, silent=False):

    if not silent:
        print(f"🔍 Iniciando observador para imagen: {os.path.basename(image_path)}")
        print(f"📊 Configuración: {max_attempts} intentos, {delay_between_attempts}s entre intentos")
    
    for attempt in range(1, max_attempts + 1):
        #if not silent:
        #    print(f"🔎 Intento {attempt}/{max_attempts}...")
        
        location = find_image(image_path, confidence, silent)
        if location:
            if not silent:
                print(f"✅ ¡Imagen encontrada en el intento {attempt}!")
            return location
        
        if attempt < max_attempts:
            #if not silent:
            #    print(f"⏳ Esperando {delay_between_attempts}s antes del siguiente intento...")
            time.sleep(delay_between_attempts)
    
    if not silent:
        print(f"❌ No se encontró la imagen después de {max_attempts} intentos")
    return None

def wait_for_creator_image(image_name, max_attempts=90, delay_between_attempts=1, confidence=0.8, silent=False, grayscale=True, region=None, browser_name=None):

    image_path = get_image_path(image_name, browser_name=browser_name)
    if not image_path:
        # No mostrar mensaje - es normal que algunas imágenes no existan (variantes opcionales)
        return None
    
    # Asegurar que confidence sea razonable (mínimo 0.7 para evitar falsos positivos)
    if confidence < 0.7:
        confidence = 0.7
    
    # Usar find_creator_image directamente para tener control sobre grayscale
    for attempt in range(1, max_attempts + 1):
        location = find_creator_image(image_name, confidence=confidence, return_box=False, grayscale=grayscale, region=region, browser_name=browser_name)
        if location:
            # Validación adicional: verificar una segunda vez para evitar falsos positivos
            # Solo si max_attempts es 1 (búsqueda rápida), hacer doble verificación
            if max_attempts == 1:
                time.sleep(0.1)  # Pequeña pausa
                location2 = find_creator_image(image_name, confidence=confidence, return_box=False, grayscale=grayscale, region=region, browser_name=browser_name)
                if not location2:
                    # Si la segunda verificación falla, probablemente fue un falso positivo
                    continue
            
            if not silent:
                print(f"✅ ¡Imagen '{image_name}' encontrada en el intento {attempt}!")
            return location
        
        if attempt < max_attempts:
            time.sleep(delay_between_attempts)
    
    if not silent:
        print(f"❌ No se encontró la imagen '{image_name}' después de {max_attempts} intentos")
    return None

def generate_random_name():
    """
    Genera un nombre aleatorio de 2 palabras usando faker - nombres en inglés (Estados Unidos)
    """
    fake = Faker('en_US')  # Usar inglés de Estados Unidos para nombres
    first_name = fake.first_name()
    second_name = fake.first_name()
    return f"{first_name} {second_name}"

def generate_random_lastname():
    """
    Genera un apellido aleatorio de 2 palabras usando faker - apellidos en inglés (Estados Unidos)
    """
    fake = Faker('en_US')  # Usar inglés de Estados Unidos para apellidos
    first_lastname = fake.last_name()
    second_lastname = fake.last_name()
    return f"{first_lastname} {second_lastname}"

def generate_email_prefix():
    """
    Genera un prefijo aleatorio para emails usando palabras del archivo JSON + números
    """
    import random
    import json
    import os
    
    # Ruta del archivo de palabras
    current_dir = os.path.dirname(os.path.abspath(__file__))
    words_file = os.path.join(current_dir, "email_words.json")
    
    try:
        # Cargar palabras desde el archivo JSON
        with open(words_file, 'r', encoding='utf-8') as f:
            words_data = json.load(f)
        
        # Combinar todas las categorías de palabras
        all_words = []
        for category, words in words_data.items():
            all_words.extend(words)
        
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        # Fallback a palabras básicas si hay error
        all_words = [
            "alex", "mike", "john", "sarah", "emma", "david", "lisa", "chris", "anna", "mark",
            "creative", "smart", "cool", "happy", "bright", "quick", "swift", "clever", "bold", "wise",
            "tech", "pro", "ace", "star", "nova", "zen", "max", "neo", "ultra", "mega",
            "blue", "red", "green", "gold", "silver", "dark", "light", "bright", "deep", "pure"
        ]
    
    # Generar prefijo combinando 1-2 palabras + números
    num_palabras = random.randint(1, 2)
    palabras_seleccionadas = random.sample(all_words, num_palabras)
    
    # Combinar palabras
    base = ''.join(palabras_seleccionadas)
    
    # Agregar números (4-6 dígitos para mayor unicidad)
    num_digitos = random.randint(4, 6)
    numeros = ''.join([str(random.randint(0, 9)) for _ in range(num_digitos)])
    
    # Combinar base + números
    prefix = base + numeros
    
    # Asegurar que tenga entre 10-18 caracteres (aumentado para acomodar más números)
    if len(prefix) < 10:
        # Agregar más números si es muy corto
        extra_digitos = 10 - len(prefix)
        prefix += ''.join([str(random.randint(0, 9)) for _ in range(extra_digitos)])
    elif len(prefix) > 18:
        # Truncar si es muy largo
        prefix = prefix[:18]
    
    return prefix

def generate_domain_fill():
    """
    Relleno de subdominio: palabra (solo letras) + tres dígitos aleatorios 0-9.
    
    Ejemplo: "creative847", "smart032"
    
    Returns:
        str: Letras minúsculas + exactamente 3 dígitos
    """
    import random
    import json
    import os
    
    # Ruta del archivo de palabras
    current_dir = os.path.dirname(os.path.abspath(__file__))
    words_file = os.path.join(current_dir, "email_words.json")
    
    try:
        # Cargar palabras desde el archivo JSON
        with open(words_file, 'r', encoding='utf-8') as f:
            words_data = json.load(f)
        
        # Combinar todas las categorías de palabras
        all_words = []
        for category, words in words_data.items():
            all_words.extend(words)
        
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        # Fallback a palabras básicas si hay error
        all_words = [
            "creative", "smart", "cool", "happy", "bright", "quick", "swift", "clever", "bold", "wise",
            "tech", "pro", "ace", "star", "nova", "zen", "max", "neo", "ultra", "mega",
            "blue", "red", "green", "gold", "silver", "dark", "light", "bright", "deep", "pure",
            "alex", "mike", "john", "sarah", "emma", "david", "lisa", "chris", "anna", "mark"
        ]
    
    palabra = random.choice(all_words)
    if isinstance(palabra, str):
        palabra = "".join(c for c in palabra.lower() if c.isalpha()) or "mail"
    digitos = "".join(str(random.randint(0, 9)) for _ in range(3))
    return f"{palabra}{digitos}"

def apply_domain_fill(domain, fill_enabled=False):
    """
    Aplica relleno al dominio si está habilitado.
    
    Ejemplo:
        - Sin relleno: @pepito.com -> @pepito.com
        - Con relleno: @pepito.com -> @creative847.pepito.com
    
    Args:
        domain (str): Dominio con o sin @ al inicio
        fill_enabled (bool): Si se debe aplicar el relleno
    
    Returns:
        str: Dominio con o sin relleno según la configuración
    """
    if not fill_enabled:
        return domain
    
    # Asegurar que el dominio tenga @ al inicio
    domain_clean = domain if domain.startswith('@') else f"@{domain}"
    
    # Remover el @ para trabajar con el dominio
    domain_without_at = domain_clean[1:]
    
    # Verificar si el dominio ya tiene relleno (contiene un punto antes del dominio base)
    # Si el dominio ya tiene relleno, no aplicar otro
    # Un dominio con relleno tiene formato: relleno.dominio.com
    # Un dominio sin relleno tiene formato: dominio.com
    parts = domain_without_at.split('.')
    
    # Si tiene más de 2 partes (ej: relleno.dominio.com), probablemente ya tiene relleno
    # Pero también podría ser un dominio como subdomain.dominio.com
    # Para ser más seguro, verificamos si la primera parte parece ser un relleno
    # (contiene números al final, que es característico del relleno)
    if len(parts) > 2:
        first_part = parts[0]
        # Ya rellenado: palabra + 3 dígitos (nuevo formato)
        if first_part and re.fullmatch(r"[a-z]{3,30}\d{3}", first_part):
            return domain_clean
        # Compatibilidad: relleno antiguo solo letras largo
        if first_part and first_part.isalpha() and len(first_part) >= 8:
            return domain_clean
    
    # Generar el relleno
    fill = generate_domain_fill()
    
    # Aplicar el relleno: @relleno.dominio (con punto entre relleno y dominio)
    filled_domain = f"@{fill}.{domain_without_at}"
    
    return filled_domain


_RANDOM_DOMAIN_TLDS = (
    "com", "net", "org", "io", "co", "app", "dev", "live", "tech",
    "studio", "digital", "global", "cloud", "online", "network", "group",
)
# Lista por defecto si el usuario no configura terminaciones (Gestión de navegadores)
DEFAULT_RANDOM_DOMAIN_TLDS = _RANDOM_DOMAIN_TLDS

# Etiquetas TLD: com, co.uk (hasta 3 segmentos alfanuméricos)
_RANDOM_TLD_PATTERN = re.compile(
    r"^([a-z0-9]{2,24})(\.[a-z0-9]{2,24}){0,2}$"
)


def parse_configured_random_tlds(raw):
    """
    Parsea texto del usuario (com, .net; gov | co.uk) en lista de TLDs válidos.
    None o vacío -> None (usar _RANDOM_DOMAIN_TLDS en el caller).
    """
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    seen = set()
    out = []
    for part in re.split(r"[\s,;|/]+", s):
        p = part.strip().lower()
        if not p:
            continue
        if p.startswith("."):
            p = p[1:]
        if _RANDOM_TLD_PATTERN.fullmatch(p) and p not in seen:
            seen.add(p)
            out.append(p)
    return out if out else None


def _normalize_single_tld(tld):
    if not tld or not isinstance(tld, str):
        return None
    p = tld.strip().lower()
    if p.startswith("."):
        p = p[1:]
    if _RANDOM_TLD_PATTERN.fullmatch(p):
        return p
    return None


def _load_terminos_tecnicos_json():
    """Términos tech desde email_words.json (categoría terminos_tecnicos)."""
    import json
    current_dir = os.path.dirname(os.path.abspath(__file__))
    words_file = os.path.join(current_dir, "email_words.json")
    try:
        with open(words_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        raw = data.get("terminos_tecnicos") or []
        return [
            "".join(c for c in w.lower() if c.isalpha())
            for w in raw
            if isinstance(w, str) and w.strip()
        ]
    except (FileNotFoundError, json.JSONDecodeError, TypeError):
        return ["tech", "node", "cloud", "data", "code", "web", "api", "dev", "net", "hub", "core", "edge"]


# Sufijos y raíces cortas con “olor” a producto tech (complementan terminos_tecnicos)
_TECH_DOMAIN_FRAGMENTS = (
    "ex", "io", "ly", "fy", "hub", "api", "dev", "net", "pro", "neo", "zen", "bit", "hex", "lab",
    "sys", "tec", "vox", "tch", "ops", "max", "web", "app", "core", "edge", "node", "data", "grid",
    "code", "byte", "pix", "sdk", "sql", "iot", "vpn", "cdn", "rpc", "gpu", "cpu", "jwt", "ssl",
    "tls", "nfc", "ocr", "log", "bin", "key", "tag", "mux", "bot", "dns", "rtc", "gui", "cli", "rx",
    "tx", "nx", "vm", "os", "ai", "ml", "ui", "ux", "qa", "ci", "cd",
)


def _random_short_name_stub():
    """Nombre / apodo muy corto en inglés (4–6 letras), estilo louis / fraddy."""
    fake = Faker("en_US")
    name = "".join(c for c in fake.first_name().lower() if c.isalpha())
    if len(name) < 4:
        name = name + "".join(c for c in fake.first_name().lower() if c.isalpha())
    if len(name) < 4:
        name = (name + "alex")[:6]
    target = random.randint(4, 6)
    if len(name) > target:
        if random.random() < 0.45 and len(name) >= 5:
            cut = random.randint(4, min(6, len(name)))
            name = name[:cut]
        else:
            name = name[:target]
    # A veces consonante doble tipo fraddy (solo consonantes, sin tocar vocales)
    if random.random() < 0.18 and len(name) >= 4:
        i = random.randint(1, len(name) - 2)
        ch = name[i]
        if ch.isalpha() and ch not in "aeiou" and ch != name[i + 1] and ch != name[i - 1]:
            name = name[: i + 1] + ch + name[i + 1 :]
    name = "".join(c for c in name if c.isalpha())
    if len(name) < 4:
        name = (name + "ian")[:6]
    return name[:6]


def _random_tech_stub_for_domain():
    """Fragmento corto tech (2–5 letras): sufijos tipo ex/io/tch o trozos de terminos_tecnicos."""
    terms = _load_terminos_tecnicos_json()
    terms = [t for t in terms if len(t) >= 2]
    if random.random() < 0.55:
        return random.choice(_TECH_DOMAIN_FRAGMENTS)
    if not terms:
        return random.choice(_TECH_DOMAIN_FRAGMENTS)
    w = random.choice(terms)
    if len(w) <= 4:
        return w
    if len(w) == 5:
        return w if random.random() < 0.55 else w[:4]
    ln = random.randint(2, min(4, len(w)))
    start = random.randint(0, len(w) - ln)
    return w[start : start + ln]


def generate_random_email_domain(tld=None):
    """
    Dominio sintético corto: nombre breve + fragmento tech (ej. louistch.gov, fraddyex.com).

    Args:
        tld: TLD fijo (ej. 'com', 'co.uk'). None = elige al azar entre _RANDOM_DOMAIN_TLDS.

    Returns:
        str: @slug.tld
    """
    name_part = _random_short_name_stub()
    tech_part = _random_tech_stub_for_domain()
    slug = (name_part + tech_part).lower()
    slug = "".join(c for c in slug if c.isalpha())
    if len(slug) < 6:
        slug = (slug + random.choice(_TECH_DOMAIN_FRAGMENTS))[:10]
    if len(slug) > 14:
        slug = slug[:14]
    fixed = _normalize_single_tld(tld) if tld else None
    if fixed:
        chosen = fixed
    else:
        chosen = random.choice(_RANDOM_DOMAIN_TLDS)
    return f"@{slug}.{chosen}"


def generate_email_with_domain_format(domain):
    """
    Genera un email con formato específico: nombre1apellido1numero1nombre2apellido2.puntoletrasnumeros@dominio
    
    Ejemplo: fernandaganavarro3886perez.b9i5@gmail.com
    
    Args:
        domain: Dominio del email (con o sin @ al inicio)
    
    Returns:
        str: Email completo con el formato especificado
    """
    import random
    import string
    
    # Asegurar que el dominio tenga @ al inicio
    if not domain.startswith('@'):
        domain = f"@{domain}"
    
    # Generar nombres y apellidos usando Faker
    fake = Faker('en_US')
    
    # Primera parte: nombre1 + apellido1 + número (4 dígitos)
    nombre1 = fake.first_name().lower()
    apellido1 = fake.last_name().lower()
    numero1 = ''.join([str(random.randint(0, 9)) for _ in range(4)])
    parte1 = f"{nombre1}{apellido1}{numero1}"
    
    # Segunda parte: nombre2/apellido2 (puede ser nombre o apellido)
    # Usar aleatoriamente un nombre o apellido
    if random.choice([True, False]):
        parte2 = fake.first_name().lower()
    else:
        parte2 = fake.last_name().lower()
    
    # Tercera parte: punto + combinación de letras y números (4 caracteres)
    caracteres = string.ascii_lowercase + string.digits
    parte3 = ''.join(random.choice(caracteres) for _ in range(4))
    
    # Combinar todo: parte1 + parte2 + . + parte3 + dominio
    email = f"{parte1}{parte2}.{parte3}{domain}"
    
    return email

def get_clipboard_content():
    """
    Obtiene el contenido del portapapeles
    """
    try:
        content = pyperclip.paste()
        return content
    except Exception as e:
        print(f"❌ Error obteniendo contenido del portapapeles: {e}")
        return ""

def wait_for_spinner(image_name, max_attempts=90, delay_between_attempts=0.2, confidence=0.5, silent=False, browser_name=None):
    """
    Detecta un spinner de carga que está en constante rotación.
    Usa un confidence bajo por defecto (0.5) para detectar el spinner aunque no sea idéntico
    a la imagen de referencia, ya que está rotando constantemente.
    
    Args:
        image_name: Nombre de la imagen del spinner
        max_attempts: Número máximo de intentos
        delay_between_attempts: Tiempo entre intentos (más corto para spinners, default: 0.2s)
        confidence: Nivel de confianza (default: 0.5 - bajo para detectar variaciones)
        silent: Si es True, no imprime mensajes
    
    Returns:
        Point (x, y) si encuentra el spinner, None si no
    """
    image_path = get_image_path(image_name, browser_name=browser_name)
    if not image_path:
        if not silent:
            print(f"❌ No se encontró la imagen del spinner: {image_name}")
        return None
    
    # Usar confidence bajo para detectar el spinner aunque esté en diferentes posiciones de rotación
    # Hacer múltiples intentos rápidos para "atrapar" el spinner en alguna de sus posiciones
    for attempt in range(1, max_attempts + 1):
        # Hacer varios intentos rápidos seguidos para aumentar las chances de detectarlo
        for quick_attempt in range(5):  # 5 intentos rápidos por ciclo
            location = find_creator_image(
                image_name,
                confidence=confidence,
                return_box=False,
                grayscale=True,
                browser_name=browser_name
            )
            if location:
                if not silent:
                    print(f"✅ Spinner '{image_name}' encontrado en el intento {attempt} (quick {quick_attempt + 1})")
                return location
            time.sleep(0.03)  # Muy corto entre intentos rápidos (30ms)
        
        if attempt < max_attempts:
            time.sleep(delay_between_attempts)
    
    if not silent:
        print(f"❌ No se encontró el spinner '{image_name}' después de {max_attempts} intentos")
    return None
