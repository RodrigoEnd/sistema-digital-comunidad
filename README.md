# Sistema de Control de Pagos - Proyectos Comunitarios

## Descripción
Sistema interactivo seguro para el control de pagos y cooperaciones de proyectos del pueblo con cifrado de datos y ubicación protegida.

## Características de Seguridad
- Cifrado AES-256 de todos los archivos
- Contraseñas hasheadas con bcrypt (12 rounds)
- Datos almacenados en ubicación segura (AppData oculto)
- Verificación de integridad con HMAC
- Archivos no editables externamente
- Protección contra manipulación

## Características del Sistema
- Tabla interactiva en pantalla completa
- Monto de cooperación ajustable
- Agregar, editar y eliminar personas
- Marcar pagos realizados
- Apartado oculto con suma total de recaudación
- Guardado automático cifrado
- Colores visuales: verde para pagados, naranja para pendientes
- Sincronización con censo de habitantes

## Cómo Ejecutar

### Primera vez - Instalación
```bash
pip install -r requirements.txt
```

### Ejecutar el Sistema
```bash
# Opción 1: Ejecutar desde el punto de entrada principal (recomendado)
python main.py

# Opción 2: Script automático PowerShell
./iniciar.ps1

# Opción 3: Manual (solo censo)
cd src
python censo_habitantes.py
```

El punto de entrada `main.py` iniciará automáticamente:
1. Servidor API (si no está corriendo)
2. Sistema de Censo de Habitantes (interfaz principal)

### Crear archivo .exe
```bash
# Instalar PyInstaller
pip install pyinstaller

# Crear el ejecutable principal
pyinstaller --onefile --windowed --name="SistemaComunidad" main.py
```

El archivo .exe se creará en la carpeta `dist/`

## Uso del Sistema

1. **Agregar Persona**: Clic en "Agregar Persona"
2. **Editar**: Selecciona una fila y clic en "Editar Seleccionado"
3. **Marcar Pago**: Selecciona una fila y clic en "Marcar como Pagado"
4. **Ver Total**: Clic en "Mostrar Total Recaudado" (se puede ocultar)
5. **Guardar**: Clic en "Guardar Datos"
6. **Abrir Control de Pagos**: Botón en el censo para gestión financiera

## Almacenamiento Seguro

Los datos se guardan cifrados en:
```
C:\Users\[TuUsuario]\AppData\Local\SistemaComunidad\
```

Archivos protegidos:
- `base_datos_habitantes.json` (cifrado)
- `datos_pagos.json` (cifrado)

La carpeta y archivos están ocultos y solo accesibles mediante el sistema.

## Primera Ejecución

Al iniciar por primera vez:
1. El sistema creará 10 habitantes de muestra
2. Se solicitará establecer una contraseña maestra
3. Los archivos se guardarán cifrados automáticamente

## Estructura del Proyecto

```
sistema-digital-comunidad/
├── main.py                    # Punto de entrada principal
├── src/
│   ├── api_local.py          # Servidor API REST
│   ├── base_datos.py         # Gestión de base de datos
│   ├── censo_habitantes.py   # Sistema de censo
│   ├── control_pagos.py      # Control de pagos
│   └── seguridad.py          # Módulo de seguridad
├── requirements.txt          # Dependencias
└── README.md                # Este archivo
```
