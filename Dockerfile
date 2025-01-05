# Basis-Image
FROM python:3.9-slim

# Arbeitsverzeichnis festlegen
WORKDIR /app

# Abhängigkeiten installieren
COPY requirements.txt .
RUN apt-get update && apt-get install -y \
    libfreetype6 \
    libjpeg62-turbo \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

# Anwendungscode kopieren
COPY . .

# Fonts kopieren
COPY fonts/ /app/fonts/

# Port freigeben
EXPOSE 8080

# Logs sofort ausgeben
ENV PYTHONUNBUFFERED=1

# Anwendung starten
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
