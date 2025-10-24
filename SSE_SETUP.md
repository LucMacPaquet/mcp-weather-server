# MCP Weather Server avec SSE (Server-Sent Events)

Ce guide explique comment utiliser le serveur MCP Weather avec le transport SSE, permettant aux clients MCP de se connecter directement via HTTP **sans aucun wrapper local**.

## Qu'est-ce que SSE?

SSE (Server-Sent Events) est un transport officiel du protocole MCP qui permet:
- ✅ **Zéro installation locale** - Les clients se connectent directement via HTTP
- ✅ **Communication bidirectionnelle** - POST pour les requêtes, SSE pour les réponses
- ✅ **Conforme au standard MCP** - Implémentation officielle du protocole
- ✅ **Multi-clients** - Plusieurs clients peuvent se connecter simultanément

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MacBook Pro (Serveur)                    │
│                   192.168.2.23:8082                         │
│                                                             │
│  ┌─────────────────────────────────────┐                   │
│  │  Docker: mcp-weather-server-sse     │                   │
│  │  (Serveur MCP avec transport SSE)   │                   │
│  └─────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
                         ▲
                         │ HTTP/SSE (port 8082)
                         │ Protocole MCP natif
                         │
        ┌────────────────┼────────────────┐
        │                │                │
┌───────▼──────┐  ┌──────▼──────┐  ┌─────▼──────┐
│   Client 1   │  │   Client 2  │  │  Client 3  │
│   (Kiro)     │  │  (Claude)   │  │   (GPT)    │
│              │  │             │  │            │
│ AUCUNE       │  │ AUCUNE      │  │ AUCUNE     │
│ INSTALLATION │  │ INSTALLATION│  │ INSTALLATION│
└──────────────┘  └─────────────┘  └────────────┘
```

## Démarrage du serveur SSE

### Sur le MacBook Pro (serveur):

```bash
# Démarrer le serveur SSE
docker-compose -f docker-compose.sse.yml up -d

# Vérifier les logs
docker logs -f mcp-weather-server-sse

# Tester
curl http://localhost:8082/health
```

Le serveur sera accessible sur le port **8082**.

## Configuration des clients MCP

### Pour Claude Desktop

**IMPORTANT:** Claude Desktop doit supporter le transport SSE (vérifier la documentation officielle).

Ajouter dans `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "weather": {
      "url": "http://192.168.2.23:8082/sse",
      "transport": "sse"
    }
  }
}
```

### Pour Kiro

**IMPORTANT:** Kiro doit supporter le transport SSE (vérifier la documentation).

Ajouter dans `.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "weather": {
      "url": "http://192.168.2.23:8082/sse",
      "transport": "sse",
      "disabled": false,
      "autoApprove": [
        "get_current_weather",
        "get_weather_forecast"
      ]
    }
  }
}
```

### Pour d'autres clients MCP

Tout client MCP qui supporte le transport SSE peut se connecter avec:
- **URL SSE**: `http://192.168.2.23:8082/sse`
- **URL Messages**: `http://192.168.2.23:8082/message`

## Protocole MCP SSE

### 1. Établir la connexion SSE

```bash
# Le client ouvre une connexion SSE
curl -N -H "Accept: text/event-stream" http://192.168.2.23:8082/sse
```

Le serveur retourne un `X-Session-ID` dans les headers.

### 2. Envoyer des requêtes

```bash
# Le client envoie des requêtes JSON-RPC via POST
curl -X POST http://192.168.2.23:8082/message \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: <session-id>" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }'
```

### 3. Recevoir les réponses

Les réponses arrivent via le flux SSE:

```
data: {"jsonrpc":"2.0","id":1,"result":{"tools":[...]}}
```

## Endpoints disponibles

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/` | GET | Informations du serveur |
| `/health` | GET | Health check |
| `/sse` | GET | Établir connexion SSE |
| `/message` | POST | Envoyer requête MCP |

## Tests

### Test manuel avec curl

```bash
# Terminal 1: Ouvrir la connexion SSE
curl -N -H "Accept: text/event-stream" http://192.168.2.23:8082/sse

# Noter le X-Session-ID dans les headers

# Terminal 2: Envoyer une requête
SESSION_ID="<votre-session-id>"

curl -X POST http://192.168.2.23:8082/message \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: $SESSION_ID" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "get_current_weather",
      "arguments": {
        "location": "Paris",
        "units": "metric"
      }
    }
  }'

# La réponse apparaîtra dans Terminal 1 via SSE
```

## Avantages du transport SSE

✅ **Zéro installation locale** - Pas de fichier Python, pas de wrapper  
✅ **Protocole MCP natif** - Conforme à la spécification officielle  
✅ **Multi-clients** - Plusieurs clients simultanés  
✅ **Temps réel** - Communication bidirectionnelle efficace  
✅ **Standard web** - Utilise HTTP/SSE standard  

## Limitations

⚠️ **Support client requis** - Le client MCP doit supporter le transport SSE  
⚠️ **Réseau local** - Fonctionne sur le même réseau (ou VPN)  
⚠️ **Pas de TLS** - Pour la production, ajouter HTTPS  

## Comparaison des transports

| Transport | Installation locale | Support clients | Complexité |
|-----------|-------------------|-----------------|------------|
| **stdio** (local) | Serveur complet | Tous | Moyenne |
| **HTTP + wrapper** | 1 fichier Python | Tous | Faible |
| **SSE** (cette option) | **AUCUNE** | Clients avec support SSE | Moyenne |

## Vérification du support SSE

Pour vérifier si ton client MCP supporte SSE:

1. Consulter la documentation du client
2. Chercher "SSE", "Server-Sent Events", ou "transport"
3. Vérifier les exemples de configuration

Si le client ne supporte pas SSE, utiliser le wrapper HTTP (`mcp_http_client.py`).

## Dépannage

### Le client ne se connecte pas

1. Vérifier que le serveur SSE est démarré:
   ```bash
   docker ps | grep mcp-weather-server-sse
   ```

2. Tester la connexion:
   ```bash
   curl http://192.168.2.23:8082/health
   ```

3. Vérifier que le client supporte SSE

### Erreur "Invalid session ID"

- La session SSE doit être établie avant d'envoyer des messages
- Vérifier que le `X-Session-ID` est correct

### Pas de réponse

- Vérifier les logs du serveur:
  ```bash
  docker logs mcp-weather-server-sse
  ```

## Documentation officielle

- [MCP Transport SSE](https://modelcontextprotocol.io/docs/concepts/transports#server-sent-events-sse)
- [Spécification MCP](https://spec.modelcontextprotocol.io/)

## Résumé

**Pour utiliser le serveur SSE:**

1. **Sur le serveur (MacBook Pro):**
   ```bash
   docker-compose -f docker-compose.sse.yml up -d
   ```

2. **Sur chaque client (si supporté):**
   ```json
   {
     "mcpServers": {
       "weather": {
         "url": "http://192.168.2.23:8082/sse",
         "transport": "sse"
       }
     }
   }
   ```

3. **C'est tout!** Aucune installation locale nécessaire! 🎉
