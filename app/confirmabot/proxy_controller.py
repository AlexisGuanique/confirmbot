import subprocess
import json
import re
import time

class ProxyController:

    
    def __init__(self):
        print("🔍 Inicializando controlador de proxy...")
    
    def get_proxy_status(self):
        """
        Obtiene el estado actual del proxy usando múltiples métodos
        """
        print("🔍 Detectando estado del proxy...")
        
        # Método 1: Usar netsh winhttp
        try:
            result = subprocess.run(
                ["netsh", "winhttp", "show", "proxy"], 
                capture_output=True, 
                text=True, 
                shell=True
            )
            
            if result.returncode == 0:
                output = result.stdout
                print(f"📡 Salida de netsh: {output}")
                
                # Buscar patrones en la salida
                if "Direct access (no proxy server)" in output:
                    return {"enabled": False, "server": "No configurado", "method": "netsh"}
                elif "Proxy Server(s):" in output:
                    # Extraer información del proxy
                    proxy_match = re.search(r"Proxy Server\(s\):\s*(.+)", output)
                    if proxy_match:
                        proxy_info = proxy_match.group(1).strip()
                        return {"enabled": True, "server": proxy_info, "method": "netsh"}
            
        except Exception as e:
            print(f"⚠️ Error con netsh: {e}")
        
        # Método 2: Usar PowerShell
        try:
            ps_script = """
            $proxy = Get-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings' -Name ProxyEnable, ProxyServer -ErrorAction SilentlyContinue
            if ($proxy.ProxyEnable -eq 1) {
                Write-Output "ENABLED:$($proxy.ProxyServer)"
            } else {
                Write-Output "DISABLED:$($proxy.ProxyServer)"
            }
            """
            
            result = subprocess.run(
                ["powershell", "-Command", ps_script], 
                capture_output=True, 
                text=True, 
                shell=True
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                print(f"📡 Salida de PowerShell: {output}")
                
                if output.startswith("ENABLED:"):
                    server = output.replace("ENABLED:", "")
                    return {"enabled": True, "server": server, "method": "powershell"}
                elif output.startswith("DISABLED:"):
                    server = output.replace("DISABLED:", "")
                    return {"enabled": False, "server": server, "method": "powershell"}
                    
        except Exception as e:
            print(f"⚠️ Error con PowerShell: {e}")
        
        # Método 3: Usar reg query
        try:
            result = subprocess.run(
                ["reg", "query", "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings", "/v", "ProxyEnable"], 
                capture_output=True, 
                text=True, 
                shell=True
            )
            
            if result.returncode == 0:
                output = result.stdout
                print(f"📡 Salida de reg query: {output}")
                
                # Buscar el valor de ProxyEnable
                enable_match = re.search(r"ProxyEnable\s+REG_DWORD\s+0x(\d+)", output)
                if enable_match:
                    proxy_enable = int(enable_match.group(1), 16)
                    
                    # Obtener ProxyServer
                    server_result = subprocess.run(
                        ["reg", "query", "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings", "/v", "ProxyServer"], 
                        capture_output=True, 
                        text=True, 
                        shell=True
                    )
                    
                    if server_result.returncode == 0:
                        server_output = server_result.stdout
                        server_match = re.search(r"ProxyServer\s+REG_SZ\s+(.+)", server_output)
                        if server_match:
                            proxy_server = server_match.group(1).strip()
                            return {
                                "enabled": bool(proxy_enable), 
                                "server": proxy_server, 
                                "method": "reg query"
                            }
                        
        except Exception as e:
            print(f"⚠️ Error con reg query: {e}")
        
        # Si ningún método funcionó
        print("❌ No se pudo detectar el estado del proxy con ningún método")
        return {"enabled": False, "server": "Error de detección", "method": "ninguno"}
    
    def enable_proxy(self, proxy_address="gw.dataimpulse.com", proxy_port="823"):
        """
        Activa el proxy del sistema usando múltiples métodos
        """
        print(f"🔓 Activando proxy: {proxy_address}:{proxy_port}")
        
        # Método 1: Usar reg add
        try:
            # Configurar ProxyServer
            subprocess.run([
                "reg", "add", 
                "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings", 
                "/v", "ProxyServer", "/t", "REG_SZ", "/d", f"{proxy_address}:{proxy_port}", "/f"
            ], shell=True, check=True)
            
            # Activar ProxyEnable
            subprocess.run([
                "reg", "add", 
                "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings", 
                "/v", "ProxyEnable", "/t", "REG_DWORD", "/d", "1", "/f"
            ], shell=True, check=True)
            
            print("✅ Proxy configurado con reg add")
            
        except Exception as e:
            print(f"⚠️ Error con reg add: {e}")
            return False
        
        # Método 2: Usar netsh winhttp
        try:
            subprocess.run([
                "netsh", "winhttp", "set", "proxy", f"{proxy_address}:{proxy_port}"
            ], shell=True, check=True)
            
            print("✅ Proxy configurado con netsh")
            
        except Exception as e:
            print(f"⚠️ Error con netsh: {e}")
        
        # Método 3: Usar PowerShell
        try:
            ps_script = f"""
            Set-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings' -Name ProxyEnable -Value 1
            Set-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings' -Name ProxyServer -Value '{proxy_address}:{proxy_port}'
            """
            
            subprocess.run([
                "powershell", "-Command", ps_script
            ], shell=True, check=True)
            
            print("✅ Proxy configurado con PowerShell")
            
        except Exception as e:
            print(f"⚠️ Error con PowerShell: {e}")
        
        # Forzar actualización
        self._refresh_settings()
        
        return True
    
    def disable_proxy(self):
        """
        Desactiva el proxy del sistema
        """
        print("🔒 Desactivando proxy...")
        
        try:
            # Desactivar con reg add
            subprocess.run([
                "reg", "add", 
                "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings", 
                "/v", "ProxyEnable", "/t", "REG_DWORD", "/d", "0", "/f"
            ], shell=True, check=True)
            
            print("✅ Proxy desactivado con reg add")
            
        except Exception as e:
            print(f"⚠️ Error al desactivar: {e}")
            return False
        
        # Limpiar con netsh
        try:
            subprocess.run([
                "netsh", "winhttp", "reset", "proxy"
            ], shell=True, check=True)
            
            print("✅ Proxy limpiado con netsh")
            
        except Exception as e:
            print(f"⚠️ Error con netsh: {e}")
        
        # Forzar actualización
        self._refresh_settings()
        
        return True
    
    def _refresh_settings(self):
        """
        Fuerza la actualización de la configuración
        """
        try:
            # Enviar mensaje de cambio de configuración
            subprocess.run([
                "rundll32", "user32.dll,UpdatePerUserSystemParameters"
            ], shell=True, check=True)
            
            print("🔄 Configuración actualizada")
            
        except Exception as e:
            print(f"⚠️ Advertencia al actualizar: {e}")


# Funciones de conveniencia
def enable_system_proxy(proxy_address="gw.dataimpulse.com", proxy_port="823"):
    controller = ProxyController()
    return controller.enable_proxy(proxy_address, proxy_port)

def disable_system_proxy():
    controller = ProxyController()
    return controller.disable_proxy()

def get_system_proxy_status():
    controller = ProxyController()
    return controller.get_proxy_status()


# Script principal
if __name__ == "__main__":
    print("🔧 Controlador de Proxy del Sistema (Versión Mejorada)")
    print("=" * 50)
    
    proxy_ctrl = ProxyController()
    
    # Mostrar estado actual
    status = proxy_ctrl.get_proxy_status()
    print(f"\n📊 Estado detectado:")
    print(f"Estado: {'🟢 Activado' if status['enabled'] else '🔴 Desactivado'}")
    print(f"Servidor: {status['server']}")
    print(f"Método: {status['method']}")
    
    print("\n¿Qué quieres hacer?")
    print("1. 🔓 Activar proxy (usar configuración por defecto)")
    print("2. 🔒 Desactivar proxy")
    print("3. ⚙️ Configurar nuevo proxy")
    print("4. 📊 Verificar estado")
    print("5. ❌ Salir")
    
    while True:
        try:
            opcion = input("\n📝 Selecciona una opción (1-5): ").strip()
            
            if opcion == "1":
                print("\n🔓 Activando proxy...")
                print("💡 Usando configuración por defecto: gw.dataimpulse.com:823")
                if proxy_ctrl.enable_proxy():
                    print("✅ Proxy activado exitosamente")
                else:
                    print("❌ Error al activar el proxy")
                    
            elif opcion == "2":
                print("\n🔒 Desactivando proxy...")
                if proxy_ctrl.disable_proxy():
                    print("✅ Proxy desactivado exitosamente")
                else:
                    print("❌ Error al desactivar el proxy")
                    
            elif opcion == "3":
                print("\n⚙️ Configurando nuevo proxy...")
                print("💡 Deja en blanco para usar la configuración por defecto")
                
                proxy_address = input("🌐 Dirección del proxy (Enter para gw.dataimpulse.com): ").strip()
                proxy_port = input("🔌 Puerto del proxy (Enter para 823): ").strip()
                
                # Usar valores por defecto si están vacíos
                if not proxy_address:
                    proxy_address = "gw.dataimpulse.com"
                if not proxy_port:
                    proxy_port = "823"
                
                print(f"📡 Configurando proxy: {proxy_address}:{proxy_port}")
                
                if proxy_ctrl.enable_proxy(proxy_address, proxy_port):
                    print("✅ Proxy configurado y activado exitosamente")
                else:
                    print("❌ Error al configurar el proxy")
                    
            elif opcion == "4":
                print("\n📊 Verificando estado...")
                new_status = proxy_ctrl.get_proxy_status()
                print(f"Estado: {'🟢 Activado' if new_status['enabled'] else '🔴 Desactivado'}")
                print(f"Servidor: {new_status['server']}")
                print(f"Método: {new_status['method']}")
                
            elif opcion == "5":
                print("\n👋 ¡Hasta luego!")
                break
                
            else:
                print("❌ Opción no válida. Selecciona 1, 2, 3, 4 o 5.")
                continue
            
            # Mostrar estado actualizado
            if opcion in ["1", "2", "3"]:
                print("\n📊 Estado actualizado:")
                updated_status = proxy_ctrl.get_proxy_status()
                print(f"Estado: {'🟢 Activado' if updated_status['enabled'] else '🔴 Desactivado'}")
                print(f"Servidor: {updated_status['server']}")
            
            # Continuar o salir
            continuar = input("\n🔄 ¿Continuar? (s/n): ").strip().lower()
            if continuar not in ['s', 'si', 'sí', 'y', 'yes']:
                break
                
        except KeyboardInterrupt:
            print("\n\n⚠️ Operación cancelada")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            break
    
    print("\n🔧 Controlador cerrado")
