"""
Cliente WebSocket para conectar ConfirmaBot a la API.

Este script integra el login existente con la conexión WebSocket.
"""

import socketio
import requests
import time
import sys
import threading
from app.utils.server_config import AUTH_API_BASE_URL, BACKEND_BASE_URL
from app.database.database import (
    save_user,
    delete_logged_in_user,
    get_logged_in_user,
    save_bot_connection_config,
    get_bot_connection_config,
    set_active_browser_by_name,
    set_active_browsers_by_names,
    set_creator_user_agent_by_browser_name,
    get_all_browsers,
    get_domain_sync_payload,
    apply_remote_domain_config,
    save_global_time_config,
)

# Configuración
LOGIN_URL = f"{AUTH_API_BASE_URL}/login"
VERIFY_TOKEN_URL = f"{AUTH_API_BASE_URL}/verify-token"
WS_URL = BACKEND_BASE_URL  # URL base para WebSocket

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


def apply_remote_browser_if_present(command_payload):
    """
    Aplica el navegador enviado desde servidor para centralizar configuración por instancia.

    Returns:
        tuple[bool, str | None]: (True, None) si está OK o no hay navegador remoto;
        (False, mensaje_error) si el navegador remoto no existe localmente.
    """
    raw_list = command_payload.get("preferred_browsers")
    if isinstance(raw_list, list) and len(raw_list) > 0:
        ok, message = set_active_browsers_by_names(raw_list)
        if ok:
            if message:
                print(f"🌐 {message}")
            return True, None
        print(f"⚠️ {message}")
        try:
            available = [b.get("name", "") for b in get_all_browsers() if b.get("name")]
            available = [name for name in available if name]
            available_text = ", ".join(available) if available else "Ninguno"
        except Exception:
            available_text = "No disponible"
        alert_message = (
            "Los navegadores seleccionados en el servidor no coinciden con esta máquina.\n\n"
            f"Detalle: {message}\n"
            f"Navegadores disponibles en este bot: {available_text}\n\n"
            "Ajusta la selección en el servidor o configura los perfiles en confirmbot."
        )
        _show_browser_not_available_messagebox(alert_message)
        return False, message

    preferred_browser = (command_payload.get('preferred_browser') or '').strip()
    if not preferred_browser:
        return True, None

    ok, message = set_active_browser_by_name(preferred_browser)
    if ok:
        print(f"🌐 {message}")
        return True, None
    else:
        print(f"⚠️ {message}")
        try:
            available = [b.get("name", "") for b in get_all_browsers() if b.get("name")]
            available = [name for name in available if name]
            available_text = ", ".join(available) if available else "Ninguno"
        except Exception:
            available_text = "No disponible"

        alert_message = (
            "El navegador seleccionado en el servidor no está configurado en este bot.\n\n"
            f"Navegador solicitado: {preferred_browser}\n"
            f"Navegadores disponibles en esta máquina: {available_text}\n\n"
            "Configura este navegador en el bot o selecciona otro en el servidor."
        )
        _show_browser_not_available_messagebox(alert_message)
        return False, alert_message


def _show_browser_not_available_messagebox(message_text):
    """Muestra alerta local cuando el navegador remoto no existe en esta máquina."""
    try:
        import tkinter as tk
        from tkinter import messagebox

        def _show():
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            messagebox.showerror("Navegador no configurado", message_text)
            root.destroy()

        threading.Thread(target=_show, daemon=True).start()
    except Exception as e:
        print(f"⚠️  No se pudo mostrar messagebox: {e}")


def apply_remote_user_agent_if_present(command_payload):
    """
    Aplica User-Agent enviado por servidor para el navegador seleccionado.
    """
    raw_list = command_payload.get("preferred_browsers")
    raw_uas = command_payload.get("remote_user_agents")
    if (
        isinstance(raw_list, list)
        and len(raw_list) > 0
        and isinstance(raw_uas, dict)
    ):
        missing_ua: list[str] = []
        for name in raw_list:
            bn = str(name).strip()
            if not bn:
                continue
            ua = (raw_uas.get(bn) or raw_uas.get(name) or "").strip()
            if not ua:
                missing_ua.append(bn)
        if missing_ua:
            msg = (
                "Faltan User-Agent en el servidor para estos navegadores: "
                + ", ".join(missing_ua)
                + "\n\nConfigúralos en Config Bots (api_login)."
            )
            _show_browser_not_available_messagebox(msg)
            return False, msg
        for name in raw_list:
            bn = str(name).strip()
            if not bn:
                continue
            ua = (raw_uas.get(bn) or raw_uas.get(name) or "").strip()
            ok, message = set_creator_user_agent_by_browser_name(bn, ua)
            if not ok:
                print(f"⚠️ {message}")
                _show_browser_not_available_messagebox(message)
                return False, message
            print(f"🌐 {message}")
        return True, None

    preferred_browser = (command_payload.get('preferred_browser') or '').strip()
    remote_user_agent = (command_payload.get('remote_user_agent') or '').strip()

    if not preferred_browser:
        return True, None

    if not remote_user_agent:
        msg = (
            "No se recibió User-Agent desde el servidor para el navegador seleccionado.\n\n"
            f"Navegador: {preferred_browser}\n"
            "Configura el User-Agent en 'Config Bots' del servidor."
        )
        _show_browser_not_available_messagebox(msg)
        return False, msg

    ok, message = set_creator_user_agent_by_browser_name(preferred_browser, remote_user_agent)
    if ok:
        print(f"🌐 {message}")
        return True, None

    print(f"⚠️ {message}")
    _show_browser_not_available_messagebox(message)
    return False, message


