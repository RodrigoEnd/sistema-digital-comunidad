"""Script de prueba para verificar la ruta DELETE de la API"""
import requests
import json

API_URL = "http://127.0.0.1:5000/api"

def test_delete():
    # Primero obtener un habitante existente
    print("1. Obteniendo lista de habitantes...")
    response = requests.get(f"{API_URL}/habitantes", timeout=5)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success') and data.get('habitantes'):
            habitantes = data.get('habitantes')
            # Buscar un habitante activo
            habitante = next((h for h in habitantes if h.get('activo', True)), None)
            
            if habitante:
                folio = habitante.get('folio')
                nombre = habitante.get('nombre')
                print(f"   ✓ Habitante encontrado: {nombre} (Folio: {folio})")
                
                # Intentar eliminar
                print(f"\n2. Intentando eliminar habitante {folio}...")
                print(f"   URL: {API_URL}/habitantes/{folio}")
                print(f"   Método: DELETE")
                
                response_delete = requests.delete(f"{API_URL}/habitantes/{folio}", timeout=5)
                
                print(f"\n3. Respuesta de DELETE:")
                print(f"   Status Code: {response_delete.status_code}")
                print(f"   Headers Allow: {response_delete.headers.get('Allow', 'No especificado')}")
                print(f"   Body: {response_delete.text}")
                
                if response_delete.status_code == 200:
                    data_delete = response_delete.json()
                    if data_delete.get('success'):
                        print("\n✓✓✓ ÉXITO: Habitante eliminado correctamente")
                    else:
                        print(f"\n✗✗✗ ERROR: {data_delete.get('message')}")
                elif response_delete.status_code == 405:
                    print("\n✗✗✗ ERROR 405: Método no permitido")
                    print("   La ruta no acepta DELETE - revisar definición en Flask")
                else:
                    print(f"\n✗✗✗ ERROR HTTP {response_delete.status_code}")
            else:
                print("   ✗ No hay habitantes activos para probar")
        else:
            print(f"   ✗ No hay habitantes en la base de datos")
    else:
        print(f"   ✗ Error HTTP {response.status_code}")

if __name__ == "__main__":
    try:
        # Verificar que la API esté corriendo
        print("Verificando API...")
        ping = requests.get("http://127.0.0.1:5000/ping", timeout=2)
        if ping.status_code == 200:
            print("✓ API está corriendo\n")
            print("="*60)
            test_delete()
            print("="*60)
        else:
            print("✗ API no responde correctamente")
    except requests.exceptions.ConnectionError:
        print("✗ No se puede conectar a la API en http://127.0.0.1:5000")
        print("  Asegúrate de que el servidor esté corriendo")
    except Exception as e:
        print(f"✗ Error: {e}")
