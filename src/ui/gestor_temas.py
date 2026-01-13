"""
Gestor Centralizado de Temas - Sistema Digital Comunidad
Proporciona aplicacion uniforme de temas en toda la interfaz
Soporta cambio de tema en tiempo real
"""

from src.config import TEMA_DEFECTO


class GestorTemas:
    """Gestor centralizado de temas con cambio dinamico"""
    
    def __init__(self, tema_inicial=TEMA_DEFECTO):
        """Inicializar con tema por defecto"""
        self.tema_actual = tema_inicial
        self.observadores = []  # Callbacks para cambios de tema
    
    def cambiar_tema(self, nombre_tema):
        """
        Cambiar tema activo
        
        Args:
            nombre_tema (str): 'claro' u 'oscuro'
        """
        if nombre_tema not in ['claro', 'oscuro']:
            raise ValueError("Tema debe ser 'claro' u 'oscuro'")
        
        self.tema_actual = nombre_tema
        
        # Notificar observadores
        for callback in self.observadores:
            callback(nombre_tema)
    
    def suscribir(self, callback):
        """
        Suscribirse a cambios de tema
        
        Args:
            callback: Funcion que sera llamada con (nombre_tema)
        """
        self.observadores.append(callback)
    
    def obtener_colores(self):
        """Obtener paleta de colores del tema actual"""
        from src.config import TEMAS
        return TEMAS.get(self.tema_actual, TEMAS['claro'])
    
    def obtener_color(self, clave):
        """
        Obtener color especifico del tema
        
        Args:
            clave (str): Nombre del color (bg, fg, button_bg, etc)
            
        Returns:
            str: Codigo de color hexadecimal
        """
        colores = self.obtener_colores()
        return colores.get(clave, '#000000')


# Instancia global del gestor
_gestor_temas = GestorTemas()


class AplicadorTemas:
    """Utilidad para aplicar temas a widgets de Tkinter"""
    
    @staticmethod
    def aplicar_frame(frame, bg_tipo='bg', gestor=_gestor_temas):
        """Aplicar tema a un Frame"""
        colores = gestor.obtener_colores()
        frame.configure(bg=colores.get(bg_tipo, colores['bg']))
    
    @staticmethod
    def aplicar_label(label, fg_tipo='fg', bg_tipo='bg', gestor=_gestor_temas):
        """Aplicar tema a un Label"""
        colores = gestor.obtener_colores()
        label.configure(
            fg=colores.get(fg_tipo, colores.get('fg', '#000000')),
            bg=colores.get(bg_tipo, colores.get('bg', '#ffffff'))
        )
    
    @staticmethod
    def aplicar_button(button, bg_tipo='button_bg', fg_tipo='fg', gestor=_gestor_temas):
        """Aplicar tema a un Button"""
        colores = gestor.obtener_colores()
        button.configure(
            bg=colores.get(bg_tipo, colores.get('button_bg', '#e9ecef')),
            fg=colores.get(fg_tipo, colores.get('fg', '#000000')),
            activebackground=colores.get('button_hover', '#d0d0d0'),
            activeforeground=colores.get(fg_tipo, colores.get('fg', '#000000'))
        )
    
    @staticmethod
    def aplicar_entry(entry, bg_tipo='entrada_bg', fg_tipo='fg', gestor=_gestor_temas):
        """Aplicar tema a un Entry"""
        colores = gestor.obtener_colores()
        entry.configure(
            bg=colores.get(bg_tipo, colores.get('entrada_bg', '#ffffff')),
            fg=colores.get(fg_tipo, colores.get('fg', '#000000')),
            insertbackground=colores.get(fg_tipo, colores.get('fg', '#000000')),
            relief='solid',
            borderwidth=1
        )
    
    @staticmethod
    def aplicar_treeview(tree, style, gestor=_gestor_temas):
        """Aplicar tema a un Treeview"""
        colores = gestor.obtener_colores()
        
        style.configure("Treeview",
                       background=colores.get('tablas_even', '#ffffff'),
                       foreground=colores.get('fg', '#000000'),
                       fieldbackground=colores.get('tablas_even', '#ffffff'))
        
        style.map('Treeview',
                 background=[('selected', colores.get('titulo_fg', '#0066cc'))])
        
        style.configure("Treeview.Heading",
                       background=colores.get('frame_bg', '#f8f9fa'),
                       foreground=colores.get('fg', '#000000'))
        
        style.map("Treeview.Heading",
                 background=[('active', colores.get('button_bg', '#e9ecef'))])
    
    @staticmethod
    def aplicar_texto(text, bg_tipo='entrada_bg', fg_tipo='fg', gestor=_gestor_temas):
        """Aplicar tema a un Text widget"""
        colores = gestor.obtener_colores()
        text.configure(
            bg=colores.get(bg_tipo, colores.get('entrada_bg', '#ffffff')),
            fg=colores.get(fg_tipo, colores.get('fg', '#000000')),
            insertbackground=colores.get(fg_tipo, colores.get('fg', '#000000')),
            relief='solid',
            borderwidth=1
        )


