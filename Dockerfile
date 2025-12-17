#Installe python 3.11
FROM python:3.11-slim

#Empeche la création de fichier python
ENV PYTHONDONTWRITEBYTECODE=1

#Affiche les logs
ENV PYTHONUNBUFFERED=1

#Dossier du container
WORKDIR /app

#Copie le fichier des dépendances
COPY requirements.txt .

#Installation des dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

#Copie du reste du code backend
COPY . .

#Exposition du port utilisé par l'API
EXPOSE 8000

#Commande de démarrage du backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
