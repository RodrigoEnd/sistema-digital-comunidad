# DOCUMENTACION DE API LOCAL

## Informacion General

- **URL Base**: http://127.0.0.1:5000/api
- **Puerto**: 5000
- **Host**: 127.0.0.1
- **Formato**: JSON (application/json)
- **CORS**: Habilitado para comunicacion local

## Tabla de Endpoints

| Metodo | Endpoint | Descripcion | Estado |
|--------|----------|-------------|--------|
| GET | /habitantes | Obtener todos los habitantes | Activo |
| GET | /habitantes/buscar | Buscar habitantes por criterio | Activo |
| GET | /habitantes/nombre/<nombre> | Obtener habitante por nombre | Activo |
| POST | /habitantes | Agregar nuevo habitante | Activo |
| PATCH | /habitantes/<folio> | Actualizar habitante | Activo |
| GET | /folio/siguiente | Obtener siguiente folio | Activo |
| POST | /sync/verificar | Verificar/crear habitante | Activo |
| GET | /ping | Estado de API | Activo |

---

## HABITANTES

### 1. Obtener Todos los Habitantes

```
GET /api/habitantes
```

**Descripcion**: Retorna la lista completa de todos los habitantes registrados.

**Parametros**: Ninguno

**Respuesta Exitosa** (200):
```json
{
  "success": true,
  "habitantes": [
    {
      "folio": "HAB-0001",
      "nombre": "Juan Perez",
      "fecha_registro": "13/01/2026",
      "activo": true,
      "nota": ""
    }
  ],
  "total": 1
}
```

**Respuesta Error** (500):
```json
{
  "success": false,
  "error": "Error al obtener habitantes"
}
```

**Casos de Uso**:
- Cargar lista inicial en interfaz
- Actualizar tabla de habitantes
- Exportar datos

---

### 2. Buscar Habitantes

```
GET /api/habitantes/buscar?q=<criterio>
```

**Descripcion**: Busca habitantes que coincidan con el criterio especificado.

**Parametros**:
- `q` (string, requerido): Criterio de busqueda (nombre, folio, etc)

**Ejemplo**:
```
GET /api/habitantes/buscar?q=Juan
```

**Respuesta Exitosa** (200):
```json
{
  "success": true,
  "resultados": [
    {
      "folio": "HAB-0001",
      "nombre": "Juan Perez",
      "fecha_registro": "13/01/2026",
      "activo": true,
      "nota": ""
    },
    {
      "folio": "HAB-0005",
      "nombre": "Juanita Lopez",
      "fecha_registro": "13/01/2026",
      "activo": true,
      "nota": ""
    }
  ],
  "total": 2
}
```

**Casos de Uso**:
- Busqueda en tiempo real
- Autocompletado de nombres
- Filtrado dinamico

---

### 3. Obtener Habitante por Nombre

```
GET /api/habitantes/nombre/<nombre>
```

**Descripcion**: Obtiene un habitante especifico por su nombre exacto.

**Parametros**:
- `nombre` (string, URL path, requerido): Nombre exacto del habitante

**Ejemplo**:
```
GET /api/habitantes/nombre/Juan%20Perez
```

**Respuesta Exitosa** (200):
```json
{
  "success": true,
  "habitante": {
    "folio": "HAB-0001",
    "nombre": "Juan Perez",
    "fecha_registro": "13/01/2026",
    "activo": true,
    "nota": "Notas importantes"
  }
}
```

**Respuesta Error** (404):
```json
{
  "success": false,
  "mensaje": "Habitante no encontrado"
}
```

**Casos de Uso**:
- Verificar existencia de habitante
- Cargar datos de habitante especifico
- Validacion de entrada

---

### 4. Agregar Nuevo Habitante

```
POST /api/habitantes
Content-Type: application/json
```

**Descripcion**: Crea un nuevo habitante en el censo con folio automatico.

**Parametros** (body JSON):
- `nombre` (string, requerido): Nombre del habitante

