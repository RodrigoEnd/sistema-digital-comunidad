# Análisis y Corrección de Arquitectura del Sistema

## Fecha: 16 de enero de 2026

## ❌ PROBLEMA IDENTIFICADO

### Arquitectura Híbrida Problemática

El sistema tenía una **arquitectura dividida** que causaba desincronización:

```
┌─────────────┐              ┌──────────────┐
│   CENSO     │              │    PAGOS     │
│             │              │              │
│  SQLite BD  │              │  JSON File   │
│ (habitantes)│              │ (cooperaciones)│
└─────────────┘              └──────────────┘
       ↓                            ↓
   FOLIO común                  FOLIO común
   (único vínculo)
```

**Consecuencias:**
- Editas nombre en Pagos → Solo cambia JSON
- Censo sigue mostrando nombre antiguo
- No hay sincronización automática
- Datos inconsistentes entre módulos

---

## ✅ SOLUCIÓN IMPLEMENTADA

### 1. Sincronización Bidireccional Real

#### A) Al Editar en Pagos → Actualiza BD:
```python
# En pagos_dialogos.py (línea ~440)
if cambios and gestor_global:
    cambios_bd = {}
    if 'nombre' in cambios:
        cambios_bd['nombre'] = nombre
    if 'notas' in cambios:
        cambios_bd['nota'] = notas_entry.get().strip()
    
    gestor_global.actualizar_habitante(folio, **cambios_bd)
```

#### B) Al Editar en Censo → Actualiza BD:
```python
# En censo_operaciones.py
def editar_nombre_habitante(folio, nuevo_nombre, gestor, callback_exito):
    exito, mensaje = gestor.actualizar_habitante(folio, nombre=nuevo_nombre.strip())
    if exito:
        callback_exito()
```

#### C) Al Cargar Pagos → Sincroniza desde BD:
```python
# En control_pagos.py (nuevo método)
def _sincronizar_nombres_desde_bd(self):
    """Sincroniza nombres al cargar cooperación"""
    for persona in self.personas:
        folio = persona.get('folio', '')
        if folio:
            habitante = self.gestor.obtener_habitante_por_folio(folio)
            if habitante and habitante['nombre'] != persona['nombre']:
                persona['nombre'] = habitante['nombre']
```

#### D) Después de Editar → Recarga desde BD:
```python
# En control_pagos.py
def on_persona_editada(persona, cambios):
    if cambios and 'nombre' in cambios:
        # Obtener nombre actualizado desde BD
        habitante = self.gestor.obtener_habitante_por_folio(folio)
        if habitante:
            persona['nombre'] = habitante['nombre']
```

---

## 📋 ARQUITECTURA CORREGIDA

```
┌─────────────────────────────────────────┐
│        GESTOR DATOS GLOBAL              │
│         (Singleton Thread-Safe)         │
└─────────────────┬───────────────────────┘
                  │
         ┌────────┴────────┐
         │                 │
         ↓                 ↓
    ┌────────┐      ┌──────────┐
    │ SQLite │      │   JSON   │
    │   BD   │      │  (Pagos) │
    └────────┘      └──────────┘
         ↑                 ↑
         │                 │
         │     FOLIO       │
         │   (inmutable)   │
         │                 │
    ┌────┴────┐      ┌────┴────┐
    │  CENSO  │      │  PAGOS  │
    └─────────┘      └─────────┘
         ↑                 ↑
         └────── ✅ ───────┘
        Sincronización
       Bidireccional
```

---

## 🔧 CAMBIOS REALIZADOS

### Archivos Modificados:

1. **`src/core/base_datos.py`**
   - ✅ Corregido `actualizar_habitante` para aceptar `**kwargs`

2. **`src/modules/pagos/pagos_dialogos.py`**
   - ✅ Agregado parámetro `gestor_global`
   - ✅ Sincronización con BD al guardar

3. **`src/modules/pagos/control_pagos.py`**
   - ✅ Pasa `gestor_global` al diálogo
   - ✅ Nuevo método `_sincronizar_nombres_desde_bd()`
   - ✅ Sincronización al cargar cooperación
   - ✅ Sincronización después de editar

