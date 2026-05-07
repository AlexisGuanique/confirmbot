def _verificar_cookie_duplicada(filepath, nueva_cookie):
    """
    Verifica si la nueva cookie ya existe en el archivo
    
    Args:
        filepath: Ruta del archivo de cookies
        nueva_cookie: Cookie nueva a verificar
    
    Returns:
        bool: True si la cookie es duplicada, False si es única
    """
    try:
        
        # Leer todas las líneas del archivo para verificar duplicados
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Buscar solo en las líneas que contienen datos (saltar encabezados)
        data_lines = []
        for line in lines:
            # Si la línea contiene tabs y no es un encabezado
            if '\t' in line and not line.startswith('CUENTAS') and not line.startswith('=') and not line.startswith('Total') and not line.startswith('Formato'):
                data_lines.append(line.strip())
        
        # Verificar TODAS las cookies guardadas (no solo las últimas 5)
        
        for i, line in enumerate(data_lines):
            parts = line.split('\t')
            if len(parts) >= 4:  # user_agent, email, password, cookie
                existing_cookie = parts[3]
                
                # Comparar cookies completas
                if existing_cookie == nueva_cookie:
                    return True
                
                # Verificar si las cookies son muy similares (mismo patrón base)
                if _son_cookies_similares(existing_cookie, nueva_cookie):
                    return True
        
        return False
        
    except Exception as e:
        return False  # En caso de error, permitir guardar


def _son_cookies_similares(cookie1, cookie2):
    """
    Verifica si dos cookies son muy similares (mismo patrón base de LinkedIn)
    """
    try:
        import json
        
        # Parsear ambas cookies como JSON
        data1 = json.loads(cookie1)
        data2 = json.loads(cookie2)
        
        # Verificar si tienen la misma estructura básica
        if len(data1) != len(data2):
            return False
        
        # Verificar si tienen los mismos nombres de cookies
        names1 = set([item.get('name', '') for item in data1])
        names2 = set([item.get('name', '') for item in data2])
        
        if names1 != names2:
            return False
        
        # Verificar si los dominios son iguales
        domains1 = set([item.get('domain', '') for item in data1])
        domains2 = set([item.get('domain', '') for item in data2])
        
        if domains1 != domains2:
            return False
        
        # Si llegamos aquí, las cookies tienen la misma estructura
        # Verificar si los valores son muy similares (mismo patrón)
        similar_count = 0
        total_cookies = len(data1)
        
        for i in range(total_cookies):
            value1 = data1[i].get('value', '')
            value2 = data2[i].get('value', '')
            
            # Si los valores son idénticos o muy similares
            if value1 == value2 or (len(value1) > 10 and len(value2) > 10 and value1[:10] == value2[:10]):
                similar_count += 1
        
        # Si más del 70% de las cookies son similares, considerarlas duplicadas
        similarity_ratio = similar_count / total_cookies if total_cookies > 0 else 0
        is_similar = similarity_ratio > 0.7
        
        
        return is_similar
        
    except Exception as e:
        return False

_password_usado = ""
_proxy_activado_por_click = False
_proxy_modo_usado = None  # "coordinates" | "windows" | None — cómo se activó el proxy en esta sesión
_session_creator_user_agent = ""  # UA del pool si bot_settings activa la extensión antes de LinkedIn


def _get_session_creator_user_agent():
    global _session_creator_user_agent
    return _session_creator_user_agent


