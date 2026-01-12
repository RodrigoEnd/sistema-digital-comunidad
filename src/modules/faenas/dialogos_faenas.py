"""
Diálogos y ventanas modales para el sistema de faenas
Separa la lógica de diálogos complejos del controlador principal
"""

import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
from typing import Dict, List, Callable, Optional

from src.ui.tema_moderno import FUENTES, ESPACIADO


class DialogoAgregarParticipantes:
    """Diálogo para agregar múltiples participantes a una faena"""

    def __init__(self, parent, faena_seleccionada: Dict, habitantes_cache: List[Dict],
                 callback_agregar: Callable, tema: Dict):
        self.parent = parent
        self.faena_seleccionada = faena_seleccionada
        self.habitantes_cache = habitantes_cache
        self.callback_agregar = callback_agregar
        self.tema = tema

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Agregar participantes")
        self.dialog.geometry("520x560")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._crear_interfaz()

    def _crear_interfaz(self):
        """Crear interfaz del diálogo"""
        tk.Label(self.dialog, text="Buscar habitante", font=FUENTES['subtitulo']).pack(
            pady=ESPACIADO['sm'])

        self.filtro_var = tk.StringVar()
        entry = tk.Entry(self.dialog, textvariable=self.filtro_var, font=FUENTES['normal'])
        entry.pack(fill=tk.X, padx=ESPACIADO['lg'])

        # TreeView para habitantes
        columns = ('check', 'folio', 'nombre')
        self.tree = ttk.Treeview(self.dialog, columns=columns, show='headings', selectmode='none')
        self.tree.heading('check', text='✔')
        self.tree.heading('folio', text='Folio')
        self.tree.heading('nombre', text='Nombre')
        self.tree.column('check', width=40, anchor='center')
        self.tree.column('folio', width=100, anchor='center')
        self.tree.column('nombre', width=320)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=ESPACIADO['lg'], pady=ESPACIADO['sm'])

        # Eventos
        self.filtro_var.trace_add('write', lambda *_: self._refrescar_lista())
        self.tree.bind('<Button-1>', self._toggle_item)

        # Botón agregar
        tk.Button(self.dialog, text="Agregar seleccionados",
                  command=self._agregar_seleccion).pack(pady=ESPACIADO['sm'])

        entry.focus()
        self._refrescar_lista()

    def _refrescar_lista(self):
        """Actualizar lista de habitantes según filtro"""
        self.tree.delete(*self.tree.get_children())
        criterio = self.filtro_var.get().lower().strip()

        for h in self.habitantes_cache:
            folio = h.get('folio', '')
            nombre = h.get('nombre', '')
            texto = f"{folio} - {nombre}".strip()

            # No mostrar habitantes que ya están en la faena
            if any(p.get('folio') == folio and p.get('nombre') == nombre
                   for p in self.faena_seleccionada['participantes']):
                continue

            if criterio and criterio not in texto.lower():
                continue

            self.tree.insert('', tk.END, values=('☐', folio, nombre))

    def _toggle_item(self, event):
        """Toggle checkbox de un item"""
        item = self.tree.identify_row(event.y)
        if not item:
            return
        vals = list(self.tree.item(item, 'values'))
        vals[0] = '☐' if vals[0] == '☑' else '☑'
        self.tree.item(item, values=vals)

    def _agregar_seleccion(self):
        """Agregar participantes seleccionados"""
        nuevos = []
        for item in self.tree.get_children():
            vals = self.tree.item(item, 'values')
            if vals and vals[0] == '☑':
                folio, nombre = vals[1], vals[2]
                if any(p.get('folio') == folio and p.get('nombre') == nombre
                       for p in self.faena_seleccionada['participantes']):
                    continue
                participante = {
                    'folio': folio,
                    'nombre': nombre or folio,
                    'hora_registro': datetime.now().isoformat()
                }
                nuevos.append(participante)

        if nuevos:
            self.callback_agregar(nuevos)

        self.dialog.destroy()