4. **`src/modules/censo/censo_operaciones.py`**
   - ✅ Nueva función `editar_nombre_habitante()`

5. **`src/modules/censo/censo_dialogos.py`**
   - ✅ Nuevo diálogo `dialogo_editar_nombre()`

6. **`src/modules/censo/censo_habitantes.py`**
   - ✅ Botón "Editar Nombre"
   - ✅ Opción en menú contextual

7. **`src/modules/censo/censo_panel_detalles.py`**
   - ✅ Botón "Editar Nombre" en panel

---

## 🔄 FLUJO DE SINCRONIZACIÓN

### Escenario 1: Editar en Pagos

```
Usuario → Pagos: Editar nombre
         ↓
DialogoEditarPersona.guardar()
         ↓
gestor_global.actualizar_habitante(folio, nombre=nuevo)
         ↓
SQLite BD actualizada
         ↓
on_persona_editada() → Recarga desde BD
         ↓
persona['nombre'] = habitante['nombre'] (desde BD)
         ↓
Tabla actualizada con nombre de BD
```

### Escenario 2: Editar en Censo

```
Usuario → Censo: Editar nombre
         ↓
dialogo_editar_nombre()
         ↓
editar_nombre_habitante()
         ↓
gestor.actualizar_habitante(folio, nombre=nuevo)
         ↓
SQLite BD actualizada
         ↓
Censo recarga tabla
```

### Escenario 3: Abrir Pagos (Sincronización Automática)

```
Pagos iniciando...
         ↓
aplicar_cooperacion_activa()
         ↓
_sincronizar_nombres_desde_bd()
         ↓
Para cada persona:
   habitante = gestor.obtener_habitante_por_folio(folio)
   persona['nombre'] = habitante['nombre']
         ↓
Todos los nombres sincronizados con BD
```

---

## 🎯 RESULTADO FINAL

### Antes:
- ❌ Editar en Pagos → Censo desactualizado
- ❌ Editar en Censo → No existía la opción
- ❌ Datos inconsistentes
- ❌ Confusión para el usuario

### Ahora:
- ✅ Editar en cualquier módulo → Se refleja en ambos
- ✅ Sincronización automática al cargar
- ✅ BD SQLite como fuente de verdad
- ✅ JSON de Pagos se sincroniza automáticamente
- ✅ Experiencia consistente

---

## 📝 IMPORTANTE: Fuente de Verdad

```
SQLite BD (habitantes)
         ↓
   FUENTE DE VERDAD
   para nombres
         ↓
JSON (pagos) se sincroniza
automáticamente desde BD
```

**El folio es inmutable y vincula ambos sistemas.**
**El nombre puede cambiar pero siempre se sincroniza con la BD.**

---

## 🧪 PRUEBAS REALIZADAS

1. ✅ Editar nombre en Pagos → Verificar en Censo
2. ✅ Editar nombre en Censo → Verificar en Pagos
3. ✅ Cerrar y reabrir Pagos → Nombres sincronizados
4. ✅ Múltiples ediciones → Consistencia mantenida

---

## 🔍 CÓDIGO NO DUPLICADO

Se verificó que **NO existen funciones duplicadas**:
- `actualizar_habitante` existe en 3 lugares pero con roles diferentes:
  - `base_datos_sqlite.py`: Actualiza SQLite directamente
  - `base_datos.py`: Wrapper de compatibilidad
  - `gestor_datos_global.py`: Interfaz pública con caché
  
Esta es una arquitectura en **capas**, no código duplicado.

---

## 💡 RECOMENDACIONES FUTURAS

1. **Migrar Pagos a SQLite**
   - Eliminar JSON de cooperaciones
   - Todo en una sola BD
   - Sincronización nativa

2. **Triggers en BD**
   - Sincronización automática a nivel de BD
   - Mayor integridad

3. **Cache Compartido**
   - Gestor global mantiene caché único
   - Ambos módulos usan mismo caché

---

**Estado: ✅ CORREGIDO Y FUNCIONAL**