**Ejemplo Request**:
```json
{
  "nombre": "Maria Gonzalez"
}
```

**Respuesta Exitosa** (200):
```json
{
  "success": true,
  "mensaje": "Habitante agregado correctamente",
  "habitante": {
    "folio": "HAB-0002",
    "nombre": "Maria Gonzalez",
    "fecha_registro": "13/01/2026",
    "activo": true,
    "nota": ""
  }
}
```

**Respuesta Error** (400):
```json
{
  "success": false,
  "mensaje": "El nombre es obligatorio"
}
```

**Validaciones**:
- Nombre no puede estar vacio
- Nombre debe tener al menos 3 caracteres
- Nombre no puede exceder 100 caracteres

**Casos de Uso**:
- Registro de nuevo habitante
- Censo inicial
- Integracion con otras aplicaciones

---

### 5. Actualizar Habitante

```
PATCH /api/habitantes/<folio>
Content-Type: application/json
```

**Descripcion**: Actualiza informacion de un habitante existente.

**Parametros**:
- `folio` (string, URL path, requerido): Folio del habitante (ej: HAB-0001)

**Body JSON** (opcional):
- `activo` (boolean): Estado activo/inactivo
- `nota` (string): Notas sobre el habitante

**Ejemplo Request**:
```json
{
  "activo": false,
  "nota": "Se mudo a otro lugar"
}
```

**Respuesta Exitosa** (200):
```json
{
  "success": true,
  "habitante": {
    "folio": "HAB-0001",
    "nombre": "Juan Perez",
    "fecha_registro": "13/01/2026",
    "activo": false,
    "nota": "Se mudo a otro lugar"
  }
}
```

**Respuesta Error** (404):
```json
{
  "success": false,
  "mensaje": "Habitante no encontrado"
}
```

**Casos de Uso**:
- Cambiar estado de habitante
- Actualizar notas
- Marcar como inactivo

---

## FOLIOS

### 6. Obtener Siguiente Folio

```
GET /api/folio/siguiente
```

**Descripcion**: Obtiene el proximo folio disponible sin crear un habitante.
Util para mostrar el folio que se asignara en el formulario.

**Parametros**: Ninguno

**Respuesta Exitosa** (200):
```json
{
  "success": true,
  "folio": "HAB-0003"
}
```

**Formato de Folio**:
- Formato: `HAB-XXXX`
- Ejemplo: `HAB-0001`, `HAB-0002`, etc.
- Secuencia: Automatica y consecutiva

**Casos de Uso**:
- Mostrar folio en formulario antes de crear
- Validacion de folios
- Informacion al usuario

---

## SINCRONIZACION

### 7. Verificar y Agregar Habitante

```
POST /api/sync/verificar
Content-Type: application/json
```

**Descripcion**: Verifica si un habitante existe. Si no existe, lo crea automaticamente.
Muy util para integracion con otros sistemas.

**Parametros** (body JSON):
- `nombre` (string, requerido): Nombre del habitante

**Ejemplo Request**:
```json
{
  "nombre": "Carlos Ruiz"
}
```

**Respuesta si Existe** (200):
```json
{
  "success": true,
  "existe": true,
  "habitante": {
    "folio": "HAB-0001",
    "nombre": "Carlos Ruiz",
    "fecha_registro": "13/01/2026",
    "activo": true,
    "nota": ""
  },
  "mensaje": "Habitante ya existe"
}
```

**Respuesta si No Existe** (200):
```json
{
  "success": true,
  "existe": false,
  "habitante": {
    "folio": "HAB-0003",
    "nombre": "Carlos Ruiz",
    "fecha_registro": "13/01/2026",
    "activo": true,
    "nota": ""
  },
  "mensaje": "Habitante agregado al censo"
}
```

**Casos de Uso**:
- Integracion con modulos de pagos/faenas
- Crear habitantes dinamicamente si no existen
- Sincronizacion entre modulos

---

