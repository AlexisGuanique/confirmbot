"""
Cliente WebSocket para conectar ConfirmaBot a la API.

Este script integra el login existente con la conexión WebSocket.
"""

import socketio
import requests
import time
import sys
import threading
from app.database.database import save_user, delete_logged_in_user, get_logged_in_user, save_bot_connection_config, get_bot_connection_config

# Configuración
BASE_API_URL = "http://34.29.59.97/api/auth"
LOGIN_URL = f"{BASE_API_URL}/login"
VERIFY_TOKEN_URL = f"{BASE_API_URL}/verify-token"
WS_URL = "http://34.29.59.97"  # URL base para WebSocket

# Crear cliente SocketIO
sio = socketio.Client()

# Variable global para controlar el bot
bot_running = False
bot_thread = None


def get_public_ip():
    """Obtiene la IP pública de la PC"""
    try:
        # Intentar obtener la IP pública desde varios servicios
        services = [
            'https://api.ipify.org',
            'https://icanhazip.com',
            'https://ifconfig.me/ip',
            'https://checkip.amazonaws.com'
        ]
        
        for service in services:
            try:
                response = requests.get(service, timeout=5)
                if response.status_code == 200:
                    ip = response.text.strip()
                    if ip and len(ip.split('.')) == 4:  # Validar formato IPv4
                        print(f"🌐 IP pública obtenida: {ip}")
                        return ip
            except:
                continue
        
        # Si no se pudo obtener la IP pública, usar hostname como fallback
        import socket
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"⚠️  No se pudo obtener IP pública, usando IP local: {local_ip}")
        return local_ip
    except Exception as e:
        print(f"⚠️  Error al obtener IP: {e}")
        import socket
        hostname = socket.gethostname()
        try:
            local_ip = socket.gethostbyname(hostname)
            return local_ip
        except:
            return "ConfirmaBot"


def get_bot_config():
    """Obtiene la configuración del bot desde la base de datos"""
    config = get_bot_connection_config()
    return config.get("bot_name", "ConfirmaBot"), config.get("bot_type", "creador")


def login(username, password):
    """Función de login existente"""
    payload = {"username": username, "password": password}

    try:
        response = requests.post(LOGIN_URL, json=payload)

        try:
            response_data = response.json()
        except ValueError:
            return {"error": "Error al procesar la respuesta del servidor"}

        if response.status_code != 200:
            return response_data 

        if "access_token" in response_data:
            user_data = {
                "id": response_data.get("id"),
                "name": response_data.get("name"),
                "lastname": response_data.get("lastname"),
                "access_token": response_data.get("access_token"),
            }
            save_user(user_data)
            return response_data  

        return {"error": "Respuesta inesperada del servidor"}

    except requests.RequestException as e:
        print(f"Error de conexión: {e}")
        return {"error": "Error de conexión con el servidor"}


def verify_token():
    """Función de verificación de token existente"""
    user = get_logged_in_user()

    if not user:
        return {"is_valid": False}  

    access_token = user.get("access_token")
    user_id = user.get("id")

    if not access_token:
        return {"is_valid": False}

    payload = {"access_token": access_token}
    url = f"{VERIFY_TOKEN_URL}/{user_id}"

    try:
        response = requests.post(url, json=payload)
        response_data = response.json()

        if response.status_code == 200:
            return response_data  
        else:
            return {"is_valid": False}

    except requests.RequestException as e:
        print(f"Error de conexión al verificar el token: {e}")
        return {"is_valid": False}


def logout():
    """Función para cerrar sesión: detiene el bot, desconecta WebSocket y elimina usuario local
    
    Returns:
        bool: True si había un usuario logueado y se cerró sesión correctamente, False si no había usuario
    """
    global bot_running
    
    # Verificar si hay un usuario logueado antes de proceder
    user = get_logged_in_user()
    if not user:
        print("⚠️  No hay usuario logueado para cerrar sesión")
        return False
    
    # Detener el bot si está corriendo
    if bot_running:
        bot_running = False
        print("🛑 Bot detenido durante logout")
    
    # Desconectar WebSocket si está conectado (enviando 'offline' antes)
    if sio.connected:
        try:
            sio.emit('status_update', {'status': 'offline'})
            time.sleep(0.3)  # Dar tiempo para que se envíe el mensaje
            sio.disconnect()
            print("🔌 WebSocket desconectado")
        except Exception as e:
            print(f"⚠️  Error al desconectar WebSocket: {e}")
    
    # Eliminar usuario de la base de datos local
    delete_logged_in_user()
    print("✅ Sesión cerrada correctamente")
    return True


# ========== HANDLERS DE WEBSOCKET ==========

