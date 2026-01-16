"""
Diálogos del módulo de censo
Contiene ventanas emergentes para agregar habitantes, estadísticas, historial, etc.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from datetime import datetime
import os
from collections import Counter

from src.core.gestor_datos_global import obtener_gestor
from src.core.logger import registrar_operacion, registrar_error
from src.core.validadores import validar_nombre


def agregar_habitante(root, habitantes, callback_actualizar):
    """Muestra diálogo para agregar nuevo habitante"""
    dialog = tk.Toplevel(root)
    dialog.title("Agregar Nuevo Habitante")
    dialog.geometry("450x150")
    dialog.transient(root)
    dialog.grab_set()
    
    ttk.Label(dialog, text="Nombre Completo del Habitante:", 
             font=('Arial', 10, 'bold')).pack(pady=10)
    nombre_entry = ttk.Entry(dialog, width=50)
    nombre_entry.pack(pady=10)
    
    def guardar(event=None):
        from .censo_operaciones import buscar_nombres_similares
        
        nombre = nombre_entry.get().strip()
        
        # Validar nombre
        try:
            nombre_validado = validar_nombre(nombre)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        
        # Buscar nombres similares
        similares = buscar_nombres_similares(habitantes, nombre_validado)
        if similares:
            nombres_str = '\n'.join([f"- {h['nombre']} (Folio: {h['folio']})" for h in similares])
            respuesta = messagebox.askyesno(
                "Posible duplicado",
                f"Se encontraron habitantes con nombres similares:\n\n{nombres_str}\n\n"
                "¿Desea continuar agregando este habitante de todos modos?",
                icon='warning'
            )
            if not respuesta:
                return
        
        try:
            # Usar gestor directo en vez de API
            gestor = obtener_gestor()
            habitante, mensaje = gestor.agregar_habitante(nombre_validado)
            
            if habitante:
                registrar_operacion('CENSO_AGREGAR', 'Habitante agregado desde censo', 
                    {'nombre': nombre_validado, 'folio': habitante['folio']})
                # SIN ALERTA - solo cerrar y actualizar
                dialog.destroy()
                callback_actualizar()
            else:
                registrar_error('censo_dialogos', 'agregar_habitante', mensaje)
                messagebox.showerror("Error", mensaje)
        except Exception as e:
            error_msg = f"Error al agregar: {str(e)}"
            registrar_error('censo_dialogos', 'agregar_habitante', str(e), contexto=f"nombre={nombre_validado}")
            messagebox.showerror("Error", error_msg)
    
    botones = ttk.Frame(dialog)
    botones.pack(pady=10)
    ttk.Button(botones, text="Confirmar", command=guardar, width=18).pack(side=tk.LEFT, padx=5)
    ttk.Button(botones, text="Cancelar", command=dialog.destroy, width=18).pack(side=tk.LEFT, padx=5)
    
    nombre_entry.bind('<Return>', guardar)
    nombre_entry.focus_set()


def dialogo_editar_nota(root, habitante, gestor, callback_actualizar):
    """Muestra diálogo para editar la nota de un habitante"""
    dialog = tk.Toplevel(root)
    dialog.title(f"Nota - {habitante['nombre']}")
    dialog.geometry("500x350")
    dialog.transient(root)
    dialog.grab_set()
    
    ttk.Label(dialog, text=f"Habitante: {habitante['nombre']}", 
             font=('Arial', 10, 'bold')).pack(pady=10)
    ttk.Label(dialog, text=f"Folio: {habitante['folio']}", 
             font=('Arial', 9)).pack(pady=5)
    
    ttk.Label(dialog, text="Nota:", font=('Arial', 10)).pack(pady=5, anchor=tk.W, padx=20)
    
    nota_text = tk.Text(dialog, width=55, height=10, font=('Arial', 10))
    nota_text.pack(pady=5, padx=20)
    nota_text.insert('1.0', habitante.get('nota', ''))
    
    def guardar_nota():
        nota_nueva = nota_text.get('1.0', 'end-1c').strip()
        try:
            exito, mensaje = gestor.actualizar_habitante(habitante['folio'], nota=nota_nueva)
            if exito:
                registrar_operacion('CENSO_NOTA', 'Nota actualizada', {'folio': habitante['folio']})
                messagebox.showinfo("Éxito", "Nota guardada correctamente")
                dialog.destroy()
                callback_actualizar()
            else:
                messagebox.showerror("Error", mensaje)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")
            registrar_error('censo_dialogos', 'dialogo_editar_nota', str(e), contexto=f"folio={habitante['folio']}")
    
    botones_frame = ttk.Frame(dialog)
    botones_frame.pack(pady=10)
    ttk.Button(botones_frame, text="Guardar", command=guardar_nota).pack(side=tk.LEFT, padx=5)
    ttk.Button(botones_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.LEFT, padx=5)


def dialogo_editar_nombre(root, habitante, gestor, callback_actualizar):
    """Muestra diálogo para editar el nombre de un habitante"""
    ventana = tk.Toplevel(root)
    ventana.title(f"Editar Nombre - {habitante['folio']}")
    ventana.geometry("450x200")
    ventana.transient(root)
    ventana.grab_set()
    
    ttk.Label(ventana, text=f"Folio: {habitante['folio']}", font=('Arial', 10, 'bold')).pack(pady=10)
    ttk.Label(ventana, text=f"Nombre actual: {habitante['nombre']}", font=('Arial', 9), 
             foreground='#666').pack(pady=5)
    
    ttk.Label(ventana, text="Nuevo nombre:", font=('Arial', 9)).pack(pady=(15, 5))
    
    entry_nombre = ttk.Entry(ventana, width=50, font=('Arial', 10))
    entry_nombre.pack(padx=20, pady=5)
    entry_nombre.insert(0, habitante['nombre'])
    entry_nombre.select_range(0, tk.END)
    entry_nombre.focus_set()
    
    def guardar():
        nuevo_nombre = entry_nombre.get().strip()
        from src.modules.censo.censo_operaciones import editar_nombre_habitante
        
        if editar_nombre_habitante(habitante['folio'], nuevo_nombre, gestor, callback_actualizar):
            messagebox.showinfo("Éxito", f"Nombre actualizado correctamente\n\nFolio: {habitante['folio']}\nNuevo nombre: {nuevo_nombre}")
            ventana.destroy()
    
    # Enter para guardar
    entry_nombre.bind('<Return>', lambda e: guardar())
    
    botones = ttk.Frame(ventana)
    botones.pack(pady=15)
    ttk.Button(botones, text="Guardar", command=guardar, width=12).pack(side=tk.LEFT, padx=5)
    ttk.Button(botones, text="Cancelar", command=ventana.destroy, width=12).pack(side=tk.LEFT, padx=5)


def mostrar_estadisticas(root, habitantes):
    """Muestra estadísticas generales del censo"""
    dialog = tk.Toplevel(root)
    dialog.title("Estadísticas del Censo")
    dialog.geometry("500x600")
    dialog.transient(root)
    dialog.grab_set()
    
    ttk.Label(dialog, text="Estadísticas del Censo", 
             font=('Arial', 14, 'bold')).pack(pady=15)
    
    # Frame para estadísticas
    stats_frame = ttk.Frame(dialog, padding=20)
    stats_frame.pack(fill=tk.BOTH, expand=True)
    
    # Calcular estadísticas
    total = len(habitantes)
    if total == 0:
        ttk.Label(stats_frame, text="No hay datos para mostrar", 
                 font=('Arial', 10), foreground='#888').pack()
        ttk.Button(dialog, text="Cerrar", command=dialog.destroy).pack(pady=15)
        return
    
    activos = sum(1 for h in habitantes if h.get('activo', True))
    inactivos = total - activos
    con_notas = sum(1 for h in habitantes if h.get('nota', ''))
    
    # Estadísticas por fecha
    fechas = [h.get('fecha_registro', '')[:7] for h in habitantes if h.get('fecha_registro')]
    conteo_fechas = Counter(fechas)
    
    # Mostrar estadísticas generales
    ttk.Label(stats_frame, text="📊 GENERALES", font=('Arial', 11, 'bold')).pack(anchor=tk.W, pady=(0, 10))
    
    stats_text = f"""
