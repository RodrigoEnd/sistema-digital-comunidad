# Sistema de Anulación de Pagos

## Descripción
Se ha implementado un sistema de anulación de pagos con autenticación por contraseña para corregir errores en el registro de pagos.

## Características

### 1. Autenticación Requerida
- **Contraseña obligatoria**: Para anular un pago, el usuario debe ingresar su contraseña
- **Validación en tiempo real**: El sistema verifica la contraseña contra la base de datos
- **Registro de intentos**: Los intentos fallidos quedan registrados en el log del sistema

### 2. Interfaz de Usuario
- **Menú contextual**: Opción "⚠️ Anular pago" en el menú de clic derecho sobre una persona
- **Diálogo intuitivo**: Muestra todos los pagos de la persona en una tabla
- **Identificación visual**: Los pagos ya anulados aparecen en gris y con la marca [ANULADO]

### 3. Proceso de Anulación

#### Pasos:
1. Clic derecho sobre una persona en la tabla
2. Seleccionar "⚠️ Anular pago"
3. Seleccionar el pago a anular de la lista
4. Ingresar contraseña del usuario actual
5. Confirmar la acción

#### Validaciones:
- ✓ Verifica que haya pagos registrados
- ✓ Impide anular un pago ya anulado
- ✓ Requiere contraseña válida
- ✓ Solicita confirmación final

### 4. Registro y Auditoría
Cada anulación registra:
- **Fecha y hora de anulación**
- **Usuario que anuló el pago**
- **Monto anulado**
- **Totales antes y después**
- **Entrada en historial de auditoría**
- **Entrada en log del sistema**

### 5. Comportamiento del Sistema

#### Pagos Anulados:
- **No se eliminan**: Los pagos permanecen en el historial
- **Marcados como anulados**: Campo `anulado: true`
- **Excluidos de totales**: No cuentan en cálculos de pagado/pendiente
- **Visibles en historial**: Aparecen con indicador "❌ ANULADO"

#### Impacto en Cálculos:
- **Total pagado**: Solo suma pagos válidos
- **Pendiente**: Se recalcula automáticamente
- **Estado de persona**: Se actualiza (puede volver a "Pendiente" o "Parcial")
- **Totales generales**: Se actualizan en tiempo real

### 6. Seguridad

#### Protecciones:
- 🔒 Autenticación por contraseña obligatoria
- 📝 Trazabilidad completa en historial
- ⚠️ Advertencias claras al usuario
- 🔍 Registro de intentos fallidos
- ✅ Confirmación doble (contraseña + diálogo)

#### Permisos:
- Requiere permiso de **"pagar"** (mismo que registrar pagos)
- Solo usuarios autenticados pueden anular pagos
- Las anulaciones quedan vinculadas al usuario que las realizó

## Ubicación en el Código

### Archivos Modificados:

1. **`src/modules/pagos/pagos_dialogos.py`**
   - Clase `DialogoAnularPago`: Diálogo completo de anulación
   - Actualización de `DialogoVerHistorial`: Muestra pagos anulados

2. **`src/modules/pagos/control_pagos.py`**
   - Función `anular_pago()`: Lógica principal
   - Función `animar_fila_anulada()`: Feedback visual
   - Actualización de menú contextual
   - Actualización de cálculos de totales (5 funciones)

### Funciones Actualizadas para Excluir Pagos Anulados:
- `actualizar_tabla()`
- `actualizar_totales()`
- `_ordenar_tabla_por_columna()`
- `eliminar_persona()`
- `animar_fila_pagada()`

## Casos de Uso

### Escenario 1: Error en el Monto
```
Situación: Se registró $500 pero debía ser $50
Solución: 
1. Anular el pago de $500
2. Registrar nuevo pago de $50
```

### Escenario 2: Pago Duplicado
```
Situación: Se registró dos veces el mismo pago
Solución:
1. Identificar el pago duplicado
2. Anular uno de los registros
```

### Escenario 3: Pago a Persona Incorrecta
```
Situación: Se asignó pago a Juan pero era de Pedro
Solución:
1. Anular pago en el registro de Juan
2. Registrar pago correcto en Pedro
```

## Consideraciones Importantes

### ⚠️ Advertencias:
- Los pagos anulados **no se pueden reactivar**
- La anulación queda **permanentemente registrada**
- No afecta al historial de auditoría (solo añade entrada)

### 💡 Buenas Prácticas:
- Revisar dos veces antes de anular
- Usar la función de "Ver historial" para confirmar
- Documentar el motivo en las notas de la persona
- Verificar los totales después de la anulación

## Ejemplo de Registro en Historial

```json
{
  "operacion": "ANULACION_PAGO",
  "tipo": "PERSONA",
  "identificador": "FOL-0019",
  "cambios": {
    "monto_anulado": 100.00,
    "fecha_pago": "16/01/2026",
    "total_anterior": 100.00,
    "total_nuevo": 0.00,
    "nombre": "Moiser García",
    "razon": "Anulación por error"
  },
  "usuario": "admin",
  "timestamp": "16/01/2026 15:30:45"
}
```

## Pruebas Recomendadas

1. **Anular un pago válido**: Verificar que se excluya de totales
2. **Intentar anular con contraseña incorrecta**: Debe rechazar
3. **Ver historial después de anular**: Debe mostrar marca de anulado
4. **Intentar anular un pago ya anulado**: Debe informar y rechazar
5. **Verificar totales generales**: Deben actualizarse correctamente

---

**Fecha de Implementación**: 16/01/2026
**Versión**: 1.0
