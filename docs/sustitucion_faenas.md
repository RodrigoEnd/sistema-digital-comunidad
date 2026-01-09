# Sistema de Sustitución de Faenas

## Concepto General

El sistema permite que una persona contrate a alguien para realizar su faena comunitaria. Sin embargo, para evitar fraudes, se aplican diferentes reglas según quién realiza el trabajo.

## Tipos de Sustitución

### 1. Contratar a un Habitante del Pueblo

**Escenario:** Juan le paga a Pedro (ambos del pueblo) para que vaya en su lugar.

**Reglas:**
- **Ambos deben aparecer en la lista de participantes** (ambos deben asistir físicamente)
- **Juan (quien pagó):** Recibe el 90% del peso de la faena como penalización
- **Pedro (quien hizo el trabajo):** Recibe el 100% del peso de la faena
- **Objetivo:** Evitar que una persona simule varias asistencias. Al exigir que ambos estén presentes, se garantiza que hubo dos cuerpos trabajando.

**Ejemplo práctico:**
- Faena de peso 5
- Juan contrata a Pedro (habitante)
- Juan obtiene: 5 × 0.9 = 4.5 puntos
- Pedro obtiene: 5 × 1.0 = 5.0 puntos
- **Total de trabajo:** 2 personas presentes

### 2. Contratar a una Persona Externa

**Escenario:** Juan contrata a un albañil externo (no habitante del pueblo) para su faena.

**Reglas:**
- **Solo Juan aparece en la lista de participantes**
- **Juan (quien pagó):** Recibe el 100% del peso de la faena (sin penalización)
- **Trabajador externo:** Se registra su nombre como referencia, pero no obtiene puntos (no es habitante)
- **Objetivo:** El trabajo sí se completó (por el externo), así que Juan recibe el crédito completo

**Ejemplo práctico:**
- Faena de peso 5
- Juan contrata a José (externo/albañil)
- Juan obtiene: 5 × 1.0 = 5.0 puntos
- José: Se registra solo como referencia
- **Total de trabajo:** 1 persona presente (Juan supervisando/coordinando)

## Lógica Anti-Fraude

### ¿Por qué la penalización del 10% para habitantes?

Si Juan le paga a Pedro (ambos del pueblo) y ambos recibieran el 100%, podrían hacer trampa:
- Juan y Pedro hacen un acuerdo simulado
- En realidad solo trabaja 1 persona pero ambos se marcan presentes
- Se estaría contando doble el trabajo

**Solución:** 
- Penalización del 10% a quien paga → Desincentivar acuerdos ficticios
- Obligar a que ambos estén presentes → Garantizar que realmente hay 2 personas trabajando

### ¿Por qué sin penalización para externos?

Los externos no reciben puntos ni beneficios del sistema, así que:
- No hay incentivo para hacer trampas
- El trabajo realmente se hizo (por el externo)
- El habitante (quien contrató) merece el crédito completo por cumplir su obligación

## Interfaz del Sistema

### Flujo de Registro

1. **Seleccionar quien pagó:** Lista con checkbox para elegir al habitante que contrató
2. **Elegir tipo de sustitución:**
   - ☐ Habitante del pueblo → Se muestra lista para seleccionar quién trabajó
   - ☐ Persona externa → Se muestra campo de texto para escribir el nombre
3. **Validaciones:**
   - No se puede seleccionar la misma persona como pagador y trabajador
   - Si contrató a habitante, ambos deben estar en la lista
4. **Guardar:** Se actualizan automáticamente los puntos y la visualización

### Visualización en la Lista de Participantes

En la columna "Estado" se muestra:
- **"Asistió"** → Participación normal (100% peso)
- **"Contrató a [Nombre] (hab.)"** → Contrató a habitante (90% peso)
- **"Contrató a [Nombre] (ext.)"** → Contrató a externo (100% peso)

### Cálculo de Puntos Anuales

El resumen anual aplica automáticamente los multiplicadores:
- `peso_aplicado = 0.9` → Quien contrató a habitante
- `peso_aplicado = 1.0` → Asistencia normal o quien contrató a externo

**Ejemplo de tabla anual:**
```
Folio    Nombre    Puntos
H001     Juan      38.5  (incluye faenas con penalización)
H002     Pedro     45.0  (incluye faenas donde fue contratado)
```

## Estructura de Datos

### Participante con Sustitución a Habitante

```json
{
  "folio": "H001",
  "nombre": "Juan Pérez",
  "hora_registro": "2025-01-15T10:30:00",
  "sustitucion_tipo": "habitante",
  "trabajador_folio": "H002",
  "trabajador_nombre": "Pedro López",
  "peso_aplicado": 0.9
}
```

### Participante con Sustitución a Externo

```json
{
  "folio": "H001",
  "nombre": "Juan Pérez",
  "hora_registro": "2025-01-15T10:30:00",
  "sustitucion_tipo": "externo",
  "trabajador_nombre": "José Martínez (albañil)",
  "peso_aplicado": 1.0
}
```

### Trabajador Contratado (cuando es habitante)

```json
{
  "folio": "H002",
  "nombre": "Pedro López",
  "hora_registro": "2025-01-15T10:30:00",
  "peso_aplicado": 1.0
}
```

## Casos de Uso

### Caso 1: Habitante Contrata a Otro Habitante

```
Faena: Limpieza de calles (peso 5)
Juan (H001) contrata a Pedro (H002)

Resultado:
- Participantes: [Juan (H001), Pedro (H002)]
- Juan: 5 × 0.9 = 4.5 puntos
- Pedro: 5 × 1.0 = 5.0 puntos
- Estado Juan: "Contrató a Pedro López (hab.)"
- Estado Pedro: "Asistió"
```

### Caso 2: Habitante Contrata a Externo

```
Faena: Reparación de barda (peso 8)
María (H003) contrata a albañil externo

Resultado:
- Participantes: [María (H003)]
- María: 8 × 1.0 = 8.0 puntos
- Externo: Solo referencia, sin puntos
- Estado María: "Contrató a José Martínez (ext.)"
```

### Caso 3: Asistencia Normal

```
Faena: Poda de árboles (peso 6)
Carlos (H004) asiste personalmente

Resultado:
- Participantes: [Carlos (H004)]
- Carlos: 6 × 1.0 = 6.0 puntos
- Estado Carlos: "Asistió"
```

## Seguridad y Auditoría

- **Historial de cambios:** Cada sustitución se registra en el historial con detalles del tipo y participantes
- **Inmutabilidad:** Una vez registrada, la sustitución no puede modificarse (solo eliminarse y volver a crear)
- **Validación:** El sistema valida que no se seleccione la misma persona como pagador y trabajador
- **Transparencia:** Todos los habitantes pueden ver quién contrató a quién en el listado de participantes

## Ventajas del Sistema

1. **Flexibilidad:** Permite contratación legítima cuando alguien no puede asistir
2. **Anti-fraude:** La penalización del 10% desalienta simulaciones
3. **Equidad:** Quien realmente trabaja recibe el crédito completo
4. **Transparencia:** Todos pueden ver quién contrató a quién
5. **Trazabilidad:** Se mantiene registro histórico de todas las sustituciones
