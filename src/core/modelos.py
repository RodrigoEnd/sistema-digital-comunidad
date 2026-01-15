"""
Modelos de datos principales del sistema.
Usar dataclasses para validación y tipo seguro.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Habitante:
    """Modelo para habitantes del censo."""
    nombre: str
    folio: str
    telefono: str = ""
    direccion: str = ""
    fecha_registro: str = field(default_factory=lambda: datetime.now().strftime("%d/%m/%Y"))
    notas: str = ""
    activo: bool = True

    def to_dict(self) -> dict:
        """Convierte a diccionario para persistencia."""
        return {
            'nombre': self.nombre,
            'folio': self.folio,
            'telefono': self.telefono,
            'direccion': self.direccion,
            'fecha_registro': self.fecha_registro,
            'notas': self.notas,
            'activo': self.activo
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Habitante':
        """Crea instancia desde diccionario."""
        return cls(
            nombre=data.get('nombre', ''),
            folio=data.get('folio', ''),
            telefono=data.get('telefono', ''),
            direccion=data.get('direccion', ''),
            fecha_registro=data.get('fecha_registro', datetime.now().strftime("%d/%m/%Y")),
            notas=data.get('notas', ''),
            activo=data.get('activo', True)
        )


@dataclass
class Pago:
    """Modelo para pagos individuales."""
    monto: float
    fecha: str
    metodo: str = "efectivo"
    referencia: str = ""
    notas: str = ""

    def to_dict(self) -> dict:
        return {
            'monto': self.monto,
            'fecha': self.fecha,
            'metodo': self.metodo,
            'referencia': self.referencia,
            'notas': self.notas
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Pago':
        return cls(
            monto=data.get('monto', 0.0),
            fecha=data.get('fecha', ''),
            metodo=data.get('metodo', 'efectivo'),
            referencia=data.get('referencia', ''),
            notas=data.get('notas', '')
        )


@dataclass
class PersonaCooperacion:
    """Modelo para persona en cooperación con historial de pagos."""
    nombre: str
    folio: str
    monto_esperado: float
    pagos: List[Pago] = field(default_factory=list)
    notas: str = ""

    @property
    def total_pagado(self) -> float:
        """Calcula total pagado."""
        return sum(p.monto for p in self.pagos)

    @property
    def pendiente(self) -> float:
        """Calcula monto pendiente."""
        return max(0, self.monto_esperado - self.total_pagado)

    @property
    def completado(self) -> bool:
        """Verifica si completó el pago."""
        return self.total_pagado >= self.monto_esperado

    def to_dict(self) -> dict:
        return {
            'nombre': self.nombre,
            'folio': self.folio,
            'monto_esperado': self.monto_esperado,
            'pagos': [p.to_dict() for p in self.pagos],
            'notas': self.notas
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PersonaCooperacion':
        return cls(
            nombre=data.get('nombre', ''),
            folio=data.get('folio', ''),
            monto_esperado=data.get('monto_esperado', 0.0),
            pagos=[Pago.from_dict(p) for p in data.get('pagos', [])],
            notas=data.get('notas', '')
        )


@dataclass
class Cooperacion:
    """Modelo para cooperaciones/proyectos."""
    id: str
    nombre: str
    proyecto: str
    monto_cooperacion: float
    personas: List[PersonaCooperacion] = field(default_factory=list)
    fecha_creacion: str = field(default_factory=lambda: datetime.now().strftime("%d/%m/%Y"))
    activa: bool = True

    @property
    def total_esperado(self) -> float:
        """Total esperado de todos los participantes."""
        return sum(p.monto_esperado for p in self.personas)

    @property
    def total_recaudado(self) -> float:
        """Total recaudado hasta el momento."""
        return sum(p.total_pagado for p in self.personas)

    @property
    def personas_completadas(self) -> int:
        """Cantidad de personas que completaron su pago."""
        return sum(1 for p in self.personas if p.completado)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'nombre': self.nombre,
            'proyecto': self.proyecto,
            'monto_cooperacion': self.monto_cooperacion,
            'personas': [p.to_dict() for p in self.personas],
            'fecha_creacion': self.fecha_creacion,
            'activa': self.activa
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Cooperacion':
        return cls(
            id=data.get('id', ''),
            nombre=data.get('nombre', ''),
            proyecto=data.get('proyecto', ''),
            monto_cooperacion=data.get('monto_cooperacion', 0.0),
            personas=[PersonaCooperacion.from_dict(p) for p in data.get('personas', [])],
            fecha_creacion=data.get('fecha_creacion', datetime.now().strftime("%d/%m/%Y")),
            activa=data.get('activa', True)
        )


@dataclass
class Participacion:
    """Modelo para participación en faena."""
    folio: str
    nombre: str
    presente: bool = True
    peso_aplicado: float = 1.0
    observaciones: str = ""

    def to_dict(self) -> dict:
        return {
            'folio': self.folio,
            'nombre': self.nombre,
            'presente': self.presente,
            'peso_aplicado': self.peso_aplicado,
            'observaciones': self.observaciones
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Participacion':
        return cls(
            folio=data.get('folio', ''),
            nombre=data.get('nombre', ''),
            presente=data.get('presente', True),
            peso_aplicado=data.get('peso_aplicado', 1.0),
            observaciones=data.get('observaciones', '')
        )


@dataclass
class Faena:
    """Modelo para registro de faena."""
    id: str
    fecha: str
    descripcion: str
    tipo: str = "faena_general"
    participantes: List[Participacion] = field(default_factory=list)
    puntos_base: float = 1.0
    notas: str = ""

    @property
    def total_participantes(self) -> int:
        """Total de participantes presentes."""
        return sum(1 for p in self.participantes if p.presente)

    @property
    def total_puntos(self) -> float:
        """Total de puntos asignados (considerando pesos)."""
        return sum(p.peso_aplicado * self.puntos_base for p in self.participantes if p.presente)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'fecha': self.fecha,
            'descripcion': self.descripcion,
            'tipo': self.tipo,
            'participantes': [p.to_dict() for p in self.participantes],
            'puntos_base': self.puntos_base,
            'notas': self.notas
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Faena':
        return cls(
            id=data.get('id', ''),
            fecha=data.get('fecha', ''),
            descripcion=data.get('descripcion', ''),
            tipo=data.get('tipo', 'faena_general'),
            participantes=[Participacion.from_dict(p) for p in data.get('participantes', [])],
            puntos_base=data.get('puntos_base', 1.0),
            notas=data.get('notas', '')
        )