Total de habitantes: {total}
Activos: {activos} ({activos/total*100:.1f}%)
Inactivos: {inactivos} ({inactivos/total*100:.1f}%)
Con notas: {con_notas} ({con_notas/total*100:.1f}%)
    """
    
    ttk.Label(stats_frame, text=stats_text, font=('Arial', 10), justify=tk.LEFT).pack(anchor=tk.W, pady=5)
    
    ttk.Separator(stats_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
    
    # Registros por mes
    ttk.Label(stats_frame, text="📅 REGISTROS POR MES (últimos 6 meses)", 
             font=('Arial', 11, 'bold')).pack(anchor=tk.W, pady=(0, 10))
    
    if conteo_fechas:
        meses_ordenados = sorted(conteo_fechas.items(), reverse=True)[:6]
        for mes, cantidad in meses_ordenados:
            try:
                mes_nombre = datetime.strptime(mes + "-01", "%Y-%m-%d").strftime("%B %Y")
            except:
                mes_nombre = mes
            
            # Barra visual simple
            barra_largo = int(cantidad / max(conteo_fechas.values()) * 30)
            barra = "█" * barra_largo
            
            label_text = f"{mes_nombre}: {cantidad} habitantes {barra}"
            ttk.Label(stats_frame, text=label_text, font=('Courier', 9)).pack(anchor=tk.W, pady=2)
    else:
        ttk.Label(stats_frame, text="No hay datos de fechas disponibles", 
                 font=('Arial', 9), foreground='#888').pack(anchor=tk.W)
    
    ttk.Separator(stats_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
    
    # Promedio de longitud de notas
    notas_con_contenido = [h.get('nota', '') for h in habitantes if h.get('nota', '')]
    if notas_con_contenido:
        promedio_longitud = sum(len(n) for n in notas_con_contenido) / len(notas_con_contenido)
        ttk.Label(stats_frame, text=f"📝 NOTAS", font=('Arial', 11, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        ttk.Label(stats_frame, text=f"Promedio de caracteres por nota: {promedio_longitud:.0f}", 
                 font=('Arial', 10)).pack(anchor=tk.W)
    
    ttk.Button(dialog, text="Cerrar", command=dialog.destroy).pack(pady=15)


def mostrar_historial(root, habitante):
    """Muestra el historial de cambios del habitante"""
    dialog = tk.Toplevel(root)
    dialog.title(f"Historial - {habitante['nombre']}")
    dialog.geometry("600x400")
    dialog.transient(root)
    dialog.grab_set()
    
    ttk.Label(dialog, text=f"Historial de: {habitante['nombre']}", 
             font=('Arial', 11, 'bold')).pack(pady=10)
    ttk.Label(dialog, text=f"Folio: {habitante['folio']}", 
             font=('Arial', 9)).pack(pady=5)
    
    # Frame para el texto del historial
    text_frame = ttk.Frame(dialog)
    text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    scrollbar = ttk.Scrollbar(text_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    historial_text = tk.Text(text_frame, font=('Courier', 9), wrap=tk.WORD,
                            yscrollcommand=scrollbar.set)
    historial_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=historial_text.yview)
    
    # Leer el log y filtrar por folio
    try:
        log_path = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 
                               'SistemaComunidad', 'sistema_comunidad.log')
        
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as f:
                lineas = f.readlines()
            
            # Filtrar líneas que contengan el folio
            eventos = []
            for linea in lineas[-500:]:
                if habitante['folio'] in linea or habitante['nombre'] in linea:
                    eventos.append(linea.strip())
            
            if eventos:
                historial_text.insert('1.0', '\n'.join(eventos))
            else:
                historial_text.insert('1.0', 'No se encontraron eventos registrados para este habitante.')
        else:
            historial_text.insert('1.0', 'No se encontró el archivo de log del sistema.')
    
    except Exception as e:
        historial_text.insert('1.0', f'Error al cargar historial: {str(e)}')
    
    historial_text.config(state=tk.DISABLED)
    
    ttk.Button(dialog, text="Cerrar", command=dialog.destroy).pack(pady=10)


def busqueda_avanzada(root, habitantes, callback_actualizar):
    """Diálogo de búsqueda avanzada con múltiples filtros"""
    dialog = tk.Toplevel(root)
    dialog.title("Búsqueda Avanzada")
    dialog.geometry("500x400")
    dialog.transient(root)
    dialog.grab_set()
    
    ttk.Label(dialog, text="Búsqueda Avanzada", 
             font=('Arial', 12, 'bold')).pack(pady=15)
    
    # Frame para filtros
    filtros_frame = ttk.LabelFrame(dialog, text="Criterios de Búsqueda", padding=15)
    filtros_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
    
    # Nombre
    ttk.Label(filtros_frame, text="Nombre contiene:").grid(row=0, column=0, sticky=tk.W, pady=5)
    nombre_var = tk.StringVar()
    ttk.Entry(filtros_frame, textvariable=nombre_var, width=30).grid(row=0, column=1, pady=5, padx=10)
    
    # Estado
    ttk.Label(filtros_frame, text="Estado:").grid(row=1, column=0, sticky=tk.W, pady=5)
    estado_var = tk.StringVar(value="Todos")
    ttk.Combobox(filtros_frame, textvariable=estado_var, 
                values=["Todos", "Activos", "Inactivos"], 
                state='readonly', width=27).grid(row=1, column=1, pady=5, padx=10)
    
    # Rango de fechas
    ttk.Label(filtros_frame, text="Fecha desde (DD/MM/AAAA):").grid(row=2, column=0, sticky=tk.W, pady=5)
    fecha_desde_var = tk.StringVar()
    ttk.Entry(filtros_frame, textvariable=fecha_desde_var, width=30).grid(row=2, column=1, pady=5, padx=10)
    
    ttk.Label(filtros_frame, text="Fecha hasta (DD/MM/AAAA):").grid(row=3, column=0, sticky=tk.W, pady=5)
    fecha_hasta_var = tk.StringVar()
    ttk.Entry(filtros_frame, textvariable=fecha_hasta_var, width=30).grid(row=3, column=1, pady=5, padx=10)
    
    # Nota contiene
    ttk.Label(filtros_frame, text="Nota contiene:").grid(row=4, column=0, sticky=tk.W, pady=5)
    nota_var = tk.StringVar()
    ttk.Entry(filtros_frame, textvariable=nota_var, width=30).grid(row=4, column=1, pady=5, padx=10)
    
    # Con/sin notas
    tiene_nota_var = tk.StringVar(value="Todos")
    ttk.Label(filtros_frame, text="Tiene nota:").grid(row=5, column=0, sticky=tk.W, pady=5)
    ttk.Combobox(filtros_frame, textvariable=tiene_nota_var,
                values=["Todos", "Con nota", "Sin nota"],
                state='readonly', width=27).grid(row=5, column=1, pady=5, padx=10)
    
    def aplicar_busqueda():
        """Aplica todos los filtros de búsqueda avanzada"""
        resultados = habitantes.copy()
        
        # Filtro por nombre
        nombre = nombre_var.get().strip().lower()
        if nombre:
            resultados = [h for h in resultados if nombre in h.get('nombre', '').lower()]
        
        # Filtro por estado
        if estado_var.get() == "Activos":
            resultados = [h for h in resultados if h.get('activo', True)]
        elif estado_var.get() == "Inactivos":
            resultados = [h for h in resultados if not h.get('activo', True)]
        
        # Filtro por rango de fechas
        fecha_desde = fecha_desde_var.get().strip()
        fecha_hasta = fecha_hasta_var.get().strip()
        
        if fecha_desde or fecha_hasta:
            try:
                desde_dt = None
                hasta_dt = None
                if fecha_desde:
                    desde_dt = datetime.strptime(fecha_desde, "%d/%m/%Y")
                if fecha_hasta:
                    hasta_dt = datetime.strptime(fecha_hasta, "%d/%m/%Y")
                
                resultados_filtrados = []
                for h in resultados:
                    fecha_registro = h.get('fecha_registro', '')
                    if fecha_registro:
                        try:
                            fecha_dt = datetime.strptime(fecha_registro, "%d/%m/%Y")
                            incluir = True
                            if desde_dt and fecha_dt < desde_dt:
                                incluir = False
                            if hasta_dt and fecha_dt > hasta_dt:
                                incluir = False
                            if incluir:
                                resultados_filtrados.append(h)
                        except:
                            pass
                resultados = resultados_filtrados
            except ValueError:
                messagebox.showerror("Error", "Formato de fecha inválido. Use DD/MM/AAAA")
                return
        
        # Filtro por contenido de nota
        nota_texto = nota_var.get().strip().lower()
        if nota_texto:
            resultados = [h for h in resultados if nota_texto in h.get('nota', '').lower()]
        
        # Filtro por tiene/no tiene nota
        if tiene_nota_var.get() == "Con nota":
            resultados = [h for h in resultados if h.get('nota', '')]
        elif tiene_nota_var.get() == "Sin nota":
            resultados = [h for h in resultados if not h.get('nota', '')]
        
        # Mostrar resultados
        callback_actualizar(resultados)
        messagebox.showinfo("Búsqueda Avanzada", 
                          f"Se encontraron {len(resultados)} habitantes que coinciden con los criterios.")
        dialog.destroy()
    
    # Botones
    botones_frame = ttk.Frame(dialog)
    botones_frame.pack(pady=15)
    ttk.Button(botones_frame, text="Buscar", command=aplicar_busqueda).pack(side=tk.LEFT, padx=5)
    ttk.Button(botones_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
