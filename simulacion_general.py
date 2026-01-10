import argparse
import os
import random
from datetime import datetime, timedelta

from reset_datos import reset_datos
from src.auth.seguridad import seguridad
from src.config import (
    ARCHIVO_FAENAS,
    ARCHIVO_HABITANTES,
    ARCHIVO_PAGOS,
    PASSWORD_CIFRADO,
    RUTA_SEGURA,
)
from src.modules.historial.historial import GestorHistorial


def _ahora():
    return datetime.now()


def generar_habitantes(n=50):
    """Genera n habitantes únicos con datos realistas"""
    nombres = [
        "Juan", "Maria", "Pedro", "Ana", "Luis", "Carmen", "Jose", "Rosa", "Miguel", "Isabel",
        "Diego", "Luisa", "Andres", "Carolina", "Javier", "Patricia", "Felipe", "Daniela", "Ricardo", "Valentina",
        "Sergio", "Camila", "Ramon", "Fernanda", "Hector", "Sofia", "Esteban", "Paula", "Gonzalo", "Teresa",
        "Roberto", "Lorena", "Mauricio", "Claudia", "Alberto", "Natalia", "Julio", "Karla", "Victor", "Elena",
        "Alvaro", "Monica", "Pablo", "Francisca", "Ignacio", "Gabriela", "Rafael", "Veronica", "Cristian", "Jimena",
    ]
    apellidos = [
        "Garcia", "Rodriguez", "Hernandez", "Gonzalez", "Martinez", "Lopez", "Perez", "Ramirez", "Diaz", "Fernandez",
        "Sanchez", "Morales", "Torres", "Flores", "Rivera", "Gomez", "Vargas", "Castillo", "Alvarez", "Mendoza",
        "Ortega", "Rojas", "Silva", "Vega", "Cortez", "Paredes", "Navarro", "Campos", "Romero", "Herrera",
    ]
    habitantes = []
    base_fecha = _ahora() - timedelta(days=365 * 3)
    
    # Usar los primeros n nombres/apellidos combinados para generar n habitantes únicos
    for idx in range(n):
        nombre = f"{nombres[idx % len(nombres)]} {apellidos[idx // len(nombres) % len(apellidos)]}"
        fecha_registro = (base_fecha + timedelta(days=random.randint(0, 900))).strftime("%d/%m/%Y")
        habitantes.append({
            "nombre": nombre,
            "folio": f"HAB-{idx+1:04d}",
            "fecha_registro": fecha_registro,
            "activo": True,  # Todos activos para el simulador
        })
    return habitantes


def generar_pagos_persona(hab, monto_base, usuario):
    """Genera pagos variados para una persona en una cooperación"""
    pagos = []
    
    # 70% de probabilidad de haber pagado
    if random.random() < 0.7:
        # Entre 1-3 cuotas
        cuotas = random.randint(1, 3)
        for _ in range(cuotas):
            monto = round(random.uniform(monto_base * 0.3, monto_base * 0.8), 2)
            fecha_pago = _ahora() - timedelta(days=random.randint(5, 350))
            pagos.append({
                "monto": monto,
                "fecha": fecha_pago.strftime("%d/%m/%Y"),
                "hora": fecha_pago.strftime("%H:%M:%S"),
                "usuario": usuario,
            })
    
    persona = {
        "nombre": hab["nombre"],
        "folio": hab["folio"],
        "monto_esperado": float(monto_base),
        "pagos": pagos,
        "notas": random.choice(["", "Pago en efectivo", "Transferencia", "Plan familiar", "Pendiente"]),
    }
    return persona


def generar_cooperaciones(habitantes):
    """Genera 3 cooperaciones activas con TODOS los habitantes"""
    usuario = "Simulador"
    cooperaciones = [
        {
            "id": "coop-agua-2023", 
            "nombre": "Cooperacion Agua 2023", 
            "proyecto": "Mejora red de agua 2023", 
            "monto_cooperacion": 90.0
        },
        {
            "id": "coop-infra-2024", 
            "nombre": "Cooperacion Infra 2024", 
            "proyecto": "Centro comunitario 2024", 
            "monto_cooperacion": 120.0
        },
        {
            "id": "coop-salud-2025", 
            "nombre": "Cooperacion Salud 2025", 
            "proyecto": "Posta rural 2025", 
            "monto_cooperacion": 150.0
        },
    ]

    for coop in cooperaciones:
        personas = []
        # IMPORTANTE: Agregar TODOS los habitantes a cada cooperación
        for hab in habitantes:
            persona = generar_pagos_persona(hab, coop["monto_cooperacion"], usuario)
            personas.append(persona)
        coop["personas"] = personas
    
    return cooperaciones