# Paletas de color mejoradas
PALETAS_COLOR = {
    'claro': {
        'bg': '#ffffff',
        'fg': '#1a1a1a',
        'frame_bg': '#f8f9fa',
        'button_bg': '#e9ecef',
        'entrada_bg': '#ffffff',
        'titulo_fg': '#0066cc',
        'exito_fg': '#28a745',
        'alerta_fg': '#ffc107',
        'error_fg': '#dc3545',
        'tablas_even': '#ffffff',
        'tablas_odd': '#f8f9fa',
        'border': '#dee2e6',
        'hover_bg': '#f0f0f0',
        'focus_border': '#0066cc',
    },
    'oscuro': {
        'bg': '#1a1a1a',
        'fg': '#e9ecef',
        'frame_bg': '#2d2d2d',
        'button_bg': '#3d3d3d',
        'entrada_bg': '#2d2d2d',
        'titulo_fg': '#4da6ff',
        'exito_fg': '#51cf66',
        'alerta_fg': '#ffd93d',
        'error_fg': '#ff6b6b',
        'tablas_even': '#1a1a1a',
        'tablas_odd': '#2d2d2d',
        'border': '#495057',
        'hover_bg': '#3d3d3d',
        'focus_border': '#4da6ff',
    }
}


def obtener_tema_actual():
    """Obtener tema actualmente activo"""
    return _gestor_temas.tema_actual


def cambiar_tema(nombre_tema):
    """Cambiar tema global"""
    _gestor_temas.cambiar_tema(nombre_tema)


def obtener_colores_tema():
    """Obtener paleta de colores del tema actual"""
    return _gestor_temas.obtener_colores()


def obtener_color(clave):
    """Obtener color especifico"""
    return _gestor_temas.obtener_color(clave)


def suscribir_cambios_tema(callback):
    """Suscribirse a cambios de tema"""
    _gestor_temas.suscribir(callback)


# Funciones de utilidad para aplicar estilos comunes
def estilo_boton_primario():
    """Retorna diccionario de estilo para boton primario"""
    colores = obtener_colores_tema()
    return {
        'bg': colores['titulo_fg'],
        'fg': '#ffffff',
        'relief': 'flat',
        'cursor': 'hand2',
        'bd': 0
    }


def estilo_boton_secundario():
    """Retorna diccionario de estilo para boton secundario"""
    colores = obtener_colores_tema()
    return {
        'bg': colores['button_bg'],
        'fg': colores['fg'],
        'relief': 'solid',
        'cursor': 'hand2',
        'bd': 1,
        'borderwidth': 1
    }


def estilo_boton_peligro():
    """Retorna diccionario de estilo para boton de peligro"""
    colores = obtener_colores_tema()
    return {
        'bg': colores['error_fg'],
        'fg': '#ffffff',
        'relief': 'flat',
        'cursor': 'hand2',
        'bd': 0
    }


def estilo_boton_exito():
    """Retorna diccionario de estilo para boton de exito"""
    colores = obtener_colores_tema()
    return {
        'bg': colores['exito_fg'],
        'fg': '#ffffff',
        'relief': 'flat',
        'cursor': 'hand2',
        'bd': 0
    }


def estilo_entrada():
    """Retorna diccionario de estilo para Entry"""
    colores = obtener_colores_tema()
    return {
        'bg': colores['entrada_bg'],
        'fg': colores['fg'],
        'relief': 'solid',
        'bd': 1,
        'insertbackground': colores['fg']
    }


def estilo_label():
    """Retorna diccionario de estilo para Label"""
    colores = obtener_colores_tema()
    return {
        'bg': colores['bg'],
        'fg': colores['fg']
    }


def estilo_label_titulo():
    """Retorna diccionario de estilo para Label titulo"""
    colores = obtener_colores_tema()
    return {
        'bg': colores['bg'],
        'fg': colores['titulo_fg']
    }


def estilo_frame():
    """Retorna diccionario de estilo para Frame"""
    colores = obtener_colores_tema()
    return {
        'bg': colores['frame_bg']
    }