def sync_available_browsers_to_server(force=False):
    """Envía al servidor el catálogo local de navegadores configurados."""
    # Durante el callback `connect` puede ocurrir que `sio.connected` aún no esté
    # en True aunque la conexión ya esté en curso. `force=True` evita perder ese primer envío.
    if not force and not sio.connected:
        return

    try:
        browsers = get_all_browsers()
        browser_names = [b.get("name", "").strip() for b in browsers if b.get("name")]
        browser_names = [name for name in browser_names if name]
        sio.emit('sync_available_browsers', {'browsers': browser_names})
        print(f"📤 Catálogo de navegadores enviado al servidor ({len(browser_names)} elementos)")
    except Exception as e:
        print(f"⚠️  No se pudo sincronizar catálogo de navegadores: {e}")


def sync_domain_config_to_server(force=False):
    """Envía al servidor la configuración local de dominios/TLD."""
    if not force and not sio.connected:
        return
    try:
        payload = get_domain_sync_payload()
        sio.emit('sync_domain_config', payload)
        domains_count = len(payload.get("domains", []))
        tlds_count = len(payload.get("random_tlds", []))
        print(f"📤 Configuración de dominios enviada al servidor ({domains_count} dominios, {tlds_count} tlds)")
    except Exception as e:
        print(f"⚠️  No se pudo sincronizar configuración de dominios: {e}")


def apply_remote_domain_config_if_present(command_payload):
    """Aplica configuración remota de dominios enviada por servidor."""
    remote_cfg = command_payload.get('remote_domain_config')
    if not remote_cfg:
        return True, None
    ok, message = apply_remote_domain_config(remote_cfg)
    if ok:
        print(f"🌐 {message}")
        return True, None
    _show_browser_not_available_messagebox(message or "No se pudo aplicar dominios remotos")
    return False, message


def apply_remote_creator_time_config_if_present(command_payload):
    """
    Aplica ciclo / hora programada del creator enviados por el servidor (SQLite global_time_config).
    Solo actúa si el payload incluye remote_creator_time_config.
    """
    remote = command_payload.get("remote_creator_time_config")
    if not remote or not isinstance(remote, dict):
        return True, None
    t = (remote.get("time_config_type") or "manual").strip().lower()
    if t not in ("manual", "scheduled", "cycle", "both"):
        t = "manual"
    st = remote.get("scheduled_time")
    tz = remote.get("timezone")
    if st is not None and not str(st).strip():
        st = None
    if tz is not None and not str(tz).strip():
        tz = None
    cm = remote.get("cycle_time_minutes")
    apc = remote.get("accounts_per_cycle")
    try:
        if cm is not None:
            cm = int(cm)
    except (TypeError, ValueError):
        cm = None
    try:
        if apc is not None:
            apc = int(apc)
    except (TypeError, ValueError):
        apc = None
    try:
        ok = save_global_time_config(
            scheduled_time=st,
            timezone=tz,
            cycle_time_minutes=cm,
            time_config_type=t,
            accounts_per_cycle=apc,
        )
    except Exception as e:
        print(f"Advertencia: error aplicando tiempo/ciclo del creator remoto: {e}")
        return False, str(e)
    if ok:
        print(
            f"Configuración de creator remota aplicada: tipo={t}, ciclo={cm} min, cuentas/ciclo={apc}"
        )
        return True, None
    return False, "No se pudo guardar la configuración de tiempo remota"


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
    # Primer intento inmediato al conectar.
    sync_available_browsers_to_server(force=True)
    sync_domain_config_to_server(force=True)

    # Reintento corto para asegurar envío cuando el transporte termina de estabilizar.
    def _retry_sync_catalog():
        try:
            time.sleep(1.0)
            sync_available_browsers_to_server(force=True)
            sync_domain_config_to_server(force=True)
        except Exception:
            pass

    sio.start_background_task(_retry_sync_catalog)


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
        domain_ok, domain_error = apply_remote_domain_config_if_present(data)
        if not domain_ok:
            sio.emit('status_update', {'status': 'stopped'})
            sio.emit('action_completed', {
                'action': 'start',
                'success': False,
                'message': domain_error
            })
            return
        browser_ok, browser_error = apply_remote_browser_if_present(data)
        if not browser_ok:
            sio.emit('status_update', {'status': 'stopped'})
            sio.emit('action_completed', {
                'action': 'start',
                'success': False,
                'message': browser_error
            })
            return
        ua_ok, ua_error = apply_remote_user_agent_if_present(data)
        if not ua_ok:
            sio.emit('status_update', {'status': 'stopped'})
            sio.emit('action_completed', {
                'action': 'start',
                'success': False,
                'message': ua_error
            })
            return

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
        domain_ok, domain_error = apply_remote_domain_config_if_present(data)
        if not domain_ok:
            sio.emit('status_update', {'status': 'stopped'})
            sio.emit('action_completed', {
                'action': 'execute_creator',
                'success': False,
                'message': domain_error
            })
            return
        browser_ok, browser_error = apply_remote_browser_if_present(data)
        if not browser_ok:
            sio.emit('status_update', {'status': 'stopped'})
            sio.emit('action_completed', {
                'action': 'execute_creator',
                'success': False,
                'message': browser_error
            })
            return
        ua_ok, ua_error = apply_remote_user_agent_if_present(data)
        if not ua_ok:
            sio.emit('status_update', {'status': 'stopped'})
            sio.emit('action_completed', {
                'action': 'execute_creator',
                'success': False,
                'message': ua_error
            })
            return

        time_ok, time_error = apply_remote_creator_time_config_if_present(data)
        if not time_ok:
            sio.emit('status_update', {'status': 'stopped'})
            sio.emit('action_completed', {
                'action': 'execute_creator',
                'success': False,
                'message': time_error or 'Error al aplicar tiempo/ciclo remoto',
            })
            return

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
