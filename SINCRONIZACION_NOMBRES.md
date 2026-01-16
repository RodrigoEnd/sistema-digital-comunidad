# Sincronización de Edición de Nombres entre Censo y Pagos

## Fecha: 16 de enero de 2026

### Problema Identificado

Cuando se editaba el nombre de una persona desde el módulo de **Control de Pagos**, el cambio **NO se sincronizaba** con el **Censo**. Esto causaba inconsistencias porque ambos módulos deberían usar el mismo **folio** como identificador único.

### Solución Implementada

Se implementó un sistema de **sincronización bidireccional** que garantiza que los cambios de nombre se reflejen en ambos módulos y en la base de datos central.

---

## Cambios Realizados

### 1. **Módulo de Censo** ✅

#### Nuevas Funcionalidades:

**a) Nueva función `editar_nombre_habitante` en censo_operaciones.py**
- Actualiza el nombre del habitante en la base de datos
- Valida que el nombre tenga al menos 3 caracteres
- Registra la operación en el log
- Ejecuta callback de actualización

**b) Nuevo diálogo `dialogo_editar_nombre` en censo_dialogos.py**
- Interfaz para editar el nombre del habitante
- Muestra folio y nombre actual
- Validación y confirmación de cambios

**c) Nuevo botón "Editar Nombre" en el panel de detalles**
- Acceso rápido desde el panel lateral
- Ubicado junto a "Editar Nota"

**d) Nueva opción en menú contextual**
- "✏️ Editar Nombre" al hacer clic derecho en la tabla
- Ubicado al inicio del menú contextual

**e) Método `_editar_nombre_seleccion` en censo_habitantes.py**
- Maneja la edición desde el menú contextual o atajos

---

### 2. **Módulo de Pagos** ✅

#### Modificaciones:

**a) Actualizado `DialogoEditarPersona.mostrar` en pagos_dialogos.py**
- Nuevo parámetro opcional: `gestor_global`
- Al guardar cambios de nombre, sincroniza con la BD de habitantes
- Sincroniza también las notas (campo 'nota' en BD)
- Logs informativos de sincronización

**b) Modificado `editar_persona` en control_pagos.py**
- Pasa `self.gestor` (gestor global) al diálogo
- Garantiza que los cambios se propaguen a la BD central

**c) Actualizado `editar_persona` en pagos_gestor_personas.py**
- Nuevo parámetro opcional: `gestor_global`
- Sincroniza cambios de nombre y notas con la BD central
- Manejo de errores en la sincronización

---

## Flujo de Sincronización

### Desde Censo → Base de Datos
```
1. Usuario edita nombre en Censo
2. censo_operaciones.editar_nombre_habitante()
3. gestor.actualizar_habitante(folio, nombre=nuevo_nombre)
4. BD actualizada
5. Censo recarga y muestra el cambio
```

### Desde Pagos → Base de Datos → Censo
```
1. Usuario edita nombre en Pagos
2. DialogoEditarPersona guarda cambio local
3. Sincroniza con gestor_global.actualizar_habitante()
4. BD actualizada
5. Al recargar Censo, muestra el nuevo nombre
```

---

## Campos Sincronizados

| Campo en Pagos | Campo en BD Habitantes | Dirección |
|----------------|------------------------|-----------|
| `nombre` | `nombre` | ✅ Bidireccional |
| `notas` | `nota` | ✅ Bidireccional |
| `folio` | `folio` | ❌ Inmutable (clave única) |

---

## Características Implementadas

### En Censo:
✅ Editar nombre desde panel de detalles
✅ Editar nombre desde menú contextual (clic derecho)
✅ Validación de longitud mínima (3 caracteres)
✅ Confirmación visual del cambio
✅ Recarga automática de la tabla

### En Pagos:
✅ Sincronización automática al editar
✅ Logs informativos en consola
✅ Manejo de errores de sincronización
✅ No requiere cambios en la interfaz existente

---

## Uso

### Para editar nombre en Censo:

**Opción 1: Panel de Detalles**
1. Seleccionar habitante en la tabla
2. En el panel derecho, clic en "Editar Nombre"
3. Modificar el nombre
4. Clic en "Guardar"

**Opción 2: Menú Contextual**
1. Clic derecho sobre el habitante en la tabla
2. Seleccionar "✏️ Editar Nombre"
3. Modificar el nombre
4. Clic en "Guardar"

### Para editar nombre en Pagos:

1. Seleccionar persona en la tabla
2. Clic en botón "Editar Persona" (o Ctrl+E)
3. Modificar el nombre
4. Clic en "Guardar Cambios"
5. **El cambio se sincroniza automáticamente con Censo**

---

## Archivos Modificados

### Censo:
1. `src/modules/censo/censo_operaciones.py` - Nueva función
2. `src/modules/censo/censo_dialogos.py` - Nuevo diálogo
3. `src/modules/censo/censo_habitantes.py` - Menú y métodos
4. `src/modules/censo/censo_panel_detalles.py` - Botón editar

### Pagos:
5. `src/modules/pagos/pagos_dialogos.py` - Sincronización
6. `src/modules/pagos/control_pagos.py` - Pasar gestor
7. `src/modules/pagos/pagos_gestor_personas.py` - Método actualizado

---

## Pruebas Recomendadas

1. ✅ Editar nombre desde Censo → verificar en Pagos
2. ✅ Editar nombre desde Pagos → verificar en Censo
3. ✅ Validación de nombre muy corto
4. ✅ Sincronización con múltiples habitantes
5. ✅ Manejo de errores si BD no disponible

---

## Beneficios

✅ **Consistencia de datos** entre módulos
✅ **Folio como identificador único e inmutable**
✅ **Sincronización automática** sin intervención del usuario
✅ **Manejo robusto de errores**
✅ **Experiencia de usuario mejorada**

---

**Nota Importante**: El **folio es inmutable** y sirve como clave única. Aunque los nombres cambien, el folio garantiza que siempre se referencia al mismo habitante en ambos módulos.