def generar_faenas(habitantes):
    """Genera múltiples faenas con participación masiva y datos realistas"""
    faenas = []
    base_fecha = _ahora() - timedelta(days=600)
    
    nombres_faena = [
        "Limpieza plaza central", 
        "Mantenimiento canal de riego", 
        "Minga de construcción sede",
        "Poda y limpieza comunitaria", 
        "Pintado cancha multiuso",
        "Reparación camino rural", 
        "Operativo de recolección",
        "Jornada de forestación",
        "Construcción cerco comunal",
        "Limpieza fuentes de agua",
    ]
    
    for i, nombre in enumerate(nombres_faena):
        fecha = base_fecha + timedelta(days=i * 50)
        peso_faena = random.choice([5, 7, 8, 10])
        participantes = []
        
        # Seleccionar 60-80% de los habitantes para esta faena
        num_participantes = random.randint(int(len(habitantes) * 0.6), int(len(habitantes) * 0.8))
        seleccion = random.sample(habitantes, k=num_participantes)
        
        for p in seleccion:
            hora_reg = fecha + timedelta(hours=random.randint(8, 17), minutes=random.randint(0, 59))
            participante = {
                "folio": p["folio"],
                "nombre": p["nombre"],
                "hora_registro": hora_reg.isoformat(),
                "peso_aplicado": 1.0,  # Por defecto peso completo
            }
            
            # Variar el tipo de participación
            r = random.random()
            if r < 0.05:
                # 5% paga en lugar de asistir
                participante["sustitucion_tipo"] = "externo"
                participante["trabajador_nombre"] = random.choice([
                    "Juan Albañil", "Pedro Constructor", "Marco Obrero", "Cesar Trabajador", "Luis Asistente"
                ])
                participante["peso_aplicado"] = 1.0
            elif r < 0.10:
                # 5% contrata a otro habitante (90% para quien pagó, 100% para quien trabajó)
                otro = random.choice([h for h in habitantes if h["folio"] != p["folio"]])
                participante["sustitucion_tipo"] = "habitante"
                participante["trabajador_folio"] = otro["folio"]
                participante["trabajador_nombre"] = otro["nombre"]
                participante["peso_aplicado"] = 0.9
                
                # Agregar el trabajador también
                trabajador_participante = {
                    "folio": otro["folio"],
                    "nombre": otro["nombre"],
                    "hora_registro": hora_reg.isoformat(),
                    "peso_aplicado": 1.0,
                }
                participantes.append(trabajador_participante)
            # Si no, simplemente asistió (peso 1.0 por defecto)
            
            participantes.append(participante)
        
        # Asegurar no hay duplicados
        folios_vistos = set()
        participantes_unicos = []
        for part in participantes:
            clave = part["folio"]
            if clave not in folios_vistos:
                folios_vistos.add(clave)
                participantes_unicos.append(part)
        
        faenas.append({
            "id": f"faena-{i+1:03d}",
            "fecha": fecha.strftime("%Y-%m-%d"),
            "nombre": nombre,
            "peso": peso_faena,
            "hora_inicio": f"{random.randint(8, 9):02d}:00",
            "hora_fin": f"{random.randint(13, 15):02d}:00",
            "es_programada": fecha.date() > _ahora().date(),
            "participantes": participantes_unicos,
            "pagos_sustitutos": [],
            "monto_pago_faena": None,
            "creado_por": "Simulador",
        })
    
    return faenas


def guardar_habitantes(habitantes):
    """Guarda el censo de habitantes"""
    datos = {
        "habitantes": habitantes,
        "total": len(habitantes),
        "fecha_actualizacion": _ahora().strftime("%d/%m/%Y %H:%M:%S"),
    }
    seguridad.cifrar_archivo(datos, ARCHIVO_HABITANTES, PASSWORD_CIFRADO)
    print(f"✓ Censo: {len(habitantes)} habitantes guardados")


def guardar_pagos(cooperaciones, coop_activa):
    """Guarda las cooperaciones con todos los pagos"""
    password_hash = seguridad.hash_password(PASSWORD_CIFRADO).decode()
    datos = {
        "cooperaciones": cooperaciones,
        "cooperacion_activa": coop_activa,
        "password_hash": password_hash,
        "tamaño": "normal",
        "fecha_guardado": _ahora().strftime("%d/%m/%Y %H:%M:%S"),
    }
    seguridad.cifrar_archivo(datos, ARCHIVO_PAGOS, PASSWORD_CIFRADO)
    
    # Contar estadísticas
    total_coop = len(cooperaciones)
    total_personas = sum(len(c.get("personas", [])) for c in cooperaciones)
    total_pagos = sum(
        len(p.get("pagos", [])) 
        for c in cooperaciones 
        for p in c.get("personas", [])
    )
    print(f"✓ Cooperaciones: {total_coop} coops, {total_personas} personas total, {total_pagos} registros de pago")


