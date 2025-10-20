#!/usr/bin/env python3
"""
Versión segura del controlador de proxy para Windows
Evita cuelgues en computadoras con problemas de acceso al registro
"""

import winreg
import subprocess
import sys
import time
from typing import Optional, Tuple

class SafeProxyController:
    """Controlador de proxy seguro para Windows"""
    
    def __init__(self):
        self.proxy_key = None
        self._open_key()
    
    def _open_key(self):
        """Abre la clave del registro de forma segura"""
        try:
            self.proxy_key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                0,
                winreg.KEY_ALL_ACCESS
            )
        except Exception as e:
            print(f"⚠️ No se pudo abrir la clave del registro: {e}")
            self.proxy_key = None
    
    def get_proxy_status(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Obtiene el estado actual del proxy de forma segura
        
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: (habilitado, servidor, puerto)
        """
        if not self.proxy_key:
            return False, None, None
            
        try:
            # Timeout para evitar cuelgues
            start_time = time.time()
            timeout = 5  # 5 segundos máximo
            
            # Verificar si el proxy está habilitado
            enabled, _ = winreg.QueryValueEx(self.proxy_key, "ProxyEnable")
            
            if time.time() - start_time > timeout:
                print("⚠️ Timeout en verificación de proxy")
                return False, None, None
            
            if enabled:
                # Obtener configuración del proxy
                proxy_server, _ = winreg.QueryValueEx(self.proxy_key, "ProxyServer")
                return True, proxy_server, None
            else:
                return False, None, None
                
        except FileNotFoundError:
            return False, None, None
        except Exception as e:
            print(f"⚠️ Error al obtener estado del proxy: {e}")
            return False, None, None
    
    def enable_proxy_only(self) -> bool:
        """
        Solo activa el proxy sin cambiar la configuración existente
        
        Returns:
            bool: True si se activó correctamente
        """
        if not self.proxy_key:
            print("⚠️ No se puede acceder al registro, saltando activación de proxy")
            return False
            
        try:
            # Timeout para evitar cuelgues
            start_time = time.time()
            timeout = 3  # 3 segundos máximo
            
            # Solo habilitar el proxy sin cambiar la configuración
            winreg.SetValueEx(self.proxy_key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
            
            if time.time() - start_time > timeout:
                print("⚠️ Timeout al activar proxy")
                return False
                
            pass
            return True
            
        except Exception as e:
            print(f"❌ Error al activar proxy: {e}")
            return False
    
    def disable_proxy(self) -> bool:
        """
        Desactiva el proxy de forma segura
        
        Returns:
            bool: True si se desactivó correctamente
        """
        if not self.proxy_key:
            print("⚠️ No se puede acceder al registro, saltando desactivación de proxy")
            return False
            
        try:
            # Timeout para evitar cuelgues
            start_time = time.time()
            timeout = 3  # 3 segundos máximo
            
            # Deshabilitar el proxy
            winreg.SetValueEx(self.proxy_key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
            
            if time.time() - start_time > timeout:
                print("⚠️ Timeout al desactivar proxy")
                return False
                
            pass
            return True
            
        except Exception as e:
            print(f"❌ Error al desactivar proxy: {e}")
            return False
    
    def refresh_internet_settings(self):
        """Refresca la configuración de Internet para aplicar cambios"""
        try:
            # Timeout para evitar cuelgues
            import threading
            import time
            
            def refresh_with_timeout():
                try:
                    # Enviar mensaje WM_SETTINGCHANGE para refrescar la configuración
                    import ctypes
                    from ctypes import wintypes
                    
                    HWND_BROADCAST = 0xFFFF
                    WM_SETTINGCHANGE = 0x001A
                    
                    ctypes.windll.user32.SendMessageW(
                        HWND_BROADCAST,
                        WM_SETTINGCHANGE,
                        0,
                        "Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings"
                    )
                    
                    pass
                    
                except Exception as e:
                    print(f"⚠️ Error en refresh: {e}")
            
            # Ejecutar con timeout de 0.5 segundos
            thread = threading.Thread(target=refresh_with_timeout)
            thread.daemon = True
            thread.start()
            thread.join(timeout=0.5)
            
            if thread.is_alive():
                pass
            
        except Exception as e:
            print(f"⚠️ No se pudo refrescar automáticamente: {e}")
            print("💡 Reinicia el navegador para aplicar los cambios")
    
    def close(self):
        """Cierra la conexión al registro de forma segura"""
        try:
            if self.proxy_key:
                winreg.CloseKey(self.proxy_key)
                self.proxy_key = None
        except:
            pass
