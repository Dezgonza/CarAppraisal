# Imagen base con Python 3.11
FROM python:3.11-slim

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Crear directorio de la app
WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt

# Copiar el código de la app
COPY . /app/

# Exponer puerto
EXPOSE 8000

# Comando por defecto para correr la app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
