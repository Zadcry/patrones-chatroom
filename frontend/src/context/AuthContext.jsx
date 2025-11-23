// frontend/src/context/AuthContext.jsx
import { createContext, useState, useContext, useEffect } from 'react';
import { jwtDecode } from "jwt-decode";
import apiClient from '../api/client';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      try {
        const decoded = jwtDecode(token);
        setUser({ username: decoded.sub });
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      } catch (error) {
        logout();
      }
    }
    setLoading(false);
  }, [token]);

  const login = async (username, password) => {
    try {
      // CORRECCIÓN 1: Usar URLSearchParams para enviar x-www-form-urlencoded
      // Esto es lo que FastAPI OAuth2PasswordRequestForm espera estrictamente.
      const params = new URLSearchParams();
      params.append('username', username);
      params.append('password', password);

      const { data } = await apiClient.post('/auth/login', params, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      
      localStorage.setItem('token', data.access_token);
      setToken(data.access_token);
      // Actualizar el header global para futuras peticiones
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`;
      
      // Decodificar usuario inmediatamente para actualizar UI
      const decoded = jwtDecode(data.access_token);
      setUser({ username: decoded.sub });

      return { success: true };
    } catch (error) {
      console.error("Login error:", error);
      // CORRECCIÓN 2: Manejo seguro del mensaje de error para evitar crash de React
      let errorMessage = 'Login failed';
      
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        if (Array.isArray(detail)) {
            // Si es un error de validación (array), tomamos el primer mensaje
            errorMessage = detail[0].msg; 
        } else if (typeof detail === 'object') {
            // Si es un objeto, lo convertimos a string
            errorMessage = JSON.stringify(detail);
        } else {
            // Si es texto plano
            errorMessage = detail;
        }
      }
      return { success: false, error: errorMessage };
    }
  };

  const register = async (username, password) => {
    try {
      // El registro usa JSON (Pydantic), así que no necesita cambios en formato
      await apiClient.post('/auth/register', { username, password });
      return { success: true };
    } catch (error) {
      console.error("Register error:", error);
      // Misma lógica de seguridad para el error
      let errorMessage = 'Registration failed';
      if (error.response?.data?.detail) {
         const detail = error.response.data.detail;
         errorMessage = Array.isArray(detail) ? detail[0].msg : String(detail);
      }
      return { success: false, error: errorMessage };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    delete apiClient.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, loading }}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);