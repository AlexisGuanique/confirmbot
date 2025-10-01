import requests
from typing import Dict, Any, Optional, Union


def http_request(method: str, url: str, body: Optional[Union[Dict, str]] = None, 
                headers: Optional[Dict] = None, params: Optional[Dict] = None, 
                timeout: int = 30) -> Optional[requests.Response]:
    """
    Función simple para realizar peticiones HTTP/HTTPS.
    
    Args:
        method (str): Método HTTP (GET, POST, PUT, DELETE, PATCH, etc.)
        url (str): URL de destino
        body (dict or str, optional): Cuerpo de la petición (para POST, PUT, PATCH)
        headers (dict, optional): Headers HTTP adicionales
        params (dict, optional): Parámetros de consulta (para GET)
        timeout (int): Tiempo límite en segundos (default: 30)
        
    Returns:
        requests.Response or None: Respuesta de la petición o None si hay error
    """
    try:

        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Combinar headers por defecto con los proporcionados
        if headers:
            default_headers.update(headers)
        
        # Preparar argumentos según el método
        kwargs = {
            'headers': default_headers,
            'timeout': timeout
        }
        
        # Agregar parámetros para GET
        if params and method.upper() == 'GET':
            kwargs['params'] = params
        
        # Agregar body para métodos que lo requieren
        if body and method.upper() in ['POST', 'PUT', 'PATCH']:
            if isinstance(body, dict):
                kwargs['json'] = body
            else:
                kwargs['data'] = body
        
        # Realizar la petición
        response = requests.request(method.upper(), url, **kwargs)
        response.raise_for_status()
        
        return response
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error en petición {method.upper()} {url}: {e}")
        return None
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return None


def get(url: str, params: Optional[Dict] = None, headers: Optional[Dict] = None, 
        timeout: int = 30) -> Optional[requests.Response]:
    """Función de conveniencia para peticiones GET."""
    return http_request('GET', url, params=params, headers=headers, timeout=timeout)


def post(url: str, body: Optional[Union[Dict, str]] = None, headers: Optional[Dict] = None, 
         timeout: int = 30) -> Optional[requests.Response]:
    """Función de conveniencia para peticiones POST."""
    return http_request('POST', url, body=body, headers=headers, timeout=timeout)


def put(url: str, body: Optional[Union[Dict, str]] = None, headers: Optional[Dict] = None, 
        timeout: int = 30) -> Optional[requests.Response]:
    """Función de conveniencia para peticiones PUT."""
    return http_request('PUT', url, body=body, headers=headers, timeout=timeout)


def delete(url: str, headers: Optional[Dict] = None, timeout: int = 30) -> Optional[requests.Response]:
    """Función de conveniencia para peticiones DELETE."""
    return http_request('DELETE', url, headers=headers, timeout=timeout)


def download_file(url: str, file_path: str, headers: Optional[Dict] = None) -> bool:

    try:
        response = get(url, headers=headers)
        if response:
            with open(file_path, 'wb') as f:
                f.write(response.content)
            print(f"✅ Archivo descargado: {file_path}")
            return True
        return False
    except Exception as e:
        print(f"❌ Error al descargar {url}: {e}")
        return False


# Ejemplo de uso
if __name__ == "__main__":
    # Ejemplos de uso
    print("🔍 Ejemplo GET...")
    response = get("https://httpbin.org/get", params={"test": "value"})
    if response:
        print(f"Status: {response.status_code}")
    
    print("\n📤 Ejemplo POST...")
    data = {"message": "Hola desde ConfirmaBot"}
    response = post("https://httpbin.org/post", body=data)
    if response:
        print(f"Status: {response.status_code}")
    
    print("\n📥 Ejemplo descarga...")
    success = download_file("https://httpbin.org/image/png", "test.png")
    print(f"Descarga exitosa: {success}")
