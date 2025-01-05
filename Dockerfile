# Basis-Image
FROM python:3.9-slim

# Arbeitsverzeichnis festlegen
WORKDIR /app

# Abhängigkeiten installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Anwendungscode kopieren
COPY . .

# Port freigeben
EXPOSE 8080

# Anwendung starten
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