def execute_creator():
    """
    Función principal del creator que ejecuta todas las acciones.
    Establece bot_running = True cuando se ejecuta desde la UI.
    """
    from app.database.database import get_creator_setting, get_global_time_config, get_active_browsers
    import app.auth.auth as auth_module
    
    # Establecer bot_running = True cuando se ejecuta desde la UI
    auth_module.bot_running = True
    print("🚀 Iniciando Creator desde UI...")
    
    global _password_usado, _proxy_activado_por_click, _proxy_modo_usado, _session_creator_user_agent
    _password_usado = ""
    _proxy_activado_por_click = False
    _proxy_modo_usado = None
    _session_creator_user_agent = ""
    
    try:
        # Obtener navegadores activos
        active_browsers = get_active_browsers()
        if not active_browsers:
            print("❌ No hay navegadores activos")
            auth_module.bot_running = False
            return
        
        # Obtener configuración del primer navegador
        settings = get_creator_setting(active_browsers[0]['id'])
        if not settings:
            print("❌ Sin configuración del navegador")
            auth_module.bot_running = False
            return
        
        # Obtener configuración global de tiempo
        global_time_config = get_global_time_config()
        cycle_time_minutes = global_time_config.get('cycle_time_minutes', 60)
        accounts_per_cycle = global_time_config.get('accounts_per_cycle', 1)
        scheduled_time = global_time_config.get('scheduled_time')
        time_config_type = global_time_config.get('time_config_type', 'manual')
        
        has_scheduled = scheduled_time and scheduled_time.strip() and time_config_type in ['scheduled', 'both']
        # Permitir ciclo con 0 minutos (ejecución continua sin espera)
        has_cycle = cycle_time_minutes is not None and cycle_time_minutes >= 0 and time_config_type in ['cycle', 'both']
        
        # Determinar modo de ejecución
        if has_scheduled and has_cycle:
            print("🔄 Ciclo + Hora programada")
            if not _verificar_hora_programada():
                auth_module.bot_running = False
                return
            _ejecutar_creator_en_ciclo(active_browsers)
        elif has_cycle:
            print("🔄 Solo ciclo")
            _ejecutar_creator_en_ciclo(active_browsers)
        elif has_scheduled:
            print("🕐 Solo hora programada")
            if not _verificar_hora_programada():
                auth_module.bot_running = False
                return
            # Ejecutar con objetivo de 1 cuenta cuando es solo hora programada
            _ejecutar_proceso_creator_con_objetivo(1, active_browsers=active_browsers)
        else:
            print("👤 Modo manual")
            # Ejecutar con objetivo de 1 cuenta en modo manual
            _ejecutar_proceso_creator_con_objetivo(1, active_browsers=active_browsers)
    except Exception as e:
        print(f"❌ Error en Creator: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Establecer bot_running = False al finalizar
        auth_module.bot_running = False
        print("✅ Creator finalizado")


def observador_unificado(coordinates, email, password, filepath, browser_id=None, browser_name=None):
    """
    Observador unificado que detecta números, captchas y éxito en la creación de cuentas
    """
    from app.creator.computer_actions import click_coordinates, wait_for_creator_image, get_clipboard_content
    from app.database.database import get_creator_setting
    import time
    import json
    
    print("👁️ Observando número, captcha rojo, captcha blanco o éxito...")
    # El proxy permanece activo durante toda la cuenta (se enciende antes del fav de LinkedIn).
    time.sleep(5)
    
    # Configuración del observador
    start_time = time.time()
    timeout_seconds = 150
    
    # Estado del observador
    estado = ObservadorEstado()
    
    while True:
        # Verificar si se debe detener el bot
        from app.auth.auth import bot_running
        if not bot_running:
            print("🛑 Señal de detención recibida en observador. Deteniendo...")
            # Cerrar navegador antes de detenerse
            close_window_coords = coordinates.get("close_window")
            if close_window_coords:
                click_coordinates(close_window_coords)
                time.sleep(1)
            return False, "detenido_por_usuario", {}
        
        # Resetear flag de captcha bueno procesado en este ciclo
        estado.captcha_bueno_procesado_en_ciclo = False
        
        # Resetear flag de captcha imposible si el captcha ya desapareció (verificación rápida)
        if hasattr(estado, 'captcha_imposible_procesado') and estado.captcha_imposible_procesado:
            from app.creator.computer_actions import wait_for_spinner
            captcha_still_found = wait_for_spinner("captcha_imposible", max_attempts=1, delay_between_attempts=0.1, confidence=0.5, silent=True, browser_name=browser_name)
            if not captcha_still_found:
                captcha_still_found = wait_for_spinner("captcha_imposible_2", max_attempts=1, delay_between_attempts=0.1, confidence=0.5, silent=True, browser_name=browser_name)
            if not captcha_still_found:
                captcha_still_found = wait_for_spinner("captcha_imposible_3", max_attempts=1, delay_between_attempts=0.1, confidence=0.5, silent=True, browser_name=browser_name)
            if not captcha_still_found:
                estado.captcha_imposible_procesado = False
        
        # Verificar timeout
        if _verificar_timeout(start_time, timeout_seconds, coordinates):
            return False, "timeout", {"tiempo_transcurrido": time.time() - start_time, "timeout_seconds": timeout_seconds}
        
        # Verificar captcha bueno PRIMERO
        captcha_bueno_result = _procesar_captcha_bueno(coordinates, estado, browser_name=browser_name)
        if captcha_bueno_result is True:  # Procesado correctamente, continuar
            continue
        
        # Verificar número
        numero_result = _procesar_numero(coordinates, estado, browser_name=browser_name)
        if numero_result is False:  # Segundo obstáculo detectado
            return False, "numero_segundo_obstaculo", {"numero_count": estado.numero_count, "obstaculo_count": estado.obstaculo_count}
        elif numero_result is True:  # Procesado correctamente, continuar
            continue
        
        # Verificar captcha error
        captcha_error_result = _procesar_captcha_error(coordinates, estado, browser_name=browser_name)
        if captcha_error_result is False:  # Segundo obstáculo detectado
            return False, "captcha_error_segundo_obstaculo", {"numero_count": estado.numero_count, "obstaculo_count": estado.obstaculo_count}
        elif captcha_error_result is True:  # Procesado correctamente, continuar
            continue
        
        # Verificar proxy error (loop hasta que desaparezca)
        proxy_error_result = _procesar_proxy_error(coordinates, estado, browser_name=browser_name)
        if proxy_error_result is True:  # Procesado o alcanzado límite, continuar
            continue
        elif proxy_error_result is None:  # No hay proxy error, continuar ciclo
            pass  # Continuar con las demás verificaciones
        
        # Verificar captcha rojo (VPS: cierra inmediatamente, Máquina física: dos verificaciones)
        captcha_result = _procesar_captcha_rojo(coordinates, estado, browser_id=browser_id, browser_name=browser_name)
        if captcha_result is False:  # VPS: primera detección o Máquina física: segunda detección
            return False, "captcha_segundo_obstaculo", {"captcha_count": estado.captcha_count, "obstaculo_count": estado.obstaculo_count}
        elif captcha_result is True:  # Máquina física: primera detección procesada, continuar
            continue
        
        # Verificar linkedin_error (error de carga de LinkedIn)
        linkedin_error_result = _procesar_linkedin_error(coordinates, estado, browser_name=browser_name)
        if linkedin_error_result is False:  # Error detectado - cerrar navegador y continuar con siguiente email
            return False, "linkedin_error", {}
        
        # Verificar formato nuevo
        formato_nuevo_result = _procesar_formato_nuevo(coordinates, estado, browser_name=browser_name)
        if formato_nuevo_result is False:  # Formato nuevo detectado - terminar inmediatamente
            return False, "formato_nuevo_detectado", {"captcha_count": estado.captcha_count, "obstaculo_count": estado.obstaculo_count}
        elif formato_nuevo_result is True:  # Procesado correctamente, continuar
            continue
        
        # Verificar captcha imposible
        captcha_imposible_result = _procesar_captcha_imposible(coordinates, estado, browser_name=browser_name)
        if captcha_imposible_result is False:  # Segundo obstáculo detectado
            return False, "captcha_imposible_segundo_obstaculo", {"captcha_count": estado.captcha_count, "obstaculo_count": estado.obstaculo_count}
        elif captcha_imposible_result is True:  # Procesado correctamente, continuar
            continue
        
        # Verificar éxito
        exito_result = _procesar_exito(coordinates, email, password, filepath, browser_id=browser_id, browser_name=browser_name)
        if exito_result is not None:
            # Si es un fallo de cookie o user agent, cerrar ventana antes de retornar
            if isinstance(exito_result, tuple) and len(exito_result) >= 2:
                if exito_result[0] is False and exito_result[1] in [
                    "cookie_vacia",
                    "cookie_invalida",
                    "cookie_duplicada",
                    "max_intentos_cookie",
                    "user_agent_no_encontrado",
                ]:
                    print("❌ Fallo en obtención de cookie o user agent - cerrando ventana")
                    close_window_coords = coordinates.get("close_window")
                    if close_window_coords:
                        click_coordinates(close_window_coords)
                        time.sleep(1)
            return exito_result
        
        # Verificar captcha blanco (solo si no hay éxito)
        captcha_blanco_result = _procesar_captcha_blanco(coordinates, estado, browser_name=browser_name)
        if captcha_blanco_result is False:  # Tercera detección de captcha blanco
            return False, "captcha_blanco_tercera_deteccion", {"captcha_blanco_flag": estado.captcha_blanco_flag}
        elif captcha_blanco_result is True:  # Procesado correctamente, continuar
            continue
        
        # Pausa entre ciclos (proxy sigue activo hasta fin de cuenta)
        time.sleep(0.5)


def observador_unificado_con_detalle(coordinates, email, password, filepath, browser_id=None, browser_name=None):
    """
    Versión mejorada del observador que devuelve información detallada sobre el resultado
    Retorna: (exito: bool, motivo_fallo: str, detalles: dict)
    """
    from app.creator.computer_actions import click_coordinates, wait_for_creator_image, get_clipboard_content
    from app.database.database import get_creator_setting
    import time
    import json
    
    print("👁️ Observando número, captcha rojo, captcha blanco o éxito...")
    # El proxy permanece activo durante toda la cuenta (se enciende antes del fav de LinkedIn).
    time.sleep(5)
    
    # Configuración del observador
    start_time = time.time()
    timeout_seconds = 150
    
    # Estado del observador
    estado = ObservadorEstado()
    
    while True:
        # Verificar si se debe detener el bot
        from app.auth.auth import bot_running
        if not bot_running:
            print("🛑 Señal de detención recibida en observador. Deteniendo...")
            # Cerrar navegador antes de detenerse
            close_window_coords = coordinates.get("close_window")
            if close_window_coords:
                click_coordinates(close_window_coords)
                time.sleep(1)
            return False, "detenido_por_usuario", {}
        
        # Resetear flag de captcha bueno procesado en este ciclo
        estado.captcha_bueno_procesado_en_ciclo = False
        
        # Resetear flag de captcha imposible si el captcha ya desapareció (verificación rápida)
        if hasattr(estado, 'captcha_imposible_procesado') and estado.captcha_imposible_procesado:
            from app.creator.computer_actions import wait_for_spinner
            captcha_still_found = wait_for_spinner("captcha_imposible", max_attempts=1, delay_between_attempts=0.1, confidence=0.5, silent=True, browser_name=browser_name)
            if not captcha_still_found:
                captcha_still_found = wait_for_spinner("captcha_imposible_2", max_attempts=1, delay_between_attempts=0.1, confidence=0.5, silent=True, browser_name=browser_name)
            if not captcha_still_found:
                captcha_still_found = wait_for_spinner("captcha_imposible_3", max_attempts=1, delay_between_attempts=0.1, confidence=0.5, silent=True, browser_name=browser_name)
            if not captcha_still_found:
                estado.captcha_imposible_procesado = False
        
        # Verificar timeout
        if _verificar_timeout(start_time, timeout_seconds, coordinates):
            return False, "timeout", {"tiempo_transcurrido": time.time() - start_time, "timeout_seconds": timeout_seconds}
        
        # Verificar captcha bueno PRIMERO
        captcha_bueno_result = _procesar_captcha_bueno(coordinates, estado, browser_name=browser_name)
        if captcha_bueno_result is True:  # Procesado correctamente, continuar
            continue
        
        # Verificar número
        numero_result = _procesar_numero(coordinates, estado, browser_name=browser_name)
        if numero_result is False:  # Segundo obstáculo detectado
            return False, "numero_segundo_obstaculo", {"numero_count": estado.numero_count, "obstaculo_count": estado.obstaculo_count}
        elif numero_result is True:  # Procesado correctamente, continuar
            continue
        
        # Verificar captcha error
        captcha_error_result = _procesar_captcha_error(coordinates, estado, browser_name=browser_name)
        if captcha_error_result is False:  # Segundo obstáculo detectado
            return False, "captcha_error_segundo_obstaculo", {"numero_count": estado.numero_count, "obstaculo_count": estado.obstaculo_count}
        elif captcha_error_result is True:  # Procesado correctamente, continuar
            continue
        
        # Verificar proxy error (loop hasta que desaparezca)
        proxy_error_result = _procesar_proxy_error(coordinates, estado, browser_name=browser_name)
        if proxy_error_result is True:  # Procesado o alcanzado límite, continuar
            continue
        elif proxy_error_result is None:  # No hay proxy error, continuar ciclo
            pass  # Continuar con las demás verificaciones
        
        # Verificar captcha rojo (VPS: cierra inmediatamente, Máquina física: dos verificaciones)
        captcha_result = _procesar_captcha_rojo(coordinates, estado, browser_id=browser_id, browser_name=browser_name)
        if captcha_result is False:  # VPS: primera detección o Máquina física: segunda detección
            return False, "captcha_segundo_obstaculo", {"captcha_count": estado.captcha_count, "obstaculo_count": estado.obstaculo_count}
        elif captcha_result is True:  # Máquina física: primera detección procesada, continuar
            continue
        
        # Verificar linkedin_error (error de carga de LinkedIn)
        linkedin_error_result = _procesar_linkedin_error(coordinates, estado, browser_name=browser_name)
        if linkedin_error_result is False:  # Error detectado - cerrar navegador y continuar con siguiente email
            return False, "linkedin_error", {}
        
        # Verificar formato nuevo
        formato_nuevo_result = _procesar_formato_nuevo(coordinates, estado, browser_name=browser_name)
        if formato_nuevo_result is False:  # Formato nuevo detectado - terminar inmediatamente
            return False, "formato_nuevo_detectado", {"captcha_count": estado.captcha_count, "obstaculo_count": estado.obstaculo_count}
        elif formato_nuevo_result is True:  # Procesado correctamente, continuar
            continue
        
        # Verificar captcha imposible
        captcha_imposible_result = _procesar_captcha_imposible(coordinates, estado, browser_name=browser_name)
        if captcha_imposible_result is False:  # Segundo obstáculo detectado
            return False, "captcha_imposible_segundo_obstaculo", {"captcha_count": estado.captcha_count, "obstaculo_count": estado.obstaculo_count}
        elif captcha_imposible_result is True:  # Procesado correctamente, continuar
            continue
        
        # Verificar éxito
        exito_result = _procesar_exito_con_detalle(coordinates, email, password, filepath, browser_id=browser_id, browser_name=browser_name)
        if exito_result is not None:
            # Si es un fallo de cookie o user agent, cerrar ventana antes de retornar
            if isinstance(exito_result, tuple) and len(exito_result) >= 2:
                if exito_result[0] is False and exito_result[1] in [
                    "cookie_vacia",
                    "cookie_invalida",
                    "cookie_duplicada",
                    "max_intentos_cookie",
                    "user_agent_no_encontrado",
                ]:
                    print("❌ Fallo en obtención de cookie o user agent - cerrando ventana")
                    close_window_coords = coordinates.get("close_window")
                    if close_window_coords:
                        click_coordinates(close_window_coords)
                        time.sleep(1)
            return exito_result
        
        # Verificar captcha blanco (solo si no hay éxito)
        captcha_blanco_result = _procesar_captcha_blanco(coordinates, estado, browser_name=browser_name)
        if captcha_blanco_result is False:  # Tercera detección de captcha blanco
            return False, "captcha_blanco_tercera_deteccion", {"captcha_blanco_flag": estado.captcha_blanco_flag}
        elif captcha_blanco_result is True:  # Procesado correctamente, continuar
            continue
        
        # Pausa entre ciclos (proxy sigue activo hasta fin de cuenta)
        time.sleep(0.5)


class ObservadorEstado:
    """Clase para manejar el estado del observador"""
    def __init__(self):
        self.numero_count = 0
        self.captcha_count = 0
        self.ciclos_sin_imagen = 0
        self.obstaculo_count = 0
        self.captcha_blanco_flag = 0
        self.captcha_bueno_count = 0
        self.captcha_bueno_procesado_en_ciclo = False
        self.captcha_blanco_ultima_deteccion_tiempo = None
        self.captcha_imposible_procesado = False  # Flag para evitar procesar captcha imposible múltiples veces


def _verificar_timeout(start_time, timeout_seconds, coordinates):
    """Verifica si ha pasado el timeout y cierra la ventana si es necesario"""
    from app.creator.computer_actions import click_coordinates
    import time
    
    elapsed_time = time.time() - start_time
    if elapsed_time > timeout_seconds:
        print("⏰ Timeout de 150 segundos - no se encontraron imágenes, cerrando ventana")
        # Intentar apagar proxy antes de cerrar para evitar que quede activo en el siguiente intento.
        try:
            _desactivar_proxy(coordinates, silent=False)
        except Exception as e:
            print(f"⚠️ No se pudo desactivar proxy en timeout: {e}")
        close_window_coords = coordinates.get("close_window")
        if close_window_coords:
            click_coordinates(close_window_coords)
            time.sleep(1)
        return True
    return False


def _procesar_numero(coordinates, estado, browser_name=None):
    """Procesa la detección de número"""
    from app.creator.computer_actions import click_coordinates, wait_for_creator_image
    import time
    
    numero_found = wait_for_creator_image("imagen_numero", max_attempts=1, delay_between_attempts=0.5, silent=True, browser_name=browser_name)
    
    if not numero_found:
        return None  # No hay número que procesar
    
    estado.numero_count += 1
    estado.obstaculo_count += 1
    estado.ciclos_sin_imagen = 0
    print(f"✅ Número encontrado (vez #{estado.numero_count})")
    
    if estado.obstaculo_count >= 2:
        print("🔄 Segundo obstáculo detectado - cerrando ventana directamente")
        close_window_coords = coordinates.get("close_window")
        if close_window_coords:
            click_coordinates(close_window_coords)
            time.sleep(1)
        return False  # Terminar el proceso
    
    # Si es la primera vez, cerrar el número y continuar
    close_number_coords = coordinates.get("close_number_click")
    if close_number_coords:
        click_coordinates(close_number_coords)
        time.sleep(1)
        
        continue2_coords = coordinates.get("continue_button2_click")
        if continue2_coords:
            click_coordinates(continue2_coords)
            time.sleep(3)
    
    return True


def _procesar_captcha_error(coordinates, estado, browser_name=None):
    """Procesa la detección de captcha error"""
    from app.creator.computer_actions import click_coordinates, wait_for_creator_image
    import time
    
    captcha_error_found = wait_for_creator_image("captcha_error", max_attempts=1, delay_between_attempts=0.5, silent=True, browser_name=browser_name)
    
    if not captcha_error_found:
        return None  # No hay captcha error que procesar
    
    estado.numero_count += 1  # Usar el mismo contador para obstáculos
    estado.obstaculo_count += 1
    estado.ciclos_sin_imagen = 0
    print(f"✅ Captcha error encontrado (vez #{estado.numero_count})")
    
    if estado.obstaculo_count >= 2:
        print("🔄 Segundo obstáculo detectado - cerrando ventana directamente")
        close_window_coords = coordinates.get("close_window")
        if close_window_coords:
            click_coordinates(close_window_coords)
            time.sleep(1)
        return False  # Terminar el proceso
    
    # Si es la primera vez, cerrar el captcha error y continuar
    close_captcha_error_coords = coordinates.get("close_captcha_error_click")
    if close_captcha_error_coords:
        print(f"📍 Haciendo clic en coordenada de captcha error: {close_captcha_error_coords}")
        click_coordinates(close_captcha_error_coords)
        time.sleep(1)
        print(f"✅ Clic realizado en captcha error")
        
        continue2_coords = coordinates.get("continue_button2_click")
        if continue2_coords:
            click_coordinates(continue2_coords)
            time.sleep(3)
    else:
        print(f"⚠️ No se encontraron coordenadas de close_captcha_error_click - por favor configúralas")
    
    return True


def _verificar_y_cerrar_proxy_error(coordinates, start_time=None, timeout_seconds=90, browser_name=None):
    """Función auxiliar para verificar y cerrar proxy error en cualquier momento del proceso"""
    from app.creator.computer_actions import click_coordinates, wait_for_creator_image
    import time
    
    close_proxy_error_coords = coordinates.get("close_proxy_error_click")
    if not close_proxy_error_coords:
        return False
    
    max_intentos = 10
    
    for intento in range(1, max_intentos + 1):
        # Verificar timeout si se proporciona
        if start_time is not None:
            elapsed_time = time.time() - start_time
            if elapsed_time >= timeout_seconds:
                print(f"⏰ Timeout alcanzado mientras se procesaba proxy error")
                return True
        
        # PRIMERO: Verificar si la imagen está presente
        proxy_error_found = wait_for_creator_image("proxy_error", max_attempts=1, delay_between_attempts=0.5, silent=True, browser_name=browser_name)
        
        if not proxy_error_found:
            # La imagen ya no está presente
            if intento > 1:
                print(f"✅ Proxy error resuelto después de {intento - 1} clics")
            return True
        
        # Proxy error aún presente, hacer clic para cerrarlo
        if intento == 1:
            print(f"✅ Proxy error detectado en proceso - haciendo clic para cerrar")
        
        print(f"📍 Intento {intento}/{max_intentos} - Haciendo clic en coordenada: {close_proxy_error_coords}")
        click_coordinates(close_proxy_error_coords)
        time.sleep(1)  # Esperar a que se procese el clic
        
        # DESPUÉS DEL CLIC: Verificar que la imagen efectivamente desapareció
        time.sleep(0.5)  # Esperar adicional para que se procese
        proxy_error_still_found = wait_for_creator_image("proxy_error", max_attempts=1, delay_between_attempts=0.3, silent=True, browser_name=browser_name)
        
        if not proxy_error_still_found:
            # La imagen desapareció después del clic
            print(f"✅ Proxy error resuelto - imagen desapareció después del clic {intento}")
            return True
        
        # Si la imagen sigue presente, continuar con el siguiente intento
        print(f"⚠️ Imagen de proxy error aún presente después del clic {intento}, continuando...")
        
        if intento >= max_intentos:
            print(f"⚠️ Proxy error persistió después de {max_intentos} intentos, continuando...")
            return True
    
    return True


def _procesar_proxy_error(coordinates, estado, browser_name=None):
    """Procesa la detección de proxy error - loop continuo hasta que desaparezca"""
    from app.creator.computer_actions import click_coordinates, wait_for_creator_image
    import time
    
    # Intentar verificar y cerrar proxy error con loop hasta que desaparezca
    close_proxy_error_coords = coordinates.get("close_proxy_error_click")
    if not close_proxy_error_coords:
        return None
    
    max_intentos = 10
    
    for intento in range(1, max_intentos + 1):
        # PRIMERO: Verificar si la imagen está presente
        proxy_error_found = wait_for_creator_image("proxy_error", max_attempts=1, delay_between_attempts=0.5, silent=True, browser_name=browser_name)
        
        if not proxy_error_found:
            # La imagen ya no está presente - VERIFICACIÓN COMPLETA
            if intento > 1:
                print(f"✅ Proxy error resuelto después de {intento - 1} clics")
                estado.ciclos_sin_imagen = 0
            return None  # No hay proxy error que procesar
        
        # Proxy error presente, hacer clic
        if intento == 1:
            estado.ciclos_sin_imagen = 0
            print(f"✅ Proxy error detectado - haciendo clic para cerrar")
        
        print(f"📍 Intento {intento}/{max_intentos} - Haciendo clic en coordenada: {close_proxy_error_coords}")
        click_coordinates(close_proxy_error_coords)
        time.sleep(1)  # Esperar a que se procese el clic
        
        # DESPUÉS DEL CLIC: Verificar que la imagen efectivamente desapareció
        time.sleep(0.5)  # Esperar adicional para que se procese
        proxy_error_still_found = wait_for_creator_image("proxy_error", max_attempts=1, delay_between_attempts=0.3, silent=True, browser_name=browser_name)
        
        if not proxy_error_still_found:
            # La imagen desapareció después del clic
            print(f"✅ Proxy error resuelto - imagen desapareció después del clic {intento}")
            estado.ciclos_sin_imagen = 0
            return None  # Error resuelto, continuar
        
        # Si la imagen sigue presente, continuar con el siguiente intento
        print(f"⚠️ Imagen de proxy error aún presente después del clic {intento}, continuando...")
        
        if intento >= max_intentos:
            print(f"⚠️ Proxy error persistió después de {max_intentos} intentos, continuando observación...")
            estado.ciclos_sin_imagen = 0
            return True
    
    return True


def _procesar_linkedin_error(coordinates, estado, browser_name=None):
    """Procesa la detección de error de carga de LinkedIn - cierra navegador y sale para continuar con siguiente email"""
    from app.creator.computer_actions import click_coordinates, wait_for_creator_image
    import time
    
    linkedin_error_found = wait_for_creator_image("linkedin_error", max_attempts=1, delay_between_attempts=0.5, silent=True, browser_name=browser_name)
    
    if not linkedin_error_found:
        return None  # No hay error de LinkedIn que procesar
    
    estado.ciclos_sin_imagen = 0
    print(f"⚠️ Error de carga de LinkedIn detectado - cerrando navegador y continuando con siguiente email")
    
    # Cerrar ventana y salir para continuar con siguiente email
    close_window_coords = coordinates.get("close_window")
    if close_window_coords:
        click_coordinates(close_window_coords)
        time.sleep(1)
    
    return False  # Salir del observador para continuar con siguiente email


def _procesar_formato_nuevo(coordinates, estado, browser_name=None):
    """Procesa la detección de formato nuevo - termina inmediatamente"""
    from app.creator.computer_actions import click_coordinates, wait_for_creator_image
    import time
    
    formato_nuevo_found = wait_for_creator_image("formato_nuevo", max_attempts=1, delay_between_attempts=0.5, silent=True, browser_name=browser_name)
    
    if not formato_nuevo_found:
        return None  # No hay formato nuevo que procesar
    
    estado.captcha_count += 1
    estado.obstaculo_count += 1
    estado.ciclos_sin_imagen = 0
    print(f"✅ Formato nuevo encontrado - cerrando ventana inmediatamente")
    
    # Cerrar ventana directamente
    close_window_coords = coordinates.get("close_window")
    if close_window_coords:
        click_coordinates(close_window_coords)
        time.sleep(1)
    
    return False  # Terminar el proceso inmediatamente


def _procesar_captcha_rojo(coordinates, estado, browser_id=None, browser_name=None):
    """Procesa la detección de captcha rojo - comportamiento según tipo de máquina"""
    from app.creator.computer_actions import click_coordinates, wait_for_creator_image
    from app.database.database import get_creator_setting
    import time
    
    captcha_found = wait_for_creator_image("imagen_captcha_rojo", max_attempts=1, delay_between_attempts=0.5, silent=True, browser_name=browser_name)
    
    if not captcha_found:
        return None  # No hay captcha que procesar
    
    # Obtener configuración para determinar tipo de máquina
    if browser_id:
        settings = get_creator_setting(browser_id)
    else:
        settings = None
    isInVps = settings.get('isInVps') if settings else None
    
    estado.captcha_count += 1
    estado.obstaculo_count += 1
    estado.ciclos_sin_imagen = 0
    
    # Comportamiento según tipo de máquina
    if isInVps is True:
        # VPS: Cerrar inmediatamente (comportamiento original)
        print(f"✅ Captcha rojo encontrado (VPS) - cerrando ventana inmediatamente")
        close_window_coords = coordinates.get("close_window")
        if close_window_coords:
            click_coordinates(close_window_coords)
            time.sleep(1)
        return False  # Terminar el proceso inmediatamente
    
    else:
        # Máquina física: Comportamiento como _procesar_numero (dos verificaciones)
        print(f"✅ Captcha rojo encontrado (Máquina física) - vez #{estado.captcha_count}")
        
        if estado.obstaculo_count >= 2:
            # Segunda detección - cerrar ventana
            print("🔄 Segundo captcha rojo detectado - cerrando ventana directamente")
            close_window_coords = coordinates.get("close_window")
            if close_window_coords:
                click_coordinates(close_window_coords)
                time.sleep(1)
            return False  # Terminar el proceso
        
        # Primera detección - cerrar captcha y continuar
        close_captcha_coords = coordinates.get("close_captcha_click")
        if close_captcha_coords:
            click_coordinates(close_captcha_coords)
            time.sleep(1)
            
        continue2_coords = coordinates.get("continue_button2_click")
        if continue2_coords:
            click_coordinates(continue2_coords)
            time.sleep(3)
        
        return True  # Continuar el proceso


def _procesar_captcha_imposible(coordinates, estado, browser_name=None):
    """Procesa la detección de captcha imposible (incluye captcha_imposible, captcha_imposible_2 y captcha_imposible_3)"""
    from app.creator.computer_actions import click_coordinates, wait_for_spinner
    import time
    
    # Si ya se procesó el captcha imposible, verificar si desapareció antes de procesar de nuevo
    if hasattr(estado, 'captcha_imposible_procesado') and estado.captcha_imposible_procesado:
        # Verificar si el captcha ya desapareció (verificación rápida)
        captcha_still_found = wait_for_spinner("captcha_imposible", max_attempts=1, delay_between_attempts=0.1, confidence=0.5, silent=True, browser_name=browser_name)
        if not captcha_still_found:
            captcha_still_found = wait_for_spinner("captcha_imposible_2", max_attempts=1, delay_between_attempts=0.1, confidence=0.5, silent=True, browser_name=browser_name)
        if not captcha_still_found:
            captcha_still_found = wait_for_spinner("captcha_imposible_3", max_attempts=1, delay_between_attempts=0.1, confidence=0.5, silent=True, browser_name=browser_name)
        
        # Si el captcha ya desapareció, resetear el flag y permitir procesamiento futuro
        if not captcha_still_found:
            estado.captcha_imposible_procesado = False
            return None
        else:
            # El captcha sigue presente pero ya se procesó la primera vez
            # Si es la segunda vez (obstaculo_count >= 1), debemos procesarlo para cerrar la ventana
            # Si no, retornar None para evitar loops infinitos de clics en continue
            if estado.obstaculo_count >= 1:
                # Es la segunda vez, resetear el flag y permitir procesamiento
                # para que se detecte como segundo obstáculo y se cierre la ventana
                estado.captcha_imposible_procesado = False
                # Continuar con el procesamiento normal (no retornar None)
            else:
                # Primera vez procesada, evitar loops infinitos
                return None
    
    # Detectar captcha imposible (versión 1) usando wait_for_spinner porque tiene un spinner rotando
    captcha_found = wait_for_spinner("captcha_imposible", max_attempts=1, delay_between_attempts=0.5, confidence=0.5, silent=True, browser_name=browser_name)
    
    # Si no se encuentra la versión 1, intentar con la versión 2
    if not captcha_found:
        captcha_found = wait_for_spinner("captcha_imposible_2", max_attempts=1, delay_between_attempts=0.5, confidence=0.5, silent=True, browser_name=browser_name)
    
    # Si no se encuentra la versión 2, intentar con la versión 3
    if not captcha_found:
        captcha_found = wait_for_spinner("captcha_imposible_3", max_attempts=1, delay_between_attempts=0.5, confidence=0.5, silent=True, browser_name=browser_name)
    
    if not captcha_found:
        return None  # No hay captcha que procesar
    
    estado.captcha_count += 1
    estado.obstaculo_count += 1
    estado.ciclos_sin_imagen = 0
    print(f"✅ Captcha imposible encontrado (vez #{estado.captcha_count})")
    
    if estado.obstaculo_count >= 2:
        print("🔄 Segundo obstáculo detectado - verificando confirmación antes de cerrar...")
        print("⏳ Esperando 8 segundos para verificar si el spinner persiste...")
        
        # Esperar un poco para ver si el captcha se convierte en captcha bueno
        time.sleep(8)
        
        # Verificar de nuevo si el spinner sigue presente
        captcha_still_found = False
        
        # Verificar las tres variantes del captcha imposible
        if wait_for_spinner("captcha_imposible", max_attempts=1, delay_between_attempts=0.2, confidence=0.5, silent=True, browser_name=browser_name):
            captcha_still_found = True
        elif wait_for_spinner("captcha_imposible_2", max_attempts=1, delay_between_attempts=0.2, confidence=0.5, silent=True, browser_name=browser_name):
            captcha_still_found = True
        elif wait_for_spinner("captcha_imposible_3", max_attempts=1, delay_between_attempts=0.2, confidence=0.5, silent=True, browser_name=browser_name):
            captcha_still_found = True
        
        if captcha_still_found:
            print("✅ Spinner de captcha imposible confirmado - procediendo a cerrar ventana")
            close_window_coords = coordinates.get("close_window")
            if close_window_coords:
                click_coordinates(close_window_coords)
                time.sleep(1)
            return False  # Terminar el proceso
        else:
            print("⚠️ Spinner ya no está presente - puede que se haya convertido en captcha bueno")
            print("🔄 Continuando el proceso en lugar de cerrar la ventana")
            # No cerrar la ventana, continuar con el proceso normal
            # Esto permite que el captcha bueno sea procesado si aparece
            return True  # Continuar el proceso
    
    # Primera detección - cerrar captcha y continuar
    close_captcha_coords = coordinates.get("close_captcha_click")
    if close_captcha_coords:
        print("📍 Cerrando captcha imposible...")
        click_coordinates(close_captcha_coords)
        time.sleep(1)
        
        continue2_coords = coordinates.get("continue_button2_click")
        if continue2_coords:
            print("📍 Haciendo clic en continue después de captcha imposible...")
            click_coordinates(continue2_coords)
            time.sleep(3)
            print("✅ Clic en continue realizado después de captcha imposible")
            # Esperar un momento para que el captcha desaparezca después del clic
            time.sleep(1)
            # Verificar si el captcha desapareció y resetear el flag si es así
            captcha_still_found = wait_for_spinner("captcha_imposible", max_attempts=1, delay_between_attempts=0.1, confidence=0.5, silent=True, browser_name=browser_name)
            if not captcha_still_found:
                captcha_still_found = wait_for_spinner("captcha_imposible_2", max_attempts=1, delay_between_attempts=0.1, confidence=0.5, silent=True, browser_name=browser_name)
            if not captcha_still_found:
                captcha_still_found = wait_for_spinner("captcha_imposible_3", max_attempts=1, delay_between_attempts=0.1, confidence=0.5, silent=True, browser_name=browser_name)
            
            # Si el captcha desapareció, no marcar como procesado (permitir detección futura si reaparece)
            if not captcha_still_found:
                estado.captcha_imposible_procesado = False
            else:
                # Marcar como procesado solo si el captcha sigue presente
                estado.captcha_imposible_procesado = True
        else:
            print("⚠️ No se encontraron coordenadas de continue_button2_click para captcha imposible")
            # Si no hay continue_button2_click, marcar como procesado de todas formas
            estado.captcha_imposible_procesado = True
    else:
        print("⚠️ No se encontraron coordenadas de close_captcha_click para captcha imposible")
        # Si no hay close_captcha_click, marcar como procesado de todas formas
        estado.captcha_imposible_procesado = True
    
    return True


def _procesar_exito(coordinates, email, password, filepath, browser_id=None, browser_name=None):
    """Procesa la detección de éxito en la creación de cuenta"""
    from app.creator.computer_actions import wait_for_creator_image
    
    exito_images = [
        "imagen_de_creacion_de_cuenta_con_exito_logo_linkedin",
        "imagen_de_creacion_de_cuenta_con_exito_logo_linkedin_2", 
        "imagen_de_confirmacion_de_codigo",
        "add_location"
    ]
    
    exito_found = False
    exito_image_name = None
    
    for image_name in exito_images:
        if wait_for_creator_image(image_name, max_attempts=1, delay_between_attempts=0.5, silent=True, browser_name=browser_name):
            exito_found = True
            exito_image_name = image_name
            break
    
    if not exito_found:
        return None

    print(f"✅ Imagen de éxito encontrada - buscando cookie...")

    from app.creator.post_account_success_actions import run_after_account_success_before_cookie

    password_cuenta = _get_password_usado() or password
    acciones_ok = run_after_account_success_before_cookie(
        coordinates,
        email,
        password_cuenta,
        filepath,
        exito_image_name=exito_image_name,
        browser_id=browser_id,
        browser_name=browser_name,
    )
    if acciones_ok is False:
        print("❌ Fallo en acciones post-éxito; cuenta NO creada, se omite guardado de cookie.")
        return False, "post_success_actions_failed", {}

    return _obtener_y_guardar_cookie(coordinates, email, password_cuenta, filepath, browser_id=browser_id, browser_name=browser_name)


def _procesar_exito_con_detalle(coordinates, email, password, filepath, exito_image_name=None, browser_id=None, browser_name=None):
    """Procesa la detección de éxito con información detallada"""
    from app.creator.computer_actions import wait_for_creator_image
    
    exito_images = [
        "imagen_de_creacion_de_cuenta_con_exito_logo_linkedin",
        "imagen_de_creacion_de_cuenta_con_exito_logo_linkedin_2", 
        "imagen_de_confirmacion_de_codigo",
        "add_location"
    ]
    
    exito_found = False
    exito_image_name_found = None
    
    for image_name in exito_images:
        if wait_for_creator_image(image_name, max_attempts=1, delay_between_attempts=0.5, silent=True, browser_name=browser_name):
            exito_found = True
            exito_image_name_found = image_name
            break
    
    if not exito_found:
        return None

    print(f"✅ Imagen de éxito encontrada - buscando cookie...")

    from app.creator.post_account_success_actions import run_after_account_success_before_cookie

    password_cuenta = _get_password_usado() or password
    acciones_ok = run_after_account_success_before_cookie(
        coordinates,
        email,
        password_cuenta,
        filepath,
        exito_image_name=exito_image_name_found,
        browser_id=browser_id,
        browser_name=browser_name,
    )
    if acciones_ok is False:
        print("❌ Fallo en acciones post-éxito; cuenta NO creada (detalle).")
        return False, "post_success_actions_failed", {"exito_image_name": exito_image_name_found}

    return _obtener_y_guardar_cookie_con_detalle(coordinates, email, password_cuenta, filepath, exito_image_name_found, browser_id=browser_id, browser_name=browser_name)


def _procesar_captcha_bueno(coordinates, estado, browser_name=None):
    """Procesa la detección de captcha bueno (máximo 2 veces). El proxy sigue activo durante la cuenta."""
    from app.creator.computer_actions import wait_for_creator_image
    import time
    
    # Verificar si ya se procesó el máximo de veces (2)
    if hasattr(estado, 'captcha_bueno_count') and estado.captcha_bueno_count >= 2:
        return None  # Ya se procesó el máximo de veces, no buscar más
    
    # Verificar si ya se procesó en este ciclo para evitar múltiples detecciones
    if hasattr(estado, 'captcha_bueno_procesado_en_ciclo') and estado.captcha_bueno_procesado_en_ciclo:
        return None  # Ya se procesó en este ciclo
    
    # Buscar variantes con verificación doble para evitar falsos positivos
    variantes = ["captcha_bueno", "captcha_bueno_2", "captcha_bueno_4"]
    captcha_bueno_found = None
    
    for nombre in variantes:
        # Primera verificación rápida
        if wait_for_creator_image(nombre, max_attempts=1, delay_between_attempts=0.3, silent=True, browser_name=browser_name):
            # Segunda verificación para confirmar que realmente está presente
            time.sleep(0.2)  # Pequeña pausa entre verificaciones
            if wait_for_creator_image(nombre, max_attempts=1, delay_between_attempts=0.1, silent=True, browser_name=browser_name):
                captcha_bueno_found = nombre
                break  # Salir del bucle al encontrar la primera variante
    
    if not captcha_bueno_found:
        return None  # No hay captcha bueno que procesar
    
    # Incrementar contador
    if not hasattr(estado, 'captcha_bueno_count'):
        estado.captcha_bueno_count = 0
    estado.captcha_bueno_count += 1
    
    # Marcar como procesado en este ciclo
    estado.captcha_bueno_procesado_en_ciclo = True
    
    # Solo mostrar mensaje en la primera detección
    if estado.captcha_bueno_count == 1:
        print(f"✅ Captcha bueno detectado (vez #1)")
    
    # Esperar un momento para que la imagen desaparezca de pantalla (reducido)
    time.sleep(0.5)  # Reducido de 2s a 0.5s
    
    return True  # Continuar con el proceso normal


def _procesar_captcha_blanco(coordinates, estado, browser_name=None):
    """Procesa la detección de captcha blanco con delay y doble verificación (incluye captcha_blanco_2)"""
    from app.creator.computer_actions import click_coordinates, wait_for_creator_image
    import time
    
    # Buscar ambas variantes de captcha blanco
    variantes_captcha_blanco = ["imagen_captcha_blanco", "captcha_blanco_2"]
    captcha_blanco_found = None
    captcha_blanco_tipo = None
    
    for nombre in variantes_captcha_blanco:
        if wait_for_creator_image(nombre, max_attempts=1, delay_between_attempts=0.5, confidence=0.95, silent=True, browser_name=browser_name):
            captcha_blanco_found = nombre
            captcha_blanco_tipo = nombre
            break
    
    if not captcha_blanco_found:
        return None  # No hay captcha blanco que procesar
    
    # Verificar que NO hay captcha rojo presente
    captcha_rojo_presente = wait_for_creator_image("imagen_captcha_rojo", max_attempts=1, delay_between_attempts=0.1, silent=True, browser_name=browser_name)
    
    if captcha_rojo_presente:
        print("⚠️ Captcha en proceso de carga detectado - ignorando detección de captcha blanco")
        return None
    
    # Verificar si ya pasaron 6 segundos desde la última detección procesada
    tiempo_actual = time.time()
    if hasattr(estado, 'captcha_blanco_ultima_deteccion_tiempo') and estado.captcha_blanco_ultima_deteccion_tiempo is not None:
        tiempo_transcurrido = tiempo_actual - estado.captcha_blanco_ultima_deteccion_tiempo
        if tiempo_transcurrido < 15:
            return None  # Aún no han pasado 15 segundos
    
    # Incrementar contador
    estado.captcha_blanco_flag += 1
    
    if estado.captcha_blanco_flag == 1:
        # Primera detección: solo marcar bandera y tiempo, no hacer nada
        estado.captcha_blanco_ultima_deteccion_tiempo = time.time()
        return True
    elif estado.captcha_blanco_flag == 2:
        # Segunda detección: desactivar proxy, cerrar captcha, continue
        print("✅ Captcha blanco encontrado (vez #2) - procesando...")
        estado.captcha_count += 1
        estado.obstaculo_count += 1
        estado.ciclos_sin_imagen = 0
        
        # Cerrar captcha blanco
        close_captcha_coords = coordinates.get("close_captcha_click")
        if close_captcha_coords:
            click_coordinates(close_captcha_coords)
            time.sleep(1)
            
            # Hacer clic en continue
            continue2_coords = coordinates.get("continue_button2_click")
            if continue2_coords:
                click_coordinates(continue2_coords)
                time.sleep(3)
        
        # Actualizar tiempo de última detección
        estado.captcha_blanco_ultima_deteccion_tiempo = time.time()
        return True
    elif estado.captcha_blanco_flag == 3:
        # Tercera detección: esperar 10 segundos nuevamente
        estado.captcha_blanco_ultima_deteccion_tiempo = time.time()
        return True
    elif estado.captcha_blanco_flag >= 4:
        # Cuarta detección: cerrar ventana y finalizar proceso
        print("❌ Captcha blanco encontrado (vez #4) - finalizando proceso")
        close_window_coords = coordinates.get("close_window")
        if close_window_coords:
            click_coordinates(close_window_coords)
            time.sleep(1)
        return False  # Terminar el proceso
    
    return True


def _obtener_y_guardar_cookie(coordinates, email, password, filepath, browser_id=None, browser_name=None):
    """Obtiene y guarda la cookie: prioriza UA de sesión (extensión + pool) si hubo; si no, creator_setting."""
    from app.creator.computer_actions import click_coordinates, get_clipboard_content
    from app.database.database import get_creator_setting
    import time
    import pyperclip
    
    max_intentos = 4
    for intento in range(1, max_intentos + 1):
        # Limpiar portapapeles
        pyperclip.copy("")
        time.sleep(0.2)
        
        # Clic en cookie_editor_icon_click
        cookie_editor_coords = coordinates.get("cookie_editor_icon_click")
        if not cookie_editor_coords:
            return False, "coordenadas_cookie_editor_no_encontradas", {}
        
        click_coordinates(cookie_editor_coords)
        time.sleep(2)
        
        # Clic en save_cookie_clipboard_click
        save_cookie_coords = coordinates.get("save_cookie_clipboard_click")
        if not save_cookie_coords:
            return False, "coordenadas_save_cookie_no_encontradas", {}
        
        click_coordinates(save_cookie_coords)
        time.sleep(1)
        
        # Obtener cookie del portapapeles
        cookie_raw = get_clipboard_content()
        
        # Validar cookie
        if not cookie_raw or len(cookie_raw.strip()) < 10:
            if intento < max_intentos:
                continue
            else:
                return False, "cookie_vacia", {"intento": intento, "max_intentos": max_intentos}
        
        # Formatear cookie
        cookie = _format_cookie_to_single_line(cookie_raw)
        
        if not cookie or len(cookie.strip()) < 10:
            if intento < max_intentos:
                continue
            else:
                return False, "cookie_vacia", {"intento": intento, "max_intentos": max_intentos}
        
        # Verificar duplicado
        if _verificar_cookie_duplicada(filepath, cookie):
            if intento < max_intentos:
                print(f"⚠️ Cookie duplicada detectada - intento {intento + 1}/{max_intentos}")
                time.sleep(1)
                continue
            else:
                return False, "cookie_vacia", {"intento": intento, "max_intentos": max_intentos}
        
        ua_sess = (_get_session_creator_user_agent() or "").strip()
        creator_settings = get_creator_setting(browser_id) if browser_id else None
        ua_cfg = (creator_settings.get("user_agent") or "").strip() if creator_settings else ""
        user_agent = ua_sess or ua_cfg
        if not user_agent:
            return False, "user_agent_no_encontrado", {}

        contenido = f"{user_agent}\t{email}\t{password}\t{cookie}"
        
        try:
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(contenido + "\n")
            print("✅ Cuenta guardada en archivo (user agent + email + cookie).")
            # Apagar proxy inmediatamente al completar la cuenta (no esperar al finally del flujo).
            _desactivar_proxy(coordinates, silent=False)
            return True
        except Exception as e:
            return False, "error_escritura_archivo", {"error": str(e)}
    
    # Cerrar ventana cuando se alcanza el máximo de intentos sin obtener cookie válida
    print("❌ Máximo de intentos alcanzado sin obtener cookie válida - cerrando ventana")
    close_window_coords = coordinates.get("close_window")
    if close_window_coords:
        click_coordinates(close_window_coords)
        time.sleep(1)
    return False, "max_intentos_cookie", {"max_intentos": max_intentos}


def _obtener_y_guardar_cookie_con_detalle(coordinates, email, password, filepath, exito_image_name, browser_id=None, browser_name=None):
    """Obtiene y guarda cookie detallada: UA de sesión (extensión) si existe, si no creator_setting."""
    from app.creator.computer_actions import click_coordinates, get_clipboard_content
    from app.database.database import get_creator_setting
    import time
    import pyperclip
    
    max_intentos = 4
    for intento in range(1, max_intentos + 1):
        # Limpiar portapapeles
        pyperclip.copy("")
        time.sleep(0.2)
        
        # Clic en cookie_editor_icon_click
        cookie_editor_coords = coordinates.get("cookie_editor_icon_click")
        if not cookie_editor_coords:
            return False, "coordenadas_cookie_editor_no_encontradas", {}
        
        click_coordinates(cookie_editor_coords)
        time.sleep(2)
        
        # Clic en save_cookie_clipboard_click
        save_cookie_coords = coordinates.get("save_cookie_clipboard_click")
        if not save_cookie_coords:
            return False, "coordenadas_save_cookie_no_encontradas", {}
        
        click_coordinates(save_cookie_coords)
        time.sleep(1)
        
        # Obtener cookie del portapapeles
        cookie_raw = get_clipboard_content()
        
        # Validar cookie
        if not cookie_raw or len(cookie_raw.strip()) < 10:
            if intento < max_intentos:
                continue
            else:
                return False, "cookie_vacia", {"intento": intento, "max_intentos": max_intentos}
        
        # Formatear cookie
        cookie = _format_cookie_to_single_line(cookie_raw)
        
        if not cookie or len(cookie.strip()) < 10:
            if intento < max_intentos:
                continue
            else:
                return False, "cookie_invalida", {"intento": intento, "max_intentos": max_intentos}
        
        # Verificar duplicado
        if _verificar_cookie_duplicada(filepath, cookie):
            if intento < max_intentos:
                print(f"⚠️ Cookie duplicada detectada - intento {intento + 1}/{max_intentos}")
                time.sleep(1)
                continue
            else:
                return False, "cookie_duplicada", {"intento": intento, "max_intentos": max_intentos}
        
        ua_sess = (_get_session_creator_user_agent() or "").strip()
        creator_settings = get_creator_setting(browser_id) if browser_id else None
        ua_cfg = (creator_settings.get("user_agent") or "").strip() if creator_settings else ""
        user_agent = ua_sess or ua_cfg
        if not user_agent:
            return False, "user_agent_no_encontrado", {}

        contenido = f"{user_agent}\t{email}\t{password}\t{cookie}"
        
        try:
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(contenido + "\n")
            print("✅ Cuenta guardada en archivo (user agent + email + cookie).")
            # Apagar proxy inmediatamente al completar la cuenta (no esperar al finally del flujo).
            _desactivar_proxy(coordinates, silent=False)
            return True, "exito", {"imagen_exito": exito_image_name, "intento": intento}
        except Exception as e:
            return False, "error_escritura_archivo", {"error": str(e)}
    
    # Cerrar ventana cuando se alcanza el máximo de intentos sin obtener cookie válida
    print("❌ Máximo de intentos alcanzado sin obtener cookie válida - cerrando ventana")
    close_window_coords = coordinates.get("close_window")
    if close_window_coords:
        click_coordinates(close_window_coords)
        time.sleep(1)
    return False, "max_intentos_cookie", {"max_intentos": max_intentos}


def _format_cookie_to_single_line(cookie_content):
    """Convierte el contenido de cookies del portapapeles a formato de una sola línea"""
    import json
    
    try:
        # Buscar el inicio del JSON (primer '[')
        json_start = cookie_content.find('[')
        if json_start == -1:
            print("⚠️ No se encontró un array JSON válido en las cookies")
            return cookie_content
        
        # Extraer solo la parte JSON
        json_content = cookie_content[json_start:]
        
        # Parsear el JSON
        data = json.loads(json_content)
        
        # Convertir a JSON compacto (una sola línea)
        json_single_line = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
        
        # Si hay contenido antes del JSON, mantenerlo
        if json_start > 0:
            prefix = cookie_content[:json_start]
            return prefix + json_single_line
        else:
            return json_single_line
            
    except json.JSONDecodeError as e:
        print(f"⚠️ Error al parsear cookies JSON: {e}")
        return cookie_content
    except Exception as e:
        print(f"⚠️ Error inesperado al formatear cookies: {e}")
        return cookie_content



def procesar_email_individual(email_id, coordinates, filepath, contador, total, browser_id=None, browser_name=None):
    """
    Procesa un email individual en el proceso de creación de cuenta LinkedIn
    """
    global _session_creator_user_agent
    _session_creator_user_agent = ""

    from app.database.database import get_creator_email_by_id
    from app.creator.computer_actions import click_coordinates, wait_for_creator_image, type_text, press_key, generate_random_password, generate_random_name, generate_random_lastname
    import time
    
    # Obtener el email por ID
    current_email = get_creator_email_by_id(email_id)
    if not current_email:
        print(f"⚠️ Email ID {email_id} no encontrado")
        return False
    
    # Paso 1: Click en el navegador
    if not _click_brave(coordinates, browser_name=browser_name):
        return False

    # Proxy encendido durante toda la cuenta; se apaga en finally al terminar (éxito o fallo)
    _activar_proxy(coordinates)
    try:
        # Paso 2: Opcional UA por extensión + clic en LinkedIn fav
        if not _click_linkedin_fav(coordinates, browser_id=browser_id):
            return False
        
        # Paso 3: Verificar carga de LinkedIn
        if not _verificar_carga_linkedin(coordinates, browser_name=browser_name):
            print("❌ LinkedIn no cargó correctamente - cerrando ventana")
            _cerrar_ventana(coordinates)
            return False
        
        # Verificar proxy error después de cargar LinkedIn
        _verificar_y_cerrar_proxy_error(coordinates, browser_name=browser_name)
        
        # Paso 4: Llenar formulario de registro
        formulario_ok, full_email = _llenar_formulario_registro(coordinates, current_email, browser_id=browser_id, browser_name=browser_name)
        if not formulario_ok:
            return False
        
        # Verificar proxy error después de llenar formulario
        _verificar_y_cerrar_proxy_error(coordinates, browser_name=browser_name)
        
        # Paso 5: Observar y crear cuenta
        cuenta_creada = observador_unificado(coordinates, full_email, _get_password_usado(), filepath, browser_id=browser_id, browser_name=browser_name)
        exito_bool = cuenta_creada if isinstance(cuenta_creada, bool) else bool(
            isinstance(cuenta_creada, tuple) and len(cuenta_creada) > 0 and cuenta_creada[0] is True
        )

        # Paso 6: Cerrar ventana si se creó exitosamente
        if exito_bool:
            _cerrar_ventana(coordinates)
            return True
        return False
    finally:
        _desactivar_proxy(coordinates, silent=True)


def procesar_email_individual_con_detalle(email_id, coordinates, filepath, contador, total, browser_id=None, browser_name=None):
    """
    Procesa un email individual en el proceso de creación de cuenta LinkedIn con información detallada
    Retorna: (exito: bool, motivo_fallo: str, detalles: dict)
    
    Args:
        email_id: Puede ser un ID de email (int) o un email directamente (str) cuando is33mail es false
        browser_id: ID del navegador activo
        browser_name: Nombre del navegador activo
    """
    global _session_creator_user_agent
    _session_creator_user_agent = ""

    from app.database.database import get_creator_email_by_id
    from app.creator.computer_actions import click_coordinates, wait_for_creator_image, type_text, press_key, generate_random_password, generate_random_name, generate_random_lastname
    import time
    
    # Si email_id es un string, usarlo directamente (modo domain)
    if isinstance(email_id, str):
        current_email = email_id
    else:
        # Obtener el email por ID
        current_email = get_creator_email_by_id(email_id)
        if not current_email:
            print(f"⚠️ Email ID {email_id} no encontrado")
            return False, "email_no_encontrado", {"email_id": email_id}
    
    # Verificar si se debe detener el bot antes de comenzar
    from app.auth.auth import bot_running
    if not bot_running:
        print("🛑 Señal de detención recibida. Deteniendo procesamiento de email...")
        close_window_coords = coordinates.get("close_window")
        if close_window_coords:
            from app.creator.computer_actions import click_coordinates
            click_coordinates(close_window_coords)
            time.sleep(1)
        return False, "detenido_por_usuario", {}
    
    # Paso 1: Click en el navegador
    if not _click_brave(coordinates, browser_name=browser_name):
        return False, "error_click_brave", {}
    
    # Verificar si se debe detener el bot
    if not bot_running:
        print("🛑 Señal de detención recibida. Deteniendo procesamiento de email...")
        close_window_coords = coordinates.get("close_window")
        if close_window_coords:
            from app.creator.computer_actions import click_coordinates
            click_coordinates(close_window_coords)
            time.sleep(1)
        return False, "detenido_por_usuario", {}

    # Proxy encendido durante toda la cuenta; se apaga en finally al terminar (éxito o fallo)
    _activar_proxy(coordinates)
    try:
        # Paso 2: Opcional UA por extensión + clic en LinkedIn fav
        if not _click_linkedin_fav(coordinates, browser_id=browser_id):
            return False, "error_click_linkedin_fav", {}
        
        # Verificar si se debe detener el bot
        if not bot_running:
            print("🛑 Señal de detención recibida. Deteniendo procesamiento de email...")
            close_window_coords = coordinates.get("close_window")
            if close_window_coords:
                from app.creator.computer_actions import click_coordinates
                click_coordinates(close_window_coords)
                time.sleep(1)
            return False, "detenido_por_usuario", {}
        
        # Paso 3: Verificar carga de LinkedIn
        if not _verificar_carga_linkedin(coordinates, browser_name=browser_name):
            print("❌ LinkedIn no cargó correctamente - cerrando ventana")
            _cerrar_ventana(coordinates)
            return False, "error_carga_linkedin", {}
        
        # Verificar si se debe detener el bot después de verificar LinkedIn
        if not bot_running:
            print("🛑 Señal de detención recibida. Deteniendo procesamiento de email...")
            close_window_coords = coordinates.get("close_window")
            if close_window_coords:
                from app.creator.computer_actions import click_coordinates
                click_coordinates(close_window_coords)
                time.sleep(1)
            return False, "detenido_por_usuario", {}
        
        # Verificar proxy error después de cargar LinkedIn
        _verificar_y_cerrar_proxy_error(coordinates, browser_name=browser_name)
        
        # Paso 4: Llenar formulario de registro
        formulario_ok, full_email = _llenar_formulario_registro(coordinates, current_email, browser_id=browser_id, browser_name=browser_name)
        if not formulario_ok:
            return False, "error_llenar_formulario", {}
        
        # Verificar proxy error después de llenar formulario
        _verificar_y_cerrar_proxy_error(coordinates, browser_name=browser_name)
        
        # Paso 5: Observar y crear cuenta con detalle
        exito, motivo_fallo, detalles = observador_unificado_con_detalle(
            coordinates, full_email, _get_password_usado(), filepath, 
            browser_id=browser_id, browser_name=browser_name
        )
        
        # Paso 6: Cerrar ventana si se creó exitosamente
        if exito:
            _cerrar_ventana(coordinates)
            return True, "exito", detalles
        return False, motivo_fallo, detalles
    finally:
        _desactivar_proxy(coordinates, silent=True)


def _click_brave(coordinates, browser_name=None):
    """Hace clic en el navegador con validación de imagen"""
    from app.creator.computer_actions import click_coordinates, wait_for_creator_image, press_key
    import time
    
    # Obtener nombre del navegador para mensajes
    nombre_navegador = browser_name if browser_name else "navegador"
    
    brave_coords = coordinates.get("brave_click")
    if not brave_coords:
        return False
    
    max_intentos = 3
    
    from app.auth.auth import bot_running
    
    for intento in range(1, max_intentos + 1):
        # Verificar si se debe detener el bot
        if not bot_running:
            print("🛑 Señal de detención recibida. Deteniendo clic en navegador...")
            return False
        
        # Hacer un solo clic, esperar medio segundo y presionar Enter
        click_coordinates(brave_coords, double_click=False)
        # Sleep interrumpible
        sleep_interval = 0.1
        slept = 0
        while slept < 0.5:
            if not bot_running:
                print("🛑 Señal de detención recibida. Deteniendo clic en navegador...")
                return False
            time.sleep(sleep_interval)
            slept += sleep_interval
        
        press_key('enter')
        # Sleep interrumpible
        sleep_interval = 0.5
        slept = 0
        while slept < 2:
            if not bot_running:
                print("🛑 Señal de detención recibida. Deteniendo clic en navegador...")
                return False
            time.sleep(sleep_interval)
            slept += sleep_interval
        
        # Validar que la imagen del navegador apareció (busca en la carpeta específica del navegador)
        browser_image_found = wait_for_creator_image("brave_image", max_attempts=2, delay_between_attempts=0.5, silent=True, browser_name=browser_name)
        
        # Si NO encuentra la imagen en el primer intento, significa que hizo el clic bien
        # (El navegador ya está abierto/no está en la pantalla de inicio)
        if not browser_image_found:
            print(f"✅ {nombre_navegador} validado en el intento {intento} - clic realizado correctamente")
            # Verificar proxy error después de abrir el navegador
            _verificar_y_cerrar_proxy_error(coordinates, browser_name=browser_name)
            return True
        
        # Si encuentra la imagen, significa que NO hizo el clic bien
        # (El navegador todavía está en la pantalla de inicio)
        if intento < max_intentos:
            print(f"⚠️ {nombre_navegador} todavía en pantalla de inicio, reintentando clic... ({intento}/{max_intentos})")
            time.sleep(1)
        else:
            # Después de 3 intentos y siempre encuentra la imagen, algo está mal
            print(f"❌ No se pudo abrir {nombre_navegador} correctamente después de 3 intentos")
            return False
    
    return False


def _click_linkedin_fav(coordinates, browser_id=None):
    """Clic en fav LinkedIn. Si en bot_settings está activado, aplica UA por extensión antes."""
    from app.creator.computer_actions import click_coordinates
    from app.auth.auth import bot_running
    from app.database.database import get_bot_settings
    import time

    global _session_creator_user_agent
    
    # Sleep interrumpible
    sleep_interval = 0.5
    slept = 0
    while slept < 3:
        if not bot_running:
            print("🛑 Señal de detención recibida. Deteniendo clic en LinkedIn...")
            return False
        time.sleep(sleep_interval)
        slept += sleep_interval

    cfg = get_bot_settings() or {}
    if cfg.get("enable_creator_user_agent_actions"):
        if not _aplicar_user_agent_antes_linkedin(browser_id):
            return False
    else:
        _session_creator_user_agent = ""

    linkedin_coords = coordinates.get("linkedin_fav_click")
    if not linkedin_coords:
        return False
    time.sleep(5)
    click_coordinates(linkedin_coords)
    
    # Sleep interrumpible
    slept = 0
    while slept < 3:
        if not bot_running:
            print("🛑 Señal de detención recibida. Deteniendo clic en LinkedIn...")
            return False
        time.sleep(sleep_interval)
        slept += sleep_interval
    
    # Verificar proxy error después de abrir LinkedIn
    if not bot_running:
        print("🛑 Señal de detención recibida. Deteniendo clic en LinkedIn...")
        return False
    
    _verificar_y_cerrar_proxy_error(coordinates)
    
    return True


def _verificar_carga_linkedin(coordinates=None, browser_name=None):
    """
    Verifica que LinkedIn haya cargado buscando una de las imágenes de éxito.
    Con proxy activo la carga tarda más: espera inicial larga y muchas rondas de
    detección sin cerrar ni reabrir el navegador.
    """
    from app.creator.computer_actions import find_creator_image
    import time

    linkedin_verification_images = [
        "imagen_de_verificacion_de_exito_carga_linkedin",
        "imagen_de_verificacion_de_exito_carga_linkedin_2",
        "imagen_de_verificacion_de_exito_carga_linkedin_3",
    ]

    # Tiempos pensados para conexión lenta / proxy (sin reiniciar el navegador)
    INITIAL_WAIT_SEC = 10.0
    MAX_ROUNDS = 40
    DELAY_BETWEEN_ROUNDS_SEC = 3.0
    EXTRA_PAUSE_FIRST_ROUND_SEC = 2.0
    confidence = 0.88

    nombre_navegador = browser_name if browser_name else "navegador"
    print(
        f"🔍 Verificando carga de LinkedIn (Navegador: {nombre_navegador}) — "
        f"hasta {MAX_ROUNDS} rondas, ~{int(INITIAL_WAIT_SEC + MAX_ROUNDS * DELAY_BETWEEN_ROUNDS_SEC)}s máx. aprox., sin cerrar ventana"
    )

    from app.auth.auth import bot_running

    if not bot_running:
        print("🛑 Señal de detención recibida. Deteniendo verificación de LinkedIn...")
        return False

    sleep_interval = 0.5
    slept = 0
    while slept < INITIAL_WAIT_SEC:
        if not bot_running:
            print("🛑 Señal de detención recibida. Deteniendo verificación de LinkedIn...")
            return False
        time.sleep(sleep_interval)
        slept += sleep_interval

    for round_idx in range(1, MAX_ROUNDS + 1):
        if not bot_running:
            print("🛑 Señal de detención recibida. Deteniendo verificación de LinkedIn...")
            return False

        if round_idx == 1:
            slept = 0
            while slept < EXTRA_PAUSE_FIRST_ROUND_SEC:
                if not bot_running:
                    print("🛑 Señal de detención recibida. Deteniendo verificación de LinkedIn...")
                    return False
                time.sleep(sleep_interval)
                slept += sleep_interval

        for image_name in linkedin_verification_images:
            if not bot_running:
                print("🛑 Señal de detención recibida. Deteniendo verificación de LinkedIn...")
                return False
            verification_image = find_creator_image(
                image_name, confidence=confidence, browser_name=browser_name
            )
            if verification_image:
                print(f"✅ Imagen de carga LinkedIn detectada (ronda {round_idx}/{MAX_ROUNDS}): {image_name}")
                return True

        if round_idx < MAX_ROUNDS:
            if round_idx % 5 == 0:
                print(f"⏳ LinkedIn aún cargando… ronda {round_idx}/{MAX_ROUNDS}, esperando {DELAY_BETWEEN_ROUNDS_SEC:.0f}s")
            slept = 0
            while slept < DELAY_BETWEEN_ROUNDS_SEC:
                if not bot_running:
                    print("🛑 Señal de detención recibida. Deteniendo verificación de LinkedIn...")
                    return False
                time.sleep(sleep_interval)
                slept += sleep_interval

    print(
        f"❌ No se encontró imagen de verificación de LinkedIn tras {MAX_ROUNDS} rondas "
        f"(~{int(INITIAL_WAIT_SEC + MAX_ROUNDS * DELAY_BETWEEN_ROUNDS_SEC)}s de espera acumulada aprox.)"
    )
    return False


def _escribir_y_verificar_campo(texto, tipo_campo="campo", max_intentos=3):
    """
    Función unificada para escribir y verificar cualquier campo del formulario.
    
    Args:
        texto (str): El texto a escribir
        tipo_campo (str): Tipo de campo para los mensajes (email, password, nombre, apellido, etc.)
        max_intentos (int): Número máximo de intentos (default: 3)
    
    Returns:
        bool: True si se escribió correctamente, False en caso contrario
    """
    from app.creator.computer_actions import type_text
    import time
    import pyperclip
    import pyautogui
    
    # Iconos para diferentes tipos de campo
    iconos = {
        "email": "📧",
        "password": "🔐", 
        "nombre": "👤",
        "apellido": "👥",
        "campo": "📝"
    }
    
    icono = iconos.get(tipo_campo, "📝")
    
    for intento in range(max_intentos):
        # Limpiar el campo primero
        pyperclip.copy("")
        time.sleep(0.05)
        
        # Seleccionar todo el texto en el campo
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.1)
        
        # Escribir el texto
        success = type_text(texto)
        if not success:
            time.sleep(0.3)
            continue
        
        # Esperar un poco más para que se complete la operación
        time.sleep(0.4)
        
        # Verificar que el texto se haya pegado correctamente
        if _verificar_campo_pegado(texto, tipo_campo):
            return True
        else:
            time.sleep(0.3)
    
    return False


