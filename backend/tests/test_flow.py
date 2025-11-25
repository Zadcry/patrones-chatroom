import pytest

def get_auth_headers(client, username="user_flow"):
    password = "123"
    client.post("/auth/register", json={"username": username, "password": password})
    response = client.post("/auth/login", data={"username": username, "password": password})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, token

def test_create_public_room(client):
    headers, _ = get_auth_headers(client)
    response = client.post(
        "/rooms/",
        json={"name": "Test Room", "is_private": False},
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Test Room"
    assert response.json()["is_private"] is False

def test_join_private_room_wrong_password(client):
    # 1. Usuario Admin crea sala privada
    headers_admin, _ = get_auth_headers(client, "admin")
    client.post(
        "/rooms/",
        json={"name": "Secret Base", "is_private": True, "password": "secret"},
        headers=headers_admin
    )
    
    # 2. Obtener ID de la sala
    rooms = client.get("/rooms/", headers=headers_admin).json()
    room_id = rooms[0]["id"]

    # 3. Otro usuario intenta entrar con password incorrecto
    headers_user, _ = get_auth_headers(client, "intruder")
    response = client.post(
        f"/rooms/{room_id}/join",
        json={"password": "wrong"},
        headers=headers_user
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid room password"

def test_websocket_chat_flow(client):
    """
    Prueba de integración completa:
    Auth -> Crear Sala -> Unirse -> WebSocket -> Enviar Mensaje
    """
    # 1. Auth
    headers, token = get_auth_headers(client, "chat_tester")
    
    # 2. Crear Sala
    res_room = client.post(
        "/rooms/",
        json={"name": "Chat Unit Test", "is_private": False},
        headers=headers
    )
    room_id = res_room.json()["id"]

    # 3. Unirse a la sala (Requisito para conectar WS)
    client.post(f"/rooms/{room_id}/join", json={}, headers=headers)

    # 4. Conectar WebSocket
    with client.websocket_connect(f"/ws/{room_id}?token={token}") as websocket:
        msg_content = "Hello from Pytest!"
        websocket.send_text(msg_content)
        
        found = False
        for _ in range(3):
            data = websocket.receive_json()
            if data.get("content") == msg_content:
                found = True
                assert data["username"] == "chat_tester"
                break
        
        assert found is True, "El mensaje enviado no fue recibido de vuelta por el WS"