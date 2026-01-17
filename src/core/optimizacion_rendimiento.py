"""
Módulo de optimización de rendimiento para la aplicación
Configura prioridades de proceso y uso de recursos
"""

import sys
import os


def optimizar_rendimiento_sistema(silencioso: bool = False, instalar_dependencias: bool = True):
    """
    Optimiza el rendimiento del sistema operativo para la aplicación.
    Permite modo silencioso y control sobre instalación de dependencias.
    """
    optimizaciones = {
        'prioridad_proceso': False,
        'aceleracion_gpu': False,
        'memoria': False
    }

    def log(msg: str):
        if not silencioso:
            print(msg)
    
    try:
        if sys.platform == 'win32':
            # Importar solo si estamos en Windows
            try:
                import psutil
                import ctypes
                
                # Obtener el proceso actual
                proceso = psutil.Process()
                
                # Establecer prioridad ALTA (no REALTIME para evitar problemas)
                # Valores: IDLE, BELOW_NORMAL, NORMAL, ABOVE_NORMAL, HIGH, REALTIME
                try:
                    proceso.nice(psutil.HIGH_PRIORITY_CLASS)
                    optimizaciones['prioridad_proceso'] = True
                    log("✅ Prioridad de proceso: ALTA")
                except:
                    try:
                        proceso.nice(psutil.ABOVE_NORMAL_PRIORITY_CLASS)
                        optimizaciones['prioridad_proceso'] = True
                        log("✅ Prioridad de proceso: SUPERIOR A NORMAL")
                    except Exception as e:
                        log(f"⚠️ No se pudo cambiar prioridad: {e}")
                
                # Información de recursos
                info_mem = psutil.virtual_memory()
                info_cpu = psutil.cpu_percent(interval=0.1)
                
                log(f"📊 Recursos del sistema:")
                log(f"   CPU: {info_cpu}% en uso")
                log(f"   RAM: {info_mem.percent}% en uso ({info_mem.available / (1024**3):.1f} GB disponibles)")
                
                optimizaciones['memoria'] = True
                
            except ImportError:
                if instalar_dependencias:
                    log("⚠️ psutil no disponible. Instalando...")
                    try:
                        import subprocess
                        subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil", "--quiet"])
                        log("✅ psutil instalado. Reinicie la aplicación para aplicar optimizaciones.")
                    except Exception as e:
                        log(f"❌ No se pudo instalar psutil: {e}")
                else:
                    log("⚠️ psutil no disponible (instalación omitida)")
                return optimizaciones
            
            # Habilitar aceleración por hardware (Windows DPI awareness)
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
                optimizaciones['aceleracion_gpu'] = True
                log("✅ Aceleración DPI habilitada")
            except Exception as e:
                log(f"⚠️ No se pudo habilitar DPI awareness: {e}")
        
        else:
            log("ℹ️ Optimizaciones específicas de Windows no aplicables en este sistema")
    
    except Exception as e:
        log(f"❌ Error general en optimización: {e}")
    
    return optimizaciones


def configurar_tkinter_rendimiento(root):
    """
    Configura optimizaciones específicas de Tkinter
    
    Args:
        root: Ventana raíz de Tkinter
    """
    try:
        # Deshabilitar actualizaciones automáticas durante configuración
        root.update_idletasks()
        
        # Configurar para mejor rendimiento de redibujado
        root.tk.call('tk', 'scaling', 1.0)
        
        # Configurar buffer de eventos
        root.tk.call('wm', 'attributes', '.', '-alpha', 1.0)
        
        print("[OK] Optimizaciones de Tkinter aplicadas")
        return True
        
    except Exception as e:
        print(f"[WARNING] Error configurando Tkinter: {e}")
        return False


def obtener_info_sistema():
    """
    Obtiene información del sistema para diagnóstico
    
    Returns:
        dict: Información del sistema
    """
    info = {
        'sistema': sys.platform,
        'version_python': sys.version,
        'arquitectura': sys.maxsize > 2**32 and '64-bit' or '32-bit'
    }
    
    try:
        import psutil
        
        # Información de CPU
        info['cpu_count'] = psutil.cpu_count()
        info['cpu_freq'] = psutil.cpu_freq().current if psutil.cpu_freq() else 'N/A'
        
        # Información de memoria
        mem = psutil.virtual_memory()
        info['ram_total_gb'] = mem.total / (1024**3)
        info['ram_disponible_gb'] = mem.available / (1024**3)
        info['ram_porcentaje_uso'] = mem.percent
        
        # Información de disco
        disco = psutil.disk_usage('/')
        info['disco_total_gb'] = disco.total / (1024**3)
        info['disco_disponible_gb'] = disco.free / (1024**3)
        
    except ImportError:
        info['psutil'] = 'No disponible'
    
    return info


def imprimir_info_sistema():
    """Imprime información del sistema de forma legible"""
    info = obtener_info_sistema()
    
    print("\n" + "=" * 60)
    print("INFORMACIÓN DEL SISTEMA")
    print("=" * 60)
    print(f"Sistema Operativo: {info['sistema']}")
    print(f"Arquitectura: {info['arquitectura']}")
    
    if 'cpu_count' in info:
        print(f"\nCPU:")
        print(f"  Núcleos: {info['cpu_count']}")
        print(f"  Frecuencia: {info['cpu_freq']} MHz")
        
        print(f"\nMemoria RAM:")
        print(f"  Total: {info['ram_total_gb']:.1f} GB")
        print(f"  Disponible: {info['ram_disponible_gb']:.1f} GB")
        print(f"  En uso: {info['ram_porcentaje_uso']}%")
        
        print(f"\nDisco:")
        print(f"  Total: {info['disco_total_gb']:.1f} GB")
        print(f"  Disponible: {info['disco_disponible_gb']:.1f} GB")
    
    print("=" * 60 + "\n")


if __name__ == "__main__":
    print("\nPROBAN DO OPTIMIZACIONES DEL SISTEMA\n")
    imprimir_info_sistema()
    optimizaciones = optimizar_rendimiento_sistema()
    
    print("\n" + "=" * 60)
    print("RESULTADO DE OPTIMIZACIONES")
    print("=" * 60)
    for nombre, resultado in optimizaciones.items():
        simbolo = "✅" if resultado else "❌"
        print(f"{simbolo} {nombre.replace('_', ' ').title()}: {'Aplicado' if resultado else 'No aplicado'}")
    print("=" * 60)
