"""
Panel lateral de detalles para el módulo de pagos
Muestra información completa de la persona seleccionada y acciones rápidas
"""

import tkinter as tk
from tkinter import ttk
from src.ui.tema_moderno import FUENTES, ESPACIADO
from src.ui.estilos_globales import TEMA_GLOBAL
from src.ui.ui_moderna import BotonModerno


class PagosPanelDetalles:
    """Clase para gestionar el panel lateral de detalles de pagos"""
    
    def __init__(self, parent, callback_registrar_pago, callback_ver_historial, 
                 callback_editar, callback_exportar_pdf):
        """
        Inicializa el panel de detalles
        
        Args:
            parent: Frame contenedor del panel
            callback_registrar_pago: Función para registrar un pago
            callback_ver_historial: Función para ver historial de pagos
            callback_editar: Función para editar datos de la persona
            callback_exportar_pdf: Función para exportar PDF (placeholder)
        """
        self.parent = parent
        self.callback_registrar_pago = callback_registrar_pago
        self.callback_ver_historial = callback_ver_historial
        self.callback_editar = callback_editar
        self.callback_exportar_pdf = callback_exportar_pdf
        
        self.persona_actual = None
        self.tema = TEMA_GLOBAL
        
        # Crear panel inicial
        self.mostrar_mensaje_inicial()
    
    def mostrar_mensaje_inicial(self):
        """Muestra mensaje cuando no hay persona seleccionada"""
        self.limpiar_panel()
        label = tk.Label(self.parent, 
                        text="Selecciona una persona\npara ver sus detalles de pago",
                        font=FUENTES['subtitulo'], 
                        foreground='#888', 
                        bg=self.tema.get('card_bg', self.tema['bg_secundario']),
                        justify=tk.CENTER)
        label.pack(expand=True, pady=20)
    
    def limpiar_panel(self):
        """Limpia todos los widgets del panel"""
        for widget in self.parent.winfo_children():
            widget.destroy()
    
    def mostrar_detalles(self, persona):
        """
        Muestra los detalles de la persona en el panel
        
        Args:
            persona: Diccionario con datos de la persona y sus pagos
        """
        self.persona_actual = persona
        self.limpiar_panel()
        
        tema = self.tema
        bg = tema.get('card_bg', tema['bg_secundario'])
        
        # === SECCIÓN: INFORMACIÓN PERSONAL ===
        titulo_personal = tk.Label(self.parent, text="📋 INFORMACIÓN PERSONAL",
                                   font=FUENTES['subtitulo'], fg=tema['accent_primary'],
                                   bg=bg, anchor=tk.W)
        titulo_personal.pack(fill=tk.X, pady=(5, 5), padx=10)
        
        datos_frame = tk.Frame(self.parent, bg=bg)
        datos_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        # Folio
        self._agregar_fila_dato(datos_frame, "Folio:", persona.get('folio', 'SIN-FOLIO'), row=0)
        
        # Nombre (con wrap para nombres largos)
        tk.Label(datos_frame, text="Nombre:", font=FUENTES['normal_bold'], 
                fg=tema['fg_secundario'], bg=bg, anchor=tk.W).grid(row=1, column=0, sticky=tk.W, pady=3)
        nombre_label = tk.Label(datos_frame, text=persona['nombre'], font=FUENTES['normal'],
                               fg=tema['fg_principal'], bg=bg, anchor=tk.W, wraplength=180, justify=tk.LEFT)
        nombre_label.grid(row=1, column=1, sticky=tk.W, pady=3, padx=(5, 0))
        
        # Fecha de registro (si existe)
        fecha_registro = persona.get('fecha_registro', 'N/A')
        self._agregar_fila_dato(datos_frame, "Fecha registro:", fecha_registro, row=2)
        
        # Estado (activo/inactivo)
        activo = persona.get('activo', True)
        estado_texto = "Activo" if activo else "Inactivo"
        estado_color = tema['success'] if activo else tema['error']
        
        tk.Label(datos_frame, text="Estado:", font=FUENTES['normal_bold'], 
                fg=tema['fg_secundario'], bg=bg, anchor=tk.W).grid(row=3, column=0, sticky=tk.W, pady=3)
        tk.Label(datos_frame, text=f"● {estado_texto}", font=FUENTES['normal'],
                fg=estado_color, bg=bg, anchor=tk.W).grid(row=3, column=1, sticky=tk.W, pady=3, padx=(5, 0))
        
        # === SEPARADOR ===
        ttk.Separator(self.parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8, padx=10)
        
        # === SECCIÓN: INFORMACIÓN DE PAGOS ===
        titulo_pagos = tk.Label(self.parent, text="💰 INFORMACIÓN DE PAGOS",
                               font=FUENTES['subtitulo'], fg=tema['accent_primary'],
                               bg=bg, anchor=tk.W)
        titulo_pagos.pack(fill=tk.X, pady=(5, 5), padx=10)
        
        pagos_frame = tk.Frame(self.parent, bg=bg)
        pagos_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        # Calcular totales
        monto_esperado = persona.get('monto_esperado', 0)
        pagos = persona.get('pagos', [])
        total_pagado = sum(p.get('monto', 0) for p in pagos)
        saldo_pendiente = max(0, monto_esperado - total_pagado)
        porcentaje = (total_pagado / monto_esperado * 100) if monto_esperado > 0 else 0
        
        # Mostrar datos
        self._agregar_fila_dato(pagos_frame, "Total pagado:", f"${total_pagado:.2f}", row=0, color=tema['success'])
        self._agregar_fila_dato(pagos_frame, "Monto esperado:", f"${monto_esperado:.2f}", row=1)
        self._agregar_fila_dato(pagos_frame, "Saldo pendiente:", f"${saldo_pendiente:.2f}", 
                               row=2, color=tema['error'] if saldo_pendiente > 0 else tema['success'])
        self._agregar_fila_dato(pagos_frame, "Porcentaje:", f"{porcentaje:.1f}%", row=3)
        
        # Último pago
        if pagos:
            ultimo_pago = pagos[-1]
            fecha_ultimo = f"{ultimo_pago.get('fecha', 'N/A')} {ultimo_pago.get('hora', '')}"
            monto_ultimo = f"(${ultimo_pago.get('monto', 0):.2f})"
            nota_ultimo = ultimo_pago.get('nota', '')
            
            texto_ultimo = f"{fecha_ultimo}\n{monto_ultimo}"
            if nota_ultimo:
                texto_ultimo += f"\n💬 {nota_ultimo}"
            
            self._agregar_fila_dato(pagos_frame, "Último pago:", texto_ultimo, row=4)
        else:
            self._agregar_fila_dato(pagos_frame, "Último pago:", "Sin pagos", row=4, color='#888')
        
        # Número de pagos
        self._agregar_fila_dato(pagos_frame, "Número de pagos:", str(len(pagos)), row=5)
        
        # === BARRA DE PROGRESO VISUAL ===
        ttk.Separator(self.parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8, padx=10)
        
        progreso_label = tk.Label(self.parent, text="📊 PROGRESO DE PAGO",
                                 font=FUENTES['subtitulo'], fg=tema['accent_primary'],
                                 bg=bg, anchor=tk.W)
        progreso_label.pack(fill=tk.X, pady=(5, 5), padx=10)
        
        # Barra de progreso
        barra_container = tk.Frame(self.parent, bg=bg, height=30)
        barra_container.pack(fill=tk.X, padx=15, pady=(0, 5))
        barra_container.pack_propagate(False)
        
        # Fondo de la barra
        barra_fondo = tk.Canvas(barra_container, bg='#ddd', highlightthickness=0, height=20)
        barra_fondo.pack(fill=tk.BOTH, expand=True)
        
        # Llenar con color según porcentaje
        if porcentaje >= 100:
            color_barra = tema['success']
        elif porcentaje >= 50:
            color_barra = tema['warning']
        else:
            color_barra = tema['error']
        
        ancho_barra = max(0, min(porcentaje, 100))  # Limitar 0-100%
        barra_fondo.create_rectangle(0, 0, 
                                     barra_fondo.winfo_reqwidth() * ancho_barra / 100, 
                                     20, 
                                     fill=color_barra, outline='')
        # Texto en la barra
        barra_fondo.create_text(barra_fondo.winfo_reqwidth() / 2, 10,
                               text=f"{porcentaje:.1f}%", 
                               font=FUENTES['normal_bold'], fill='#333')
        
        # === SEPARADOR ===
        ttk.Separator(self.parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10, padx=10)
        
        # === ACCIONES RÁPIDAS ===
        titulo_acciones = tk.Label(self.parent, text="⚡ ACCIONES RÁPIDAS",
                                   font=FUENTES['subtitulo'], fg=tema['accent_primary'],
                                   bg=bg, anchor=tk.W)
        titulo_acciones.pack(fill=tk.X, pady=(5, 5), padx=10)
        
        botones_frame = tk.Frame(self.parent, bg=bg)
        botones_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        # Botones
        BotonModerno(botones_frame, "💵 Registrar Pago", tema=tema, tipo='primary',
                    command=self.callback_registrar_pago).pack(fill=tk.X, pady=3)
        BotonModerno(botones_frame, "📜 Ver Historial", tema=tema, tipo='ghost',
                    command=self.callback_ver_historial).pack(fill=tk.X, pady=3)
        BotonModerno(botones_frame, "✏️ Editar Datos", tema=tema, tipo='ghost',
                    command=self.callback_editar).pack(fill=tk.X, pady=3)
        # PDF export (placeholder por ahora)
        # BotonModerno(botones_frame, "📄 Exportar PDF", tema=tema, tipo='secondary',
        #             command=self.callback_exportar_pdf).pack(fill=tk.X, pady=3)
    
    def _agregar_fila_dato(self, parent, etiqueta, valor, row, color=None):
        """Helper para agregar una fila de dato con etiqueta y valor"""
        tema = self.tema
        bg = tema.get('card_bg', tema['bg_secundario'])
        
        tk.Label(parent, text=etiqueta, font=FUENTES['normal_bold'], 
                fg=tema['fg_secundario'], bg=bg, anchor=tk.W).grid(row=row, column=0, sticky=tk.W, pady=3)
        
        valor_color = color if color else tema['fg_principal']
        tk.Label(parent, text=valor, font=FUENTES['normal'],
                fg=valor_color, bg=bg, anchor=tk.W).grid(row=row, column=1, sticky=tk.W, pady=3, padx=(5, 0))

