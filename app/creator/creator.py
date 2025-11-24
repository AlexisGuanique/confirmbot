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


def observador_unificado(coordinates, email, password, filepath, browser_id=None, browser_name=None):
    """
    Observador unificado que detecta números, captchas y éxito en la creación de cuentas
    """
    from app.creator.computer_actions import click_coordinates, wait_for_creator_image, get_clipboard_content
    from app.database.database import get_creator_setting
    import time
    import json
    
    print("👁️ Observando número, captcha rojo, captcha blanco o éxito...")
    time.sleep(5)
    
    # Configuración del observador
    start_time = time.time()
    timeout_seconds = 150
    
    # Estado del observador
    estado = ObservadorEstado()
    
    while True:
        # Resetear flag de captcha bueno procesado en este ciclo
        estado.captcha_bueno_procesado_en_ciclo = False
        
        # Verificar timeout
        if _verificar_timeout(start_time, timeout_seconds, coordinates):
            return False, "timeout", {"tiempo_transcurrido": time.time() - start_time, "timeout_seconds": timeout_seconds}
        
        # Verificar captcha bueno PRIMERO (solo desactiva proxy)
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
            # Si es un fallo de cookie, cerrar ventana antes de retornar
            if isinstance(exito_result, tuple) and len(exito_result) >= 2:
                if exito_result[0] is False and exito_result[1] in ["cookie_vacia", "cookie_invalida", "cookie_duplicada", "max_intentos_cookie"]:
                    print("❌ Fallo en obtención de cookie - cerrando ventana")
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
        
        # Pausa entre ciclos
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
    time.sleep(5)
    
    # Configuración del observador
    start_time = time.time()
    timeout_seconds = 150
    
    # Estado del observador
    estado = ObservadorEstado()
    
    while True:
        # Resetear flag de captcha bueno procesado en este ciclo
        estado.captcha_bueno_procesado_en_ciclo = False
        
        # Verificar timeout
        if _verificar_timeout(start_time, timeout_seconds, coordinates):
            return False, "timeout", {"tiempo_transcurrido": time.time() - start_time, "timeout_seconds": timeout_seconds}
        
        # Verificar captcha bueno PRIMERO (solo desactiva proxy)
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
            # Si es un fallo de cookie, cerrar ventana antes de retornar
            if isinstance(exito_result, tuple) and len(exito_result) >= 2:
                if exito_result[0] is False and exito_result[1] in ["cookie_vacia", "cookie_invalida", "cookie_duplicada", "max_intentos_cookie"]:
                    print("❌ Fallo en obtención de cookie - cerrando ventana")
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
        
        # Pausa entre ciclos
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


def _verificar_timeout(start_time, timeout_seconds, coordinates):
    """Verifica si ha pasado el timeout y cierra la ventana si es necesario"""
    from app.creator.computer_actions import click_coordinates
    import time
    
    elapsed_time = time.time() - start_time
    if elapsed_time > timeout_seconds:
        print("⏰ Timeout de 150 segundos - no se encontraron imágenes, cerrando ventana")
        _desactivar_proxy()
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
    
    # Desactivar proxy inmediatamente al detectar número
    _desactivar_proxy()
    
    if estado.obstaculo_count >= 2:
        print("🔄 Segundo obstáculo detectado - cerrando ventana directamente")
        _desactivar_proxy()
        close_window_coords = coordinates.get("close_window")
        if close_window_coords:
            click_coordinates(close_window_coords)
            time.sleep(1)
        return False  # Terminar el proceso
    
    close_number_coords = coordinates.get("close_number_click")
    if close_number_coords:
        click_coordinates(close_number_coords)
        time.sleep(1)
        
        continue2_coords = coordinates.get("continue_button2_click")
        if continue2_coords:
            # Reactivar proxy antes de hacer clic en continue_button2_click
            click_coordinates(continue2_coords)
            _activar_proxy()
            time.sleep(2)
    
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
    
    # Desactivar proxy inmediatamente al detectar captcha error
    _desactivar_proxy()
    
    if estado.obstaculo_count >= 2:
        print("🔄 Segundo obstáculo detectado - cerrando ventana directamente")
        _desactivar_proxy()
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
            # Reactivar proxy antes de hacer clic en continue_button2_click
            click_coordinates(continue2_coords)
            _activar_proxy()
            time.sleep(2)
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
    
    # Desactivar proxy inmediatamente al detectar formato nuevo
    _desactivar_proxy()
    
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
    
    # Desactivar proxy inmediatamente al detectar captcha rojo
    _desactivar_proxy()
    
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
                # Reactivar proxy antes de hacer clic en continue_button2_click
                click_coordinates(continue2_coords)
                _activar_proxy()
                time.sleep(2)
        
        return True  # Continuar el proceso