@sio.event
def connect():
    """Se ejecuta cuando el bot se conecta exitosamente"""
    bot_name, _ = get_bot_config()
    print(f"✅ Bot '{bot_name}' conectado al servidor WebSocket")
    print(f"   Socket ID: {sio.sid}")
    # Notificar al servidor el estado actual (stopped si no está corriendo, running si está corriendo)
    try:
        if bot_running:
            sio.emit('status_update', {'status': 'running'})
            print("   📤 Estado 'running' enviado al servidor")
        else:
            sio.emit('status_update', {'status': 'stopped'})
            print("   📤 Estado 'stopped' enviado al servidor")
    except Exception as e:
        print(f"   ⚠️  Error al enviar status_update: {e}")


@sio.event
def disconnect():
    """Se ejecuta cuando el bot se desconecta del servidor"""
    global bot_running
    bot_running = False
    print("❌ Bot desconectado del servidor WebSocket")


@sio.event
def connected(data):
    """Recibe confirmación de conexión del servidor"""
    print(f"✅ Conexión confirmada por el servidor")
    print(f"   Datos recibidos: {data}")
    bot_id = data.get('bot_id')
    status = data.get('status', 'unknown')
    message = data.get('message', '')
    
    if bot_id:
        print(f"   🆔 Bot ID asignado: {bot_id}")
    if status:
        print(f"   📊 Estado: {status}")
    if message:
        print(f"   💬 Mensaje: {message}")


@sio.event
def command(data):
    """Recibe comandos del servidor (start, stop, etc.)"""
    global bot_running, bot_thread
    
    cmd = data.get('command')
    bot_id = data.get('bot_id')
    
    print(f"📨 Comando recibido: {cmd} (bot_id: {bot_id})")
    
    if cmd == 'start':
        if bot_running:
            print("⚠️  El bot ya está corriendo. No se puede iniciar otro.")
            sio.emit('action_completed', {
                'action': 'start',
                'success': False,
                'message': 'El bot ya está corriendo'
            })
            return
        
        print("🚀 Iniciando bot...")
        bot_running = True
        
        # Importar aquí para evitar importaciones circulares
        from app.confirmabot.confirm_bot import run_checker
        
        # Ejecutar el bot en un hilo separado
        bot_thread = threading.Thread(target=run_checker, daemon=True)
        bot_thread.start()
        
        # Enviar confirmación de inicio
        sio.emit('status_update', {'status': 'running'})
        print("✅ Bot iniciado correctamente")
        
        sio.emit('action_completed', {
            'action': 'start',
            'success': True,
            'message': 'Bot iniciado correctamente'
        })
        
    elif cmd == 'execute_creator':
        if bot_running:
            print("⚠️  El bot ya está corriendo. No se puede iniciar otro.")
            sio.emit('action_completed', {
                'action': 'execute_creator',
                'success': False,
                'message': 'El bot ya está corriendo'
            })
            return
        
        print("🚀 Iniciando Creator...")
        bot_running = True
        
        # Importar aquí para evitar importaciones circulares
        from app.creator.creator import execute_creator
        
        def execute_creator_wrapper():
            """Wrapper para ejecutar el creator y actualizar el estado al finalizar"""
            try:
                execute_creator()
            except Exception as e:
                print(f"❌ Error en Creator: {e}")
                import traceback
                traceback.print_exc()
            finally:
                # Actualizar estado cuando termine (exitoso o con error)
                global bot_running
                bot_running = False
                if sio.connected:
                    sio.emit('status_update', {'status': 'stopped'})
                    print("✅ Creator finalizado, estado actualizado a 'stopped'")
        
        # Ejecutar el creator en un hilo separado
        bot_thread = threading.Thread(target=execute_creator_wrapper, daemon=True)
        bot_thread.start()
        
        # Enviar confirmación de inicio
        sio.emit('status_update', {'status': 'running'})
        print("✅ Creator iniciado correctamente")
        
        sio.emit('action_completed', {
            'action': 'execute_creator',
            'success': True,
            'message': 'Creator iniciado correctamente'
        })
        
    elif cmd == 'stop':
        print("🛑 Deteniendo bot...")
        bot_running = False
        
        # Cerrar navegador si está abierto (usando coordenadas close_window)
        try:
            from app.database.database import get_active_browsers, get_creator_coordinates
            from app.creator.computer_actions import click_coordinates
            import time
            
            # Obtener navegadores activos
            active_browsers = get_active_browsers()
            if active_browsers:
                # Cerrar el primer navegador activo (o todos si hay varios)
                for browser in active_browsers[:1]:  # Solo cerrar el primero
                    browser_id = browser.get('id')
                    browser_name = browser.get('name', 'navegador')
                    
                    # Obtener coordenadas del navegador
                    coordinates = get_creator_coordinates(browser_id)
                    if coordinates:
                        close_window_coords = coordinates.get("close_window")
                        if close_window_coords:
                            print(f"🔄 Cerrando navegador {browser_name}...")
                            click_coordinates(close_window_coords)
                            time.sleep(1)
                            print(f"✅ Navegador {browser_name} cerrado")
                        else:
                            print(f"⚠️  No hay coordenadas 'close_window' configuradas para {browser_name}")
                    else:
                        print(f"⚠️  No se encontraron coordenadas para {browser_name}")
        except Exception as e:
            print(f"⚠️  Error al cerrar navegador: {e}")
        
        # Intentar detener tanto el confirm_bot como el creator
        try:
            from app.confirmabot.confirm_bot import stop_bot
            stop_bot()
        except Exception as e:
            print(f"⚠️  Error al detener confirm_bot: {e}")
        
        # También intentar detener el creator si está corriendo
        try:
            # El creator se detiene con la variable global bot_running
            # No hay una función stop_creator específica, se detiene naturalmente
            pass
        except Exception as e:
            print(f"⚠️  Error al detener creator: {e}")
        
        # Esperar a que el hilo termine si existe
        if bot_thread and bot_thread.is_alive():
            print("⏳ Esperando a que el bot termine...")
            bot_thread.join(timeout=5)
        
        # Enviar confirmación de detención
        sio.emit('status_update', {'status': 'stopped'})
        print("✅ Bot detenido correctamente")
        
        sio.emit('action_completed', {
            'action': 'stop',
            'success': True,
            'message': 'Bot detenido correctamente'
        })
    else:
        print(f"⚠️  Comando desconocido: {cmd}")


