// frontend/src/main.jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom' // <--- IMPORTANTE: Importar esto
import App from './App'
// import './index.css' // Si tienes estilos globales, déjalos aquí

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>  {/* <--- IMPORTANTE: Envolver App aquí */}
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)