def _verificar_campo_pegado(texto_esperado, tipo_campo="campo"):
    """
    Verifica que el texto se haya pegado correctamente en el campo.
    Lee el contenido del portapapeles después de seleccionar todo el texto del campo.
    
    Args:
        texto_esperado (str): El texto que se espera encontrar
        tipo_campo (str): Tipo de campo para los mensajes de error
    
    Returns:
        bool: True si el texto se pegó correctamente, False en caso contrario
    """
    import pyperclip
    import pyautogui
    import time
    
    try:
        # Seleccionar todo el texto en el campo actual
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.1)
        
        # Copiar el texto seleccionado
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.2)
        
        # Leer el contenido del portapapeles
        texto_pegado = pyperclip.paste()
        
        # Verificar si el texto está en el texto pegado
        if texto_esperado in texto_pegado:
            return True
        else:
            return False, "timeout", {"tiempo_transcurrido": 0, "timeout_seconds": 0}
            
    except Exception as e:
        return False


def _llenar_formulario_registro(coordinates, email, browser_id=None, browser_name=None):
    """Llena el formulario de registro de LinkedIn"""
    from app.creator.computer_actions import click_coordinates, type_text, press_key, generate_random_password, generate_random_name, generate_random_lastname, wait_for_creator_image, generate_email_prefix, generate_email_with_domain_format
    from app.database.database import get_creator_setting
    import random
    import time
    import pyperclip

    def _agregar_sufijo_4_digitos(email_base):
        """Agrega un sufijo aleatorio de 4 dígitos al local-part del email."""
        if not email_base or "@" not in email_base:
            return email_base
        local, domain = email_base.split("@", 1)
        sufijo = f"{random.randint(0, 9999):04d}"
        return f"{local}{sufijo}@{domain}"
    
    # Click en email_input_click
    email_coords = coordinates.get("email_input_click")
    if not email_coords:
        return False, None
    
    time.sleep(0.5)
    click_coordinates(email_coords)
    time.sleep(0.5)
    
    # Limpiar portapapeles antes de escribir email
    pyperclip.copy("")
    time.sleep(0.2)
    
    # Generar email según configuración
    if email.startswith('@'):
        # Obtener configuración para verificar is33mail
        if browser_id:
            settings = get_creator_setting(browser_id)
        else:
            settings = None
        is33mail = settings.get('is33mail', True) if settings else True
        
        random_domains = settings.get('random_domains', False) if settings else False
        if (not is33mail) or random_domains:
            # El dominio ya viene con el relleno aplicado desde _ejecutar_proceso_creator
            # No aplicar relleno aquí para evitar doble relleno
            # Usar formato específico para dominio personalizado
            full_email_base = generate_email_with_domain_format(email)
            full_email = _agregar_sufijo_4_digitos(full_email_base)
            print(f"[DEBUG] email completo={full_email!r} (formato personalizado + 4 dígitos, dominio={email!r})")
        else:
            # Generar prefijo aleatorio y concatenar con el dominio (modo 33mail)
            prefix = generate_email_prefix()
            full_email_base = f"{prefix}{email}"
            full_email = _agregar_sufijo_4_digitos(full_email_base)
            print(f"[DEBUG] email completo={full_email!r} (33mail + 4 dígitos, dominio={email!r})")
    else:
        # Si ya viene completo, usar tal como está
        full_email = _agregar_sufijo_4_digitos(email)
        print(f"[DEBUG] email completo={full_email!r} (recibido + 4 dígitos)")
    
    # Escribir email completo con verificación (proxy desactivado - no se necesita)
    if not _escribir_y_verificar_campo(full_email, "email"):
        return False, None
    
    # Verificar proxy error (sin activar proxy)
    _verificar_y_cerrar_proxy_error(coordinates, browser_name=browser_name)
    
    # Ir al campo de contraseña
    press_key("tab")
    time.sleep(0.5)
    
    # Escribir contraseña aleatoria (sin verificación para mayor velocidad, proxy desactivado)
    password = generate_random_password()
    print(f"[DEBUG] password={password!r}")
    type_text(password)
    time.sleep(0.3)  # Tiempo mínimo para que se escriba
    
    # Presionar tecla Esc después de pegar la contraseña
    press_key("esc")
    # Si llegamos aquí, la verificación fue exitosa
    time.sleep(2)
    
    # Determinar qué botón continue usar según si hay checkbox
    checkbox_found = wait_for_creator_image("Checkbox recuerdame", max_attempts=1, delay_between_attempts=0.3, silent=True, browser_name=browser_name)
    
    if checkbox_found:
        continue_coords = coordinates.get("continue_button_click")
    else:
        continue_coords = coordinates.get("continue_button_click_optional")
    
    if not continue_coords:
        print("⚠️ No se encontraron coordenadas de continue_button")
        return False, None
    
    # Verificar que se cargó correctamente el email y contraseña DESPUÉS del clic en continue
    max_intentos_verificacion = 4
    email_password_loaded = False
    
    for intento_verificacion in range(1, max_intentos_verificacion + 1):
        # Hacer clic en continue_button SIN activar proxy (no se necesita para este clic)
        # print(f"🔄 Haciendo clic en continue_button (intento {intento_verificacion}/{max_intentos_verificacion})")
        click_coordinates(continue_coords)
        time.sleep(2)  # Tiempo de espera después del clic (sin proxy)
        
        # DESPUÉS del clic, verificar imagen de carga de email y contraseña
        # Usar confidence muy alto (0.98) para evitar falsos positivos con botones similares
        email_password_loaded = wait_for_creator_image(
            "Imagen de verificación de carga email y contraseña", 
            max_attempts=3, 
            delay_between_attempts=0.5, 
            silent=True,  # Silencioso para reducir ruido en consola
            confidence=0.98,  # Confidence muy alto para evitar falsos positivos
            browser_name=browser_name
        )
        
        if email_password_loaded:
            # print("✅ Email y contraseña cargados correctamente")
            break
        
        # Si no se encontró la imagen
        if intento_verificacion < max_intentos_verificacion:
            # print(f"⚠️ No se encontró imagen de verificación después del clic (intento {intento_verificacion}/{max_intentos_verificacion})")
            # Esperar un poco antes de volver a intentar
            time.sleep(1)
        else:
            # Último intento fallido
            # print("❌ No se pudo verificar la carga correcta del email y contraseña después de 4 intentos")
            # print("🔄 Cerrando ventana y continuando con el siguiente email")
            close_window_coords = coordinates.get("close_window")
            if close_window_coords:
                click_coordinates(close_window_coords)
                time.sleep(1)
            return False, None
    

    
    # Verificar proxy error antes de continuar
    _verificar_y_cerrar_proxy_error(coordinates, browser_name=browser_name)
    
    # Click en name_input_click
    name_coords = coordinates.get("name_input_click")
    if not name_coords:
        return False, None
    
    click_coordinates(name_coords)
    time.sleep(0.5)
    
    # Escribir nombre aleatorio con verificación (proxy desactivado - no se necesita)
    random_name = generate_random_name()
    if not _escribir_y_verificar_campo(random_name, "nombre"):
        return False, None
    
    # Ir al campo de apellido
    press_key("tab")
    time.sleep(0.5)
    
    # Escribir apellido aleatorio con verificación (proxy desactivado - no se necesita)
    random_lastname = generate_random_lastname()
    if not _escribir_y_verificar_campo(random_lastname, "apellido"):
        return False, None

    print(
        f"[DEBUG] resumen registro: email={full_email!r} | password={password!r} | "
        f"nombre={random_name!r} | apellido={random_lastname!r}"
    )

    # Click en continue_button2_click (proxy ya activo desde antes del fav de LinkedIn)
    continue2_coords = coordinates.get("continue_button2_click")
    if not continue2_coords:
        return False, None
    click_coordinates(continue2_coords)
    time.sleep(3)
    
    # Guardar password para uso posterior
    global _password_usado
    _password_usado = password
    return True, full_email


