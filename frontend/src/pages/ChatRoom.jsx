// src/pages/ChatRoom.jsx
import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useChat } from '../hooks/useChat';
import { useAuth } from '../context/AuthContext';

export default function ChatRoom() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [input, setInput] = useState('');
  const { messages, sendMessage, isConnected } = useChat(id);
  const messagesEndRef = useRef(null);

  // Scroll automático al fondo
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    sendMessage(input);
    setInput('');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: '#f5f5f5' }}>
      {/* Header */}
      <header style={{ padding: '1rem', background: '#fff', borderBottom: '1px solid #ddd', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
           <h3 style={{ margin: 0 }}>Sala #{id}</h3>
           <small style={{ color: isConnected ? 'green' : 'red' }}>
             {isConnected ? '● Conectado en tiempo real' : '● Desconectado'}
           </small>
        </div>
        <button onClick={() => navigate('/')} style={{ padding: '5px 10px' }}>Volver</button>
      </header>

      {/* Area de Mensajes */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '1rem' }}>
        {messages.map((msg, index) => {
          // Manejar mensajes de sistema
          if (msg.type === 'system') {
            return (
              <div key={index} style={{ textAlign: 'center', margin: '10px 0', color: '#888', fontSize: '0.8em' }}>
                <em>{msg.content}</em>
              </div>
            );
          }

          // Mensajes de usuarios
          const isMe = msg.username === user?.username;
          return (
            <div key={index} style={{ 
              display: 'flex', 
              justifyContent: isMe ? 'flex-end' : 'flex-start', 
              marginBottom: '10px' 
            }}>
              <div style={{ 
                maxWidth: '70%', 
                padding: '10px 15px', 
                borderRadius: '15px',
                borderTopLeftRadius: isMe ? '15px' : '2px',
                borderTopRightRadius: isMe ? '2px' : '15px',
                background: isMe ? '#007bff' : '#ffffff',
                color: isMe ? '#fff' : '#333',
                boxShadow: '0 1px 2px rgba(0,0,0,0.1)'
              }}>
                {!isMe && <strong style={{ display: 'block', fontSize: '0.75em', marginBottom: '2px', color: '#555' }}>{msg.username}</strong>}
                <div>{msg.content}</div>
                <div style={{ fontSize: '0.65em', textAlign: 'right', marginTop: '5px', opacity: 0.7 }}>
                  {new Date(msg.created_at).toLocaleTimeString()}
                </div>
              </div>
            </div>
          );
        })}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <form onSubmit={handleSend} style={{ padding: '1rem', background: '#fff', borderTop: '1px solid #ddd', display: 'flex' }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Escribe un mensaje..."
          style={{ flex: 1, padding: '12px', marginRight: '10px', borderRadius: '20px', border: '1px solid #ccc' }}
        />
        <button 
          type="submit" 
          disabled={!isConnected}
          style={{ padding: '0 20px', borderRadius: '20px', background: isConnected ? '#007bff' : '#ccc', color: '#fff', border: 'none', fontWeight: 'bold' }}
        >
          Enviar
        </button>
      </form>
    </div>
  );
}