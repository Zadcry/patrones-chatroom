// src/hooks/useChat.js
import { useEffect, useState, useRef } from 'react';
import apiClient from '../api/client';

// Usamos window.location.hostname para que funcione tanto en localhost como en red
const PROTOCOL = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const WS_BASE = `${PROTOCOL}//${window.location.hostname}:8000`; // Ajusta el puerto si cambias el backend

export const useChat = (roomId) => {
  const [messages, setMessages] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef(null);

  // Cargar historial inicial (Requisito: Paginación)
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await apiClient.get(`/rooms/${roomId}/messages?limit=50`);
        // La API devuelve los más recientes primero, los invertimos para mostrar en el chat
        setMessages(res.data.reverse()); 
      } catch (error) {
        console.error("Error cargando historial", error);
      }
    };
    if (roomId) fetchHistory();
  }, [roomId]);

  // Conexión WebSocket
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token || !roomId) return;

    // Conectar pasando el token en query params
    const wsUrl = `${WS_BASE}/ws/${roomId}?token=${token}`;
    socketRef.current = new WebSocket(wsUrl);

    socketRef.current.onopen = () => {
      console.log('WS Connected');
      setIsConnected(true);
    };

    socketRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMessages((prev) => [...prev, data]);
    };

    socketRef.current.onclose = (e) => {
        console.log("WS Disconnected", e.code, e.reason);
        setIsConnected(false);
        // Si el código es 4003, es un error de permisos (no unido a sala)
        if(e.code === 4003) {
            alert("Error de permisos: " + e.reason);
            window.location.href = "/";
        }
    };

    return () => {
      if (socketRef.current) socketRef.current.close();
    };
  }, [roomId]);

  const sendMessage = (content) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(content);
    }
  };

  return { messages, sendMessage, isConnected };
};