def _get_password_usado():
    """Obtiene el password usado en el formulario"""
    global _password_usado
    return _password_usado


def _aplicar_user_agent_antes_linkedin(browser_id=None):
    """Ejecuta user_agent_actions y guarda el UA del pool en sesión para el archivo de cuentas."""
    from app.creator.user_agent_actions import resolve_browser_id, run_user_agent_extension_click

    global _session_creator_user_agent
    bid = resolve_browser_id(browser_id)
    if bid is None:
        print("⚠️ Sin navegador para aplicar user agent.")
        _session_creator_user_agent = ""
        return False

    ok, ua = run_user_agent_extension_click(bid)
    if ok and ua:
        _session_creator_user_agent = ua.strip()
        return True

    _session_creator_user_agent = ""
    print("❌ No se pudo aplicar user agent antes de LinkedIn.")
    return False


def _cerrar_ventana(coordinates):
    """Cierra la ventana después de crear la cuenta exitosamente"""
    from app.creator.computer_actions import click_coordinates
    import time
    
    close_window_coords = coordinates.get("close_window")
    if close_window_coords:
        click_coordinates(close_window_coords)
        time.sleep(2)


def _ejecutar_modo_avion():
    """Ejecuta el modo avión si está disponible"""
    import os
    import subprocess
    import time
    from app.database.database import get_bot_settings
    
    config = get_bot_settings()
    
    # Ruta del ejecutable ADB - verificar si existe
    adb_path = r"C:\Adb\adb.exe"
    adb_available = os.path.exists(adb_path)
    
    if not adb_available:
        return
    
    # Ejecutar comandos ADB solo si está disponible y habilitado
    enable_adb = config.get("enable_adb", True)
    if adb_available and enable_adb:
        try:
            # Ejecutar el comando para activar el modo avión
            subprocess.run([adb_path, "shell", "cmd", "connectivity", "airplane-mode", "enable"], 
                            capture_output=True, text=True, timeout=10)
            print("########################################################")
            print("✈️ Modo avión activado")
            time.sleep(3)

            # Ejecutar el comando para desactivar el modo avión
            subprocess.run([adb_path, "shell", "cmd", "connectivity", "airplane-mode", "disable"], 
                            capture_output=True, text=True, timeout=10)
            print("📶 Modo avión desactivado")
            time.sleep(3)
            try:
                from app.auth.auth import reconnect_bot_websocket_after_network_recovery

                reconnect_bot_websocket_after_network_recovery()
            except Exception as e:
                print(f"⚠️ Reconexión WebSocket tras modo avión: {e}")
        except Exception as e:
            pass
    else:
        print("❌ Modo avión no activado")
        time.sleep(2)