def _procesar_captcha_imposible(coordinates, estado, browser_name=None):
    """Procesa la detección de captcha imposible (incluye captcha_imposible, captcha_imposible_2 y captcha_imposible_3)"""
    from app.creator.computer_actions import click_coordinates, wait_for_spinner
    import time
    
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
    
    # Desactivar proxy inmediatamente al detectar captcha imposible
    _desactivar_proxy()
    
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
            _desactivar_proxy()
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
    
    close_captcha_coords = coordinates.get("close_captcha_click")
    if close_captcha_coords:
        click_coordinates(close_captcha_coords)
        time.sleep(1)
        
        continue2_coords = coordinates.get("continue_button2_click")
        if continue2_coords:
            # Reactivar proxy antes de hacer clic en continue_button2_click
            
            click_coordinates(continue2_coords)
            _activar_proxy()
            time.sleep(2)
    
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
    _desactivar_proxy()
    
    return _obtener_y_guardar_cookie(coordinates, email, password, filepath, browser_id=browser_id, browser_name=browser_name)


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
    _desactivar_proxy()
    
    return _obtener_y_guardar_cookie_con_detalle(coordinates, email, password, filepath, exito_image_name_found, browser_id=browser_id, browser_name=browser_name)


def _procesar_captcha_bueno(coordinates, estado, browser_name=None):
    """Procesa la detección de captcha bueno - solo desactiva el proxy (máximo 2 veces)"""
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
    
    # Solo desactivar el proxy UNA VEZ por detección (no por cada variante)
    _desactivar_proxy()
    
    # Esperar un momento para que la imagen desaparezca de pantalla
    time.sleep(2)
    
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
        
        # Desactivar proxy
        _desactivar_proxy()
        
        # Cerrar captcha blanco
        close_captcha_coords = coordinates.get("close_captcha_click")
        if close_captcha_coords:
            click_coordinates(close_captcha_coords)
            time.sleep(1)
            
            # Hacer clic en continue
            continue2_coords = coordinates.get("continue_button2_click")
            if continue2_coords:

                click_coordinates(continue2_coords)                
                # Reactivar proxy después de hacer clic en continue
                _activar_proxy()
                time.sleep(2)
        
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
        _desactivar_proxy()
        close_window_coords = coordinates.get("close_window")
        if close_window_coords:
            click_coordinates(close_window_coords)
            time.sleep(1)
        return False  # Terminar el proceso
    
    return True


def _obtener_y_guardar_cookie(coordinates, email, password, filepath, browser_id=None, browser_name=None):
    """Obtiene y guarda la cookie de la cuenta creada"""
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
        
        # Guardar cookie
        print("✅ Cookie única guardada")
        
        if browser_id:
            creator_settings = get_creator_setting(browser_id)
        else:
            creator_settings = None
        if not creator_settings or not creator_settings.get('user_agent'):
            return False, "user_agent_no_encontrado", {}
        
        user_agent = creator_settings.get('user_agent')
        contenido = f"{user_agent}\t{email}\t{password}\t{cookie}"
        
        try:
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(contenido + "\n")
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
    """Obtiene y guarda la cookie con información detallada"""
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
        
        # Guardar cookie
        print("✅ Cookie única guardada")
        
        if browser_id:
            creator_settings = get_creator_setting(browser_id)
        else:
            creator_settings = None
        if not creator_settings or not creator_settings.get('user_agent'):
            return False, "user_agent_no_encontrado", {}
        
        user_agent = creator_settings.get('user_agent')
        contenido = f"{user_agent}\t{email}\t{password}\t{cookie}"
        
        
        try:
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(contenido + "\n")
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
    
    # Paso 2: Click en LinkedIn fav
    if not _click_linkedin_fav(coordinates):
        return False
    
    # Paso 3: Verificar carga de LinkedIn
    if not _verificar_carga_linkedin(coordinates, browser_name=browser_name):
        print("❌ LinkedIn no cargó correctamente - cerrando ventana")
        _desactivar_proxy()
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
    
    # Paso 6: Cerrar ventana si se creó exitosamente
    if cuenta_creada:
        _cerrar_ventana(coordinates)
        return True
    else:
        return False


