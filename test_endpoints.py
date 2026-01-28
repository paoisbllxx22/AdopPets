import httpx
import asyncio
import uuid

# URL del Backend (NodePort definido en k8s/backend-service.yaml es 30000)
# - Puerto 30000: API Backend Directa (JSON/Data puro) -> Lo que vamos a probar aquí.
# - Puerto 30001: Frontend Visual (HTML) -> Donde ves la página web.
#
# URL del Backend
# Al probar DENTRO de la VPS, usamos localhost:30000
BASE_URL = "http://localhost:30000" 

async def test_register_and_login():
    random_id = str(uuid.uuid4())[:8]
    email = f"test_{random_id}@example.com"
    password = "password123"
    name = f"Test User {random_id}"

    print(f"--- Probando Registro con: {email} ---")
    
    # Datos de formulario como espera FastAPI (Form)
    data = {
        "name": name,
        "email": email,
        "password": password
    }

    async with httpx.AsyncClient() as client:
        try:
            # 1. PRUEBA DE REGISTRO
            print(f"Enviando POST a {BASE_URL}/users/register...")
            response = await client.post(f"{BASE_URL}/users/register", data=data)
            
            print(f"Status Code Registro: {response.status_code}")
            print(f"Respuesta Registro: {response.text}")

            if response.status_code != 200:
                print("❌ Falló el registro. Deteniendo prueba.")
                return

            print("✅ Registro exitoso.")

            # 2. PRUEBA DE LOGIN
            print(f"\n--- Probando Login con: {email} ---")
            login_data = {
                "email": email,
                "password": password
            }
            # Login espera JSON según tu código Backend
            print(f"Enviando POST a {BASE_URL}/users/login (JSON)...") 
            # OJO: En tu router backend/routers/user.py dijimos:
            # @router.post("/login") async def login(data: UserLogin): ...
            # UserLogin es pydantic, así que espera JSON body.
            
            login_resp = await client.post(f"{BASE_URL}/users/login", json=login_data)
            
            print(f"Status Code Login: {login_resp.status_code}")
            print(f"Respuesta Login: {login_resp.text}")

            if login_resp.status_code == 200:
                print("✅ Login exitoso. Token recibido.")
            else:
                print("❌ Falló el login.")

        except Exception as e:
            print(f"❌ Error de conexión: {e}")
            print("Asegúrate de que la IP sea correcta y el puerto 30000 esté abierto en el firewall de Google Cloud.")

if __name__ == "__main__":
    asyncio.run(test_register_and_login())
