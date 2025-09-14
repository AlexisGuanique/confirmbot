#!/usr/bin/env python3
"""
Script para controlar el proxy de Windows
Permite activar/desactivar el proxy del sistema
"""

import winreg
import subprocess
import sys
import time
from typing import Optional, Tuple

class ProxyController:
    """Controlador de proxy para Windows"""
    
    def __init__(self):
        self.proxy_key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
            0,
            winreg.KEY_ALL_ACCESS
        )
    
    def get_proxy_status(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Obtiene el estado actual del proxy
        
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: (habilitado, servidor, puerto)
        """
        try:
            # Verificar si el proxy está habilitado
            enabled, _ = winreg.QueryValueEx(self.proxy_key, "ProxyEnable")
            
            if enabled:
                # Obtener configuración del proxy
                proxy_server, _ = winreg.QueryValueEx(self.proxy_key, "ProxyServer")
                return True, proxy_server, None
            else:
                return False, None, None
                
        except FileNotFoundError:
            return False, None, None
        except Exception as e:
            print(f"❌ Error al obtener estado del proxy: {e}")
            return False, None, None
    
    def set_proxy(self, proxy_server: str, proxy_port: int = 8080) -> bool:
        """
        Configura y activa el proxy
        
        Args:
            proxy_server: Dirección del servidor proxy (ej: "127.0.0.1")
            proxy_port: Puerto del proxy (default: 8080)
            
        Returns:
            bool: True si se configuró correctamente
        """
        try:
            # Configurar el servidor proxy
            proxy_string = f"{proxy_server}:{proxy_port}"
            winreg.SetValueEx(self.proxy_key, "ProxyServer", 0, winreg.REG_SZ, proxy_string)
            
            # Habilitar el proxy
            winreg.SetValueEx(self.proxy_key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
            
            # Configurar para usar proxy en todas las conexiones
            winreg.SetValueEx(self.proxy_key, "ProxyOverride", 0, winreg.REG_SZ, "")
            
            print(f"✅ Proxy configurado: {proxy_string}")
            return True
            
        except Exception as e:
            print(f"❌ Error al configurar proxy: {e}")
            return False
    
    def enable_proxy_only(self) -> bool:
        """
        Solo activa el proxy sin cambiar la configuración existente
        
        Returns:
            bool: True si se activó correctamente
        """
        try:
            # Solo habilitar el proxy sin cambiar la configuración
            winreg.SetValueEx(self.proxy_key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
            print("✅ Proxy activado (configuración preservada)")
            return True
            
        except Exception as e:
            print(f"❌ Error al activar proxy: {e}")
            return False
    
    def disable_proxy(self) -> bool:
        """
        Desactiva el proxy
        
        Returns:
            bool: True si se desactivó correctamente
        """
        try:
            # Deshabilitar el proxy
            winreg.SetValueEx(self.proxy_key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
            
            print("✅ Proxy desactivado")
            return True
            
        except Exception as e:
            print(f"❌ Error al desactivar proxy: {e}")
            return False
    
    def refresh_internet_settings(self):
        """Refresca la configuración de Internet para aplicar cambios"""
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
            
            print("🔄 Configuración de Internet refrescada")
            
        except Exception as e:
            print(f"⚠️ No se pudo refrescar automáticamente: {e}")
            print("💡 Reinicia el navegador para aplicar los cambios")
    
    def close(self):
        """Cierra la conexión al registro"""
        try:
            winreg.CloseKey(self.proxy_key)
        except:
            pass

def show_current_status():
    """Muestra el estado actual del proxy"""
    controller = ProxyController()
    
    try:
        enabled, server, port = controller.get_proxy_status()
        
        print("📊 Estado actual del proxy:")
        print("=" * 40)
        
        if enabled:
            print(f"🟢 Proxy: ACTIVADO")
            print(f"🔗 Servidor: {server}")
        else:
            print(f"🔴 Proxy: DESACTIVADO")
        
        print("=" * 40)
        
    finally:
        controller.close()

def toggle_proxy():
    """Alterna el estado del proxy"""
    controller = ProxyController()
    
    try:
        enabled, server, port = controller.get_proxy_status()
        
        if enabled:
            print("🔄 Desactivando proxy...")
            if controller.disable_proxy():
                controller.refresh_internet_settings()
                print("✅ Proxy desactivado exitosamente")
            else:
                print("❌ Error al desactivar proxy")
        else:
            print("🔄 Activando proxy...")
            # Configurar proxy local por defecto
            if controller.set_proxy("127.0.0.1", 8080):
                controller.refresh_internet_settings()
                print("✅ Proxy activado exitosamente")
            else:
                print("❌ Error al activar proxy")
                
    finally:
        controller.close()

def set_custom_proxy():
    """Permite configurar un proxy personalizado"""
    controller = ProxyController()
    
    try:
        print("🔧 Configuración de proxy personalizado")
        print("=" * 40)
        
        server = input("Ingresa la dirección del servidor proxy (ej: 127.0.0.1): ").strip()
        if not server:
            print("❌ Dirección del servidor requerida")
            return
        
        try:
            port = int(input("Ingresa el puerto (default: 8080): ").strip() or "8080")
        except ValueError:
            print("❌ Puerto inválido, usando 8080")
            port = 8080
        
        print(f"🔄 Configurando proxy: {server}:{port}")
        
        if controller.set_proxy(server, port):
            controller.refresh_internet_settings()
            print("✅ Proxy personalizado configurado exitosamente")
        else:
            print("❌ Error al configurar proxy personalizado")
            
    finally:
        controller.close()

def main():
    """Función principal con menú interactivo"""
    print("🌐 Controlador de Proxy de Windows")
    print("=" * 40)
    
    while True:
        print("\n📋 Opciones disponibles:")
        print("1. Ver estado actual del proxy")
        print("2. Activar/Desactivar proxy (toggle)")
        print("3. Configurar proxy personalizado")
        print("4. Solo activar proxy")
        print("5. Solo desactivar proxy")
        print("0. Salir")
        
        try:
            choice = input("\nSelecciona una opción (0-5): ").strip()
            
            if choice == "0":
                print("👋 ¡Hasta luego!")
                break
            elif choice == "1":
                show_current_status()
            elif choice == "2":
                toggle_proxy()
            elif choice == "3":
                set_custom_proxy()
            elif choice == "4":
                controller = ProxyController()
                try:
                    if controller.set_proxy("127.0.0.1", 8080):
                        controller.refresh_internet_settings()
                        print("✅ Proxy activado")
                    else:
                        print("❌ Error al activar proxy")
                finally:
                    controller.close()
            elif choice == "5":
                controller = ProxyController()
                try:
                    if controller.disable_proxy():
                        controller.refresh_internet_settings()
                        print("✅ Proxy desactivado")
                    else:
                        print("❌ Error al desactivar proxy")
                finally:
                    controller.close()
            else:
                print("❌ Opción inválida")
                
        except KeyboardInterrupt:
            print("\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    main()