def connect_bot():
    """Conecta el bot al servidor vía WebSocket"""
    user = get_logged_in_user()
    
    if not user:
        print("❌ No hay usuario logueado. Ejecuta login() primero.")
        return False
    
    access_token = user.get("access_token")
    if not access_token:
        print("❌ No hay access_token disponible.")
        return False
    
    # Verificar que el token sea válido
    print("🔍 Verificando token...")
    verify_result = verify_token()
    if not verify_result.get("is_valid", False):
        print("❌ Token inválido o expirado. Haz login nuevamente.")
        return False
    print("✅ Token válido")
    
    # Si ya está conectado, desconectar primero (enviando 'offline' antes)
    if sio.connected:
        print("⚠️  Ya hay una conexión activa. Desconectando...")
        try:
            sio.emit('status_update', {'status': 'offline'})
            time.sleep(0.3)  # Dar tiempo para que se envíe el mensaje
        except Exception as e:
            print(f"⚠️  Error al enviar estado offline: {e}")
        try:
            sio.disconnect()
            time.sleep(0.5)  # Esperar un momento antes de reconectar
        except Exception as e:
            print(f"⚠️  Error al desconectar: {e}")
    
    try:
        # Obtener configuración del bot desde la base de datos
        bot_name, bot_type = get_bot_config()
        
        # Si no hay configuración guardada, usar valores por defecto y guardarlos
        if bot_name == "ConfirmaBot":
            import socket
            hostname = socket.gethostname()
            bot_name = f"ConfirmaBot-{hostname}"
            # Guardar como 'creador' para compatibilidad con la API
            save_bot_connection_config(bot_name, 'creador')
            bot_type = 'creador'
        
        # Conectar al servidor con autenticación
        print(f"🔌 Conectando bot '{bot_name}' al servidor {WS_URL}...")
        print(f"   Tipo de bot: {bot_type}")
        
        sio.connect(
            WS_URL,
            auth={
                'access_token': access_token,
                'bot_name': bot_name,
                'bot_type': bot_type
            },
            wait_timeout=10,
            transports=['websocket', 'polling']  # Intentar ambos métodos
        )
        
        print("✅ Conexión WebSocket establecida")
        return True
        
    except socketio.exceptions.ConnectionError as e:
        print(f"❌ Error de conexión: {e}")
        print("\n💡 Verifica que:")
        print("  1. El servidor esté corriendo en " + WS_URL)
        print("  2. La URL sea correcta")
        print("  3. El servidor tenga WebSockets habilitados")
        print("  4. No haya problemas de firewall o red")
        return False
    except socketio.exceptions.TimeoutError as e:
        print(f"❌ Timeout al conectar: {e}")
        print("   El servidor no respondió a tiempo")
        return False
    except Exception as e:
        print(f"❌ Error inesperado al conectar: {e}")
        import traceback
        traceback.print_exc()
        return False
