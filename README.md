# Sistema Digital de Gestión Comunitaria

## Descripción
Sistema integral para la gestión comunitaria incluyendo censo de habitantes, control de pagos y registro de faenas con seguridad, auditoría y cifrado de datos.

## Módulos Principales
- **Censo de Habitantes** - Registro y gestión de datos comunitarios
- **Control de Pagos** - Administración de pagos y cooperaciones
- **Registro de Faenas** - Seguimiento de trabajo comunitario

## Características
- ✅ Autenticación con usuario y contraseña
- ✅ Cifrado AES-256 de datos sensibles
- ✅ Auditoría completa de todas las operaciones
- ✅ Historial de cambios con usuario y timestamp
- ✅ Guardado automático en tiempo real
- ✅ Interfaz moderna y responsiva
- ✅ Backups automáticos

## Instalación Rápida

### Requisitos
- Python 3.13+

### Pasos
```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Ejecutar el sistema
python main.py
```

El sistema abrirá un menú con las opciones disponibles.

## Uso

1. **Censo** - Gestionar habitantes de la comunidad
2. **Pagos** - Administrar pagos y cooperaciones
3. **Faenas** - Registrar trabajo comunitario

## Almacenamiento de Datos

Los datos se guardan cifrados en:
```
C:\Users\[usuario]\AppData\Local\SistemaComunidad\
```

Protección:
- Cifrado AES-256
- Contraseñas hasheadas con bcrypt
- Archivos ocultos
- Auditoría de cambios

## Estructura del Proyecto

```
src/
├── auth/              # Autenticación y seguridad
├── core/              # Funciones core (BD, logger, validadores)
├── modules/
│   ├── censo/        # Censo de habitantes
│   ├── pagos/        # Control de pagos
│   ├── faenas/       # Registro de faenas
│   └── historial/    # Auditoría y cambios
├── tools/             # Backups y exportación
├── ui/                # Componentes de interfaz
└── config.py          # Configuración global
```

## Licencia
Uso comunitario