def _activar_proxy(coordinates):
    """Activa proxy según bot_settings: coordenadas (extensión) o proxy de Windows."""
    import sys
    import time
    import winreg
    from app.database.database import get_bot_settings
    from app.creator.computer_actions import click_coordinates
    from app.confirmabot.utils.proxy_tool_safe import SafeProxyController

    global _proxy_activado_por_click, _proxy_modo_usado
    config = get_bot_settings() or {}
    if not config.get("enable_proxy"):
        return

    use_coord = bool(config.get("proxy_via_coordinates"))
    use_win = bool(config.get("proxy_via_windows"))

    if use_coord:
        try:
            proxy_extension_coords = coordinates.get("proxy_extension_click") if coordinates else None
            activate_proxy_coords = coordinates.get("activate_proxy_click") if coordinates else None
            if not proxy_extension_coords or not activate_proxy_coords:
                print("⚠️ Faltan coordenadas de proxy (extensión/activar)")
                return
            click_coordinates(proxy_extension_coords)
            time.sleep(1)
            click_coordinates(activate_proxy_coords)
            _proxy_activado_por_click = True
            _proxy_modo_usado = "coordinates"
            print("✅ Proxy por coordenadas activado")
        except Exception as e:
            print(f"❌ Error al activar proxy por coordenadas: {e}")
        return

    if not use_win:
        return

    if sys.platform != "win32":
        print("⚠️ Proxy por registro de Windows solo disponible en Windows")
        return

    controller = None
    try:
        controller = SafeProxyController()
        if not controller.proxy_key:
            print("⚠️ No se pudo abrir la clave de proxy de Windows")
            return

        enabled_before, server_status, _ = controller.get_proxy_status()
        server = server_status
        if not server and controller.proxy_key:
            try:
                server, _ = winreg.QueryValueEx(controller.proxy_key, "ProxyServer")
            except OSError:
                server = None
        server = (str(server).strip() if server else "")
        if not enabled_before and not server:
            print(
                "⚠️ No hay servidor proxy en Windows; configura el proxy en "
                "Configuración de Internet antes de usar esta opción"
            )
            return

        if not controller.enable_proxy_only():
            print("⚠️ No se pudo activar el proxy de Windows")
            return

        controller.refresh_internet_settings()
        if not enabled_before:
            _proxy_activado_por_click = True
            _proxy_modo_usado = "windows"
        print("✅ Proxy de Windows activado")
    except Exception as e:
        print(f"❌ Error al activar proxy: {e}")
    finally:
        if controller:
            try:
                controller.close()
            except Exception:
                pass


def _desactivar_proxy(coordinates, silent=False):
    """Desactiva el proxy del modo usado en _activar_proxy (coordenadas o Windows)."""
    import sys
    import time
    from app.database.database import get_bot_settings
    from app.creator.computer_actions import click_coordinates
    from app.confirmabot.utils.proxy_tool_safe import SafeProxyController

    global _proxy_activado_por_click, _proxy_modo_usado
    config = get_bot_settings() or {}
    if not config.get("enable_proxy"):
        return

    if not _proxy_activado_por_click:
        return

    modo = _proxy_modo_usado

    if modo == "coordinates":
        try:
            proxy_extension_coords = coordinates.get("proxy_extension_click") if coordinates else None
            disable_proxy_coords = coordinates.get("disable_proxy_click") if coordinates else None
            if not proxy_extension_coords or not disable_proxy_coords:
                if not silent:
                    print("⚠️ Faltan coordenadas para desactivar proxy (extensión/apagar)")
                return
            click_coordinates(proxy_extension_coords)
            time.sleep(0.5)
            click_coordinates(disable_proxy_coords)
            _proxy_activado_por_click = False
            _proxy_modo_usado = None
            if not silent:
                print("✅ Proxy por coordenadas desactivado")
        except Exception as e:
            if not silent:
                print(f"❌ Error al desactivar proxy por coordenadas: {e}")
        return

    if modo != "windows":
        return

    if sys.platform != "win32":
        return

    controller = None
    try:
        controller = SafeProxyController()
        if not controller.proxy_key:
            if not silent:
                print("⚠️ No se pudo acceder al registro para desactivar proxy")
            return

        if not controller.disable_proxy():
            if not silent:
                print("⚠️ No se pudo desactivar el proxy de Windows")
            return

        controller.refresh_internet_settings()
        _proxy_activado_por_click = False
        _proxy_modo_usado = None
        if not silent:
            print("✅ Proxy de Windows desactivado")
    except Exception as e:
        if not silent:
            print(f"❌ Error al desactivar proxy: {e}")
    finally:
        if controller:
            try:
                controller.close()
            except Exception:
                pass


def _actualizar_encabezado_con_exitos(filepath, total_emails, emails_exitosos):
    """Actualiza el encabezado del archivo con la información de éxitos"""
    from datetime import datetime
    
    try:
        # Leer el contenido actual del archivo
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Crear nuevo encabezado con información de éxitos
        fecha_hora = datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')
        nuevo_encabezado = [
            f"CUENTAS LINKEDIN CREADAS - {fecha_hora}\n",
            "="*60 + "\n",
            f"Total de emails a procesar: {total_emails}\n",
            f"Emails procesados con éxito: {emails_exitosos}\n",
            f"Emails fallidos: {total_emails - emails_exitosos}\n",
            "Formato: User-Agent | Email | Password | Cookie\n",
            "="*60 + "\n\n"
        ]
        
        # Encontrar donde empiezan las cuentas (después del segundo separador)
        inicio_cuentas = 0
        separadores_encontrados = 0
        for i, line in enumerate(lines):
            if line.strip() == "="*60:
                separadores_encontrados += 1
                if separadores_encontrados == 2:  # Segundo separador
                    inicio_cuentas = i + 2  # Saltar las líneas de separación
                    break
        
        # Escribir el archivo actualizado
        with open(filepath, 'w', encoding='utf-8') as f:
            # Escribir nuevo encabezado
            f.writelines(nuevo_encabezado)
            # Escribir las cuentas existentes
            if inicio_cuentas < len(lines):
                f.writelines(lines[inicio_cuentas:])
                
    except Exception as e:
        pass


def _inicializar_archivo_salida(total_emails):
    """Inicializa el archivo de salida para el bucle"""
    import os
    from datetime import datetime
    from app.utils.path_utils import get_linkedin_accounts_path, ensure_directory_exists
    
    # Crear carpeta linkedin_accounts si no existe (al lado del ejecutable)
    folder_path = get_linkedin_accounts_path()
    ensure_directory_exists(folder_path)
    
    # Crear un solo archivo para todo el bucle
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"cuentas_creadas_bucle_{timestamp}.txt"
    filepath = os.path.join(folder_path, filename)
    
    # Escribir encabezado del archivo
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            fecha_hora = datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')
            f.write(f"CUENTAS LINKEDIN CREADAS - {fecha_hora}\n")
            f.write("="*60 + "\n")
            f.write(f"Total de emails a procesar: {total_emails}\n")
            f.write("Formato: User-Agent | Email | Password | Cookie\n")
            f.write("="*60 + "\n\n")
        return filepath
    except Exception as e:
        return None


def _verificar_hora_programada(browser_id=None):
    """
    Verifica si hay una hora programada y espera hasta esa hora si es necesario.
    Usa la configuración global de tiempo (no requiere browser_id)
    
    Args:
        browser_id: IGNORADO - mantenido por compatibilidad. La configuración ahora es global.
    
    Returns:
        bool: True si debe continuar con el proceso, False si debe detenerse
    """
    from app.database.database import get_global_time_config
    import time
    import datetime
    import pytz
    import re
    
    # Obtener configuración global de tiempo
    global_time_config = get_global_time_config()
    
    # Solo verificar hora programada si el tipo de configuración es 'scheduled' o 'both'
    time_config_type = global_time_config.get('time_config_type')
    if time_config_type not in ['scheduled', 'both']:
        print("⚡ Configuración de ciclo de tiempo, ejecutando inmediatamente")
        return True  # No es configuración programada, continuar inmediatamente
    
    # Verificar si hay hora programada configurada
    if not global_time_config.get('scheduled_time') or not global_time_config.get('timezone'):
        print("⚡ No hay hora programada configurada, ejecutando inmediatamente")
        return True  # No hay hora programada, continuar inmediatamente
    
    scheduled_time = global_time_config.get('scheduled_time')
    timezone_str = global_time_config.get('timezone')
    
    print(f"🕐 Hora programada configurada: {scheduled_time} ({timezone_str})")
    
    try:
        # Extraer el offset GMT del string del país
        offset_match = re.search(r'GMT([+-]\d{1,2}(?::\d{2})?)', timezone_str)
        if not offset_match:
            return True  # No se pudo parsear, continuar inmediatamente
        
        offset_str = offset_match.group(1)
        
        # Manejar formato GMT+5:30 (India)
        if ':' in offset_str:
            hours, minutes = offset_str.split(':')
            offset_hours = int(hours) + (int(minutes) / 60)
        else:
            offset_hours = int(offset_str)
        
        # Crear zona horaria personalizada
        custom_tz = pytz.FixedOffset(offset_hours * 60)
        
        # Obtener hora actual y objetivo
        now = datetime.datetime.now(custom_tz)
        target_hour, target_minute = map(int, scheduled_time.split(':'))
        target_datetime = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
        
        # Si la hora ya pasó hoy, programar para mañana
        if target_datetime <= now:
            target_datetime += datetime.timedelta(days=1)
        
        # Calcular tiempo de espera
        wait_seconds = (target_datetime - now).total_seconds()
        
        if wait_seconds > 0:
            wait_hours = wait_seconds / 3600
            print(f"⏳ Esperando {wait_hours:.1f}h para iniciar...")
            
            # Esperar hasta la hora programada
            time.sleep(wait_seconds)
            print("🚀 ¡Iniciando proceso!")
        
        return True
        
    except Exception as e:
        print(f"⚠️ Error en hora programada: {e}")
        return True  # En caso de error, continuar inmediatamente


