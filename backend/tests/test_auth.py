def test_register_user(client):
    response = client.post(
        "/auth/register",
        json={"username": "testuser", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert "id" in data

def test_register_duplicate_user(client):
    client.post("/auth/register", json={"username": "user1", "password": "123"})
    response = client.post("/auth/register", json={"username": "user1", "password": "123"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already registered"

def test_login_user(client):
    client.post("/auth/register", json={"username": "loginuser", "password": "securepass"})
    
    response = client.post(
        "/auth/login",
        data={"username": "loginuser", "password": "securepass"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client):
    client.post("/auth/register", json={"username": "user2", "password": "123"})
    response = client.post(
        "/auth/login",
        data={"username": "user2", "password": "WRONG_PASSWORD"}
    )
    assert response.status_code == 401