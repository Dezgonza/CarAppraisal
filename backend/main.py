from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict
import asyncio
import uuid

from scrap_pipeline import scrap_pipeline_async
from get_info_by_patente import get_info_by_patente

app = FastAPI(title="Car Valuation API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",
                   "http://localhost:5173",
                   "https://car-appraisal.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Almacenar conexiones WebSocket activas
websocket_connections: Dict[str, WebSocket] = {}

class VehicleData(BaseModel):
    brand: str
    model: str
    year: int
    version: Optional[str] = None

class ValuationRequest(BaseModel):
    # Opción 1: Por patente
    patente: Optional[str] = None
    
    # Opción 2: Por datos del vehículo
    vehicle_data: Optional[VehicleData] = None
    
    # Campos comunes
    kilometers: Optional[int] = None
    session_id: Optional[str] = None
    
    # Validación: debe tener patente O vehicle_data
    def __init__(self, **data):
        super().__init__(**data)
        if not self.patente and not self.vehicle_data:
            raise ValueError("Debe proporcionar patente o datos del vehículo")
        if self.patente and self.vehicle_data:
            raise ValueError("Debe proporcionar solo patente o datos del vehículo, no ambos")

class ValuationResponse(BaseModel):
    # Campos de identificación del vehículo
    patente: Optional[str] = None
    vehicle_data: Optional[VehicleData] = None
    
    # Resultado
    precio_estimado: float
    precio_compra: Optional[float] = None
    kilometers: Optional[int] = None
    message: str
    session_id: str

class ProgressMessage(BaseModel):
    step: int
    total_steps: int
    message: str
    percentage: float
    session_id: str

# Función para enviar progreso
async def send_progress(session_id: str, step: int, total_steps: int, message: str):
    if session_id in websocket_connections:
        percentage = (step / total_steps) * 100
        progress_msg = ProgressMessage(
            step=step,
            total_steps=total_steps,
            message=message,
            percentage=percentage,
            session_id=session_id
        )
        try:
            await websocket_connections[session_id].send_text(progress_msg.json())
        except:
            # Si falla el envío, remover la conexión
            if session_id in websocket_connections:
                del websocket_connections[session_id]

async def get_base_df_price_async(patente: Optional[str], vehicle_data: Optional[VehicleData], session_id: str, global_step_offset: int = 0, global_total_steps: int = 8) -> float:
    """
    Función async con steps de progreso global unificado.
    Funciona con patente o datos del vehículo.
    Reemplaza con tu lógica de tasación real manteniendo la estructura de progreso.
    
    Args:
        patente: Patente del vehículo (opcional si se proveen datos del vehículo)
        vehicle_data: Datos del vehículo (marca, modelo, año, versión)
        session_id: ID de sesión para WebSocket
        global_step_offset: Offset para el progreso global
        global_total_steps: Total de steps en todo el proceso de tasación
    """
    
    if patente:
        await send_progress(session_id, global_step_offset + 1, global_total_steps, "Validando patente...")
        await asyncio.sleep(1)
        
        await send_progress(session_id, global_step_offset + 2, global_total_steps, "Consultando base de datos por patente...")
        await asyncio.sleep(1)
        
        vehicle_data = get_info_by_patente(patente)
        brand = vehicle_data["Marca"].lower()
        model = vehicle_data["Modelo"].lower()
        year = int(vehicle_data["Año"])
        
    else:  # vehicle_data
        await send_progress(session_id, global_step_offset + 1, global_total_steps, "Validando datos del vehículo...")
        await asyncio.sleep(1)
        
        await send_progress(session_id, global_step_offset + 2, global_total_steps, f"Consultando precios para {vehicle_data.brand} {vehicle_data.model}...")
        await asyncio.sleep(1)
        
        # Simulación de precios base según datos del vehículo
        brand = vehicle_data.brand.lower()
        model = vehicle_data.model.lower()
        year = vehicle_data.year

    await send_progress(session_id, global_step_offset + 3, global_total_steps, "Consultando base de datos por patente...")  
    df = scrap_pipeline_async(brand, model, year)
    df = df[(df.price.notna()) & (df.year==year)].drop_duplicates()
    print(df)

    return df

async def ajust_price_by_kilometers_deprecation_async(df_base_price, kilometers: int, session_id: str, global_step_offset: int = 5, global_total_steps: int = 8) -> float:
    """
    Función async con regresión lineal para ajuste por kilometraje basado en datos reales.
    
    Args:
        df_base_price: DataFrame con datos de precios y kilómetros
        kilometers: Kilometraje del vehículo a tasar
        session_id: ID de sesión para WebSocket
        global_step_offset: Offset para el progreso global
        global_total_steps: Total de steps en todo el proceso
    """
    from sklearn.linear_model import LinearRegression
    
    await send_progress(session_id, global_step_offset + 1, global_total_steps, "Analizando datos de kilometraje...")
    await asyncio.sleep(1)
    
    # Filtrar datos válidos
    valid_data = df_base_price[(df_base_price.km.notna()) & (df_base_price.price.notna())].copy()
    
    if len(valid_data) < 3:
        # Si no hay suficientes datos, usar método tradicional
        await send_progress(session_id, global_step_offset + 2, global_total_steps, "Pocos datos disponibles, usando método estándar...")
        base_price = valid_data['price'].mean() if len(valid_data) > 0 else 10000000
        
        if kilometers <= 50000:
            final_price = base_price
        elif kilometers <= 100000:
            final_price = base_price * 0.9
        elif kilometers <= 150000:
            final_price = base_price * 0.8
        else:
            final_price = base_price * 0.7
    else:
        await send_progress(session_id, global_step_offset + 2, global_total_steps, "Entrenando modelo de regresión...")
        await asyncio.sleep(1)
        
        # Preparar datos para regresión
        X = valid_data[['km']].values
        y = valid_data['price'].values
        
        # Entrenar modelo
        model = LinearRegression()
        model.fit(X, y)
        
        # Predecir precio basado en kilometraje
        predicted_price = model.predict([[kilometers]])[0]
        
        # Asegurar que el precio no sea negativo
        final_price = max(predicted_price, valid_data['price'].min())
    
    await send_progress(session_id, global_step_offset + 3, global_total_steps, "Ajuste por kilometraje completado")
    await asyncio.sleep(0.5)
    
    return final_price

# Funciones síncronas para compatibilidad (mantener para el endpoint original)
def obtener_base_price(patente: Optional[str], vehicle_data: Optional[VehicleData]) -> float:
    """
    Función síncrona para tasación rápida (sin progreso).
    Reemplaza con tu lógica de tasación real.
    """
    if patente:
        example_prices = {
            "ABC123": 15000000,
            "DEF456": 8500000,
            "GHI789": 12000000,
        }
        return example_prices.get(patente.upper(), 10000000)
    
    else:  # vehicle_data
        brand = vehicle_data.brand.upper()
        model = vehicle_data.model.upper()
        year = vehicle_data.year
        
        # Base de datos simulada por marca/modelo/año
        precios_vehiculos = {
            ("TOYOTA", "COROLLA"): 12000000,
            ("HONDA", "CIVIC"): 14000000,
            ("NISSAN", "SENTRA"): 11000000,
            ("CHEVROLET", "CRUZE"): 10000000,
        }
        
        base_price = precios_vehiculos.get((brand, model), 9000000)
        
        # Ajuste por año
        actual_year = 2024
        year_diff = actual_year - year
        year_factor = max(0.5, 1 - (year_diff * 0.05))
        base_price = base_price * year_factor
        
        return base_price

def ajust_price_by_kilometers_deprecation(base_price: float, kilometers: int) -> float:
    """
    Placeholder para ajuste de precio por kilometraje.
    Reemplaza con tu lógica real.
    """
    if kilometers <= 50000:
        return base_price
    elif kilometers <= 100000:
        return base_price * 0.9
    elif kilometers <= 150000:
        return base_price * 0.8
    else:
        return base_price * 0.7
    
def ajust_price_by_year_deprecation(base_price, year, percent=5):
        
    # Ajuste por año (depreciación/apreciación)
    actual_year = 2025
    year_diff = actual_year - year
    year_factor = max(0.5, 1 - (year_diff * percent/100))  # 5% menos por año

    return base_price * year_factor

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    websocket_connections[session_id] = websocket
    
    try:
        while True:
            # Mantener conexión viva
            await websocket.receive_text()
    except WebSocketDisconnect:
        if session_id in websocket_connections:
            del websocket_connections[session_id]

@app.get("/")
def read_root():
    return {"message": "API de Tasación de Automóviles"}

@app.post("/valuar", response_model=ValuationResponse)
def valuar_vehiculo(request: ValuationRequest):
    try:
        session_id = request.session_id or str(uuid.uuid4())
        
        # Usar las funciones síncronas (sin progreso)
        base_price = obtener_base_price(request.patente, request.vehicle_data)
        
        if request.kilometers:
            final_price = ajust_price_by_kilometers_deprecation(base_price, request.kilometers)
            message = f"Precio ajustado por kilometraje ({request.kilometers:,} km)"
        else:
            final_price = base_price
            message = "Precio base (sin ajuste por kilometraje)"
        
        # Determinar qué información mostrar en la respuesta
        response_data = {
            "precio_estimado": final_price,
            "kilometers": request.kilometers,
            "message": message,
            "session_id": session_id
        }
        
        if request.patente:
            response_data["patente"] = request.patente.upper()
        else:
            response_data["vehicle_data"] = request.vehicle_data
        
        return ValuationResponse(**response_data)
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al valuar vehículo: {str(e)}")

@app.post("/valuar-con-progreso", response_model=ValuationResponse)
async def valuar_vehiculo_con_progreso(request: ValuationRequest):
    def custom_func(x: float) -> float:
        return 0.1 * x + 1e6
    try:
        session_id = request.session_id or str(uuid.uuid4())
        
        # Definir el total de steps global para todo el proceso
        total_global_steps = 10 if request.kilometers else 7
        
        # Usar las funciones async con progreso global unificado
        # Precio base: steps 1-5 (offset 0)
        df_base_price = await get_base_df_price_async(
            request.patente, 
            request.vehicle_data,
            session_id, 
            global_step_offset=0, 
            global_total_steps=total_global_steps
        )
        
        if request.kilometers:
            # Ajuste por kilometraje: steps 6-8 (offset 5)
            estimed_price = await ajust_price_by_kilometers_deprecation_async(
                df_base_price, 
                request.kilometers, 
                session_id,
                global_step_offset=5,
                global_total_steps=total_global_steps
            )
            message = f"Precio ajustado por kilometraje ({request.kilometers:,} km)"
        else:
            estimed_price = df_base_price['price'].mean() if len(df_base_price) > 0 else 10000000
            message = "Precio base (sin ajuste por kilometraje)"

        # Enviar progreso final
        await send_progress(session_id, total_global_steps-1, total_global_steps, "Ajuste toma vehiculo")
        final_price = estimed_price - custom_func(estimed_price)
        
        # Enviar progreso final
        await send_progress(session_id, total_global_steps, total_global_steps, "¡Tasación completada!")
        
        # Determinar qué información mostrar en la respuesta
        response_data = {
            "precio_estimado": estimed_price,
            "precio_compra": final_price,
            "kilometers": request.kilometers,
            "message": message,
            "session_id": session_id
        }
        
        if request.patente:
            response_data["patente"] = request.patente.upper()
        else:
            response_data["vehicle_data"] = request.vehicle_data
        
        return ValuationResponse(**response_data)
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al valuar vehículo: {str(e)}")

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# await send_progress(session_id, global_step_offset + 3, global_total_steps, "Analizando características del vehículo...")
#     await asyncio.sleep(2)
    
#     await send_progress(session_id, global_step_offset + 4, global_total_steps, "Calculando precio base...")
#     await asyncio.sleep(1)
    
#     await send_progress(session_id, global_step_offset + 5, global_total_steps, "Precio base calculado correctamente")
#     await asyncio.sleep(0.5)
    
#     return base_price