# Aplicación de Tasación de Automóviles

Una aplicación web completa para estimar el precio de automóviles basada en patente y kilometraje.

## Estructura del Proyecto

```
app/
├── backend/          # API FastAPI
│   ├── main.py      # Servidor principal
│   ├── requirements.txt
│   └── README.md
└── frontend/         # Aplicación React
    ├── src/
    │   ├── App.jsx   # Componente principal
    │   ├── App.css   # Estilos
    │   └── main.jsx
    └── package.json
```

## Instalación y Ejecución

### Backend (FastAPI)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

El backend estará disponible en: http://localhost:8000

### Frontend (React)

```bash
cd frontend
npm install
npm run dev
```

El frontend estará disponible en: http://localhost:5173

## Integración de Funciones de Tasación

Para integrar tus funciones existentes de tasación:

### Opción 1: Funciones Simples (Sin progreso)
1. Reemplaza las funciones síncronas en `backend/main.py`:
   - `obtener_precio_base_por_patente(patente: str)` - Tu lógica de tasación base
   - `ajustar_precio_por_kilometraje(precio_base: float, kilometros: int)` - Ajuste por kilometraje

### Opción 2: Funciones con Progreso en Tiempo Real
1. Reemplaza las funciones asíncronas en `backend/main.py`:
   - `obtener_precio_base_por_patente_async(patente: str, session_id: str)` 
   - `ajustar_precio_por_kilometraje_async(precio_base: float, kilometros: int, session_id: str)`

2. Mantén las llamadas a `await send_progress()` para notificar el progreso:
   ```python
   await send_progress(session_id, step, total_steps, "Mensaje de progreso...")
   ```

## Características

- **Frontend moderno**: Interface intuitiva construida con React
- **API robusta**: Backend FastAPI con validación de datos
- **Progreso en tiempo real**: WebSockets para mostrar el progreso de funciones largas
- **Modo dual**: Tasación rápida o con progreso detallado
- **Responsive**: Diseño adaptable para móviles y desktop
- **CORS configurado**: Comunicación segura entre frontend y backend
- **Validación de datos**: Validación tanto en frontend como backend
- **Estados de carga**: Feedback visual durante las consultas

## API Endpoints

- `POST /valuar`: Estima el precio de un vehículo (modo rápido)
  - Body: `{"patente": "ABC123", "kilometros": 50000}`
- `POST /valuar-con-progreso`: Estima el precio con progreso en tiempo real
  - Body: `{"patente": "ABC123", "kilometros": 50000, "session_id": "opcional"}`
- `WebSocket /ws/{session_id}`: Conexión para recibir actualizaciones de progreso
- `GET /health`: Verificar estado del servicio
- `GET /`: Información de la API

## Uso del Sistema de Progreso

1. **Frontend**: Activa/desactiva "Mostrar progreso detallado" en la interfaz
2. **Backend**: Las funciones async envían progreso usando:
   ```python
   await send_progress(session_id, paso_actual, total_pasos, "Mensaje descriptivo")
   ```
3. **WebSocket**: La conexión se establece automáticamente cuando se activa el modo progreso

## Próximos Pasos

1. Integra tus funciones de tasación reales en `backend/main.py`
2. Personaliza los estilos en `frontend/src/App.css` si es necesario
3. Agrega más validaciones o campos según tus necesidades