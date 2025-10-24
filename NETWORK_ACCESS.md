# Accès Réseau - MCP Weather Server

Ce guide explique comment déployer le serveur MCP Weather pour qu'il soit accessible depuis d'autres ordinateurs sur le réseau.

## Architecture

Le serveur peut fonctionner en deux modes:

1. **Mode Local (stdio)**: Communication via stdin/stdout (pour usage local uniquement)
2. **Mode Réseau (HTTP)**: Communication via HTTP/REST API (accessible depuis le réseau)

## Déploiement en Mode Réseau

### Option 1: Docker Compose (Recommandé)

```bash
# Démarrer le serveur réseau
docker-compose -f docker-compose.network.yml up -d

# Vérifier que le serveur fonctionne
curl http://localhost:8081/health
```

Le serveur sera accessible sur le port **8081** (mappé depuis le port interne 8080).

### Option 2: Docker manuel

```bash
# Construire l'image
docker build -f Dockerfile.network -t mcp-weather-server:network .

# Démarrer le conteneur
docker run -d \
  --name mcp-weather-server-network \
  -p 8080:8081 \
  -e WEATHERAPI_KEY=13ced4f0f05a4a4f986223827252410 \
  mcp-weather-server:network

# Vérifier
curl http://localhost:8081/health
```

### Option 3: Python directement

```bash
# Installer les dépendances supplémentaires
pip install fastapi uvicorn websockets

# Lancer le serveur
python network_server.py
```

## Configuration Réseau

### Trouver l'adresse IP de votre machine

**macOS/Linux:**
```bash
# Adresse IP locale
ifconfig | grep "inet " | grep -v 127.0.0.1

# Ou
ip addr show | grep "inet " | grep -v 127.0.0.1
```

**Windows:**
```cmd
ipconfig | findstr IPv4
```

Exemple de sortie: `192.168.1.100`

### Accès depuis un autre ordinateur

Une fois le serveur démarré, il est accessible depuis n'importe quel ordinateur sur le même réseau:

```
http://[ADRESSE_IP]:8081
```

Exemple: `http://192.168.1.100:8081`

## Endpoints API

### 1. Informations du serveur

```bash
curl http://192.168.1.100:8081/
```

Réponse:
```json
{
  "name": "MCP Weather Server",
  "version": "1.0.0",
  "status": "running",
  "endpoints": {
    "health": "/health",
    "current_weather": "/weather/current",
    "forecast": "/weather/forecast",
    "tools": "/tools"
  }
}
```

### 2. Health Check

```bash
curl http://192.168.1.100:8081/health
```

### 3. Liste des outils disponibles

```bash
curl http://192.168.1.100:8081/tools
```

### 4. Météo actuelle

```bash
# Par nom de ville
curl "http://192.168.1.100:8081/weather/current?location=Paris&units=metric"

# Par coordonnées
curl "http://192.168.1.100:8081/weather/current?location=48.8566,2.3522&units=metric"
```

### 5. Prévisions météo

```bash
# 5 jours pour Paris
curl "http://192.168.1.100:8081/weather/forecast?location=Paris&days=5&units=metric"

# 3 jours pour Montréal
curl "http://192.168.1.100:8081/weather/forecast?location=Montreal&days=3&units=metric"
```

### 6. Endpoint MCP (JSON-RPC)

```bash
# Lister les outils
curl -X POST http://192.168.1.100:8081/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }'

# Appeler un outil
curl -X POST http://192.168.1.100:8081/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "get_current_weather",
      "arguments": {
        "location": "Paris",
        "units": "metric"
      }
    }
  }'
```

## Configuration des Clients

### Client Python

```python
import requests

# Adresse du serveur
SERVER_URL = "http://192.168.1.100:8081"

# Obtenir la météo actuelle
response = requests.get(
    f"{SERVER_URL}/weather/current",
    params={"location": "Paris", "units": "metric"}
)
weather = response.json()
print(f"Température à Paris: {weather['current']['temperature']}")

# Obtenir les prévisions
response = requests.get(
    f"{SERVER_URL}/weather/forecast",
    params={"location": "Montreal", "days": 5, "units": "metric"}
)
forecast = response.json()
print(f"Prévisions pour {forecast['location']}")
for day in forecast['forecast']:
    print(f"  {day['date']}: {day['temperature']['min']} - {day['temperature']['max']}")
```

### Client JavaScript/Node.js

```javascript
const axios = require('axios');

const SERVER_URL = 'http://192.168.1.100:8081';

// Météo actuelle
async function getCurrentWeather(location) {
  const response = await axios.get(`${SERVER_URL}/weather/current`, {
    params: { location, units: 'metric' }
  });
  return response.data;
}

// Prévisions
async function getForecast(location, days = 7) {
  const response = await axios.get(`${SERVER_URL}/weather/forecast`, {
    params: { location, days, units: 'metric' }
  });
  return response.data;
}

// Utilisation
getCurrentWeather('Paris').then(weather => {
  console.log(`Température: ${weather.current.temperature}`);
});
```

### Client cURL (Bash)

