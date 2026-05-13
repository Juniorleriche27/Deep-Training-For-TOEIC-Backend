# Deep Training For TOEIC Backend

Backend API aligne sur le frontend Next.js de `C:\DP Training for TOEIC\frontend` et sur les contraintes serveur de production.

## Stack

- Python 3.11
- FastAPI
- AI Gateway uniquement pour l'IA
- Supabase SQL unique dans `supabase/schema.sql`
- Donnees mockees temporaires pour les endpoints non encore relies a Supabase

## Demarrage

```bash
python -m pip install .
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Le backend ecoute sur `0.0.0.0:8000`.

## Branchement frontend

Dans le frontend, definir:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Variables d'environnement

```env
APP_HOST=0.0.0.0
APP_PORT=8000
FRONTEND_ORIGIN=http://localhost:3000
AI_GATEWAY_BASE_URL=https://ai.deeptrainingfortoeic.com
AI_GATEWAY_API_KEY=
AI_GATEWAY_TIMEOUT_SECONDS=120
AI_DEFAULT_RESPONSE_MODE=fast
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
```

## Supabase

Le script SQL unique a conserver et enrichir est ici :

`supabase/schema.sql`

Regle de projet :

- un seul script SQL
- on rejoue ce meme fichier
- on l'enrichit dans le temps avec des `create ... if not exists`, `alter table ... add column if not exists`, `drop policy if exists`, `create or replace ...`

Ce script cree :

- le schema `app`
- les tables adherent, programme, scores, notes, ressources, messages, chat, activite, missions
- les policies RLS de base
- les triggers `updated_at`
- un jeu de donnees seed minimal coherent avec le frontend actuel

## Keepalive Supabase

Le workflow GitHub Actions `.github/workflows/supabase-keepalive.yml` ping le projet Supabase Deep Training For TOEIC toutes les 12 heures pour eviter une mise en pause automatique.

Secrets GitHub requis dans ce repo uniquement :

```env
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
```

Le workflow interroge `app.profiles` via l'API REST Supabase avec le header `Accept-Profile: app`. Il peut aussi etre lance manuellement depuis l'onglet Actions.

## AI Gateway

Le backend n'appelle jamais Ollama directement.

Il passe uniquement par :

- `POST {AI_GATEWAY_BASE_URL}/v1/chat`

Le service central est dans [ai_gateway.py](/C:/Deep%20Training%20For%20TOEIC%20Backend/app/services/ai_gateway.py:1).

Il :

- lit les variables `AI_GATEWAY_BASE_URL`, `AI_GATEWAY_API_KEY`, `AI_GATEWAY_TIMEOUT_SECONDS`
- envoie `Authorization: Bearer ...`
- utilise `response_mode=fast` par defaut
- recupere seulement `response`
- gere timeout, erreurs HTTP, JSON invalide et reponse vide
- ne log jamais la cle API
- log seulement statut, temps, mode et taille de reponse

## Endpoints exposes

- `GET /health`
- `GET /adherent/me`
- `GET /adherent/coach-ia/context`
- `GET /adherent/coach-ia/history`
- `POST /adherent/coach-ia/chat`

## Docker

Le conteneur est prevu pour exposer :

- `0.0.0.0:8000`

Le routage cible attendu cote serveur reste :

- `https://api.deeptrainingfortoeic.com -> prod_deeptraining_api:8000`
