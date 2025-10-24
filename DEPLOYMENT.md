# Guide de Déploiement - MCP Weather Server

Ce guide explique comment déployer et utiliser le serveur MCP Weather sur un autre ordinateur.

## Table des matières

1. [Prérequis](#prérequis)
2. [Installation via Docker (Recommandé)](#installation-via-docker-recommandé)
3. [Installation via Python](#installation-via-python)
4. [Configuration](#configuration)
5. [Utilisation avec des clients MCP](#utilisation-avec-des-clients-mcp)
6. [Accès Réseau](#accès-réseau)
7. [Dépannage](#dépannage)

---

## Prérequis

### Pour Docker (Recommandé)
- Docker Desktop installé ([télécharger ici](https://www.docker.com/products/docker-desktop))
- Git installé
- Accès au repo GitHub privé

### Pour Python
- Python 3.10 ou supérieur
- pip (gestionnaire de paquets Python)
- Git installé

---

## Installation via Docker (Recommandé)

### Étape 1: Cloner le repository

```bash
# Cloner le repo privé (nécessite authentification GitHub)
git clone https://github.com/LucMacPaquet/mcp-weather-server.git
cd mcp-weather-server
```

Si vous n'avez pas accès, configurez d'abord GitHub CLI:
```bash
# Installer GitHub CLI (si nécessaire)
# macOS
brew install gh

# Windows
winget install --id GitHub.cli

# Linux
# Voir: https://github.com/cli/cli/blob/trunk/docs/install_linux.md

# Authentification
gh auth login
```

### Étape 2: Basculer sur la branche Docker

```bash
git checkout docker-support
```

### Étape 3: Construire et démarrer le conteneur

**Option A: Avec le script helper (plus simple)**
```bash
# Rendre le script exécutable (Linux/macOS)
chmod +x docker-run.sh

# Démarrer le serveur
./docker-run.sh start
```

**Option B: Avec Docker directement**
```bash
# Construire l'image
docker build -t mcp-weather-server:latest .

# Démarrer le conteneur
docker run -d \
  --name mcp-weather-server \
  -e WEATHERAPI_KEY=13ced4f0f05a4a4f986223827252410 \
  -i \
  mcp-weather-server:latest
```

**Option C: Avec Docker Compose**
```bash
docker-compose up -d
```

### Étape 4: Vérifier que le conteneur fonctionne

```bash
# Voir les logs
docker logs mcp-weather-server

# Ou avec le script helper
./docker-run.sh logs
```

Vous devriez voir:
```
Starting MCP Weather Server
Validating configuration...
API key validated successfully
Server initialized, starting main loop...
```

---

## Installation via Python

### Étape 1: Cloner le repository

```bash
git clone https://github.com/LucMacPaquet/mcp-weather-server.git
cd mcp-weather-server
```

### Étape 2: Installer les dépendances

```bash
# Créer un environnement virtuel (recommandé)
python3 -m venv venv

# Activer l'environnement
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Installer le package
pip install -e .
```

### Étape 3: Configurer la clé API

```bash
# Créer un fichier .env
echo "WEATHERAPI_KEY=13ced4f0f05a4a4f986223827252410" > .env
```

### Étape 4: Tester le serveur

```bash
python -m mcp_weather_server
```

---

## Configuration

### Variables d'environnement

| Variable | Description | Défaut |
|----------|-------------|--------|
| `WEATHERAPI_KEY` | Clé API WeatherAPI.com | `13ced4f0f05a4a4f986223827252410` |
| `LOG_LEVEL` | Niveau de log (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `API_TIMEOUT` | Timeout des requêtes API (secondes) | `10` |

### Obtenir votre propre clé API (optionnel)

1. Créer un compte sur [WeatherAPI.com](https://www.weatherapi.com/)
2. Aller dans "My Account" → "API Keys"
3. Copier votre clé API
4. Remplacer la clé dans la configuration

---

## Utilisation avec des clients MCP

### Claude Desktop

**Fichier de configuration:** 
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

**Configuration avec Docker:**
```json
{
  "mcpServers": {
    "weather": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "mcp-weather-server",
        "python",
        "-m",
        "mcp_weather_server"
      ]
    }
  }
}
```

**Configuration avec Python:**
```json
{
  "mcpServers": {
    "weather": {
      "command": "python",
      "args": ["-m", "mcp_weather_server"],
      "env": {
        "WEATHERAPI_KEY": "13ced4f0f05a4a4f986223827252410",
        "PYTHONPATH": "/chemin/vers/mcp-weather-server/src"
      }
    }
  }
}
```

**Important:** Remplacez `/chemin/vers/mcp-weather-server` par le chemin réel.

### Kiro IDE

**Fichier de configuration:** `.kiro/settings/mcp.json` dans votre workspace

**Configuration avec Docker:**
```json
{
  "mcpServers": {
    "weather": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "mcp-weather-server",
        "python",
        "-m",
        "mcp_weather_server"
      ],
      "disabled": false,
      "autoApprove": [
        "get_current_weather",
        "get_weather_forecast"
      ]
    }
  }
}
```

**Configuration avec Python:**
```json
{
  "mcpServers": {
    "weather": {
      "command": "/chemin/absolu/vers/mcp-weather-server/run_mcp_server.sh",
      "args": [],
      "env": {
        "WEATHERAPI_KEY": "13ced4f0f05a4a4f986223827252410"
      },
      "disabled": false,
      "autoApprove": [
        "get_current_weather",
        "get_weather_forecast"
      ]
    }
  }
}
```

### Redémarrage requis

Après avoir modifié la configuration:
1. **Quittez complètement** l'application (Claude Desktop ou Kiro)
2. **Relancez** l'application
3. Le serveur MCP devrait maintenant être disponible

---

## Commandes utiles

### Docker

```bash
# Démarrer le serveur
./docker-run.sh start

# Voir les logs en temps réel
./docker-run.sh logs

# Arrêter le serveur
./docker-run.sh stop

# Redémarrer le serveur
./docker-run.sh restart

# Tester le serveur
./docker-run.sh test

# Voir les conteneurs en cours
docker ps

# Voir tous les conteneurs
docker ps -a

# Supprimer le conteneur
docker rm -f mcp-weather-server

# Supprimer l'image
docker rmi mcp-weather-server:latest
```

### Python

```bash
# Activer l'environnement virtuel
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Lancer le serveur
python -m mcp_weather_server

# Voir les logs
# Les logs s'affichent dans la console

# Désactiver l'environnement
deactivate
```

---

## Dépannage

### Le conteneur ne démarre pas

**Vérifier les logs:**
```bash
docker logs mcp-weather-server
```

**Vérifier que Docker est en cours d'exécution:**
```bash
docker ps
```

**Reconstruire l'image:**
```bash
docker rm -f mcp-weather-server
docker rmi mcp-weather-server:latest
./docker-run.sh start
```

### Le serveur ne répond pas dans Claude/Kiro

1. **Vérifier que le conteneur est en cours d'exécution:**
   ```bash
   docker ps | grep mcp-weather-server
   ```

2. **Vérifier les logs du serveur:**
   ```bash
   docker logs mcp-weather-server
   ```

3. **Redémarrer le conteneur:**
   ```bash
   ./docker-run.sh restart
   ```

4. **Redémarrer l'application cliente** (Claude Desktop ou Kiro)

### Erreur "Permission denied" sur Linux

```bash
# Ajouter votre utilisateur au groupe docker
sudo usermod -aG docker $USER

# Se déconnecter et se reconnecter pour appliquer les changements
```

### Erreur de clé API

**Vérifier la clé dans le conteneur:**
```bash
docker exec mcp-weather-server env | grep WEATHERAPI_KEY
```

**Mettre à jour la clé:**
```bash
# Arrêter le conteneur
docker stop mcp-weather-server
docker rm mcp-weather-server

# Redémarrer avec la nouvelle clé
docker run -d \
  --name mcp-weather-server \
  -e WEATHERAPI_KEY=votre_nouvelle_cle \
  -i \
  mcp-weather-server:latest
```

### Le repo est privé, je ne peux pas cloner

**Configurer l'authentification GitHub:**
```bash
# Avec GitHub CLI
gh auth login

# Ou avec un token personnel
git clone https://TOKEN@github.com/LucMacPaquet/mcp-weather-server.git
```

**Créer un token personnel:**
1. Aller sur GitHub → Settings → Developer settings → Personal access tokens
2. Générer un nouveau token avec les permissions `repo`
3. Utiliser le token pour cloner

---

## Déploiement sur un serveur distant

### Via SSH

```bash
# Se connecter au serveur
ssh user@serveur.com

# Cloner le repo
git clone https://github.com/LucMacPaquet/mcp-weather-server.git
cd mcp-weather-server
git checkout docker-support

# Démarrer le conteneur
./docker-run.sh start

# Le serveur est maintenant accessible via Docker
```

### Avec Docker Hub (optionnel)

```bash
# Sur votre machine locale, construire et pousser l'image
docker build -t lucmacpaquet/mcp-weather-server:latest .
docker push lucmacpaquet/mcp-weather-server:latest

# Sur le serveur distant
docker pull lucmacpaquet/mcp-weather-server:latest
docker run -d \
  --name mcp-weather-server \
  -e WEATHERAPI_KEY=13ced4f0f05a4a4f986223827252410 \
  -i \
  lucmacpaquet/mcp-weather-server:latest
```

---

## Support

Pour toute question ou problème:
1. Vérifier les logs: `docker logs mcp-weather-server`
2. Consulter [DOCKER.md](DOCKER.md) pour plus de détails
3. Ouvrir une issue sur GitHub (si vous avez accès au repo)

---

## Résumé rapide

**Installation la plus simple (Docker):**
```bash
git clone https://github.com/LucMacPaquet/mcp-weather-server.git
cd mcp-weather-server
git checkout docker-support
chmod +x docker-run.sh
./docker-run.sh start
```

**Configuration Claude Desktop:**
```json
{
  "mcpServers": {
    "weather": {
      "command": "docker",
      "args": ["exec", "-i", "mcp-weather-server", "python", "-m", "mcp_weather_server"]
    }
  }
}
```

**Redémarrer Claude Desktop et c'est prêt!** 🌤️

---

## Accès Réseau

Pour rendre le serveur accessible depuis d'autres ordinateurs sur le réseau, consultez le guide complet: **[NETWORK_ACCESS.md](NETWORK_ACCESS.md)**

### Démarrage rapide (Mode Réseau)

```bash
# Démarrer le serveur avec accès réseau
docker-compose -f docker-compose.network.yml up -d

# Trouver votre adresse IP
ifconfig | grep "inet " | grep -v 127.0.0.1

# Le serveur est accessible sur http://[VOTRE_IP]:8080
```

### Tester depuis un autre ordinateur

```bash
# Remplacer [IP] par l'adresse IP du serveur
curl http://[IP]:8080/health
curl "http://[IP]:8080/weather/current?location=Paris"
```

### Endpoints disponibles

- `GET /` - Informations du serveur
- `GET /health` - Health check
- `GET /tools` - Liste des outils
- `GET /weather/current?location=Paris&units=metric` - Météo actuelle
- `GET /weather/forecast?location=Paris&days=5&units=metric` - Prévisions
- `POST /mcp` - Endpoint MCP JSON-RPC

Pour plus de détails sur l'accès réseau, la sécurité, et les exemples de clients, voir **[NETWORK_ACCESS.md](NETWORK_ACCESS.md)**.