def guardar_faenas(faenas):
    """Guarda las faenas con participantes"""
    datos = {
        "faenas": faenas,
        "fecha_guardado": _ahora().isoformat(),
    }
    seguridad.cifrar_archivo(datos, ARCHIVO_FAENAS, PASSWORD_CIFRADO)
    
    # Estadísticas
    total_participaciones = sum(len(f.get("participantes", [])) for f in faenas)
    print(f"✓ Faenas: {len(faenas)} faenas, {total_participaciones} participaciones registradas")


def poblar_historial(cooperaciones, faenas):
    """Genera historiales detallados para cooperaciones y faenas"""
    usuario = "Simulador"
    
    # Historial por cooperación
    for coop in cooperaciones:
        hist = GestorHistorial(id_cooperacion=coop["id"])
        
        # Registrar creación de la cooperación
        hist.registrar_creacion("COOPERACION", coop["id"], coop, usuario)
        
        # Registrar algunas personas y sus pagos
        for persona in coop.get("personas", [])[:20]:  # Primeras 20 personas
            hist.registrar_creacion("PERSONA", persona.get("folio", ""), persona, usuario)
            
            # Si tiene pagos, registrar el cambio
            if persona.get("pagos"):
                total_pagado = sum(p.get("monto", 0) for p in persona.get("pagos", []))
                hist.registrar_cambio(
                    "PAGO",
                    "PERSONA",
                    persona.get("folio", ""),
                    {
                        "pagos_registrados": {"anterior": 0, "nuevo": len(persona["pagos"])},
                        "total_pagado": {"anterior": 0, "nuevo": f"${total_pagado:.2f}"}
                    },
                    usuario,
                )
    
    # Historial para faenas
    hist_faenas = GestorHistorial(id_cooperacion="faenas")
    for faena in faenas[:5]:  # Primeras 5 faenas
        hist_faenas.registrar_creacion("FAENA", faena.get("id", ""), faena, usuario)
        
        # Registrar participaciones
        if faena.get("participantes"):
            hist_faenas.registrar_cambio(
                "PARTICIPANTES",
                "FAENA",
                faena.get("id", ""),
                {
                    "total_participantes": {"anterior": 0, "nuevo": len(faena["participantes"])},
                    "peso_faena": {"anterior": 0, "nuevo": faena.get("peso", 0)},
                },
                usuario,
            )
    
    print(f"✓ Historiales: Registrados eventos para cooperaciones y faenas")


def aplicar_simulacion():
    """Aplica la simulación completa: reset + generación de datos + historiales"""
    print("\n" + "="*70)
    print("GENERADOR DE DATOS DE SIMULACIÓN COMPLETA")
    print("="*70 + "\n")
    
    print("1. Limpiando datos previos...")
    reset_datos()
    
    os.makedirs(RUTA_SEGURA, exist_ok=True)
    
    print("2. Generando 50 habitantes únicos...")
    habitantes = generar_habitantes(50)
    guardar_habitantes(habitantes)
    
    print("3. Generando 3 cooperaciones con pagos variados...")
    cooperaciones = generar_cooperaciones(habitantes)
    guardar_pagos(cooperaciones, coop_activa="coop-salud-2025")
    
    print("4. Generando 10 faenas con participantes...")
    faenas = generar_faenas(habitantes)
    guardar_faenas(faenas)
    
    print("5. Registrando historiales detallados...")
    poblar_historial(cooperaciones, faenas)
    
    print("\n" + "="*70)
    print("✓ SIMULACIÓN COMPLETADA EXITOSAMENTE")
    print("="*70)
    print("\nEstadísticas finales:")
    print(f"  • Habitantes: 50")
    print(f"  • Cooperaciones: 3 (Agua 2023, Infra 2024, Salud 2025)")
    print(f"  • Pagos: Variados (0-3 cuotas por persona por cooperación)")
    print(f"  • Faenas: 10")
    print(f"  • Participaciones: ~500-600 registros")
    print(f"\nAhora abre la app y prueba:")
    print(f"  1. Censo: Ver 50 habitantes registrados")
    print(f"  2. Pagos: Ver cooperaciones con participantes y pagos")
    print(f"  3. Faenas: Ver faenas con asistencias y resumen anual de puntos")
    print("="*70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Generar datos de simulación completa")
    parser.add_argument("--aplicar", action="store_true", help="Resetear datos y cargar simulación completa")
    args = parser.parse_args()

    if not args.aplicar:
        print("Uso: python simulacion_general.py --aplicar")
        print("  --aplicar : Resetea el sistema y carga datos de simulación completa")
        return

    aplicar_simulacion()


if __name__ == "__main__":
    main()

