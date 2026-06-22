# Externam Studio Hub

Outil d'agence pour piloter les **campagnes Meta Ads** des clients et leur envoyer
automatiquement un **rapport de performance hebdomadaire par email**.

Monorepo **Turborepo** : API **FastAPI** + interface **Next.js 16** + types partagés.

```
externam-hub/
├── apps/
│   ├── backend/      # API FastAPI (SQLAlchemy, Alembic, JWT, Meta Marketing API, SMTP)
│   └── frontend/     # Interface Next.js 16 (App Router, Tailwind v4, shadcn, Zustand)
├── packages/shared/  # Types TypeScript partagés (@externam/shared)
└── docker-compose.yml
```

## Ce que fait l'app

- **Clients** — gérer les clients : email(s) destinataire, jour d'envoi du rapport, actif/inactif.
- **Portefeuille business** — comptes publicitaires Meta regroupés par portefeuille, liés à un client ;
  sélection des campagnes à inclure dans le rapport.
- **Modèles d'email** — objet, intro, note de clôture, signature ; personnalisables par client, avec variables (`{{client}}`, `{{periode}}`, `{{expediteur}}`…).
- **Boîte d'envoi** — aperçu du rapport (vraies données Meta) puis envoi, à la demande ou
  **planifié** le jour choisi par chaque client.
- **Paramètres** — configuration SMTP (envoi des emails).

> Les comptes utilisateurs sont créés **par un admin** — il n'y a pas d'inscription publique.

## Stack

| | |
|---|---|
| **Backend** | FastAPI · SQLAlchemy 2.0 · Alembic · JWT (RS256) · Meta Marketing API · SMTP · APScheduler |
| **Frontend** | Next.js 16 (App Router) · Tailwind v4 · shadcn/base-ui · Zustand · Biome |
| **Base** | PostgreSQL (ou SQLite en local) |

Le navigateur ne parle qu'au **front Next.js**, qui relaie `/api` vers FastAPI et gère les
cookies HttpOnly (rafraîchissement auto du token sur `401`).

## Prérequis

- Node.js ≥ 20 + npm
- Python **3.12 ou 3.13** (évite 3.14 : wheels pas encore dispo pour certaines deps)
- Docker + Docker Compose (optionnel mais recommandé)

## Démarrage rapide

### 1. Configuration

```bash
cp .env.example .env
cp apps/backend/.env.example apps/backend/.env
cp apps/frontend/.env.example apps/frontend/.env.local

# Génère la paire de clés RSA qui signe les JWT
cd apps/backend && pip install -r requirements.txt && python scripts/generate_keys.py && cd ../..
```

### 2a. Avec Docker (recommandé)

```bash
npm run docker:up      # build + démarre Postgres, backend et frontend
```

### 2b. En local (sans Docker)

```bash
npm install            # frontend + types partagés

# Backend (venv Python 3.12)
cd apps/backend
py -3.12 -m venv .venv && source .venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt
python scripts/generate_keys.py
python run.py          # API sur :8000 (reload auto)

# Frontend (autre terminal)
npm run dev:frontend   # interface sur :3000
```

- Interface : http://localhost:3000
- API + docs : http://localhost:8000/docs

> **Sans aucune base à lancer** : mets `DATABASE_URL=sqlite:///./local.db` dans `apps/backend/.env`.

### 3. Connexion

Un **admin** est créé au démarrage à partir de `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD`
(défaut `admin@example.com` / `admin1234`). **À changer en prod.**

## Variables d'environnement (essentiel)

**Backend** (`apps/backend/.env`)

| Variable | Rôle |
|---|---|
| `DATABASE_URL` | URL Postgres (prioritaire sur `POSTGRES_*`) ; `sqlite:///./local.db` en local |
| `ENVIRONMENT` | `local` \| `production` |
| `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` | admin créé au 1er démarrage |
| `META_ACCESS_TOKEN`, `META_APP_ID`, `META_APP_SECRET`, `META_BUSINESS_ID` | accès Meta Marketing API (sinon données de démo) |
| `SMTP_HOST/PORT/USER/PASSWORD`, `FROM_EMAIL` | envoi des emails (Gmail : mot de passe d'application) |

**Frontend** (`apps/frontend/.env.local`)

| Variable | Rôle |
|---|---|
| `API_URL` | URL de l'API FastAPI (ex. `http://localhost:8000`) |

## Commandes utiles

```bash
npm run test:api                    # tests backend (pytest, SQLite in-memory)
npm run db:revision -- "message"    # génère une migration Alembic
npm run db:migrate                  # applique les migrations (upgrade head)
npm run lint                        # lint front (Biome) + back (ruff)
```

> Tout nouveau modèle SQLAlchemy doit être importé dans `apps/backend/app/models.py`
> pour qu'Alembic le détecte.

## Déploiement

- **Frontend → Vercel** (racine du projet `apps/frontend`).
- **Backend + PostgreSQL → Railway** (Dockerfile de `apps/backend`).

Brancher le `API_URL` du frontend sur l'URL publique du backend Railway, et renseigner
les variables d'environnement ci-dessus côté Railway (clés RSA, Meta, SMTP, `DATABASE_URL`).
