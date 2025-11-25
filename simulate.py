import asyncio
import aiohttp
import websockets
import json
import time
import random
import string
import numpy as np

# --- CONFIGURACIÓN ---
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"
NUM_USERS = 20          
MESSAGES_PER_USER = 5   
ROOM_NAME = "LoadTestRoom"

latencies = []

def generate_random_string(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

async def ensure_room_exists(session, token):
    """Crea la sala de pruebas si no existe"""
    # 1. Listar salas para ver si existe
    async with session.get(f"{BASE_URL}/rooms/") as resp:
        rooms = await resp.json()
        for r in rooms:
            if r['name'] == ROOM_NAME:
                print(f"--- Sala '{ROOM_NAME}' encontrada (ID: {r['id']}) ---")
                return r['id']

    # 2. Si no existe, crearla
    print(f"--- Creando sala '{ROOM_NAME}' ---")
    payload = {"name": ROOM_NAME, "is_private": False}
    async with session.post(f"{BASE_URL}/rooms/", json=payload, headers={"Authorization": f"Bearer {token}"}) as resp:
        if resp.status == 200:
            data = await resp.json()
            return data['id']
        else:
            print(f"Error creando sala: {await resp.text()}")
            return None

async def bot_lifecycle(session, user_idx, room_id):
    username = f"bot_{generate_random_string(5)}"
    password = "password123"
    
    try:
        # Registro y Login
        await session.post(f"{BASE_URL}/auth/register", json={"username": username, "password": password})
        
        data = {'username': username, 'password': password}
        async with session.post(f"{BASE_URL}/auth/login", data=data) as resp:
            if resp.status != 200:
                print(f"[{user_idx}] Error login")
                return
            token = (await resp.json())['access_token']

        # Unirse a la sala (Usando el ID dinámico)
        await session.post(f"{BASE_URL}/rooms/{room_id}/join", headers={"Authorization": f"Bearer {token}"}, json={})

        # Conexión WebSocket
        ws_endpoint = f"{WS_URL}/ws/{room_id}?token={token}"
        
        # Configuración tolerante a latencia
        async with websockets.connect(ws_endpoint, ping_interval=None, close_timeout=10) as websocket:
            for i in range(MESSAGES_PER_USER):
                msg_content = f"ping_{username}_{i}_{time.time()}"
                start_time = time.perf_counter()
                
                await websocket.send(msg_content)
                
                while True:
                    response = await websocket.recv()
                    data = json.loads(response)
                    if data.get("username") == username and data.get("content") == msg_content:
                        latencies.append((time.perf_counter() - start_time) * 1000)
                        break
                
                await asyncio.sleep(random.uniform(0.1, 0.5))

    except Exception as e:
        print(f"[{user_idx}] Error: {e}")

async def main():
    print(f"--- INICIANDO SIMULACIÓN DE CARGA ---")
    
    async with aiohttp.ClientSession() as session:
        # 1. Crear un usuario admin temporal para crear la sala
        admin_user = "admin_bot_" + generate_random_string(3)
        await session.post(f"{BASE_URL}/auth/register", json={"username": admin_user, "password": "123"})
        async with session.post(f"{BASE_URL}/auth/login", data={"username": admin_user, "password": "123"}) as resp:
             token = (await resp.json())['access_token']

        # 2. Obtener/Crear ID de sala valido
        room_id = await ensure_room_exists(session, token)
        if not room_id: return

        # 3. Lanzar bots
        tasks = [bot_lifecycle(session, i, room_id) for i in range(NUM_USERS)]
        start_global = time.time()
        await asyncio.gather(*tasks)
        duration = time.time() - start_global
        
    print(f"\n--- RESULTADOS ---")
    print(f"Tiempo: {duration:.2f}s | Mensajes: {len(latencies)}/{NUM_USERS*MESSAGES_PER_USER}")
    if latencies:
        print(f"Latencia P95: {np.percentile(latencies, 95):.2f} ms")
        if np.percentile(latencies, 95) < 850:
            print("✅ ÉXITO: Latencia aceptable (<850)")
        else:
            print("⚠️ ALERTA: Latencia alta (>850)")

if __name__ == "__main__":
    asyncio.run(main())