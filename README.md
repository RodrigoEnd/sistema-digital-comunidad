# Sistema de Control de Pagos - Proyectos Comunitarios

## 📋 Descripción
Sistema interactivo para el control de pagos y cooperaciones de proyectos del pueblo.

## ✨ Características
- ✅ Tabla interactiva en pantalla completa
- ✅ Monto de cooperación ajustable
- ✅ Agregar, editar y eliminar personas
- ✅ Marcar pagos realizados
- ✅ Apartado oculto con suma total de recaudación
- ✅ Guardado automático de datos en JSON
- ✅ Colores visuales: verde para pagados, naranja para pendientes

## 🚀 Cómo Ejecutar

### Opción 1: Ejecutar directamente con Python
```bash
cd src
python control_pagos.py
```

### Opción 2: Crear archivo .exe
```bash
# Instalar PyInstaller
pip install pyinstaller

# Crear el ejecutable
pyinstaller --onefile --windowed --name="ControlPagos" src/control_pagos.py
```

El archivo .exe se creará en la carpeta `dist/`

## 📖 Uso del Sistema

1. **Agregar Persona**: Clic en "➕ Agregar Persona"
2. **Editar**: Selecciona una fila y clic en "✏️ Editar Seleccionado"
3. **Marcar Pago**: Selecciona una fila y clic en "✅ Marcar como Pagado"
4. **Ver Total**: Clic en "👁️ Mostrar Total Recaudado" (se puede ocultar)
5. **Guardar**: Clic en "💾 Guardar Datos"

## 💾 Almacenamiento
Los datos se guardan en `datos_pagos.json` en la misma carpeta del programa.
