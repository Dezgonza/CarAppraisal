# API de Tasación de Automóviles - Backend

## Instalación

```bash
cd backend
pip install -r requirements.txt
```

## Ejecutar el servidor

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Integrar tus funciones de tasación

### Opción 1: Funciones Síncronas (sin progreso)
Reemplaza estas funciones en `main.py` para tasaciones rápidas:

1. `obtener_precio_base_por_patente(patente: str)` - Tu lógica para obtener el precio base
2. `ajustar_precio_por_kilometraje(precio_base: float, kilometros: int)` - Tu lógica de ajuste por kilometraje

### Opción 2: Funciones Asíncronas (con progreso en tiempo real)
Para procesos largos, reemplaza estas funciones manteniendo las llamadas de progreso:

1. `obtener_precio_base_por_patente_async(patente: str, session_id: str)`
2. `ajustar_precio_por_kilometraje_async(precio_base: float, kilometros: int, session_id: str)`

**Ejemplo de integración con progreso global unificado:**
```python
async def obtener_precio_base_por_patente_async(patente: str, session_id: str, 
                                                global_step_offset: int = 0, 
                                                global_total_steps: int = 8) -> float:
    # Esta función tiene 5 pasos locales dentro del proceso global
    
    # Step 1 del proceso global (1/8 = 12.5%)
    await send_progress(session_id, global_step_offset + 1, global_total_steps, 
                       "Consultando base de datos...")
    # Tu lógica aquí
    
    # Step 2 del proceso global (2/8 = 25%)
    await send_progress(session_id, global_step_offset + 2, global_total_steps, 
                       "Analizando características...")
    # Tu lógica aquí
    
    # Steps 3-5...
    await send_progress(session_id, global_step_offset + 5, global_total_steps, 
                       "Precio base calculado")
    
    return precio_calculado

# La función de kilometraje continúa el progreso desde donde se quedó
async def ajustar_precio_por_kilometraje_async(precio_base: float, kilometros: int, 
                                               session_id: str, global_step_offset: int = 5, 
                                               global_total_steps: int = 8) -> float:
    # Steps 6-8 del proceso global (75% - 100%)
    await send_progress(session_id, global_step_offset + 1, global_total_steps, 
                       "Analizando kilometraje...")
    # Tu lógica aquí
    
    return precio_final
```

**Progreso Global:**
- **Sin kilometraje**: 5 steps total (precio base solamente)
- **Con kilometraje**: 8 steps total (5 precio base + 3 ajuste kilometraje)
- La barra progresa de 0% a 100% **una sola vez** durante todo el proceso

## Endpoints

### REST API
- `POST /valuar` - Estima el precio de un vehículo (modo rápido)
  - Body: `{"patente": "ABC123", "kilometros": 50000}`
- `POST /valuar-con-progreso` - Estima el precio con progreso en tiempo real
  - Body: `{"patente": "ABC123", "kilometros": 50000, "session_id": "opcional"}`
- `GET /health` - Verificar estado del servicio

### WebSocket
- `WebSocket /ws/{session_id}` - Conexión para recibir actualizaciones de progreso
  - Envía mensajes JSON con el progreso: `{"step": 1, "total_steps": 5, "message": "Procesando...", "percentage": 20.0, "session_id": "abc123"}`

## Sistema de Progreso

El sistema utiliza WebSockets para comunicación en tiempo real:

1. **Cliente** establece conexión WebSocket con un `session_id`
2. **Cliente** realiza petición POST a `/valuar-con-progreso` con el mismo `session_id`
3. **Servidor** envía actualizaciones de progreso a través del WebSocket
4. **Cliente** recibe y muestra el progreso en tiempo real

## Estructura de Mensajes de Progreso

```json
{
  "step": 3,
  "total_steps": 5,
  "message": "Analizando características del vehículo...",
  "percentage": 60.0,
  "session_id": "session_abc123_1234567890"
}
```