def procesar_email_individual_con_detalle(email_id, coordinates, filepath, contador, total, browser_id=None, browser_name=None):
    """
    Procesa un email individual en el proceso de creación de cuenta LinkedIn con información detallada
    Retorna: (exito: bool, motivo_fallo: str, detalles: dict)
    
    Args:
        email_id: Puede ser un ID de email (int) o un email directamente (str) cuando is33mail es false
        browser_id: ID del navegador activo
        browser_name: Nombre del navegador activo
    """
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
    
    # Paso 1: Click en el navegador
    if not _click_brave(coordinates, browser_name=browser_name):
        return False, "error_click_brave", {}
    
    # Paso 2: Click en LinkedIn fav
    if not _click_linkedin_fav(coordinates):
        return False, "error_click_linkedin_fav", {}
    
    # Paso 3: Verificar carga de LinkedIn
    if not _verificar_carga_linkedin(coordinates, browser_name=browser_name):
        print("❌ LinkedIn no cargó correctamente - cerrando ventana")
        _desactivar_proxy()
        _cerrar_ventana(coordinates)
        return False, "error_carga_linkedin", {}
    
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
    else:
        return False, motivo_fallo, detalles


def _click_brave(coordinates, browser_name=None):
    """Hace clic en el navegador con validación de imagen"""
    from app.creator.computer_actions import click_coordinates, wait_for_creator_image
    import time
    
    # Obtener nombre del navegador para mensajes
    nombre_navegador = browser_name if browser_name else "navegador"
    
    brave_coords = coordinates.get("brave_click")
    if not brave_coords:
        return False
    
    max_intentos = 3
    
    for intento in range(1, max_intentos + 1):
        # Hacer doble clic
        click_coordinates(brave_coords, double_click=True)
        time.sleep(2)
        
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


def _click_linkedin_fav(coordinates):
    """Hace clic en el favorito de LinkedIn"""
    from app.creator.computer_actions import click_coordinates
    import time
    
    linkedin_coords = coordinates.get("linkedin_fav_click")
    if not linkedin_coords:
        return False
    
    click_coordinates(linkedin_coords)
    time.sleep(3)
    
    # Verificar proxy error después de abrir LinkedIn
    _verificar_y_cerrar_proxy_error(coordinates)
    
    return True