## SALUD

### 8. Verificar Estado de API

```
GET /api/ping
```

**Descripcion**: Verifica que la API este funcionando correctamente.
Se usa para healthcheck y debugging.

**Parametros**: Ninguno

**Respuesta Exitosa** (200):
```json
{
  "success": true,
  "mensaje": "API Local funcionando correctamente",
  "total_habitantes": 5
}
```

**Casos de Uso**:
- Verificar conectividad con API
- Healthcheck de sistema
- Debugging de problemas

---

## CODIGOS DE ESTADO HTTP

| Codigo | Significado | Cuando Ocurre |
|--------|-------------|---------------|
| 200 | OK | Solicitud exitosa |
| 400 | Bad Request | Parametros invalidos o incompletos |
| 404 | Not Found | Recurso no encontrado |
| 500 | Internal Server Error | Error del servidor |

---

## EJEMPLOS DE USO CON CURL

### Obtener todos los habitantes
```bash
curl -X GET "http://127.0.0.1:5000/api/habitantes"
```

### Buscar habitantes
```bash
curl -X GET "http://127.0.0.1:5000/api/habitantes/buscar?q=Juan"
```

### Agregar nuevo habitante
```bash
curl -X POST "http://127.0.0.1:5000/api/habitantes" \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Pedro Lopez"}'
```

### Actualizar habitante
```bash
curl -X PATCH "http://127.0.0.1:5000/api/habitantes/HAB-0001" \
  -H "Content-Type: application/json" \
  -d '{"activo": false, "nota": "Inactivo"}'
```

### Verificar API
```bash
curl -X GET "http://127.0.0.1:5000/api/ping"
```

---

## EJEMPLOS DE USO CON PYTHON

### Obtener todos los habitantes
```python
import requests

response = requests.get('http://127.0.0.1:5000/api/habitantes')
datos = response.json()

if datos['success']:
    for habitante in datos['habitantes']:
        print(f"{habitante['folio']}: {habitante['nombre']}")
```

### Agregar nuevo habitante
```python
import requests

payload = {
    'nombre': 'Ana Martinez'
}

response = requests.post(
    'http://127.0.0.1:5000/api/habitantes',
    json=payload
)

datos = response.json()
if datos['success']:
    print(f"Habitante creado: {datos['habitante']['folio']}")
else:
    print(f"Error: {datos['mensaje']}")
```

### Verificar y crear si no existe
```python
import requests

payload = {'nombre': 'Roberto Silva'}

response = requests.post(
    'http://127.0.0.1:5000/api/sync/verificar',
    json=payload
)

datos = response.json()
if datos['existe']:
    print("Habitante ya estaba registrado")
else:
    print("Habitante fue creado automaticamente")
```

---

## NOTAS IMPORTANTES

1. **CORS**: CORS esta habilitado para permitir llamadas desde la interfaz local.

2. **Seguridad**: 
   - API solo escucha en localhost (127.0.0.1)
   - No expuesto a la red
   - Para produccion, implementar autenticacion

3. **Errores**:
   - Siempre revisar campo 'success' en respuesta
   - Campo 'mensaje' contiene detalles del error
   - Usar codigos HTTP para routing de errores

4. **Performance**:
   - Usar GET /api/habitantes/buscar para filtrado
   - Cachear resultados cuando sea posible
   - Evitar queries frecuentes al mismo recurso

5. **Integracion**:
   - POST /api/sync/verificar es ideal para crear habitantes dinamicamente
   - PATCH es para actualizaciones menores
   - POST es para creacion de nuevos records

---

## FUTURO

Endpoints planificados para futuras versiones:

- DELETE /api/habitantes/<folio> - Eliminar habitante
- GET /api/estadisticas - Estadisticas del censo
- GET /api/exportar - Exportar datos a Excel
- GET /api/historial - Historial de cambios
- POST /api/backup - Crear respaldo manual

---

Ultima actualizacion: 13 de enero de 2026