class DialogoRegistroPagoEnLugar:
    """Diálogo para registrar sustitución de faena (pago en lugar)"""

    def __init__(self, parent, faena_seleccionada: Dict, habitantes_cache: List[Dict],
                 callback_guardar: Callable, tema: Dict):
        self.parent = parent
        self.faena_seleccionada = faena_seleccionada
        self.habitantes_cache = habitantes_cache
        self.callback_guardar = callback_guardar
        self.tema = tema

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Registrar sustitución de faena")
        self.dialog.geometry("620x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._crear_interfaz()

    def _crear_interfaz(self):
        """Crear interfaz del diálogo"""
        # Instrucciones
        instrucciones = tk.Label(
            self.dialog,
            text="Selecciona quién pagó por la faena y especifica si contrató a un habitante o a alguien externo.\n"
                 "• Habitante del pueblo: 90% de peso para quien pagó + 100% para quien trabajó\n"
                 "• Externo (albañil, etc.): 100% de peso para quien pagó",
            font=FUENTES['pequeño'], justify=tk.LEFT, wraplength=560,
            bg=self.tema['bg_principal'], fg=self.tema['fg_secundario'])
        instrucciones.pack(pady=ESPACIADO['md'], padx=ESPACIADO['lg'], anchor='w')

        # Selector de quien pagó
        self._crear_selector_pagador()

        # Separador
        ttk.Separator(self.dialog, orient='horizontal').pack(
            fill=tk.X, pady=ESPACIADO['md'], padx=ESPACIADO['lg'])

        # Tipo de sustitución
        self._crear_selector_tipo_sustitucion()

        # Botón guardar
        tk.Button(self.dialog, text="Registrar sustitución",
                  command=self._guardar_sustitucion,
                  font=FUENTES['normal'], bg=self.tema['accent_primary'],
                  fg='white', relief=tk.FLAT, cursor='hand2').pack(pady=ESPACIADO['md'])

    def _crear_selector_pagador(self):
        """Crear selector de quien pagó"""
        tk.Label(self.dialog, text="¿Quién pagó por la faena?",
                 font=FUENTES['subtitulo']).pack(pady=(ESPACIADO['sm'], 2),
                                                  padx=ESPACIADO['lg'], anchor='w')

        self.filtro_pagador_var = tk.StringVar()
        tk.Entry(self.dialog, textvariable=self.filtro_pagador_var,
                 font=FUENTES['normal']).pack(fill=tk.X, padx=ESPACIADO['lg'])

        columns = ('check', 'folio', 'nombre')
        self.tree_pagador = ttk.Treeview(self.dialog, columns=columns, show='headings',
                                         selectmode='none', height=6)
        self.tree_pagador.heading('check', text='✔')
        self.tree_pagador.heading('folio', text='Folio')
        self.tree_pagador.heading('nombre', text='Nombre')
        self.tree_pagador.column('check', width=40, anchor='center')
        self.tree_pagador.column('folio', width=100, anchor='center')
        self.tree_pagador.column('nombre', width=420)
        self.tree_pagador.pack(fill=tk.X, padx=ESPACIADO['lg'],
                               pady=(ESPACIADO['sm'], ESPACIADO['md']))

        self.filtro_pagador_var.trace_add('write', lambda *_: self._refrescar_lista_pagador())
        self.tree_pagador.bind('<Button-1>', self._toggle_pagador)
        self._refrescar_lista_pagador()

    def _crear_selector_tipo_sustitucion(self):
        """Crear selector de tipo de sustitución"""
        tk.Label(self.dialog, text="¿Quién realizó el trabajo?",
                 font=FUENTES['subtitulo'],
                 bg=self.tema['bg_principal'], fg=self.tema['fg_principal']).pack(
            pady=(ESPACIADO['sm'], 2), padx=ESPACIADO['lg'], anchor='w')

        self.tipo_sustitucion_var = tk.StringVar(value='habitante')
        frame_tipo = tk.Frame(self.dialog, bg=self.tema['bg_principal'])
        frame_tipo.pack(fill=tk.X, padx=ESPACIADO['lg'], pady=ESPACIADO['sm'])

        tk.Radiobutton(frame_tipo, text="Habitante del pueblo",
                       variable=self.tipo_sustitucion_var,
                       value='habitante', font=FUENTES['normal'],
                       bg=self.tema['bg_principal'],
                       fg=self.tema['fg_principal']).pack(anchor='w')

        tk.Radiobutton(frame_tipo, text="Persona externa (albañil, etc.)",
                       variable=self.tipo_sustitucion_var,
                       value='externo', font=FUENTES['normal'],
                       bg=self.tema['bg_principal'],
                       fg=self.tema['fg_principal']).pack(anchor='w', pady=(ESPACIADO['xs'], 0))

        # Frames condicionales
        self._crear_frame_habitante()
        self._crear_frame_externo()

        # Actualizar visibilidad
        self.tipo_sustitucion_var.trace_add('write', lambda *_: self._actualizar_visibilidad_frames())
        self._actualizar_visibilidad_frames()

    def _crear_frame_habitante(self):
        """Frame para seleccionar habitante trabajador"""
        self.frame_habitante = tk.Frame(self.dialog, bg=self.tema['bg_principal'])
        self.frame_habitante.pack(fill=tk.X, padx=ESPACIADO['lg'], pady=ESPACIADO['sm'])

        tk.Label(self.frame_habitante, text="Selecciona al habitante que realizó el trabajo:",
                 font=FUENTES['pequeño'],
                 bg=self.tema['bg_principal'], fg=self.tema['fg_principal']).pack(anchor='w')

        self.filtro_trabajador_var = tk.StringVar()
        tk.Entry(self.frame_habitante, textvariable=self.filtro_trabajador_var,
                 font=FUENTES['normal']).pack(fill=tk.X, pady=(2, ESPACIADO['xs']))

        columns = ('check', 'folio', 'nombre')
        self.tree_trabajador = ttk.Treeview(self.frame_habitante, columns=columns,
                                            show='headings', selectmode='none', height=5)
        self.tree_trabajador.heading('check', text='✔')
        self.tree_trabajador.heading('folio', text='Folio')
        self.tree_trabajador.heading('nombre', text='Nombre')
        self.tree_trabajador.column('check', width=40, anchor='center')
        self.tree_trabajador.column('folio', width=100, anchor='center')
        self.tree_trabajador.column('nombre', width=390)
        self.tree_trabajador.pack(fill=tk.X)

        self.filtro_trabajador_var.trace_add('write', lambda *_: self._refrescar_lista_trabajador())
        self.tree_trabajador.bind('<Button-1>', self._toggle_trabajador)
        self._refrescar_lista_trabajador()

    def _crear_frame_externo(self):
        """Frame para registrar persona externa"""
        self.frame_externo = tk.Frame(self.dialog, bg=self.tema['bg_principal'])
        self.frame_externo.pack(fill=tk.X, padx=ESPACIADO['lg'], pady=ESPACIADO['sm'])

        tk.Label(self.frame_externo, text="Nombre de la persona externa:",
                 font=FUENTES['pequeño'],
                 bg=self.tema['bg_principal'], fg=self.tema['fg_principal']).pack(anchor='w')

        self.nombre_externo_var = tk.StringVar()
        tk.Entry(self.frame_externo, textvariable=self.nombre_externo_var,
                 font=FUENTES['normal']).pack(fill=tk.X)

    def _refrescar_lista_pagador(self):
        """Actualizar lista de posibles pagadores"""
        self.tree_pagador.delete(*self.tree_pagador.get_children())
        criterio = self.filtro_pagador_var.get().lower().strip()

        for h in self.habitantes_cache:
            folio = h.get('folio', '')
            nombre = h.get('nombre', '')
            texto = f"{folio} - {nombre}".strip()

            if criterio and criterio not in texto.lower():
                continue

            # Verificar si ya está en la faena
            participante_existente = next((p for p in self.faena_seleccionada['participantes']
                                          if p.get('folio') == folio), None)

            if not participante_existente:
                self.tree_pagador.insert('', tk.END, values=('☐', folio, nombre))

    def _refrescar_lista_trabajador(self):
        """Actualizar lista de trabajadores"""
        self.tree_trabajador.delete(*self.tree_trabajador.get_children())
        criterio = self.filtro_trabajador_var.get().lower().strip()

        for h in self.habitantes_cache:
            folio = h.get('folio', '')
            nombre = h.get('nombre', '')
            texto = f"{folio} - {nombre}".strip()

            if criterio and criterio not in texto.lower():
                continue

            self.tree_trabajador.insert('', tk.END, values=('☐', folio, nombre))

    def _toggle_pagador(self, event):
        """Toggle selección de pagador (solo uno)"""
        item = self.tree_pagador.identify_row(event.y)
        if not item:
            return

        # Desmarcar todos primero
        for child in self.tree_pagador.get_children():
            vals = list(self.tree_pagador.item(child, 'values'))
            vals[0] = '☐'
            self.tree_pagador.item(child, values=vals)

        # Marcar el seleccionado
        vals = list(self.tree_pagador.item(item, 'values'))
        vals[0] = '☑'
        self.tree_pagador.item(item, values=vals)

    def _toggle_trabajador(self, event):
        """Toggle selección de trabajador (solo uno)"""
        item = self.tree_trabajador.identify_row(event.y)
        if not item:
            return

        # Desmarcar todos primero
        for child in self.tree_trabajador.get_children():
            vals = list(self.tree_trabajador.item(child, 'values'))
            vals[0] = '☐'
            self.tree_trabajador.item(child, values=vals)

        # Marcar el seleccionado
        vals = list(self.tree_trabajador.item(item, 'values'))
        vals[0] = '☑'
        self.tree_trabajador.item(item, values=vals)

    def _actualizar_visibilidad_frames(self):
        """Mostrar/ocultar frames según tipo de sustitución"""
        if self.tipo_sustitucion_var.get() == 'habitante':
            self.frame_habitante.pack(fill=tk.X, padx=ESPACIADO['lg'], pady=ESPACIADO['sm'])
            self.frame_externo.pack_forget()
        else:
            self.frame_habitante.pack_forget()
            self.frame_externo.pack(fill=tk.X, padx=ESPACIADO['lg'], pady=ESPACIADO['sm'])

    def _guardar_sustitucion(self):
        """Procesar y guardar la sustitución"""
        # Obtener quien pagó
        pagador_seleccionado = None
        for item in self.tree_pagador.get_children():
            vals = self.tree_pagador.item(item, 'values')
            if vals and vals[0] == '☑':
                pagador_seleccionado = (vals[1], vals[2])
                break

        if not pagador_seleccionado:
            messagebox.showwarning("Selección incompleta",
                                   "Debes seleccionar quién pagó por la faena")
            return

        folio_pagador, nombre_pagador = pagador_seleccionado
        tipo = self.tipo_sustitucion_var.get()

        # Validar según tipo
        if tipo == 'habitante':
            trabajador_seleccionado = self._obtener_trabajador_seleccionado()
            if not trabajador_seleccionado:
                messagebox.showwarning("Selección incompleta",
                                       "Debes seleccionar al habitante que realizó el trabajo")
                return

            folio_trabajador, nombre_trabajador = trabajador_seleccionado

            if folio_pagador == folio_trabajador:
                messagebox.showwarning("Error",
                                       "No puedes seleccionar a la misma persona como pagador y trabajador.\n"
                                       "Si asistió personalmente, agrégalo desde el botón 'Agregar participantes'.")
                return

            # Callback con datos de sustitución habitante
            datos = {
                'tipo': 'habitante',
                'folio_pagador': folio_pagador,
                'nombre_pagador': nombre_pagador,
                'folio_trabajador': folio_trabajador,
                'nombre_trabajador': nombre_trabajador
            }
            self.callback_guardar(datos)

        else:  # externo
            nombre_ext = self.nombre_externo_var.get().strip()
            if not nombre_ext:
                messagebox.showwarning("Dato faltante",
                                       "Debes escribir el nombre de la persona externa")
                return

            # Callback con datos de sustitución externa
            datos = {
                'tipo': 'externo',
                'folio_pagador': folio_pagador,
                'nombre_pagador': nombre_pagador,
                'nombre_externo': nombre_ext
            }
            self.callback_guardar(datos)

        self.dialog.destroy()

    def _obtener_trabajador_seleccionado(self) -> Optional[tuple]:
        """Obtener trabajador seleccionado"""
        for item in self.tree_trabajador.get_children():
            vals = self.tree_trabajador.item(item, 'values')
            if vals and vals[0] == '☑':
                return (vals[1], vals[2])
        return None