```bash
#!/bin/bash

SERVER_URL="http://192.168.1.100:8081"

# Fonction pour obtenir la météo
get_weather() {
    local location=$1
    curl -s "${SERVER_URL}/weather/current?location=${location}&units=metric" | jq .
}

# Fonction pour obtenir les prévisions
get_forecast() {
    local location=$1
    local days=${2:-7}
    curl -s "${SERVER_URL}/weather/forecast?location=${location}&days=${days}&units=metric" | jq .
}

# Utilisation
get_weather "Paris"
get_forecast "Montreal" 5
```

## Sécurité

### Pare-feu

**Autoriser le port 8080:**

**macOS:**
```bash
# Vérifier le pare-feu
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# Autoriser l'application
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/local/bin/docker
```

**Linux (UFW):**
```bash
sudo ufw allow 8080/tcp
sudo ufw reload
```

**Windows:**
```powershell
# Ouvrir le pare-feu Windows
New-NetFirewallRule -DisplayName "MCP Weather Server" -Direction Inbound -LocalPort 8080 -Protocol TCP -Action Allow
```

### Authentification (Optionnel)

Pour ajouter une authentification basique, modifiez `network_server.py`:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

security = HTTPBasic()

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "admin")
    correct_password = secrets.compare_digest(credentials.password, "your_password")
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# Ajouter à chaque endpoint
@app.get("/weather/current")
async def get_current_weather_endpoint(
    location: str,
    units: str = "metric",
    username: str = Depends(verify_credentials)
):
    # ... reste du code
```

### HTTPS (Production)

Pour un déploiement en production, utilisez HTTPS:

```bash
# Avec un reverse proxy (nginx)
docker run -d \
  --name nginx-proxy \
  -p 443:443 \
  -v /path/to/certs:/etc/nginx/certs \
  nginx

# Ou avec Caddy (auto-SSL)
docker run -d \
  --name caddy \
  -p 443:443 \
  -v caddy_data:/data \
  caddy:latest \
  caddy reverse-proxy --from weather.example.com --to mcp-weather-server-network:8081
```

## Accès depuis Internet (Optionnel)

### Avec ngrok (Tunnel temporaire)

```bash
# Installer ngrok
brew install ngrok  # macOS
# ou télécharger depuis https://ngrok.com/

# Créer un tunnel
ngrok http 8080

# Vous obtiendrez une URL publique comme:
# https://abc123.ngrok.io
```

### Avec un VPN (Tailscale)

```bash
# Installer Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Se connecter
sudo tailscale up

# Le serveur sera accessible via l'IP Tailscale
# Exemple: http://100.x.y.z:8081
```

## Monitoring

### Logs en temps réel

```bash
# Docker
docker logs -f mcp-weather-server-network

# Docker Compose
docker-compose -f docker-compose.network.yml logs -f
```

### Métriques

```bash
# Nombre de requêtes
docker exec mcp-weather-server-network cat /proc/net/tcp | wc -l

# Utilisation CPU/Mémoire
docker stats mcp-weather-server-network
```

## Dépannage

### Le serveur n'est pas accessible depuis un autre ordinateur

1. **Vérifier que le serveur écoute sur 0.0.0.0:**
   ```bash
   docker exec mcp-weather-server-network netstat -tuln | grep 8080
   ```

2. **Vérifier le pare-feu:**
   ```bash
   # Tester depuis le serveur lui-même
   curl http://localhost:8081/health
   
   # Tester depuis un autre ordinateur
   curl http://[IP_DU_SERVEUR]:8081/health
   ```

3. **Vérifier que les ordinateurs sont sur le même réseau:**
   ```bash
   ping [IP_DU_SERVEUR]
   ```

### Erreur "Connection refused"

- Vérifier que le conteneur est en cours d'exécution
- Vérifier que le port est bien mappé: `docker ps`
- Vérifier le pare-feu

### Performance lente

- Augmenter le timeout: `API_TIMEOUT=30`
- Vérifier la connexion réseau
- Vérifier les logs pour des erreurs

## Commandes Utiles

```bash
# Démarrer le serveur réseau
docker-compose -f docker-compose.network.yml up -d

# Arrêter le serveur
docker-compose -f docker-compose.network.yml down

# Redémarrer le serveur
docker-compose -f docker-compose.network.yml restart

# Voir les logs
docker-compose -f docker-compose.network.yml logs -f

# Tester depuis un autre ordinateur
curl http://[IP]:8081/health
curl "http://[IP]:8081/weather/current?location=Paris"

# Voir les connexions actives
docker exec mcp-weather-server-network netstat -an | grep 8080
```

## Résumé

**Démarrage rapide:**
```bash
# Sur le serveur
docker-compose -f docker-compose.network.yml up -d

# Trouver l'IP
ifconfig | grep "inet " | grep -v 127.0.0.1

# Depuis un autre ordinateur
curl http://[IP]:8081/health
curl "http://[IP]:8081/weather/current?location=Paris"
```

Le serveur est maintenant accessible depuis n'importe quel ordinateur sur votre réseau! 🌐🌤️
