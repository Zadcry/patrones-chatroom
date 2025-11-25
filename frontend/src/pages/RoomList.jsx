import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function RoomList() {
  const [rooms, setRooms] = useState([]);
  const [showCreate, setShowCreate] = useState(false);
  const { logout, user } = useAuth();
  const navigate = useNavigate();

  const [newRoomName, setNewRoomName] = useState('');
  const [isPrivate, setIsPrivate] = useState(false);
  const [newRoomPass, setNewRoomPass] = useState('');

  useEffect(() => {
    fetchRooms();
  }, []);

  const fetchRooms = async () => {
    try {
      const res = await apiClient.get('/rooms/');
      setRooms(res.data);
    } catch (error) {
      console.error("Error fetching rooms", error);
    }
  };

  const handleCreateRoom = async (e) => {
    e.preventDefault();
    try {
      await apiClient.post('/rooms/', {
        name: newRoomName,
        is_private: isPrivate,
        password: isPrivate ? newRoomPass : null
      });
      setShowCreate(false);
      setNewRoomName('');
      setNewRoomPass('');
      fetchRooms();
    } catch (error) {
      alert("Error creando sala: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleJoinRoom = async (room) => {
    let password = null;
    
    if (room.is_private) {
      password = prompt(`Ingrese la contraseña para la sala "${room.name}":`);
      if (!password) return;
    }

    try {
      await apiClient.post(`/rooms/${room.id}/join`, { password });
      navigate(`/room/${room.id}`);
    } catch (error) {
      if (error.response?.data?.message === "Already joined") {
         navigate(`/room/${room.id}`);
      } else {
         alert("No se pudo entrar: " + (error.response?.data?.detail || "Error desconocido"));
      }
    }
  };

  return (
    <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h1>Hola, {user?.username}</h1>
        <button onClick={logout} style={{ padding: '5px 10px', background: '#dc3545', color: 'white', border: 'none' }}>Cerrar Sesión</button>
      </header>

      {/* Formulario de Creación (Toggle) */}
      <div style={{ marginBottom: '2rem', padding: '1rem', border: '1px solid #ddd', borderRadius: '8px' }}>
        <button onClick={() => setShowCreate(!showCreate)} style={{ marginBottom: '10px' }}>
          {showCreate ? 'Cancelar' : '+ Crear Nueva Sala'}
        </button>
        
        {showCreate && (
          <form onSubmit={handleCreateRoom} style={{ marginTop: '10px' }}>
            <div style={{ marginBottom: '10px' }}>
              <input 
                type="text" 
                placeholder="Nombre de la sala" 
                value={newRoomName} 
                onChange={e => setNewRoomName(e.target.value)} 
                required 
                style={{ padding: '5px', marginRight: '10px' }}
              />
              <label>
                <input 
                  type="checkbox" 
                  checked={isPrivate} 
                  onChange={e => setIsPrivate(e.target.checked)} 
                /> Privada
              </label>
            </div>
            {isPrivate && (
              <div style={{ marginBottom: '10px' }}>
                <input 
                  type="password" 
                  placeholder="Contraseña de sala" 
                  value={newRoomPass} 
                  onChange={e => setNewRoomPass(e.target.value)} 
                  required={isPrivate}
                  style={{ padding: '5px' }} 
                />
              </div>
            )}
            <button type="submit" style={{ background: '#28a745', color: 'white', border: 'none', padding: '5px 15px' }}>Guardar</button>
          </form>
        )}
      </div>

      {/* Lista de Salas */}
      <h3>Salas Disponibles</h3>
      <ul style={{ listStyle: 'none', padding: 0 }}>
        {rooms.map((room) => (
          <li key={room.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px', borderBottom: '1px solid #eee', alignItems: 'center' }}>
            <div>
              <strong>{room.name}</strong>
              {room.is_private && <span style={{ marginLeft: '10px', fontSize: '0.8em' }}>🔒 Privada</span>}
            </div>
            <button onClick={() => handleJoinRoom(room)} style={{ padding: '5px 10px', cursor: 'pointer' }}>
              Entrar
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}