def _determinar_emails_realmente_fallidos(emails_procesados, browser_id=None):
    """
    Determina qué emails realmente fallaron (no se usaron exitosamente en ningún momento)
    
    Args:
        emails_procesados (list): Lista de emails procesados con sus resultados
        browser_id (int, optional): ID del navegador para obtener configuración
    
    Returns:
        list: Lista de emails que realmente fallaron (no exitosos)
    """
    try:
        from app.database.database import get_creator_setting, get_default_browser
        from datetime import datetime
        
        cuentas_realmente_fallidas = []
        
        # Si no se proporciona browser_id, intentar obtenerlo del primer email procesado o usar el navegador por defecto
        if not browser_id:
            # Intentar obtener browser_id del primer email procesado que tenga browser_name
            for email_resultado in emails_procesados:
                if 'browser_name' in email_resultado:
                    # Buscar el browser_id basado en el browser_name
                    from app.database.database import get_active_browsers
                    active_browsers = get_active_browsers()
                    for browser in active_browsers:
                        if browser['name'] == email_resultado['browser_name']:
                            browser_id = browser['id']
                            break
                    if browser_id:
                        break
            
            # Si aún no hay browser_id, usar el navegador por defecto
            if not browser_id:
                default_browser = get_default_browser()
                if default_browser:
                    browser_id = default_browser['id']
        
        if browser_id:
            creator_settings = get_creator_setting(browser_id)
        else:
            creator_settings = None
        user_agent = creator_settings.get('user_agent', '') if creator_settings else ''
        
        # Agrupar emails por dirección de email para determinar el estado final
        emails_por_direccion = {}
        for email_resultado in emails_procesados:
            email = email_resultado['email']
            if email not in emails_por_direccion:
                emails_por_direccion[email] = []
            emails_por_direccion[email].append(email_resultado)
        
        # Determinar el estado final de cada email
        for email, resultados in emails_por_direccion.items():
            # Si algún resultado fue exitoso, el email no es realmente fallido
            tiene_exito = any(resultado['exito'] for resultado in resultados)
            
            if not tiene_exito:
                # Buscar el último resultado fallido para obtener los detalles más recientes
                ultimo_fallo = max(resultados, key=lambda x: x.get('contador', 0))
                
                # Excluir linkedin_error de la lista de fallidos (es un error transitorio)
                if ultimo_fallo.get('motivo_fallo') == 'linkedin_error':
                    continue
                
                cuenta_fallida = {
                    "email": email,
                    "password": _get_password_usado(),
                    "user_agent": user_agent,
                    "motivo_fallo": ultimo_fallo['motivo_fallo'],
                    "detalles": ultimo_fallo['detalles'],
                    "fecha_fallo": datetime.now().isoformat(),
                    "contador": ultimo_fallo['contador'],
                    "total": len(emails_procesados)
                }
                cuentas_realmente_fallidas.append(cuenta_fallida)
        
        return cuentas_realmente_fallidas
        
    except Exception as e:
        print(f"❌ Error al determinar emails realmente fallidos: {e}")
        return []


def _enviar_archivo_por_correo(filepath, total_emails, emails_exitosos, cuentas_fallidas=None, es_ciclo=False, ciclo_minutes=None, tiempo_inicio_ciclo=None, browser_id=None):
    """
    Envía un correo de informe. Retorna rápidamente si no hay configuración necesaria.
    """
    try:
        from app.confirmabot.hostinger_actions import send_email_with_file
        from app.database.database import get_creator_setting, get_all_emails, get_user_data, get_default_browser
        from app.utils.http_utils import post
        import os
        from datetime import datetime, timedelta
        import json
        
        # Verificar archivo
        if not os.path.exists(filepath):
            print("⚠️ Archivo no encontrado, omitiendo envío de correo")
            return True
        
        # Si no se proporciona browser_id, usar el navegador por defecto
        if not browser_id:
            default_browser = get_default_browser()
            if default_browser:
                browser_id = default_browser['id']
        
        # Obtener email de destino PRIMERO (antes de hacer operaciones costosas)
        try:
            if browser_id:
                settings = get_creator_setting(browser_id)
            else:
                settings = None
            email_destino = settings.get('notification_email') if settings else None
        except Exception as e:
            print(f"⚠️ Error al obtener configuración del navegador: {e}")
            print("ℹ️ Omitiendo envío de correo debido a error")
            return True
        
        if not email_destino:
            print("ℹ️ No hay email de destino configurado, omitiendo envío de correo")
            return True  # No hay email de destino configurado, continuar
        
        # Intentar obtener credenciales de correo (opcional)
        try:
            emails_data = get_all_emails()
        except Exception as e:
            print(f"⚠️ Error al obtener emails de la base de datos: {e}")
            print("ℹ️ Omitiendo envío de correo debido a error")
            return True
        
        if not emails_data or len(emails_data) == 0:
            print("ℹ️ No hay emails configurados, omitiendo envío de correo")
            return True  # No hay emails configurados, omitir envío
        
        # Buscar email con credenciales de Hostinger
        email_address = None
        email_password = None
        for email_data in emails_data:
            if email_data.get('email_hostinger') and email_data.get('password_hostinger'):
                email_address = email_data['email_hostinger']
                email_password = email_data['password_hostinger']
                break
        
        if not email_address or not email_password:
            print("ℹ️ No hay credenciales de Hostinger configuradas, omitiendo envío de correo")
            return True  # No hay credenciales, omitir envío
        
        # Si llegamos aquí, tenemos todo lo necesario para enviar el correo
        print("📧 Iniciando envío de correo de informe...")
        
        # Obtener conteo total de cuentas en el servidor (opcional, no crítico)
        try:
            total_cuentas_servidor = _obtener_conteo_cuentas_servidor()
        except Exception as e:
            print(f"⚠️ No se pudo obtener conteo de cuentas del servidor: {e}")
            total_cuentas_servidor = 0
        
        # Preparar correo
        fecha_hora = datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')
        asunto = f"Reporte LinkedIn Creator - {fecha_hora}"
        
        # Calcular estadísticas reales
        emails_fallidos = len(cuentas_fallidas) if cuentas_fallidas else 0
        total_emails_solicitados = emails_exitosos + emails_fallidos
        tasa_exito_real = (emails_exitosos / total_emails_solicitados * 100) if total_emails_solicitados > 0 else 0
        
        # Calcular tiempo total del ciclo y estadísticas detalladas
        tiempo_total_minutos = 0
        promedio_minutos_por_cuenta = 0
        tiempo_por_cuenta_procesada = 0
        porcentaje_tiempo_por_cuenta = 0
        
        if tiempo_inicio_ciclo:
            tiempo_total_segundos = (datetime.now() - tiempo_inicio_ciclo).total_seconds()
            tiempo_total_minutos = round(tiempo_total_segundos / 60, 2)
            
            if emails_exitosos > 0:
                promedio_minutos_por_cuenta = round(tiempo_total_minutos / emails_exitosos, 2)
                tiempo_por_cuenta_procesada = round(tiempo_total_minutos / total_emails_solicitados, 2) if total_emails_solicitados > 0 else 0
                porcentaje_tiempo_por_cuenta = round((promedio_minutos_por_cuenta / tiempo_total_minutos) * 100, 1) if tiempo_total_minutos > 0 else 0
        
        # Calcular próxima ejecución si es ciclo
        proxima_ejecucion = ""
        if es_ciclo and ciclo_minutes:
            proxima = datetime.now() + timedelta(minutes=ciclo_minutes)
            proxima_ejecucion = f"\n            ⏰ PRÓXIMO CICLO:\n            - Iniciará a las: {proxima.strftime('%H:%M:%S')}\n"
        
        cuerpo = f"""Hola,

            El proceso de creación de cuentas LinkedIn ha finalizado.

            📊 RESUMEN DEL PROCESO:
            - Total de emails solicitados del servidor: {total_emails_solicitados}
            - Cuentas creadas exitosamente: {emails_exitosos}
            - Cuentas que fallaron: {emails_fallidos}
            - Tasa de éxito real: {tasa_exito_real:.1f}%
            
            ⏱️ ESTADÍSTICAS DE TIEMPO:
            - Tiempo total del ciclo: {tiempo_total_minutos} minutos
            - Promedio por cuenta exitosa: {promedio_minutos_por_cuenta} minutos/cuenta
            - Tiempo promedio por cuenta procesada: {tiempo_por_cuenta_procesada} minutos/cuenta
            - Porcentaje de tiempo por cuenta: {porcentaje_tiempo_por_cuenta}%
            
            
            {proxima_ejecucion}
            Saludos,
            ConfirmaBot
        """
        
        # Crear archivo de estadísticas detalladas temporal
        archivo_estadisticas = _crear_archivo_estadisticas_detalladas(cuentas_fallidas, tiempo_total_minutos, promedio_minutos_por_cuenta, tiempo_por_cuenta_procesada, porcentaje_tiempo_por_cuenta)
        
        # Enviar correo con archivo adjunto (con timeout implícito en connect_smtp)
        try:
            exito = send_email_with_file(
                email_address=email_address,
                password=email_password,
                to_email=email_destino,
                subject=asunto,
                body=cuerpo,
                attachment_path=archivo_estadisticas
            )
            
            if exito:
                print("✅ Correo enviado con éxito")
            else:
                print("❌ Error al enviar correo (verificar credenciales o conexión)")
        except Exception as e:
            print(f"❌ Error al intentar enviar correo: {str(e)}")
            exito = False
        finally:
            # Eliminar archivo temporal después del envío (siempre, incluso si falló)
            if archivo_estadisticas and os.path.exists(archivo_estadisticas):
                try:
                    os.remove(archivo_estadisticas)
                except Exception:
                    pass  # Ignorar errores al eliminar
        
        # Retornar True para continuar el proceso incluso si falló el envío
        return True
            
    except Exception as e:
        print(f"❌ Error inesperado al procesar envío de correo: {str(e)}")
        # Retornar True para no bloquear el proceso principal
        return True


    

