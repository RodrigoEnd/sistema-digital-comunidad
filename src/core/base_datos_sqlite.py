"""
Sistema de Base de Datos SQLite
Reemplaza el sistema JSON anterior con SQLite para mejor rendimiento y escalabilidad
"""

import sqlite3
import os
from datetime import datetime
from pathlib import Path
from src.config import RUTA_SEGURA
from src.core.logger import registrar_operacion, registrar_error
import hashlib
import time

class BaseDatosSQLite:
    """Gestor de base de datos SQLite para el sistema"""
    
    def __init__(self):
        self.ruta_db = os.path.join(RUTA_SEGURA, 'sistema.db')
        self.conexion = None
        self.inicializar_bd()
        
    def conectar(self):
        """Conectar a la base de datos con reintentos automáticos"""
        max_intentos = 5
        tiempo_espera = 0.2
        
        for intento in range(max_intentos):
            try:
                # Timeout más largo para evitar "database is locked"
                self.conexion = sqlite3.connect(self.ruta_db, timeout=60.0, check_same_thread=False)
                self.conexion.row_factory = sqlite3.Row
                # Habilitar claves foráneas
                self.conexion.execute("PRAGMA foreign_keys = ON")
                # Configurar WAL mode para mejor concurrencia (permite lecturas mientras se escribe)
                self.conexion.execute("PRAGMA journal_mode=WAL")
                # Timeout para operaciones bloqueadas (10 segundos)
                self.conexion.execute("PRAGMA busy_timeout=10000")
                # Optimizaciones de rendimiento
                self.conexion.execute("PRAGMA synchronous=NORMAL")
                self.conexion.execute("PRAGMA cache_size=10000")
                return self.conexion
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and intento < max_intentos - 1:
                    print(f"[BD] Base de datos bloqueada, reintentando ({intento+1}/{max_intentos})...")
                    time.sleep(tiempo_espera)
                    tiempo_espera *= 1.5
                    continue
                registrar_error('BaseDatosSQLite', 'conectar', str(e))
                raise
            except sqlite3.Error as e:
                registrar_error('BaseDatosSQLite', 'conectar', str(e))
                raise
    
    def desconectar(self):
        """Desconectar de la base de datos"""
        if self.conexion:
            self.conexion.close()
            self.conexion = None
    
    def inicializar_bd(self):
        """Inicializar estructura de base de datos"""
        self.conectar()
        cursor = self.conexion.cursor()
        
        try:
            # Tabla de usuarios
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre_usuario TEXT UNIQUE NOT NULL,
                    contraseña TEXT NOT NULL,
                    email TEXT UNIQUE,
                    rol TEXT DEFAULT 'delegado',
                    activo BOOLEAN DEFAULT 1,
                    fecha_creacion TEXT,
                    ultimo_acceso TEXT,
                    intentos_fallidos INTEGER DEFAULT 0,
                    bloqueado BOOLEAN DEFAULT 0
                )
            ''')
            
            # Tabla de habitantes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS habitantes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    folio TEXT UNIQUE NOT NULL,
                    nombre TEXT NOT NULL,
                    apellidos TEXT,
                    rut TEXT UNIQUE,
                    telefono TEXT,
                    email TEXT,
                    direccion TEXT,
                    fecha_nacimiento TEXT,
                    activo BOOLEAN DEFAULT 1,
                    fecha_registro TEXT,
                    nota TEXT,
                    grupo_familiar INTEGER,
                    FOREIGN KEY (grupo_familiar) REFERENCES habitantes(id)
                )
            ''')
            
            # Tabla de pagos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pagos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    habitante_id INTEGER NOT NULL,
                    monto REAL NOT NULL,
                    concepto TEXT,
                    fecha_pago TEXT,
                    estado TEXT DEFAULT 'pendiente',
                    observaciones TEXT,
                    registrado_por INTEGER,
                    fecha_registro TEXT,
                    FOREIGN KEY (habitante_id) REFERENCES habitantes(id),
                    FOREIGN KEY (registrado_por) REFERENCES usuarios(id)
                )
            ''')
            
            # Tabla de faenas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS faenas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    descripcion TEXT,
                    fecha_inicio TEXT NOT NULL,
                    fecha_fin TEXT,
                    estado TEXT DEFAULT 'pendiente',
                    horas_requeridas REAL,
                    encargado_id INTEGER,
                    fecha_creacion TEXT,
                    FOREIGN KEY (encargado_id) REFERENCES usuarios(id)
                )
            ''')
            
            # Tabla de participación en faenas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS participacion_faenas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    faena_id INTEGER NOT NULL,
                    habitante_id INTEGER NOT NULL,
                    horas_trabajadas REAL,
                    fecha_participacion TEXT,
                    validada BOOLEAN DEFAULT 0,
                    validada_por INTEGER,
                    UNIQUE(faena_id, habitante_id),
                    FOREIGN KEY (faena_id) REFERENCES faenas(id),
                    FOREIGN KEY (habitante_id) REFERENCES habitantes(id),
                    FOREIGN KEY (validada_por) REFERENCES usuarios(id)
                )
            ''')
            
            # Tabla de historial
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS historial (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo_evento TEXT NOT NULL,
                    descripcion TEXT,
                    usuario_id INTEGER,
                    habitante_id INTEGER,
                    fecha_evento TEXT,
                    detalles TEXT,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
                    FOREIGN KEY (habitante_id) REFERENCES habitantes(id)
                )
            ''')
            
            # Tabla de preferencias
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS preferencias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER,
                    clave TEXT NOT NULL,
                    valor TEXT,
                    UNIQUE(usuario_id, clave),
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                )
            ''')
            
            # Tabla de auditoría - Registra todas las operaciones críticas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS auditoria (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario TEXT NOT NULL,
                    accion TEXT NOT NULL,
                    tabla TEXT,
                    registro_id INTEGER,
                    fecha_operacion TEXT NOT NULL,
                    detalles TEXT,
                    ip_origen TEXT,
                    resultado TEXT DEFAULT 'exitoso'
                )
            ''')
            
            # Crear índices para auditoría
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_auditoria_fecha 
                ON auditoria(fecha_operacion DESC)
            ''')
            
            # Crear índices para mejorar rendimiento de búsquedas
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_habitantes_nombre 
                ON habitantes(nombre)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_habitantes_folio 
                ON habitantes(folio)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_habitantes_activo 
                ON habitantes(activo)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_auditoria_usuario 
                ON auditoria(usuario)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_auditoria_tabla 
                ON auditoria(tabla)
            ''')
            
            # ===== ÍNDICES PARA COOPERACIONES (Centro de Pagos) =====
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_cooperaciones_activa 
                ON cooperaciones(activa)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_cooperaciones_nombre 
                ON cooperaciones(nombre)
            ''')
            
            # Índices para personas_cooperacion
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_personas_coop_coop_id 
                ON personas_cooperacion(cooperacion_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_personas_coop_habitante_id 
                ON personas_cooperacion(habitante_id)
            ''')
            
            # Índices para pagos_coop
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_pagos_coop_persona_id 
                ON pagos_coop(persona_coop_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_pagos_coop_fecha 
                ON pagos_coop(fecha_pago DESC)
            ''')
            
            # ===== TABLAS PARA COOPERACIONES (Centro de Pagos) =====
            # Índices de rendimiento para cooperaciones
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_cooperaciones_activa 
                ON cooperaciones(activa)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_cooperaciones_nombre 
                ON cooperaciones(nombre)
            ''')
            
            # Índices para personas_cooperacion (búsquedas frecuentes)
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_personas_coop_coop_id 
                ON personas_cooperacion(cooperacion_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_personas_coop_habitante_id 
                ON personas_cooperacion(habitante_id)
            ''')
            
            # Índices para pagos_coop (búsquedas de historial)
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_pagos_coop_persona_id 
                ON pagos_coop(persona_coop_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_pagos_coop_fecha 
                ON pagos_coop(fecha_pago DESC)
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cooperaciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL UNIQUE,
                    proyecto TEXT NOT NULL,
                    monto_cooperacion REAL DEFAULT 300.0,
                    activa BOOLEAN DEFAULT 1,
                    fecha_creacion TEXT NOT NULL,
                    descripcion TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS personas_cooperacion (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cooperacion_id INTEGER NOT NULL,
                    habitante_id INTEGER NOT NULL,
                    monto_esperado REAL DEFAULT 300.0,
                    pagado REAL DEFAULT 0.0,
                    estado TEXT DEFAULT 'pendiente',
                    notas TEXT,
                    fecha_agregado TEXT NOT NULL,
                    UNIQUE(cooperacion_id, habitante_id),
                    FOREIGN KEY (cooperacion_id) REFERENCES cooperaciones(id),
                    FOREIGN KEY (habitante_id) REFERENCES habitantes(id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pagos_coop (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    persona_coop_id INTEGER NOT NULL,
                    monto REAL NOT NULL,
                    fecha_pago TEXT NOT NULL,
                    hora_pago TEXT,
                    concepto TEXT,
                    registrado_por INTEGER,
                    anulado BOOLEAN DEFAULT 0,
                    motivo_anulacion TEXT,
                    fecha_registro TEXT NOT NULL,
                    FOREIGN KEY (persona_coop_id) REFERENCES personas_cooperacion(id),
                    FOREIGN KEY (registrado_por) REFERENCES usuarios(id)
                )
            ''')
            
            self.conexion.commit()
            
            # Crear usuario admin si no existe
            self._crear_admin_default()
            
            # Crear cooperación inicial si no existe
            self._crear_cooperacion_initial()
            
            print("[OK] Base de datos SQLite inicializada correctamente")
            
        except sqlite3.Error as e:
            registrar_error('BaseDatosSQLite', 'inicializar_bd', str(e))
            self.conexion.rollback()
            raise
    
    def _crear_admin_default(self):
        """Crear usuario admin por defecto si no existe"""
        cursor = self.conexion.cursor()
        
        try:
            cursor.execute("SELECT id FROM usuarios WHERE nombre_usuario = 'admin'")
            if not cursor.fetchone():
                # Hash de contraseña: admin3112
                hash_pwd = hashlib.sha256("admin3112".encode()).hexdigest()
                
                cursor.execute('''
                    INSERT INTO usuarios 
                    (nombre_usuario, contraseña, email, rol, activo, fecha_creacion)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', ('admin', hash_pwd, 'admin@comunidad.local', 'admin', 1, 
                      datetime.now().strftime("%d/%m/%Y")))
                
                self.conexion.commit()
                print("[OK] Usuario admin creado")
                registrar_operacion('ADMIN', 'Usuario admin creado', {})
        except sqlite3.Error as e:
            registrar_error('BaseDatosSQLite', '_crear_admin_default', str(e))
    
    # ==================== HABITANTES ====================
    
    def crear_habitante(self, folio, nombre, apellidos="", rut="", telefono="", email="", direccion="", 
                       fecha_nacimiento="", nota="", grupo_familiar=None, activo=True):
        """Crear nuevo habitante en el sistema
        
        MEJORADO: Evita reconectar si ya hay conexión activa
        
        Args:
            folio (str): Identificador único FOL-XXXX
            nombre (str): Nombre del habitante
            apellidos (str): Apellidos del habitante
            rut (str): RUT en formato XXXXXXXX-X
            telefono (str): Teléfono de contacto
            email (str): Correo electrónico
            direccion (str): Dirección física
            fecha_nacimiento (str): Fecha de nacimiento YYYY-MM-DD
            nota (str): Nota o comentario
            grupo_familiar (int): ID del grupo familiar (si aplica)
            activo (bool): Estado del habitante
            
        Returns:
            tuple: (dict con datos del habitante, str mensaje de confirmación)
        """
        # MEJORA: Usar conexión existente si está disponible
        if not self.conexion:
            self.conectar()
        
        cursor = self.conexion.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO habitantes 
                (folio, nombre, apellidos, rut, telefono, email, direccion, 
                 fecha_nacimiento, nota, grupo_familiar, activo, fecha_registro)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (folio, nombre, apellidos, rut, telefono, email, direccion,
                  fecha_nacimiento, nota, grupo_familiar, 1 if activo else 0,
                  datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            
            self.conexion.commit()
            registrar_operacion('HABITANTES', f'Habitante creado: {nombre}', {'folio': folio})
            
            cursor.execute("SELECT * FROM habitantes WHERE folio = ?", (folio,))
            return dict(cursor.fetchone()), "Habitante creado correctamente"
            
        except sqlite3.IntegrityError as e:
            if 'UNIQUE constraint failed' in str(e):
                return None, "Ya existe un habitante con este folio o RUT"
            return None, f"Error de integridad: {str(e)}"
        except sqlite3.Error as e:
            registrar_error('BaseDatosSQLite', 'crear_habitante', str(e))
            return None, f"Error al crear habitante: {str(e)}"
    
    def agregar_habitante(self, nombre, apellidos="", rut="", telefono="", email="", direccion=""):
        """[MEJORADO] Agregar habitante - ahora sin reconectar
        
        Antes usaba conectar() lo que causaba bloqueos. Ahora usa la conexión existente.
        """
        # Asegurar que hay conexión
        if not self.conexion:
            self.conectar()
        
        cursor = self.conexion.cursor()
        
        try:
            # Generar folio automáticamente
            cursor.execute("SELECT MAX(CAST(SUBSTR(folio, 5) AS INTEGER)) FROM habitantes WHERE folio LIKE 'FOL-%'")
            max_num_result = cursor.fetchone()
            max_num = max_num_result[0] if max_num_result and max_num_result[0] else 0
            folio = f"FOL-{max_num + 1:04d}"
            
            return self.crear_habitante(folio, nombre, apellidos, rut, telefono, email, direccion)
            
        except sqlite3.Error as e:
            registrar_error('BaseDatosSQLite', 'agregar_habitante', str(e))
            return None, f"Error al agregar habitante: {str(e)}"
    
    def obtener_todos_habitantes(self):
        """Obtener todos los habitantes activos ordenados por folio"""
        cursor = self.conectar().cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM habitantes WHERE activo = 1 
                ORDER BY CAST(SUBSTR(folio, 5) AS INTEGER) ASC
            """)
            habitantes = [dict(row) for row in cursor.fetchall()]
            return habitantes
        except sqlite3.Error as e:
            registrar_error('BaseDatosSQLite', 'obtener_todos_habitantes', str(e))
            return []
    
    def buscar_habitante(self, criterio):
        """Buscar habitante por nombre, folio o RUT"""
        cursor = self.conectar().cursor()
        
        try:
            criterio_lower = criterio.lower()
            cursor.execute("""
                SELECT * FROM habitantes 
                WHERE activo = 1 AND (
                    LOWER(nombre) LIKE ? OR 
                    LOWER(folio) LIKE ? OR 
                    LOWER(rut) LIKE ?
                )
                ORDER BY nombre ASC
            """, (f"%{criterio_lower}%", f"%{criterio_lower}%", f"%{criterio_lower}%"))
            
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            registrar_error('BaseDatosSQLite', 'buscar_habitante', str(e))
            return []
    
    def obtener_habitante_por_folio(self, folio):
        """Obtener habitante por folio"""
        cursor = self.conectar().cursor()
        
        try:
            cursor.execute("SELECT * FROM habitantes WHERE folio = ? AND activo = 1", (folio,))
            resultado = cursor.fetchone()
            return dict(resultado) if resultado else None
        except sqlite3.Error as e:
            registrar_error('BaseDatosSQLite', 'obtener_habitante_por_folio', str(e))
            return None
    
    def actualizar_habitante(self, folio, **datos):
        """Actualizar datos de habitante"""
        cursor = self.conectar().cursor()
        
        try:
            campos = []
            valores = []
            
            for clave, valor in datos.items():
                if clave != 'folio' and clave != 'id':
                    campos.append(f"{clave} = ?")
                    valores.append(valor)
            
            if not campos:
                return True, "Sin cambios"
            
            valores.append(folio)
            query = f"UPDATE habitantes SET {', '.join(campos)} WHERE folio = ?"
            
            cursor.execute(query, valores)
            self.conexion.commit()
            
            registrar_operacion('HABITANTES', f'Habitante actualizado: {folio}', datos)
            return True, "Habitante actualizado"
            
        except sqlite3.Error as e:
            registrar_error('BaseDatosSQLite', 'actualizar_habitante', str(e))
            return False, f"Error al actualizar: {str(e)}"
    
    def eliminar_habitante(self, folio):
        """Marcar habitante como inactivo (soft delete)"""
        cursor = self.conectar().cursor()
        
        try:
            cursor.execute("UPDATE habitantes SET activo = 0 WHERE folio = ?", (folio,))
            self.conexion.commit()
            registrar_operacion('HABITANTES', f'Habitante desactivado: {folio}', {})
            return True, "Habitante eliminado"
        except sqlite3.Error as e:
            registrar_error('BaseDatosSQLite', 'eliminar_habitante', str(e))
            return False, f"Error al eliminar: {str(e)}"
    
    # ==================== PAGOS ====================
    
    def registrar_pago(self, habitante_id, monto, concepto="", usuario_id=None, observaciones=""):
        """Registrar un pago"""
        cursor = self.conectar().cursor()
        
        try:
            cursor.execute('''
                INSERT INTO pagos 
                (habitante_id, monto, concepto, estado, observaciones, registrado_por, fecha_registro, fecha_pago)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (habitante_id, monto, concepto, 'completado', observaciones, usuario_id,
                  datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%d/%m/%Y")))
            
            self.conexion.commit()
            registrar_operacion('PAGOS', f'Pago registrado', {'habitante_id': habitante_id, 'monto': monto})
            return True, "Pago registrado"
            
        except sqlite3.Error as e:
            registrar_error('BaseDatosSQLite', 'registrar_pago', str(e))
            return False, f"Error al registrar pago: {str(e)}"
    
    def obtener_pagos_habitante(self, habitante_id):
        """Obtener pagos de un habitante"""
        cursor = self.conectar().cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM pagos WHERE habitante_id = ? 
                ORDER BY fecha_registro DESC
            """, (habitante_id,))
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            registrar_error('BaseDatosSQLite', 'obtener_pagos_habitante', str(e))
            return []
    
    def obtener_todos_pagos(self):
        """Obtener todos los pagos"""
        cursor = self.conectar().cursor()
        
        try:
            cursor.execute("""
                SELECT p.*, h.nombre, h.folio 
                FROM pagos p
                JOIN habitantes h ON p.habitante_id = h.id
                ORDER BY p.fecha_registro DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            registrar_error('BaseDatosSQLite', 'obtener_todos_pagos', str(e))
            return []
    
    # ==================== FAENAS ====================
    
    def crear_faena(self, nombre, descripcion="", fecha_inicio="", fecha_fin="", horas_requeridas=0, encargado_id=None):
        """Crear nueva faena"""
        cursor = self.conectar().cursor()
        
        try:
            cursor.execute('''
                INSERT INTO faenas 
                (nombre, descripcion, fecha_inicio, fecha_fin, horas_requeridas, encargado_id, fecha_creacion, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (nombre, descripcion, fecha_inicio, fecha_fin, horas_requeridas, encargado_id,
                  datetime.now().strftime("%d/%m/%Y"), 'pendiente'))
            
            self.conexion.commit()
            registrar_operacion('FAENAS', f'Faena creada: {nombre}', {})
            return True, "Faena creada"
            
        except sqlite3.Error as e:
            registrar_error('BaseDatosSQLite', 'crear_faena', str(e))
            return False, f"Error al crear faena: {str(e)}"
    
    def obtener_todas_faenas(self):
        """Obtener todas las faenas activas"""
        cursor = self.conectar().cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM faenas WHERE estado != 'cancelada'
                ORDER BY fecha_inicio DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            registrar_error('BaseDatosSQLite', 'obtener_todas_faenas', str(e))
            return []
    
    def registrar_participacion_faena(self, faena_id, habitante_id, horas=0):
        """Registrar participación en faena"""
        cursor = self.conectar().cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO participacion_faenas 
                (faena_id, habitante_id, horas_trabajadas, fecha_participacion)
                VALUES (?, ?, ?, ?)
            ''', (faena_id, habitante_id, horas, datetime.now().strftime("%d/%m/%Y")))
            
            self.conexion.commit()
            return True, "Participación registrada"
            
        except sqlite3.Error as e:
            registrar_error('BaseDatosSQLite', 'registrar_participacion_faena', str(e))
            return False, f"Error: {str(e)}"
    
    # ==================== USUARIOS ====================
    
    def obtener_usuario(self, nombre_usuario):
        """Obtener usuario por nombre"""
        cursor = self.conectar().cursor()
        
        try:
            cursor.execute("SELECT * FROM usuarios WHERE nombre_usuario = ?", (nombre_usuario,))
            resultado = cursor.fetchone()
            return dict(resultado) if resultado else None
        except sqlite3.Error as e:
            registrar_error('BaseDatosSQLite', 'obtener_usuario', str(e))
            return None
    
    def obtener_usuarios(self, activos_solo=True):
        """Obtener todos los usuarios"""
        cursor = self.conectar().cursor()
        
        try:
            if activos_solo:
                cursor.execute("SELECT * FROM usuarios WHERE activo = 1 ORDER BY nombre_usuario")
            else:
                cursor.execute("SELECT * FROM usuarios ORDER BY nombre_usuario")
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            registrar_error('BaseDatosSQLite', 'obtener_usuarios', str(e))
            return []
    
    def crear_usuario(self, nombre_usuario, contraseña, email="", rol="delegado"):
        """Crear nuevo usuario"""
        cursor = self.conectar().cursor()
        
        try:
            # Hash de contraseña
            hash_pwd = hashlib.sha256(contraseña.encode()).hexdigest()
            
            cursor.execute('''
                INSERT INTO usuarios 
                (nombre_usuario, contraseña, email, rol, activo, fecha_creacion)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (nombre_usuario, hash_pwd, email, rol, 1, datetime.now().strftime("%d/%m/%Y")))
            
            self.conexion.commit()
            registrar_operacion('USUARIOS', f'Usuario creado: {nombre_usuario}', {})
            return True, "Usuario creado"
            
        except sqlite3.IntegrityError:
            return False, "El usuario ya existe"
        except sqlite3.Error as e:
            registrar_error('BaseDatosSQLite', 'crear_usuario', str(e))
            return False, f"Error: {str(e)}"
    
    def actualizar_contraseña(self, nombre_usuario, nueva_contraseña):
        """Actualizar contraseña de usuario"""
        cursor = self.conectar().cursor()
        
        try:
            hash_pwd = hashlib.sha256(nueva_contraseña.encode()).hexdigest()
            cursor.execute("""
                UPDATE usuarios SET contraseña = ? WHERE nombre_usuario = ?
            """, (hash_pwd, nombre_usuario))
            
            self.conexion.commit()
            registrar_operacion('USUARIOS', f'Contraseña actualizada: {nombre_usuario}', {})
            return True, "Contraseña actualizada"
            
        except sqlite3.Error as e:
            registrar_error('BaseDatosSQLite', 'actualizar_contraseña', str(e))
            return False, f"Error: {str(e)}"
    
    # ==================== HISTORIAL ====================
    
    def registrar_evento(self, tipo_evento, descripcion="", usuario_id=None, habitante_id=None, detalles=""):
        """Registrar evento en historial"""
        cursor = self.conectar().cursor()
        
        try:
            cursor.execute('''
                INSERT INTO historial 
                (tipo_evento, descripcion, usuario_id, habitante_id, fecha_evento, detalles)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (tipo_evento, descripcion, usuario_id, habitante_id, 
                  datetime.now().strftime("%d/%m/%Y %H:%M:%S"), detalles))
            
            self.conexion.commit()
        except sqlite3.Error as e:
            registrar_error('BaseDatosSQLite', 'registrar_evento', str(e))
    
    def obtener_historial(self, limite=100):
        """Obtener historial de eventos"""
        cursor = self.conectar().cursor()
        
        try:
            cursor.execute("""
                SELECT h.*, u.nombre_usuario, hab.nombre as habitante_nombre
                FROM historial h
                LEFT JOIN usuarios u ON h.usuario_id = u.id
                LEFT JOIN habitantes hab ON h.habitante_id = hab.id
                ORDER BY h.fecha_evento DESC
                LIMIT ?
            """, (limite,))
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            registrar_error('BaseDatosSQLite', 'obtener_historial', str(e))
            return []
    
    # ==================== BACKUP Y MANTENIMIENTO ====================
    
    def vaciar_base_datos(self):
        """Vaciar toda la base de datos (excepto usuario admin)"""
        cursor = self.conectar().cursor()
        
        try:
            cursor.execute("DELETE FROM historial")
            cursor.execute("DELETE FROM participacion_faenas")
            cursor.execute("DELETE FROM faenas")
            cursor.execute("DELETE FROM pagos")
            cursor.execute("DELETE FROM habitantes")
            # Mantener usuarios pero eliminar los que no sean admin
            cursor.execute("DELETE FROM usuarios WHERE nombre_usuario != 'admin'")
            
            self.conexion.commit()
            registrar_operacion('ADMIN', 'Base de datos vaciada', {})
            print("[OK] Base de datos vaciada (admin preservado)")
            return True, "Base de datos vaciada"
            
        except sqlite3.Error as e:
            registrar_error('BaseDatosSQLite', 'vaciar_base_datos', str(e))
            self.conexion.rollback()
            return False, f"Error: {str(e)}"
    
    def obtener_estadisticas(self):
        """Obtener estadísticas de la base de datos"""
        cursor = self.conectar().cursor()
        
        try:
            stats = {}
            
            cursor.execute("SELECT COUNT(*) as total FROM habitantes WHERE activo = 1")
            stats['habitantes'] = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as total FROM pagos")
            stats['pagos'] = cursor.fetchone()['total']
            
            cursor.execute("SELECT SUM(monto) as total FROM pagos WHERE estado = 'completado'")
            stats['monto_pagos'] = cursor.fetchone()['total'] or 0
            
            cursor.execute("SELECT COUNT(*) as total FROM faenas WHERE estado = 'activa'")
            stats['faenas_activas'] = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as total FROM usuarios WHERE activo = 1")
            stats['usuarios'] = cursor.fetchone()['total']
            
            return stats
        except sqlite3.Error as e:
            registrar_error('BaseDatosSQLite', 'obtener_estadisticas', str(e))
            return {}
    
    # ==================== AUDITORÍA ====================
    
    def registrar_auditoria(self, usuario, accion, tabla=None, registro_id=None, detalles=None):
        """
        Registrar una operación en la auditoría del sistema
        
        Args:
            usuario (str): Usuario que realizó la operación
            accion (str): Tipo de acción (CREAR, ACTUALIZAR, ELIMINAR, etc)
            tabla (str): Tabla afectada
            registro_id (int): ID del registro afectado
            detalles (str): Detalles adicionales de la operación
            
        Returns:
            bool: True si se registró exitosamente
        """
        cursor = self.conectar().cursor()
        
        try:
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute('''
                INSERT INTO auditoria 
                (usuario, accion, tabla, registro_id, fecha_operacion, detalles, resultado)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (usuario, accion, tabla, registro_id, fecha, detalles, 'exitoso'))
            
            self.conexion.commit()
            return True
            
        except sqlite3.Error as e:
            registrar_error('BaseDatosSQLite', 'registrar_auditoria', str(e))
            return False
    
    def obtener_auditoria(self, limite=100, usuario=None, accion=None, tabla=None):
        """
        Obtener registros de auditoría con filtros opcionales
        
        Args:
            limite (int): Cantidad máxima de registros a retornar
            usuario (str): Filtrar por usuario (opcional)
            accion (str): Filtrar por acción (opcional)
            tabla (str): Filtrar por tabla (opcional)
            
        Returns:
            list: Lista de registros de auditoría ordenados por fecha descendente
        """
        cursor = self.conectar().cursor()
        
        try:
            query = 'SELECT * FROM auditoria WHERE 1=1'
            params = []
            
            if usuario:
                query += ' AND usuario = ?'
                params.append(usuario)
            
            if accion:
                query += ' AND accion = ?'
                params.append(accion)
            
            if tabla:
                query += ' AND tabla = ?'
                params.append(tabla)
            
            query += ' ORDER BY fecha_operacion DESC LIMIT ?'
            params.append(limite)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
            
        except sqlite3.Error as e:
            registrar_error('BaseDatosSQLite', 'obtener_auditoria', str(e))
            return []
    
    def limpiar_auditoria_antigua(self, dias=90):
        """
        Eliminar registros de auditoría más antiguos que X días
        
        Args:
            dias (int): Días de antigüedad para eliminar
            
        Returns:
            tuple: (bool exito, str mensaje)
        """
        cursor = self.conectar().cursor()
        
        try:
            from datetime import timedelta
            fecha_limite = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d")
            
            cursor.execute('DELETE FROM auditoria WHERE fecha_operacion < ?', (fecha_limite,))
            self.conexion.commit()
            
            filas_eliminadas = cursor.rowcount
            return True, f"Se eliminaron {filas_eliminadas} registros de auditoría antiguos"
            
        except sqlite3.Error as e:
            registrar_error('BaseDatosSQLite', 'limpiar_auditoria_antigua', str(e))
            return False, f"Error: {str(e)}"
    
    def crear_cooperacion_bd(self, nombre, proyecto, monto_cooperacion):
        """Crear una cooperación en BD SQLite"""
        cursor = self.conectar().cursor()
        try:
            from datetime import datetime
            ahora = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO cooperaciones (nombre, proyecto, monto_cooperacion, activa, fecha_creacion)
                VALUES (?, ?, ?, ?, ?)
            ''', (nombre, proyecto, monto_cooperacion, 1, ahora))
            
            self.conexion.commit()
            coop_id = cursor.lastrowid
            registrar_operacion('CREAR_COOP', f'Cooperación creada: {nombre}', 
                {'id': coop_id, 'monto': monto_cooperacion})
            return coop_id
        except sqlite3.IntegrityError as e:
            registrar_error('BaseDatosSQLite', 'crear_cooperacion_bd', f'Duplicado: {str(e)}')
            return None
        except Exception as e:
            registrar_error('BaseDatosSQLite', 'crear_cooperacion_bd', str(e))
            return None
    
    def agregar_persona_coop_bd(self, coop_id, habitante_id, monto_esperado, notas=''):
        """Agregar una persona a una cooperación en BD SQLite"""
        cursor = self.conectar().cursor()
        try:
            from datetime import datetime
            ahora = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO personas_cooperacion 
                (cooperacion_id, habitante_id, monto_esperado, estado, notas, fecha_agregado)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (coop_id, habitante_id, monto_esperado, 'pendiente', notas, ahora))
            
            self.conexion.commit()
            persona_coop_id = cursor.lastrowid
            registrar_operacion('AGREGAR_PERSONA_COOP', f'Persona agregada a cooperación {coop_id}',
                {'persona_coop_id': persona_coop_id, 'habitante_id': habitante_id})
            return persona_coop_id
        except sqlite3.IntegrityError as e:
            registrar_error('BaseDatosSQLite', 'agregar_persona_coop_bd', f'Duplicado: {str(e)}')
            return None
        except Exception as e:
            registrar_error('BaseDatosSQLite', 'agregar_persona_coop_bd', str(e))
            return None
    
    def registrar_pago_coop_bd(self, persona_coop_id, monto, fecha_pago, hora_pago, concepto, registrado_por=None):
        """Registrar un pago en cooperación en BD SQLite"""
        cursor = self.conectar().cursor()
        try:
            from datetime import datetime
            ahora = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO pagos_coop
                (persona_coop_id, monto, fecha_pago, hora_pago, concepto, registrado_por, fecha_registro, anulado)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (persona_coop_id, monto, fecha_pago, hora_pago, concepto, registrado_por, ahora, 0))
            
            self.conexion.commit()
            pago_id = cursor.lastrowid
            registrar_operacion('PAGO_REGISTRADO', 'Pago registrado en cooperación',
                {'pago_id': pago_id, 'monto': monto, 'fecha': fecha_pago})
            return pago_id
        except Exception as e:
            registrar_error('BaseDatosSQLite', 'registrar_pago_coop_bd', str(e))
            return None
    
    def actualizar_persona_coop_bd(self, persona_coop_id, monto_esperado=None, estado=None, notas=None):
        """Actualizar datos de persona en cooperación en BD SQLite"""
        cursor = self.conectar().cursor()
        try:
            updates = []
            params = []
            
            if monto_esperado is not None:
                updates.append('monto_esperado = ?')
                params.append(monto_esperado)
            
            if estado is not None:
                updates.append('estado = ?')
                params.append(estado)
            
            if notas is not None:
                updates.append('notas = ?')
                params.append(notas)
            
            if not updates:
                return True  # No hay nada que actualizar
            
            params.append(persona_coop_id)
            query = f"UPDATE personas_cooperacion SET {', '.join(updates)} WHERE id = ?"
            
            cursor.execute(query, params)
            self.conexion.commit()
            
            registrar_operacion('ACTUALIZAR_PERSONA_COOP', f'Persona cooperación {persona_coop_id} actualizada',
                {'persona_coop_id': persona_coop_id, 'estado': estado})
            return True
            
        except Exception as e:
            registrar_error('BaseDatosSQLite', 'actualizar_persona_coop_bd', str(e))
            return False
    
    def eliminar_persona_coop_bd(self, persona_coop_id):
        """Eliminar persona de cooperación (NO elimina habitante del censo)"""
        cursor = self.conectar().cursor()
        try:
            # Solo elimina de personas_cooperacion, no del censo
            cursor.execute('''
                DELETE FROM personas_cooperacion WHERE id = ?
            ''', (persona_coop_id,))
            
            self.conexion.commit()
            registrar_operacion('ELIMINAR_PERSONA_COOP', f'Persona de cooperación {persona_coop_id} eliminada',
                {'persona_coop_id': persona_coop_id})
            return True
            
        except Exception as e:
            registrar_error('BaseDatosSQLite', 'eliminar_persona_coop_bd', str(e))
            return False
    
    def crear_cooperacion_bd(self, nombre, proyecto, monto_cooperacion):
        """Crear una cooperación en BD SQLite"""
        cursor = self.conectar().cursor()
        try:
            from datetime import datetime
            ahora = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO cooperaciones (nombre, proyecto, monto_cooperacion, activa, fecha_creacion)
                VALUES (?, ?, ?, ?, ?)
            ''', (nombre, proyecto, monto_cooperacion, 1, ahora))
            
            self.conexion.commit()
            coop_id = cursor.lastrowid
            registrar_operacion('CREAR_COOP', f'Cooperación creada: {nombre}', 
                {'id': coop_id, 'monto': monto_cooperacion})
            return coop_id
        except sqlite3.IntegrityError as e:
            registrar_error('BaseDatosSQLite', 'crear_cooperacion_bd', f'Duplicado: {str(e)}')
            return None
        except Exception as e:
            registrar_error('BaseDatosSQLite', 'crear_cooperacion_bd', str(e))
            return None
    
    def agregar_persona_coop_bd(self, coop_id, habitante_id, monto_esperado, notas=''):
        """Agregar una persona a una cooperación en BD SQLite"""
        cursor = self.conectar().cursor()
        try:
            from datetime import datetime
            ahora = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO personas_cooperacion 
                (cooperacion_id, habitante_id, monto_esperado, estado, notas, fecha_agregado)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (coop_id, habitante_id, monto_esperado, 'pendiente', notas, ahora))
            
            self.conexion.commit()
            persona_coop_id = cursor.lastrowid
            registrar_operacion('AGREGAR_PERSONA_COOP', f'Persona agregada a cooperación {coop_id}',
                {'persona_coop_id': persona_coop_id, 'habitante_id': habitante_id})
            return persona_coop_id
        except sqlite3.IntegrityError as e:
            registrar_error('BaseDatosSQLite', 'agregar_persona_coop_bd', f'Duplicado: {str(e)}')
            return None
        except Exception as e:
            registrar_error('BaseDatosSQLite', 'agregar_persona_coop_bd', str(e))
            return None
    
    def _crear_cooperacion_initial(self):
        """Crea la cooperación inicial si no existe"""
        try:
            cursor = self.conectar().cursor()
            
            # Verificar si ya existe
            cursor.execute("SELECT id FROM cooperaciones WHERE nombre = 'Cooperación General'")
            if cursor.fetchone():
                return  # Ya existe
            
            # Crear cooperación inicial
            from datetime import datetime
            ahora = datetime.now().isoformat()
            cursor.execute('''
                INSERT INTO cooperaciones (nombre, proyecto, monto_cooperacion, activa, fecha_creacion)
                VALUES (?, ?, ?, ?, ?)
            ''', ('Cooperación General', 'Proyecto General', 300.0, 1, ahora))
            
            self.conexion.commit()
        except:
            pass  # Silenciar errores en inicialización

# ==================== INSTANCIA GLOBAL ====================
_instancia_bd = None

def obtener_bd():
    """Obtener instancia de base de datos (singleton)"""
    global _instancia_bd
    if _instancia_bd is None:
        _instancia_bd = BaseDatosSQLite()
    return _instancia_bd