def _verificar_carga_linkedin(coordinates=None, browser_name=None):
    """Verifica que LinkedIn haya cargado correctamente con matching 100% exacto - busca tres imágenes posibles"""
    from app.creator.computer_actions import find_creator_image, click_coordinates, wait_for_creator_image
    from app.database.database import get_creator_coordinates, get_default_browser
    import time
    
    # Lista de imágenes posibles para verificar carga de LinkedIn
    linkedin_verification_images = [
        "imagen_de_verificacion_de_exito_carga_linkedin",
        "imagen_de_verificacion_de_exito_carga_linkedin_2",
        "imagen_de_verificacion_de_exito_carga_linkedin_3"
    ]
    
    nombre_navegador = browser_name if browser_name else "navegador"
    print(f"🔍 Verificando carga de LinkedIn (Navegador: {nombre_navegador})")
    
    # Esperar un momento inicial para que LinkedIn cargue completamente
    time.sleep(3)
    
    max_attempts_per_cycle = 6
    max_reintentos = 3
    delay_between_attempts = 1.5  # Aumentar delay entre intentos
    # Reducir confianza ligeramente para permitir pequeñas variaciones (resolución, antialiasing, etc.)
    confidence = 0.90  # 90% de precisión - permite pequeñas variaciones pero mantiene alta precisión
    
    # Obtener coordenadas necesarias para reinicio si no se proporcionaron
    if not coordinates:
        # Si no hay browser_name, obtener navegador por defecto
        if not browser_name:
            default_browser = get_default_browser()
            if default_browser:
                browser_id = default_browser['id']
            else:
                browser_id = None
        else:
            browser_id = None  # No podemos obtener browser_id solo con nombre sin consultar DB
        
        if browser_id:
            coordinates = get_creator_coordinates(browser_id)
        else:
            coordinates = None
        if not coordinates:
            print("❌ No se pudieron obtener las coordenadas")
            return False
    
    for reintento in range(1, max_reintentos + 1):
        # Buscar imágenes en cada ciclo hasta encontrar una o llegar al límite
        for attempt in range(1, max_attempts_per_cycle + 1):
            # Intentar buscar cada imagen en este ciclo
            for image_name in linkedin_verification_images:
                # Esperar un poco antes de buscar para dar tiempo a que cargue la página
                if attempt == 1:
                    time.sleep(1)
                
                verification_image = find_creator_image(image_name, confidence=confidence, browser_name=browser_name)
                if verification_image:
                    print(f"✅ ¡Imagen encontrada en el intento {attempt}! Usando: {image_name}")
                    return True
            
            # Si no se encontró ninguna imagen en este ciclo, esperar antes del siguiente
            if attempt < max_attempts_per_cycle:
                time.sleep(delay_between_attempts)
        
        # Si llegamos aquí, no se encontró ninguna imagen después de max_attempts_per_cycle intentos
        # Solo mostrar mensaje si no es el último reintento para reducir ruido en consola
        if reintento < max_reintentos:
            print(f"⚠️ No se encontró imagen después de {max_attempts_per_cycle} intentos")
        
        # Si no es el último reintento, reiniciar el proceso
        if reintento < max_reintentos:
            print(f"🔄 Reiniciando proceso (reintento {reintento}/{max_reintentos})...")
            
            # 1. Cerrar ventana
            close_window_coords = coordinates.get("close_window")
            if close_window_coords:
                print(f"🔄 Cerrando ventana...")
                click_coordinates(close_window_coords)
                time.sleep(1)
            
            # 2. Doble clic en el navegador con validación
            # Obtener nombre del navegador para mensajes
            nombre_navegador = browser_name if browser_name else "navegador"
            
            brave_coords = coordinates.get("brave_click")
            if brave_coords:
                print(f"🔄 Haciendo doble clic en {nombre_navegador}...")
                click_coordinates(brave_coords, double_click=True)
                time.sleep(2)
                
                # Validar que la imagen del navegador NO apareció (significa que el navegador se abrió correctamente)
                browser_image_found = wait_for_creator_image("brave_image", max_attempts=2, delay_between_attempts=0.5, silent=True, browser_name=browser_name)
                if browser_image_found:
                    print(f"⚠️ {nombre_navegador} todavía en pantalla de inicio, reintentando clic...")
                    click_coordinates(brave_coords, double_click=True)
                    time.sleep(2)
                    browser_image_found = wait_for_creator_image("brave_image", max_attempts=2, delay_between_attempts=0.5, silent=True, browser_name=browser_name)
                    if browser_image_found:
                        print(f"❌ No se pudo abrir {nombre_navegador} correctamente")
                        return False
                print(f"✅ {nombre_navegador} validado - clic realizado correctamente")
            
            # 3. Clic en LinkedIn fav
            linkedin_coords = coordinates.get("linkedin_fav_click")
            if linkedin_coords:
                print(f"🔄 Haciendo clic en LinkedIn fav...")
                click_coordinates(linkedin_coords)
                # Esperar más tiempo para que LinkedIn cargue completamente
                time.sleep(5)
            
            # 4. Continuar buscando imágenes en el siguiente reintento
            print(f"🔄 Continuando búsqueda de imágenes...")
            time.sleep(1)
        else:
            # Último reintento completado sin éxito
            print(f"❌ No se encontró ninguna imagen de verificación de LinkedIn después de {max_reintentos} reintentos")
            return False
    
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
    import time
    import pyperclip
    
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
        
        if not is33mail:
            # Usar formato específico para dominio personalizado
            full_email = generate_email_with_domain_format(email)
            print(f"📧 Email generado con formato personalizado: {full_email} (dominio: {email})")
        else:
            # Generar prefijo aleatorio y concatenar con el dominio (modo 33mail)
            prefix = generate_email_prefix()
            full_email = f"{prefix}{email}"
            print(f"📧 Email generado: {full_email} (dominio: {email})")
    else:
        # Si ya viene completo, usar tal como está
        full_email = email
        print(f"📧 Email completo recibido: {full_email}")
    
    # Escribir email completo con verificación
    if not _escribir_y_verificar_campo(full_email, "email"):
        return False, None
    
    # Verificar proxy error
    _verificar_y_cerrar_proxy_error(coordinates, browser_name=browser_name)
    
    # Ir al campo de contraseña
    press_key("tab")
    time.sleep(0.5)
    
    # Escribir contraseña aleatoria (sin verificación para mayor velocidad)
    password = generate_random_password()
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
        # Hacer clic en continue_button
        # print(f"🔄 Haciendo clic en continue_button (intento {intento_verificacion}/{max_intentos_verificacion})")
        click_coordinates(continue_coords)
        time.sleep(2)  # Esperar a que se procese el clic
        
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
            _desactivar_proxy()
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
    
    # Escribir nombre aleatorio con verificación
    random_name = generate_random_name()
    if not _escribir_y_verificar_campo(random_name, "nombre"):
        return False, None
    
    # Ir al campo de apellido
    press_key("tab")
    time.sleep(0.5)
    
    # Escribir apellido aleatorio con verificación
    random_lastname = generate_random_lastname()
    if not _escribir_y_verificar_campo(random_lastname, "apellido"):
        return False, None


    # Click en continue_button2_click (sin activar proxy prematuramente)
    continue2_coords = coordinates.get("continue_button2_click")
    if not continue2_coords:
        return False, None
    # Activar proxy después de hacer clic en continue_button2_click
    _activar_proxy()
    time.sleep(1)
    click_coordinates(continue2_coords)
    time.sleep(10)
    


    
    # Guardar password para uso posterior
    global _password_usado
    _password_usado = password
    return True, full_email


