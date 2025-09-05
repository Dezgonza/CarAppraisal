# Imagen base con Python 3.11
FROM python:3.11-slim

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    chromium \
    fonts-liberation \
    libnss3 \
    libatk-bridge2.0-0 \
    libx11-xcb1 \
    libxcomposite1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libgtk-3-0 \
    wget \
    unzip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*
    
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