def _crear_archivo_estadisticas_detalladas(cuentas_fallidas, tiempo_total_minutos, promedio_minutos_por_cuenta, tiempo_por_cuenta_procesada, porcentaje_tiempo_por_cuenta):
    """Crea un archivo detallado con estadísticas del ciclo"""
    from datetime import datetime
    import os
    
    # Crear nombre del archivo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archivo_path = f"estadisticas_ciclo_{timestamp}.txt"
    
    try:
        with open(archivo_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("REPORTE DETALLADO DE CICLO LINKEDIN CREATOR\n")
            f.write("=" * 60 + "\n")
            f.write(f"Fecha y hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"Tiempo total del ciclo: {tiempo_total_minutos} minutos\n")
            f.write(f"Promedio por cuenta exitosa: {promedio_minutos_por_cuenta} minutos/cuenta\n")
            f.write(f"Tiempo promedio por cuenta procesada: {tiempo_por_cuenta_procesada} minutos/cuenta\n")
            f.write(f"Porcentaje de tiempo por cuenta: {porcentaje_tiempo_por_cuenta}%\n")
            f.write("\n")
            
            if cuentas_fallidas:
                f.write("ESTADÍSTICAS DE FALLOS DETALLADAS:\n")
                f.write("-" * 40 + "\n")
                
                # Contar tipos de fallos
                tipos_fallos = {}
                for cuenta in cuentas_fallidas:
                    motivo = cuenta.get('motivo_fallo', 'desconocido')
                    tipos_fallos[motivo] = tipos_fallos.get(motivo, 0) + 1
                
                for motivo, cantidad in tipos_fallos.items():
                    f.write(f"{motivo}: {cantidad} cuentas\n")
                
                f.write("\nDETALLES DE CUENTAS FALLIDAS:\n")
                f.write("-" * 40 + "\n")
                
                for i, cuenta in enumerate(cuentas_fallidas, 1):
                    f.write(f"{i}. Email: {cuenta.get('email', 'N/A')}\n")
                    f.write(f"   Motivo: {cuenta.get('motivo_fallo', 'N/A')}\n")
                    f.write(f"   Detalles: {cuenta.get('detalles', {})}\n")
                    f.write("\n")
            else:
                f.write("No hubo fallos en este ciclo.\n")
        
        return archivo_path
        
    except Exception as e:
        print(f"❌ Error al crear archivo de estadísticas: {e}")
        return None


def _enviar_correo_sin_adjunto(email_address: str, password: str, to_email: str, 
                               subject: str, body: str) -> bool:
    """
    Envía un correo sin archivo adjunto usando las credenciales de Hostinger
    """
    try:
        from app.confirmabot.hostinger_actions import HostingerEmailClient
        
        # Crear cliente de correo
        email_client = HostingerEmailClient(email_address, password)
        
        # Conectar al servidor
        if not email_client.connect():
            print("❌ Error al conectar con el servidor de correo")
            return False, "timeout", {"tiempo_transcurrido": 0, "timeout_seconds": 0}
        
        # Enviar correo
        success = email_client.send_email(to_email, subject, body)
        
        # Desconectar
        email_client.disconnect()
        
        return success
        
    except Exception as e:
        print(f"❌ Error al enviar correo: {e}")
        return False


def _enviar_notificacion_inicio_ciclo(ciclo_numero: int, objetivo_cuentas: int, ciclo_minutes: int, browser_id=None):
    """
    Envía una notificación por email al inicio de cada ciclo
    
    Args:
        ciclo_numero: Número del ciclo
        objetivo_cuentas: Objetivo de cuentas a crear
        ciclo_minutes: Minutos del ciclo
        browser_id: ID del navegador para obtener configuración
    """
    try:
        from app.database.database import get_creator_setting, get_all_emails, get_default_browser
        from datetime import datetime, timedelta
        
        # Si no se proporciona browser_id, usar el navegador por defecto
        if not browser_id:
            default_browser = get_default_browser()
            if default_browser:
                browser_id = default_browser['id']
        
        # Obtener credenciales de correo
        emails_data = get_all_emails()
        if not emails_data:
            return False, "timeout", {"tiempo_transcurrido": 0, "timeout_seconds": 0}
        
        # Buscar email con credenciales de Hostinger
        email_address = None
        email_password = None
        for email_data in emails_data:
            if email_data.get('email_hostinger') and email_data.get('password_hostinger'):
                email_address = email_data['email_hostinger']
                email_password = email_data['password_hostinger']
                break
        
        if not email_address or not email_password:
            return False, "timeout", {"tiempo_transcurrido": 0, "timeout_seconds": 0}
        
        # Obtener email de destino
        if browser_id:
            settings = get_creator_setting(browser_id)
        else:
            settings = None
        email_destino = settings.get('notification_email') if settings else None
        
        if not email_destino:
            return True  # No hay email configurado, continuar
        
        # Preparar correo
        fecha_hora = datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')
        asunto = f"Inicio Ciclo #{ciclo_numero} - LinkedIn Creator"
        
        # Calcular hora estimada de finalización
        hora_finalizacion = datetime.now() + timedelta(minutes=ciclo_minutes)
        hora_fin = hora_finalizacion.strftime('%H:%M:%S')
        
        cuerpo = f"""Hola,

            🔄 CICLO #{ciclo_numero} INICIADO

            📊 INFORMACIÓN DEL CICLO:
            - Hora de inicio: {fecha_hora}
            - Objetivo: {objetivo_cuentas} cuentas

            🎯 El bot está procesando las cuentas...
            Te notificaremos cuando termine este ciclo.

            Saludos,
            ConfirmaBot
            """
        
        # Enviar correo
        exito = _enviar_correo_sin_adjunto(
            email_address=email_address,
            password=email_password,
            to_email=email_destino,
            subject=asunto,
            body=cuerpo
        )
        
        if exito:
            print(f"📧 Notificación de inicio de ciclo #{ciclo_numero} enviada")
        
        return exito
            
    except Exception as e:
        print(f"❌ Error al enviar notificación de inicio de ciclo: {e}")
        return False


def _obtener_conteo_cuentas_servidor():
    """
    Obtiene el conteo total de cuentas en la base de datos del servidor
    """
    try:
        from app.database.database import get_user_data
        from app.utils.http_utils import post
        from app.utils.server_config import build_api_url
        import json
        
        # Obtener datos del usuario logueado
        user_data = get_user_data()
        if not user_data:
            print("❌ No se encontraron datos del usuario logueado")
            return 0
        
        user_id = user_data.get('id')
        access_token = user_data.get('access_token')
        
        if not user_id or not access_token:
            print("❌ Faltan datos del usuario (ID o access_token)")
            return 0
        
        # Preparar datos para el servidor
        payload = {
            "access_token": access_token
        }
        
        # URL del servidor
        url = build_api_url(f"/api/accounts/count/{user_id}")
        
        # Headers
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Enviar petición al servidor
        response = post(url, body=payload, headers=headers)
        
        if response:
            try:
                response_data = response.json()
                account_count = response_data.get('account_count', 0)
                print(f"📊 Total de cuentas en servidor: {account_count}")
                return account_count
            except json.JSONDecodeError:
                print("❌ Error al procesar respuesta del servidor")
                return 0
        else:
            print("❌ Error al conectar con el servidor")
            return 0
            
    except Exception as e:
        print(f"❌ Error al obtener conteo de cuentas: {e}")
        return 0


def _guardar_cuentas_en_servidor(filepath):
    """
    Guarda las cuentas creadas en la base de datos del servidor
    """
    print("📤 Iniciando guardado de cuentas en servidor...")
    
    try:
        from app.database.database import get_user_data
        from app.utils.http_utils import post
        from app.utils.server_config import build_api_url
        import json
        
        # Obtener datos del usuario logueado
        user_data = get_user_data()
        if not user_data:
            print("❌ Error: No se encontraron datos del usuario logueado")
            return False, "timeout", {"tiempo_transcurrido": 0, "timeout_seconds": 0}
        
        user_id = user_data.get('id')
        access_token = user_data.get('access_token')
        
        if not user_id or not access_token:
            print("❌ Error: Faltan datos del usuario (ID o access_token)")
            return False, "timeout", {"tiempo_transcurrido": 0, "timeout_seconds": 0}
        
        # Leer y parsear el archivo de cuentas
        accounts = _leer_cuentas_del_archivo(filepath)
        if not accounts:
            print("❌ Error: No se encontraron cuentas en el archivo")
            return False, "timeout", {"tiempo_transcurrido": 0, "timeout_seconds": 0}
        
        # Preparar datos para el servidor
        payload = {
            "access_token": access_token,
            "accounts": accounts
        }
        
        # URL del servidor
        url = build_api_url(f"/api/accounts/save/{user_id}")
        
        # Headers
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Enviar petición al servidor
        response = post(url, body=payload, headers=headers)
        
        if response:
            try:
                response_data = response.json()
                saved_count = response_data.get('saved_count', 0)
                duplicate_count = response_data.get('duplicate_count', 0)
                
                if saved_count > 0 or duplicate_count > 0:
                    print(f"✅ Cuentas guardadas en servidor: {saved_count} nuevas, {duplicate_count} duplicadas")
                else:
                    print("⚠️ No se guardaron cuentas en el servidor")
                return True
            except json.JSONDecodeError as json_err:
                print(f"❌ Error al procesar respuesta del servidor: {json_err}")
                return False, "numero_segundo_obstaculo", {"numero_count": 0, "obstaculo_count": 0}
        else:
            print("❌ Error: No se pudo conectar con el servidor")
            return False, "timeout", {"tiempo_transcurrido": 0, "timeout_seconds": 0}
            
    except Exception as e:
        print(f"❌ Error inesperado al guardar cuentas: {str(e)}")
        return False


def _guardar_cuentas_fallidas_en_servidor(cuentas_fallidas):
    """
    Guarda las cuentas fallidas en la base de datos del servidor
    """
    try:
        from app.database.database import get_user_data
        from app.utils.http_utils import post
        from app.utils.server_config import build_api_url
        import json
        
        if not cuentas_fallidas:
            print("📝 No hay cuentas fallidas para guardar")
            return True
        
        # Obtener datos del usuario logueado
        user_data = get_user_data()
        if not user_data:
            print("❌ No se encontraron datos del usuario logueado")
            return False, "timeout", {"tiempo_transcurrido": 0, "timeout_seconds": 0}
        
        user_id = user_data.get('id')
        access_token = user_data.get('access_token')
        
        if not user_id or not access_token:
            print("❌ Faltan datos del usuario (ID o access_token)")
            return False, "timeout", {"tiempo_transcurrido": 0, "timeout_seconds": 0}
        
        # Extraer solo los emails de las cuentas fallidas
        emails_fallidos = [cuenta['email'] for cuenta in cuentas_fallidas]
        
        # Preparar datos para el servidor (formato correcto)
        payload = {
            "access_token": access_token,
            "emails": emails_fallidos
        }
        
        # URL del servidor para emails fallidos
        url = build_api_url(f"/api/emails/save/{user_id}")
        
        # Headers
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Enviar petición al servidor
        response = post(url, body=payload, headers=headers)
        
        if response:
            try:
                response_data = response.json()
                saved_count = response_data.get('saved_count', 0)
                total_processed = response_data.get('total_processed', 0)
                
                # Si el servidor no devuelve saved_count, usar el número de emails enviados
                if saved_count == 0 and len(emails_fallidos) > 0:
                    saved_count = len(emails_fallidos)
                
                print(f"💾 Emails fallidos guardados en servidor: {saved_count}")
                return True
            except json.JSONDecodeError:
                print("❌ Error al procesar respuesta del servidor")
                return False, "numero_segundo_obstaculo", {"numero_count": 0, "obstaculo_count": 0}
        else:
            print("❌ Error al conectar con el servidor")
            return False, "timeout", {"tiempo_transcurrido": 0, "timeout_seconds": 0}
            
    except Exception as e:
        print(f"❌ Error al guardar emails fallidos en servidor: {e}")
        return False


def _leer_cuentas_del_archivo(filepath):
    """
    Lee las cuentas del archivo y las convierte al formato requerido por el servidor
    """
    try:
        accounts = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        
        # Buscar las líneas que contienen datos de cuentas (saltar encabezados)
        for i, line in enumerate(lines):
            line = line.strip()
            # Si la línea contiene tabs y no es un encabezado
            if '\t' in line and not line.startswith('CUENTAS') and not line.startswith('=') and not line.startswith('Total') and not line.startswith('Formato'):
                parts = line.split('\t')
                if len(parts) >= 4:  # user_agent, email, password, cookie
                    user_agent = parts[0].strip()
                    email = parts[1].strip()
                    password = parts[2].strip()
                    cookie = parts[3].strip()
                    
                    
                    # Agregar cuenta al array
                    account = {
                        "user_agent": user_agent,
                        "email": email,
                        "password": password,
                        "cookie": cookie
                    }
                    accounts.append(account)
        
        return accounts
        
    except Exception as e:
        print(f"❌ Error al leer archivo de cuentas: {e}")
        return []


def _validar_navegador_configurado(browser_id, browser_name, mostrar_detalles=False):
    """
    Valida que un navegador tenga la configuración necesaria (coordenadas e imágenes esenciales)
    
    Args:
        browser_id: ID del navegador
        browser_name: Nombre del navegador
        mostrar_detalles: Si es True, muestra detalles de la validación
    
    Returns:
        tuple: (bool, str) - (True si está configurado, motivo si no está configurado)
    """
    from app.database.database import get_bot_settings, get_creator_coordinates, get_creator_setting
    from app.creator.image_config import get_image_path
    from app.creator.user_agent_actions import COORD_APPLY, COORD_EXTENSION, COORD_OUTSIDE, COORD_PLACE
    from app.utils.path_utils import get_browser_images_path
    import os
    
    # Verificar coordenadas
    coordinates = get_creator_coordinates(browser_id)
    if not coordinates:
        motivo = "sin coordenadas configuradas"
        if mostrar_detalles:
            print(f"⚠️ Navegador '{browser_name}' ignorado: {motivo}")
        return False, motivo

    cfg = get_bot_settings() or {}
    if cfg.get("enable_creator_user_agent_actions"):
        for key, etiqueta in (
            (COORD_EXTENSION, "extensión"),
            (COORD_PLACE, "colocar"),
            (COORD_APPLY, "aplicar"),
            (COORD_OUTSIDE, "fuera"),
        ):
            if not (coordinates.get(key) or "").strip():
                motivo = f"falta coordenada user agent ({etiqueta}); desactiva el checkbox o configura Creator"
                if mostrar_detalles:
                    print(f"⚠️ Navegador '{browser_name}' ignorado: {motivo}")
                return False, motivo
    else:
        st = get_creator_setting(browser_id)
        if not st or not (st.get("user_agent") or "").strip():
            motivo = "falta user agent en la configuración del navegador"
            if mostrar_detalles:
                print(f"⚠️ Navegador '{browser_name}' ignorado: {motivo}")
            return False, motivo

    # Verificar que exista la carpeta de imágenes del navegador
    images_dir = get_browser_images_path(browser_name)
    if not os.path.exists(images_dir):
        motivo = "carpeta de imágenes no existe"
        if mostrar_detalles:
            print(f"⚠️ Navegador '{browser_name}' ignorado: {motivo}")
        return False, motivo
    
    # Verificar al menos algunas imágenes esenciales
    imagenes_esenciales = [
        "brave_image",
        "imagen_de_verificacion_de_exito_carga_linkedin",
        "imagen_de_creacion_de_cuenta_con_exito_logo_linkedin"
    ]
    
    imagenes_encontradas = 0
    for imagen in imagenes_esenciales:
        if get_image_path(imagen, browser_name=browser_name):
            imagenes_encontradas += 1
    
    # Requerir al menos 2 imágenes esenciales
    if imagenes_encontradas < 2:
        motivo = f"faltan imágenes esenciales (encontradas: {imagenes_encontradas}/{len(imagenes_esenciales)})"
        if mostrar_detalles:
            print(f"⚠️ Navegador '{browser_name}' ignorado: {motivo}")
        return False, motivo
    
    return True, None


def _filtrar_navegadores_configurados(active_browsers):
    """
    Filtra los navegadores activos para incluir solo los que tienen configuración completa
    
    Args:
        active_browsers: Lista de navegadores activos
    
    Returns:
        tuple: (list, list) - (navegadores configurados, navegadores ignorados con motivos)
    """
    navegadores_configurados = []
    navegadores_ignorados = []
    
    for browser in active_browsers:
        es_valido, motivo = _validar_navegador_configurado(browser['id'], browser['name'], mostrar_detalles=False)
        if es_valido:
            navegadores_configurados.append(browser)
        else:
            navegadores_ignorados.append({
                'browser': browser,
                'motivo': motivo
            })
    
    return navegadores_configurados, navegadores_ignorados


def _mostrar_error_navegadores_sin_configuracion(active_browsers_originales):
    """
    Muestra un messagebox de error cuando no hay navegadores con configuración completa
    
    Args:
        active_browsers_originales: Lista original de navegadores activos (antes del filtro)
    """
    import tkinter as tk
    from tkinter import messagebox
    
    # Crear ventana temporal para el messagebox
    root = tk.Tk()
    root.withdraw()  # Ocultar ventana principal
    
    # Construir mensaje detallado
    mensaje = "❌ No hay navegadores con configuración completa.\n\n"
    mensaje += "El bot requiere que al menos un navegador activo tenga:\n"
    mensaje += "• Coordenadas configuradas; user agent en ajustes del navegador (o extensión UA si está activada en opciones)\n"
    mensaje += "• Carpeta de imágenes creada\n"
    mensaje += "• Al menos 2 imágenes esenciales cargadas\n\n"
    
    if active_browsers_originales:
        mensaje += f"Navegadores activos encontrados ({len(active_browsers_originales)}):\n"
        for browser in active_browsers_originales:
            mensaje += f"  - {browser['name']}\n"
        mensaje += "\nPor favor, configura al menos un navegador antes de continuar."
    else:
        mensaje += "No hay navegadores activos.\n\nPor favor, activa y configura al menos un navegador."
    
    messagebox.showerror(
        "Error de Configuración",
        mensaje
    )
    
    root.destroy()


PROXY_ROTATION_INTERVAL_SEC = 60.0


def _maybe_run_proxy_rotation_tras_cuenta(browser_id: int, clock_ref: dict) -> None:
    """
    Si rotación proxy está habilitada para el navegador y pasaron PROXY_ROTATION_INTERVAL_SEC
    desde la última ejecución (o intento), ejecuta el flujo de proxy_rotation_actions.
    Solo debe llamarse cuando terminó procesar_email_individual_con_detalle (no en medio de una cuenta).
    """
    import time
    from app.database.database import get_creator_setting

    st = get_creator_setting(browser_id) or {}
    if not st.get("proxy_rotation_enabled"):
        return
    now = time.monotonic()
    if now - clock_ref["last"] < PROXY_ROTATION_INTERVAL_SEC:
        return
    try:
        from app.creator.proxy_rotation_actions import run_proxy_rotation_flow

        print(f"🔄 Rotación de proxy (cada {int(PROXY_ROTATION_INTERVAL_SEC)} s, tras cuenta completada)…")
        ok = run_proxy_rotation_flow(browser_id)
        if not ok:
            print("⚠️ Rotación proxy no completada; revisa coordenadas y enlace en la app.")
    except Exception as e:
        print(f"⚠️ Error en rotación proxy: {e}")
    finally:
        clock_ref["last"] = time.monotonic()


def _run_proxy_rotation_al_inicio_si_corresponde(active_browsers, clock_ref) -> None:
    """
    Al arrancar el creator: si la rotación proxy está habilitada para el navegador
    de configuración principal (mismo criterio que la ventana principal), ejecuta
    una vez run_proxy_rotation_flow y actualiza el reloj para que el siguiente
    disparo periódico sea 60 s después de terminar esta secuencia.
    """
    import time
    from app.database.database import get_creator_setting, get_default_browser

    ids_active = {b["id"] for b in active_browsers}
    db = get_default_browser()
    bid = db["id"] if db and db["id"] in ids_active else active_browsers[0]["id"]
    st = get_creator_setting(bid) or {}
    if not st.get("proxy_rotation_enabled"):
        return
    try:
        from app.creator.proxy_rotation_actions import run_proxy_rotation_flow

        print("🔄 Rotación de proxy al inicio del proceso…")
        run_proxy_rotation_flow(bid)
    except Exception as e:
        print(f"⚠️ Error en rotación proxy al inicio: {e}")
    finally:
        clock_ref["last"] = time.monotonic()


def _ejecutar_proceso_creator_con_objetivo(objetivo_cuentas, es_ciclo=False, ciclo_minutes=None, active_browsers=None, browser_index_start=0, domain_index_start=0):
    """
    Ejecuta el proceso de creación de cuentas con un objetivo específico
    Rota entre navegadores activos y dominios
    """
    from app.database.database import (
        get_creator_coordinates, get_all_available_creator_emails_for_objective,
        update_creator_email_progress, fetch_and_append_emails_for_cycle, get_creator_setting, get_active_browsers
    )
    import time
    import tkinter as tk
    from tkinter import messagebox
    
    print(f"🎯 Objetivo: {objetivo_cuentas} cuentas")
    
    # Obtener navegadores activos si no se proporcionaron
    if not active_browsers:
        active_browsers = get_active_browsers()
        if not active_browsers:
            print("❌ No hay navegadores activos")
            return 0, 0
    
    # Guardar lista original para el mensaje de error
    active_browsers_originales = active_browsers.copy()
    
    # Filtrar navegadores con configuración completa
    active_browsers, navegadores_ignorados = _filtrar_navegadores_configurados(active_browsers)
    
    # Mostrar resumen de navegadores ignorados si los hay
    if navegadores_ignorados:
        print("\n" + "="*60)
        print("⚠️  RESUMEN DE NAVEGADORES IGNORADOS")
        print("="*60)
        for item in navegadores_ignorados:
            browser = item['browser']
            motivo = item['motivo']
            print(f"   ❌ {browser['name']} (ID: {browser['id']}) - {motivo}")
        print("="*60 + "\n")
    
    if not active_browsers:
        print("❌ No hay navegadores con configuración completa para procesar")
        _mostrar_error_navegadores_sin_configuracion(active_browsers_originales)
        return 0, 0
    
    # Obtener configuración del primer navegador
    settings = get_creator_setting(active_browsers[0]['id'])
    if not settings:
        print("❌ Sin configuración del navegador")
        return 0, browser_index_start, domain_index_start
    
    is33mail = settings.get('is33mail', True)
    random_domains = settings.get('random_domains', False)
    domain = settings.get('domain', '')
    
    filepath = _inicializar_archivo_salida(objetivo_cuentas)
    if not filepath:
        return 0, browser_index_start, domain_index_start
    
    cuentas_creadas = 0
    emails_procesados = []  # Lista para trackear todos los emails procesados
    intento = 1
    from datetime import datetime
    tiempo_inicio_proceso = datetime.now()

    # Rotación proxy: intervalo en tiempo monotónico (solo tras terminar cada cuenta)
    proxy_rotation_clock = {"last": time.monotonic()}
    _run_proxy_rotation_al_inicio_si_corresponde(active_browsers, proxy_rotation_clock)

    # Índice para rotar entre navegadores (usar el índice inicial pasado como parámetro)
    browser_index = browser_index_start
    
    # Dominios desde BD o generados al vuelo (sin 33mail)
    if random_domains or not is33mail:
        from app.database.database import get_all_domains
        from app.creator.computer_actions import apply_domain_fill, generate_random_email_domain
        import random
        
        active_domains = None
        if not random_domains:
            active_domains = get_all_domains(active_only=True)
            if not active_domains:
                print("❌ No hay dominios configurados. Configura al menos un dominio en 'Gestión de Navegadores'.")
                return 0, browser_index_start, domain_index_start
        
        fill_global = bool(settings.get('fill_domain'))
        user_random_tlds = settings.get('random_tld_list') or []
        
        while cuentas_creadas < objetivo_cuentas and intento <= 10:
            # Verificar si se debe detener el bot
            from app.auth.auth import bot_running
            if not bot_running:
                print("🛑 Señal de detención recibida. Deteniendo creator...")
                # Cerrar navegador antes de detenerse
                current_browser = active_browsers[browser_index] if active_browsers else None
                if current_browser:
                    browser_id = current_browser['id']
                    browser_name = current_browser.get('name', 'navegador')
                    coordinates = get_creator_coordinates(browser_id)
                    if coordinates:
                        close_window_coords = coordinates.get("close_window")
                        if close_window_coords:
                            from app.creator.computer_actions import click_coordinates
                            print(f"🔄 Cerrando navegador {browser_name}...")
                            click_coordinates(close_window_coords)
                            time.sleep(1)
                return cuentas_creadas, browser_index, 0
            
            print(f"📧 Intento {intento} - {cuentas_creadas}/{objetivo_cuentas}")
            
            # Generar dominios seleccionando aleatoriamente entre los disponibles
            cuentas_restantes = objetivo_cuentas - cuentas_creadas
            email_ids = []
            for i in range(cuentas_restantes):
                if random_domains:
                    if user_random_tlds:
                        # Incluir `intento` para rotar TLD entre reintentos (antes i=0 repetía siempre el primero)
                        tld_pick = user_random_tlds[
                            (intento - 1 + cuentas_creadas + i) % len(user_random_tlds)
                        ]
                        domain_base = generate_random_email_domain(tld=tld_pick)
                    else:
                        domain_base = generate_random_email_domain()
                    filled_domain = apply_domain_fill(domain_base, fill_global)
                    email_ids.append(filled_domain)
                    print(f"📧 Dominio aleatorio para cuenta {cuentas_creadas + i + 1}: {filled_domain}")
                else:
                    domain_data = random.choice(active_domains)
                    domain_base = domain_data['domain']
                    fill_domain = domain_data['fill_domain']
                    filled_domain = apply_domain_fill(domain_base, fill_domain)
                    email_ids.append(filled_domain)
                    print(f"📧 Dominio seleccionado aleatoriamente para cuenta {cuentas_creadas + i + 1}: {domain_base}")
            
            # Procesar emails
            for i, email_id in enumerate(email_ids, 1):
                # Verificar si se debe detener el bot
                if not bot_running:
                    print("🛑 Señal de detención recibida. Deteniendo creator...")
                    # Cerrar navegador antes de detenerse
                    current_browser = active_browsers[browser_index] if active_browsers else None
                    if current_browser:
                        browser_id = current_browser['id']
                        browser_name = current_browser.get('name', 'navegador')
                        coordinates = get_creator_coordinates(browser_id)
                        if coordinates:
                            close_window_coords = coordinates.get("close_window")
                            if close_window_coords:
                                from app.creator.computer_actions import click_coordinates
                                print(f"🔄 Cerrando navegador {browser_name}...")
                                click_coordinates(close_window_coords)
                                time.sleep(1)
                    return cuentas_creadas, browser_index, 0
                
                if cuentas_creadas >= objetivo_cuentas:
                    break
                
                # Seleccionar navegador activo (rotación)
                current_browser = active_browsers[browser_index]
                browser_id = current_browser['id']
                browser_name = current_browser['name']
                
                print("#########################################################")
                print(f"🌐 Usando navegador: {browser_name} (ID: {browser_id})")
                _ejecutar_modo_avion()
                print(f"📧 {cuentas_creadas + 1}/{objetivo_cuentas}")
                
                # Obtener coordenadas del navegador actual
                coordinates = get_creator_coordinates(browser_id)
                if not coordinates:
                    print(f"❌ Sin coordenadas para navegador {browser_name}")
                    # Rotar al siguiente navegador
                    browser_index = (browser_index + 1) % len(active_browsers)
                    continue
                
                # En modo domain, email_id es el email directamente
                current_email = email_id
                
                exito, motivo_fallo, detalles = procesar_email_individual_con_detalle(
                    email_id, coordinates, filepath, cuentas_creadas + 1, objetivo_cuentas,
                    browser_id=browser_id, browser_name=browser_name
                )
                
                # Trackear el resultado del procesamiento
                email_resultado = {
                    "email_id": email_id,
                    "email": current_email,
                    "exito": exito,
                    "motivo_fallo": motivo_fallo,
                    "detalles": detalles,
                    "contador": cuentas_creadas + 1,
                    "intento": intento,
                    "browser_name": browser_name
                }
                emails_procesados.append(email_resultado)
                
                if exito:
                    cuentas_creadas += 1
                    print(f"✅ Cuenta {cuentas_creadas} (Navegador: {browser_name})")
                elif motivo_fallo == "linkedin_error":
                    print(f"⚠️ Error de carga de LinkedIn - continuando con siguiente email (Navegador: {browser_name})")
                else:
                    print(f"❌ Falló - {motivo_fallo} (Navegador: {browser_name})")
                
                _maybe_run_proxy_rotation_tras_cuenta(browser_id, proxy_rotation_clock)

                # Rotar al siguiente navegador para el próximo email
                browser_index = (browser_index + 1) % len(active_browsers)
                
                if i < len(email_ids):
                    time.sleep(1)
            
            intento += 1
    else:
        # Modo normal con 33mail
        while cuentas_creadas < objetivo_cuentas and intento <= 10:
            # Verificar si se debe detener el bot
            from app.auth.auth import bot_running
            if not bot_running:
                print("🛑 Señal de detención recibida. Deteniendo creator...")
                # Cerrar navegador antes de detenerse
                current_browser = active_browsers[browser_index] if active_browsers else None
                if current_browser:
                    browser_id = current_browser['id']
                    browser_name = current_browser.get('name', 'navegador')
                    coordinates = get_creator_coordinates(browser_id)
                    if coordinates:
                        close_window_coords = coordinates.get("close_window")
                        if close_window_coords:
                            from app.creator.computer_actions import click_coordinates
                            print(f"🔄 Cerrando navegador {browser_name}...")
                            click_coordinates(close_window_coords)
                            time.sleep(1)
                return cuentas_creadas, browser_index, 0
            
            print(f"📧 Intento {intento} - {cuentas_creadas}/{objetivo_cuentas}")
            
            # Obtener emails disponibles
            email_ids = get_all_available_creator_emails_for_objective()
            
            # Si no hay emails, solicitar más
            if not email_ids:
                faltantes = objetivo_cuentas - cuentas_creadas
                print(f"📭 Solicitando {faltantes} emails...")
                resultado = fetch_and_append_emails_for_cycle(faltantes)
                
                if resultado == "NO_EMAILS_AVAILABLE":
                    print("📭 No hay más emails disponibles en el servidor")
                    # Mostrar messagebox y detener el bot
                    root = tk.Tk()
                    root.withdraw()  # Ocultar ventana principal
                    messagebox.showwarning(
                        "Sin Emails Disponibles", 
                        "Te quedaste sin emails en la base de datos.\n\nEl bot se detendrá."
                    )
                    root.destroy()
                    break
                elif not resultado:
                    print("❌ Error al obtener emails")
                    break
                    
                email_ids = get_all_available_creator_emails_for_objective()
                if not email_ids:
                    break
        
            # Procesar emails
            for i, email_id in enumerate(email_ids, 1):
                # Verificar si se debe detener el bot
                if not bot_running:
                    print("🛑 Señal de detención recibida. Deteniendo creator...")
                    # Cerrar navegador antes de detenerse
                    current_browser = active_browsers[browser_index] if active_browsers else None
                    if current_browser:
                        browser_id = current_browser['id']
                        browser_name = current_browser.get('name', 'navegador')
                        coordinates = get_creator_coordinates(browser_id)
                        if coordinates:
                            close_window_coords = coordinates.get("close_window")
                            if close_window_coords:
                                from app.creator.computer_actions import click_coordinates
                                print(f"🔄 Cerrando navegador {browser_name}...")
                                click_coordinates(close_window_coords)
                                time.sleep(1)
                    return cuentas_creadas, browser_index, 0
                
                if cuentas_creadas >= objetivo_cuentas:
                    break
                
                # Seleccionar navegador activo (rotación)
                current_browser = active_browsers[browser_index]
                browser_id = current_browser['id']
                browser_name = current_browser['name']
                
                print("#########################################################")
                print(f"🌐 Usando navegador: {browser_name} (ID: {browser_id})")
                _ejecutar_modo_avion()
                print(f"📧 {cuentas_creadas + 1}/{objetivo_cuentas}")
                
                # Obtener coordenadas del navegador actual
                coordinates = get_creator_coordinates(browser_id)
                if not coordinates:
                    print(f"❌ Sin coordenadas para navegador {browser_name}")
                    # Rotar al siguiente navegador
                    browser_index = (browser_index + 1) % len(active_browsers)
                    continue
                
                # Obtener email antes de procesarlo
                from app.database.database import get_creator_email_by_id
                current_email = get_creator_email_by_id(email_id)
                
                exito, motivo_fallo, detalles = procesar_email_individual_con_detalle(
                    email_id, coordinates, filepath, cuentas_creadas + 1, objetivo_cuentas,
                    browser_id=browser_id, browser_name=browser_name
                )
                
                # Trackear el resultado del procesamiento
                email_resultado = {
                    "email_id": email_id,
                    "email": current_email if current_email else f"email_id_{email_id}",
                    "exito": exito,
                    "motivo_fallo": motivo_fallo,
                    "detalles": detalles,
                    "contador": cuentas_creadas + 1,
                    "intento": intento,
                    "browser_name": browser_name
                }
                emails_procesados.append(email_resultado)
                
                if exito:
                    cuentas_creadas += 1
                    print(f"✅ Cuenta {cuentas_creadas} (Navegador: {browser_name})")
                else:
                    print(f"❌ Falló - {motivo_fallo} (Navegador: {browser_name})")
                
                update_creator_email_progress(email_id, cuentas_creadas)

                _maybe_run_proxy_rotation_tras_cuenta(browser_id, proxy_rotation_clock)
                
                # Rotar al siguiente navegador para el próximo email
                browser_index = (browser_index + 1) % len(active_browsers)
                
                if i < len(email_ids):
                    time.sleep(1)
            
            intento += 1
    
    print(f"🎉 Completado: {cuentas_creadas}/{objetivo_cuentas}")
    _actualizar_encabezado_con_exitos(filepath, objetivo_cuentas, cuentas_creadas)
    
    # Obtener browser_id del primer navegador activo para funciones auxiliares
    first_browser_id = active_browsers[0]['id'] if active_browsers else None
    
    # Determinar emails realmente fallidos (no usados exitosamente)
    cuentas_realmente_fallidas = _determinar_emails_realmente_fallidos(emails_procesados, browser_id=first_browser_id)
    
    # Guardar solo emails realmente fallidos en el servidor
    if cuentas_realmente_fallidas:
        print(f"💾 Guardando {len(cuentas_realmente_fallidas)} emails realmente fallidos en el servidor...")
        print("📧 EMAILS REALMENTE FALLIDOS:")
        for i, cuenta in enumerate(cuentas_realmente_fallidas, 1):
            print(f"  {i}. {cuenta['email']} - {cuenta['motivo_fallo']}")
        _guardar_cuentas_fallidas_en_servidor(cuentas_realmente_fallidas)
    else:
        print("✅ No hay emails realmente fallidos para reportar")
    
    # Guardar cuentas en servidor (INDEPENDIENTE del email)
    if cuentas_creadas > 0:
        _guardar_cuentas_en_servidor(filepath)
    
    # Enviar correo de informe (opcional)
    _enviar_archivo_por_correo(filepath, objetivo_cuentas, cuentas_creadas, cuentas_realmente_fallidas, es_ciclo, ciclo_minutes, tiempo_inicio_proceso, browser_id=first_browser_id)
    
    # Retornar tanto las cuentas creadas como el índice del navegador actual para continuar la rotación
    # El dominio ahora se selecciona aleatoriamente, no necesitamos mantener el índice
    return cuentas_creadas, browser_index, 0  # domain_index ya no se usa, pero mantenemos compatibilidad


def _ejecutar_creator_en_ciclo(active_browsers):
    """
    Ejecuta el proceso de creación de cuentas en ciclo continuo
    Rota entre navegadores activos
    """
    from app.database.database import (
        get_creator_setting, fetch_and_save_emails_for_cycle, 
        delete_all_creator_emails, reset_creator_email_progress, get_active_browsers
    )
    import time
    
    # Obtener navegadores activos si no se proporcionaron
    if not active_browsers:
        active_browsers = get_active_browsers()
        if not active_browsers:
            print("❌ No hay navegadores activos")
            return
    
    # Guardar lista original para el mensaje de error
    active_browsers_originales = active_browsers.copy()
    
    # Filtrar navegadores con configuración completa
    active_browsers, navegadores_ignorados = _filtrar_navegadores_configurados(active_browsers)
    
    # Mostrar resumen de navegadores ignorados si los hay
    if navegadores_ignorados:
        print("\n" + "="*60)
        print("⚠️  RESUMEN DE NAVEGADORES IGNORADOS")
        print("="*60)
        for item in navegadores_ignorados:
            browser = item['browser']
            motivo = item['motivo']
            print(f"   ❌ {browser['name']} (ID: {browser['id']}) - {motivo}")
        print("="*60 + "\n")
    
    if not active_browsers:
        print("❌ No hay navegadores con configuración completa para procesar")
        _mostrar_error_navegadores_sin_configuracion(active_browsers_originales)
        return
    
    # Obtener configuración del primer navegador
    settings = get_creator_setting(active_browsers[0]['id'])
    if not settings:
        print("❌ Sin configuración del navegador")
        return
    
    # Obtener configuración global de tiempo
    from app.database.database import get_global_time_config
    global_time_config = get_global_time_config()
    cycle_minutes = global_time_config.get('cycle_time_minutes', 60)
    accounts_per_cycle = global_time_config.get('accounts_per_cycle', 1)
    is33mail = settings.get('is33mail', True)
    random_domains = settings.get('random_domains', False)
    domain = settings.get('domain', '')
    
    if cycle_minutes == 0:
        print(f"🔄 Ciclo: 0min (continuo) - Objetivo: {accounts_per_cycle} cuentas por ciclo")
    else:
        print(f"🔄 Ciclo: {cycle_minutes}min - Objetivo: {accounts_per_cycle} cuentas")
    print("💡 Ctrl+C para detener")
    
    ciclo = 1
    # Mantener el índice del navegador entre ciclos para continuar la rotación
    browser_index = 0
    # El dominio ahora se selecciona aleatoriamente, no necesitamos mantener el índice
    domain_index = 0  # Mantenido por compatibilidad pero no se usa
    
    try:
        while True:
            # Verificar si se debe detener el bot
            from app.auth.auth import bot_running
            if not bot_running:
                print("🛑 Señal de detención recibida. Deteniendo creator...")
                # Cerrar navegador antes de detenerse
                current_browser = active_browsers[browser_index] if active_browsers else None
                if current_browser:
                    browser_id = current_browser['id']
                    browser_name = current_browser.get('name', 'navegador')
                    from app.database.database import get_creator_coordinates
                    coordinates = get_creator_coordinates(browser_id)
                    if coordinates:
                        close_window_coords = coordinates.get("close_window")
                        if close_window_coords:
                            from app.creator.computer_actions import click_coordinates
                            print(f"🔄 Cerrando navegador {browser_name}...")
                            click_coordinates(close_window_coords)
                            time.sleep(1)
                break
            
            print("########################################################")
            print(f"\n🔄 CICLO #{ciclo}")
            
            # Obtener browser_id del primer navegador activo para notificación
            first_browser_id = active_browsers[0]['id'] if active_browsers else None
            
            # Enviar notificación de inicio de ciclo
            _enviar_notificacion_inicio_ciclo(ciclo, accounts_per_cycle, cycle_minutes, browser_id=first_browser_id)
            
            # Solo 33mail pide emails al servidor; dominios propios o aleatorios no
            if is33mail and not random_domains:
                # Limpiar emails del ciclo anterior
                if ciclo > 1:
                    print("🧹 Limpiando emails...")
                    delete_all_creator_emails()
                    reset_creator_email_progress()
                
                # Obtener emails del servidor
                print(f"🌐 Obteniendo {accounts_per_cycle} emails...")
                resultado = fetch_and_save_emails_for_cycle(accounts_per_cycle)
                
                if resultado == "NO_EMAILS_AVAILABLE":
                    print("📭 No hay más emails disponibles en el servidor")
                    # Mostrar messagebox y detener el bot
                    import tkinter as tk
                    from tkinter import messagebox
                    root = tk.Tk()
                    root.withdraw()
                    messagebox.showwarning(
                        "Sin Emails Disponibles", 
                        "Te quedaste sin emails en la base de datos.\n\nEl bot se detendrá."
                    )
                    root.destroy()
                    break
                elif not resultado:
                    print(f"❌ Error - Esperando {cycle_minutes}min...")
                    # Sleep interrumpible para poder detener el bot durante la espera
                    sleep_seconds = cycle_minutes * 60
                    sleep_interval = 1
                    slept = 0
                    while slept < sleep_seconds:
                        from app.auth.auth import bot_running
                        if not bot_running:
                            print("🛑 Señal de detención recibida durante la espera. Deteniendo creator...")
                            # Cerrar navegador antes de detenerse
                            current_browser = active_browsers[browser_index] if active_browsers else None
                            if current_browser:
                                browser_id = current_browser['id']
                                browser_name = current_browser.get('name', 'navegador')
                                from app.database.database import get_creator_coordinates
                                coordinates = get_creator_coordinates(browser_id)
                                if coordinates:
                                    close_window_coords = coordinates.get("close_window")
                                    if close_window_coords:
                                        from app.creator.computer_actions import click_coordinates
                                        print(f"🔄 Cerrando navegador {browser_name}...")
                                        click_coordinates(close_window_coords)
                                        time.sleep(1)
                            break
                        time.sleep(sleep_interval)
                        slept += sleep_interval
                    
                    if not bot_running:
                        break
                    
                    ciclo += 1
                    continue
            else:
                if random_domains:
                    print("🌐 Usando dominios aleatorios generados localmente (email_words.json + TLDs)")
                else:
                    from app.database.database import get_all_domains
                    active_domains = get_all_domains(active_only=True)
                    if not active_domains:
                        print("❌ No hay dominios configurados. Configura al menos un dominio en 'Gestión de Navegadores'.")
                        break
                    print(f"🌐 Usando {len(active_domains)} dominio(s) con rotación automática")
            
            # Ejecutar proceso de creación, pasando el índice del navegador actual
            # El dominio se selecciona aleatoriamente, no necesitamos pasar domain_index
            resultado = _ejecutar_proceso_creator_con_objetivo(
                accounts_per_cycle, es_ciclo=True, ciclo_minutes=cycle_minutes, 
                active_browsers=active_browsers, browser_index_start=browser_index, domain_index_start=0
            )
            cuentas_creadas, browser_index, _ = resultado
            
            if cuentas_creadas >= accounts_per_cycle:
                print(f"🎉 Objetivo completado: {cuentas_creadas}/{accounts_per_cycle}")
            else:
                print(f"⚠️ Objetivo parcial: {cuentas_creadas}/{accounts_per_cycle}")
            
            # Si cycle_minutes es 0, continuar inmediatamente sin espera
            if cycle_minutes == 0:
                print(f"⚡ Ciclo de 0 minutos - continuando inmediatamente con siguiente ciclo...")
            else:
                print(f"⏰ Esperando {cycle_minutes}min...")
                # Sleep interrumpible para poder detener el bot durante la espera
                sleep_seconds = cycle_minutes * 60
                sleep_interval = 1  # Verificar cada segundo
                slept = 0
                while slept < sleep_seconds:
                    # Verificar si se debe detener el bot
                    from app.auth.auth import bot_running
                    if not bot_running:
                        print("🛑 Señal de detención recibida durante la espera. Deteniendo creator...")
                        # Cerrar navegador antes de detenerse
                        current_browser = active_browsers[browser_index] if active_browsers else None
                        if current_browser:
                            browser_id = current_browser['id']
                            browser_name = current_browser.get('name', 'navegador')
                            from app.database.database import get_creator_coordinates
                            coordinates = get_creator_coordinates(browser_id)
                            if coordinates:
                                close_window_coords = coordinates.get("close_window")
                                if close_window_coords:
                                    from app.creator.computer_actions import click_coordinates
                                    print(f"🔄 Cerrando navegador {browser_name}...")
                                    click_coordinates(close_window_coords)
                                    time.sleep(1)
                        break
                    time.sleep(sleep_interval)
                    slept += sleep_interval
            
            # Si se detuvo durante el sleep, salir del loop
            from app.auth.auth import bot_running
            if not bot_running:
                break
            
            ciclo += 1
            
    except KeyboardInterrupt:
        print(f"\n🛑 Detenido - {ciclo - 1} ciclos completados")
        # Cerrar navegador antes de detenerse
        current_browser = active_browsers[browser_index] if active_browsers else None
        if current_browser:
            browser_id = current_browser['id']
            browser_name = current_browser.get('name', 'navegador')
            from app.database.database import get_creator_coordinates
            coordinates = get_creator_coordinates(browser_id)
            if coordinates:
                close_window_coords = coordinates.get("close_window")
                if close_window_coords:
                    from app.creator.computer_actions import click_coordinates
                    print(f"🔄 Cerrando navegador {browser_name}...")
                    click_coordinates(close_window_coords)
                    time.sleep(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        # Cerrar navegador antes de detenerse
        current_browser = active_browsers[browser_index] if active_browsers else None
        if current_browser:
            browser_id = current_browser['id']
            browser_name = current_browser.get('name', 'navegador')
            from app.database.database import get_creator_coordinates
            coordinates = get_creator_coordinates(browser_id)
            if coordinates:
                close_window_coords = coordinates.get("close_window")
                if close_window_coords:
                    from app.creator.computer_actions import click_coordinates
                    print(f"🔄 Cerrando navegador {browser_name}...")
                    click_coordinates(close_window_coords)
                    time.sleep(1)