def _get_password_usado():
    """Obtiene el password usado en el formulario"""
    global _password_usado
    return _password_usado


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
        except Exception as e:
            pass
    else:
        print("❌ Modo avión no activado")
        time.sleep(2)


def _activar_proxy():
    """Activa el proxy si está habilitado en la configuración - VERSIÓN SEGURA"""
    import time
    from app.database.database import get_bot_settings
    from app.confirmabot.utils.proxy_tool_safe import SafeProxyController
    
    config = get_bot_settings()
    enable_proxy = config.get("enable_proxy", True)
    
    if enable_proxy:
        try:
            proxy_controller = SafeProxyController()
            try:
                # Solo activar el proxy sin verificaciones que puedan colgarse
                success = proxy_controller.enable_proxy_only()
                if success:
                    proxy_controller.refresh_internet_settings()
                    print("✅ Proxy activado")
                else:
                    print("⚠️ No se pudo activar proxy")
                    
            finally:
                proxy_controller.close()
        except Exception as e:
            print(f"❌ Error al activar proxy: {e}")
    else:
        pass


def _desactivar_proxy():
    """Desactiva el proxy si está habilitado en la configuración - VERSIÓN SEGURA"""
    import time
    from app.database.database import get_bot_settings
    from app.confirmabot.utils.proxy_tool_safe import SafeProxyController
    
    config = get_bot_settings()
    enable_proxy = config.get("enable_proxy", True)
    
    if enable_proxy:
        try:
            proxy_controller = SafeProxyController()
            try:
                success = proxy_controller.disable_proxy()
                if success:
                    proxy_controller.refresh_internet_settings()
                    print("✅ Proxy desactivado")
                else:
                    print("⚠️ No se pudo desactivar proxy")
                time.sleep(0.5)  # Esperar un momento para que el proxy se desactive
            finally:
                proxy_controller.close()
        except Exception as e:
            print(f"❌ Error al desactivar proxy: {e}")
    else:
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
    
    Args:
        browser_id: ID del navegador para obtener la configuración
    
    Returns:
        bool: True si debe continuar con el proceso, False si debe detenerse
    """
    from app.database.database import get_creator_setting, get_default_browser
    import time
    import datetime
    import pytz
    import re
    
    # Si no se proporciona browser_id, obtener el navegador por defecto
    if not browser_id:
        default_browser = get_default_browser()
        if default_browser:
            browser_id = default_browser['id']
    
    if browser_id:
        settings = get_creator_setting(browser_id)
    else:
        settings = None
    if not settings:
        print("⚡ No hay configuración de tiempo, ejecutando inmediatamente")
        return True  # No hay configuración, continuar inmediatamente
    
    # Solo verificar hora programada si el tipo de configuración es 'scheduled' o 'both'
    time_config_type = settings.get('time_config_type')
    if time_config_type not in ['scheduled', 'both']:
        print("⚡ Configuración de ciclo de tiempo, ejecutando inmediatamente")
        return True  # No es configuración programada, continuar inmediatamente
    
    # Verificar si hay hora programada configurada
    if not settings.get('scheduled_time') or not settings.get('timezone'):
        print("⚡ No hay hora programada configurada, ejecutando inmediatamente")
        return True  # No hay hora programada, continuar inmediatamente
    
    scheduled_time = settings.get('scheduled_time')
    timezone_str = settings.get('timezone')
    
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
    print("📧 Iniciando envío de correo de informe...")
    
    try:
        from app.confirmabot.hostinger_actions import send_email_with_file
        from app.database.database import get_creator_setting, get_all_emails, get_user_data, get_default_browser
        from app.utils.http_utils import post
        import os
        from datetime import datetime, timedelta
        import json
        
        # Verificar archivo
        if not os.path.exists(filepath):
            return False
        
        # Intentar obtener credenciales de correo (opcional)
        emails_data = get_all_emails()
        if not emails_data:
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
            return True  # No hay credenciales, omitir envío
        
        # Si no se proporciona browser_id, usar el navegador por defecto
        if not browser_id:
            default_browser = get_default_browser()
            if default_browser:
                browser_id = default_browser['id']
        
        # Obtener email de destino
        if browser_id:
            settings = get_creator_setting(browser_id)
        else:
            settings = None
        email_destino = settings.get('notification_email') if settings else None
        
        if not email_destino:
            return True  # No hay email de destino configurado, continuar
        
        # Obtener conteo total de cuentas en el servidor
        total_cuentas_servidor = _obtener_conteo_cuentas_servidor()
        
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
        
        # Enviar correo con archivo adjunto
        exito = send_email_with_file(
            email_address=email_address,
            password=email_password,
            to_email=email_destino,
            subject=asunto,
            body=cuerpo,
            attachment_path=archivo_estadisticas
        )
        
        # Eliminar archivo temporal después del envío
        if archivo_estadisticas and os.path.exists(archivo_estadisticas):
            try:
                os.remove(archivo_estadisticas)
            except Exception:
                pass  # Ignorar errores al eliminar
        
        if exito:
            print("✅ Correo enviado con éxito")
        else:
            print("❌ Error al enviar correo")
        
        return exito
            
    except Exception as e:
        print(f"❌ Error inesperado al enviar correo: {str(e)}")
        return False


    

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
        url = f"http://34.29.59.97/api/accounts/count/{user_id}"
        
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
        url = f"http://34.29.59.97/api/accounts/save/{user_id}"
        
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
        url = f"http://34.29.59.97/api/emails/save/{user_id}"
        
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
    from app.database.database import get_creator_coordinates
    from app.creator.image_config import get_image_path
    from app.utils.path_utils import get_browser_images_path
    import os
    
    # Verificar coordenadas
    coordinates = get_creator_coordinates(browser_id)
    if not coordinates:
        motivo = "sin coordenadas configuradas"
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
    mensaje += "• Coordenadas configuradas\n"
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


def execute_creator():
    """
    Función principal del creator que ejecuta todas las acciones
    Rota entre navegadores activos
    """
    from app.database.database import get_active_browsers, get_creator_setting
    import time
    
    global _password_usado
    _password_usado = ""
    
    # Obtener navegadores activos
    active_browsers = get_active_browsers()
    if not active_browsers:
        print("❌ No hay navegadores activos. Por favor activa al menos un navegador.")
        return
    
    print(f"🌐 Navegadores activos encontrados: {len(active_browsers)}")
    for browser in active_browsers:
        print(f"   - {browser['name']} (ID: {browser['id']})")
    
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
        print("❌ No hay navegadores activos con configuración completa. Por favor configura al menos un navegador.")
        _mostrar_error_navegadores_sin_configuracion(active_browsers_originales)
        return
    
    print(f"✅ Navegadores configurados válidos: {len(active_browsers)}")
    for browser in active_browsers:
        print(f"   ✓ {browser['name']} (ID: {browser['id']})")
    
    # Obtener configuración del primer navegador activo para determinar modo de ejecución
    # (todos los navegadores activos deberían tener la misma configuración de tiempo)
    settings = get_creator_setting(active_browsers[0]['id'])
    if not settings:
        print("❌ Sin configuración")
        return
    
    time_config_type = settings.get('time_config_type', 'manual')
    scheduled_time = settings.get('scheduled_time')
    cycle_time_minutes = settings.get('cycle_time_minutes', 60)
    
    has_scheduled = scheduled_time and scheduled_time.strip()
    # El ciclo se considera habilitado aunque los minutos sean 0
    has_cycle = settings.get('time_config_type') in ['cycle', 'both']
    
    # Determinar modo de ejecución
    if has_scheduled and has_cycle:
        print("🔄 Ciclo + Hora programada")
        if not _verificar_hora_programada(active_browsers[0]['id']):
            return
        _ejecutar_creator_en_ciclo(active_browsers)
    elif has_cycle:
        print("🔄 Solo ciclo")
        _ejecutar_creator_en_ciclo(active_browsers)
    elif has_scheduled:
        print("🕐 Solo hora programada")
        if not _verificar_hora_programada(active_browsers[0]['id']):
            return
        _ejecutar_proceso_creator(active_browsers)
    else:
        print("👤 Modo manual")
        _ejecutar_proceso_creator(active_browsers)


def _ejecutar_proceso_creator(active_browsers):
    """
    Ejecuta el proceso de creación de cuentas una sola vez
    Rota entre navegadores activos
    """
    from app.database.database import (
        get_creator_coordinates, get_all_available_creator_emails, get_next_creator_emails, 
        get_creator_setting, update_creator_email_progress, fetch_and_save_emails_for_cycle,
        reset_creator_email_progress
    )
    import time
    
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
        return False
    
    # Obtener configuración del primer navegador (todos deberían tener la misma configuración de tiempo)
    settings = get_creator_setting(active_browsers[0]['id'])
    time_config_type = settings.get('time_config_type', 'manual')
    is33mail = settings.get('is33mail', True)
    domain = settings.get('domain', '')
    
    # Si is33mail es false, usar domain directamente
    if not is33mail:
        if not domain:
            print("❌ Domain no configurado")
            return False
        
        # Preparar el dominio con @ al inicio si no lo tiene
        domain_email = domain if domain.startswith('@') else f"@{domain}"
        
        # Obtener cantidad de cuentas a crear
        if time_config_type in ['cycle', 'both']:
            accounts_per_cycle = settings.get('accounts_per_cycle', 1)
            email_ids = [domain_email] * accounts_per_cycle
            print(f"🔄 Procesando {accounts_per_cycle} cuentas usando domain: {domain_email}")
        else:
            accounts_to_create = settings.get('accounts_to_create', 1)
            email_ids = [domain_email] * accounts_to_create
            print(f"🔄 Procesando {accounts_to_create} cuentas usando domain: {domain_email}")
    else:
        # Obtener emails según configuración (modo normal con 33mail)
        if time_config_type in ['cycle', 'both']:
            accounts_per_cycle = settings.get('accounts_per_cycle', 1)
            email_ids = get_next_creator_emails(accounts_per_cycle)
            print(f"🔄 Procesando {accounts_per_cycle} cuentas")
        else:
            print("🌐 Obteniendo emails del servidor...")
            resultado = fetch_and_save_emails_for_cycle(100)
            
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
                return False, "timeout", {"tiempo_transcurrido": 0, "timeout_seconds": 0}
            elif not resultado:
                print("❌ Error al obtener emails")
                return False, "timeout", {"tiempo_transcurrido": 0, "timeout_seconds": 0}
                
            email_ids = get_all_available_creator_emails()
            print(f"🔄 Procesando {len(email_ids)} cuentas")
    
    if not email_ids:
        print("❌ Sin emails disponibles")
        if is33mail:
            reset_creator_email_progress()
        return False
    
    filepath = _inicializar_archivo_salida(len(email_ids))
    if not filepath:
        return
    
    # Procesar emails rotando entre navegadores activos
    emails_exitosos = 0
    emails_procesados = []  # Lista para trackear todos los emails procesados
    from datetime import datetime
    tiempo_inicio_proceso = datetime.now()
    
    # Índice para rotar entre navegadores
    browser_index = 0
    
    for i, email_id in enumerate(email_ids, 1):
        # Seleccionar navegador activo (rotación)
        current_browser = active_browsers[browser_index]
        browser_id = current_browser['id']
        browser_name = current_browser['name']
        
        print("#########################################################")
        print(f"🌐 Usando navegador: {browser_name} (ID: {browser_id})")
        _ejecutar_modo_avion()
        print(f"📧 {i}/{len(email_ids)}")
        
        # Obtener coordenadas del navegador actual
        coordinates = get_creator_coordinates(browser_id)
        if not coordinates:
            print(f"❌ Sin coordenadas para navegador {browser_name}")
            # Rotar al siguiente navegador
            browser_index = (browser_index + 1) % len(active_browsers)
            continue
        
        # Obtener email antes de procesarlo
        if is33mail:
            from app.database.database import get_creator_email_by_id
            current_email = get_creator_email_by_id(email_id)
        else:
            # En modo domain, email_id es el email directamente
            current_email = email_id
        
        exito, motivo_fallo, detalles = procesar_email_individual_con_detalle(
            email_id, coordinates, filepath, i, len(email_ids), 
            browser_id=browser_id, browser_name=browser_name
        )
        
        # Trackear el resultado del procesamiento
        email_resultado = {
            "email_id": email_id,
            "email": current_email if current_email else (email_id if isinstance(email_id, str) else f"email_id_{email_id}"),
            "exito": exito,
            "motivo_fallo": motivo_fallo,
            "detalles": detalles,
            "contador": i,
            "browser_name": browser_name
        }
        emails_procesados.append(email_resultado)
        
        if exito:
            emails_exitosos += 1
            print(f"✅ Cuenta {emails_exitosos} (Navegador: {browser_name})")
        else:
            print(f"❌ Falló - {motivo_fallo} (Navegador: {browser_name})")
        
        # Solo actualizar progreso si estamos usando 33mail
        if is33mail:
            update_creator_email_progress(email_id, emails_exitosos)
        
        # Rotar al siguiente navegador para el próximo email
        browser_index = (browser_index + 1) % len(active_browsers)
        
        if i < len(email_ids):
            time.sleep(1)
    
    print(f"🎉 Completado: {emails_exitosos}/{len(email_ids)}")
    _actualizar_encabezado_con_exitos(filepath, len(email_ids), emails_exitosos)
    
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
    if emails_exitosos > 0:
        _guardar_cuentas_en_servidor(filepath)
    
    # Enviar correo de informe (opcional)
    _enviar_archivo_por_correo(filepath, len(email_ids), emails_exitosos, cuentas_realmente_fallidas, False, None, tiempo_inicio_proceso, browser_id=first_browser_id)
    
    return True


def _ejecutar_proceso_creator_con_objetivo(objetivo_cuentas: int, es_ciclo: bool = False, ciclo_minutes: int = None, active_browsers=None) -> int:
    """
    Ejecuta el proceso de creación de cuentas con un objetivo específico
    Rota entre navegadores activos
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
            return 0
    
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
        return 0
    
    # Obtener configuración del primer navegador
    settings = get_creator_setting(active_browsers[0]['id'])
    is33mail = settings.get('is33mail', True)
    domain = settings.get('domain', '')
    
    filepath = _inicializar_archivo_salida(objetivo_cuentas)
    if not filepath:
        return 0
    
    cuentas_creadas = 0
    emails_procesados = []  # Lista para trackear todos los emails procesados
    intento = 1
    from datetime import datetime
    tiempo_inicio_proceso = datetime.now()
    
    # Índice para rotar entre navegadores
    browser_index = 0
    
    # Si is33mail es false, usar domain directamente
    if not is33mail:
        if not domain:
            print("❌ Domain no configurado")
            return 0
        
        # Preparar el dominio con @ al inicio si no lo tiene
        domain_email = domain if domain.startswith('@') else f"@{domain}"
        
        # Procesar directamente con el dominio
        while cuentas_creadas < objetivo_cuentas and intento <= 10:
            print(f"📧 Intento {intento} - {cuentas_creadas}/{objetivo_cuentas}")
            
            # Usar el dominio directamente
            email_ids = [domain_email] * (objetivo_cuentas - cuentas_creadas)
            
            # Procesar emails
            for i, email_id in enumerate(email_ids, 1):
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
                else:
                    print(f"❌ Falló - {motivo_fallo} (Navegador: {browser_name})")
                
                # Rotar al siguiente navegador para el próximo email
                browser_index = (browser_index + 1) % len(active_browsers)
                
                if i < len(email_ids):
                    time.sleep(1)
            
            intento += 1
    else:
        # Modo normal con 33mail
        while cuentas_creadas < objetivo_cuentas and intento <= 10:
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
    
    return cuentas_creadas


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
    cycle_minutes = settings.get('cycle_time_minutes', 60)
    accounts_per_cycle = settings.get('accounts_per_cycle', 1)
    is33mail = settings.get('is33mail', True)
    domain = settings.get('domain', '')
    
    print(f"🔄 Ciclo: {cycle_minutes}min - Objetivo: {accounts_per_cycle} cuentas")
    print("💡 Ctrl+C para detener")
    
    ciclo = 1
    
    try:
        while True:
            print("########################################################")
            print(f"\n🔄 CICLO #{ciclo}")
            
            # Obtener browser_id del primer navegador activo para notificación
            first_browser_id = active_browsers[0]['id'] if active_browsers else None
            
            # Enviar notificación de inicio de ciclo
            _enviar_notificacion_inicio_ciclo(ciclo, accounts_per_cycle, cycle_minutes, browser_id=first_browser_id)
            
            # Si is33mail es false, no solicitar emails del servidor
            if is33mail:
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
                    time.sleep(cycle_minutes * 60)
                    ciclo += 1
                    continue
            else:
                # Verificar que el dominio esté configurado
                if not domain:
                    print("❌ Domain no configurado")
                    break
                print(f"🌐 Usando domain: {domain}")
            
            # Ejecutar proceso de creación
            cuentas_creadas = _ejecutar_proceso_creator_con_objetivo(accounts_per_cycle, es_ciclo=True, ciclo_minutes=cycle_minutes, active_browsers=active_browsers)
            
            # Mostrar resultado
            if cuentas_creadas >= accounts_per_cycle:
                print(f"🎉 Objetivo completado: {cuentas_creadas}/{accounts_per_cycle}")
            else:
                print(f"⚠️ Objetivo parcial: {cuentas_creadas}/{accounts_per_cycle}")
            
            print(f"⏰ Esperando {cycle_minutes}min...")
            time.sleep(cycle_minutes * 60)
            ciclo += 1
            
    except KeyboardInterrupt:
        print(f"\n🛑 Detenido - {ciclo - 1} ciclos completados")
    except Exception as e:
        print(f"\n❌ Error: {e}")