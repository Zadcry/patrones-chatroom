
# Chatroom en Tiempo Real — Proyecto/Parcial III

Aplicación de chat en tiempo real con salas públicas y privadas, autenticación JWT, historial DB PostgreSQL y mensajería con RabbitMQ. El proyecto tiene un backend en FastAPI que maneja REST y WebSockets, un frontend en React, un broker RabbitMQ y un worker que persiste los mensajes en la base de datos.

## Características principales

- Autenticación JWT con contraseñas hasheadas.
- Salas públicas y privadas.
- Chat en tiempo real con WebSockets.
- Persistencia de mensajes con RabbitMQ y el worker.
- Historial de mensajes.

## Cómo ejecutar con Docker Compose

### 1. Clonar el repositorio

```bash
git clone https://github.com/Zadcry/patrones-chatroom.git
cd patrones-chatroom
```

### 2. Levantar servicios

```bash
docker-compose up --build
```

Servicios disponibles:

| Servicio | URL |
|---------|-----|
| Backend (FastAPI) | http://localhost:8000 |
| Frontend (React) | http://localhost:3000 |
| RabbitMQ UI | http://localhost:15672 |
| PostgreSQL | localhost:5432 |

Credenciales por defecto de RabbitMQ: guest / guest

### 3. Ejecutar el worker

```bash
docker-compose exec backend sh
python worker.py
```

## Endpoints principales (REST)

### Autenticación
- POST /auth/register — Registro
- POST /auth/login — Obtención de token JWT

### Salas
- GET /rooms/ — Listado
- POST /rooms/ — Crear sala
- POST /rooms/{id}/join — Unirse a sala

### Historial
- GET /rooms/{id}/messages?limit=50&offset=0

## WebSocket

Conexión:

```
ws://localhost:8000/ws/{room_id}?token=<JWT>
```

Ejemplo de mensaje:

```json
{
  "room_id": 1,
  "user_id": 3,
  "username": "Mauricio",
  "content": "Hola soy Mauricio",
  "created_at": "2025-01-01T18:00:00Z"
}
```

## Modelo de datos

Tablas principales:

- users
- rooms
- room_members (PrimaryKey: room_id, user_id)
- messages

## Flujo general

1. Usuario se registra o inicia sesión.
2. Crea o se une a una sala.
3. Frontend abre WebSocket con JWT.
4. Backend valida token.
5. Usuario manda mensajes.
6. Worker guarda los mensajes en PostgreSQL.
7. Historial se consulta por REST (para cargar chats).

## Tecnologías utilizadas

- Backend: FastAPI, SQLAlchemy, WebSockets, JWT, Bcrypt, RabbitMQ, PostgreSQL
- Frontend: React, Vite, Axios
- Infraestructura: Docker

## Autores

Arciniegas Guerrero, Camilo  
Zafra Moreno, Julián Mauricio
