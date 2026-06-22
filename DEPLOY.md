# Déploiement — Externam Hub

La **même base de code** se déploie de deux façons. Dans les deux cas, le navigateur ne parle
qu'au **front Next.js**, qui relaie `/api` vers FastAPI (modèle « Next = portail »).

| | **Vercel + Railway** (managé) | **VPS** (auto-hébergé, nginx) |
|---|---|---|
| Front | Vercel (build natif) | conteneur `frontend` |
| API | Railway (Dockerfile) | conteneur `backend` |
| Postgres | Railway managé | conteneur `postgres` (ou externe) |
| HTTPS | automatique | reverse proxy + TLS (toi) |
| Déploiement | `git push` → auto | `git pull && docker compose ...` |

**Pré-requis commun** : générer la paire de clés RSA.
```bash
cd apps/backend && python scripts/generate_keys.py   # crée keys/private.pem + keys/public.pem
```

---

## Voie A — Vercel + Railway

### 1. Railway — API + Postgres
1. Nouveau projet → **Add Postgres** (fournit automatiquement `DATABASE_URL`).
2. **Add service → Deploy from repo** → *Root Directory* = `apps/backend` (Railway build le `Dockerfile`).
3. Variables d'environnement du service API :
   - `ENVIRONMENT=prod`
   - `DATABASE_URL` → référencer la variable du Postgres Railway (`${{Postgres.DATABASE_URL}}`)
   - `JWT_ALGORITHM=RS256`
   - `JWT_PRIVATE_KEY` = **contenu** de `keys/private.pem` (colle le PEM complet, multi-lignes)
   - `JWT_PUBLIC_KEY`  = **contenu** de `keys/public.pem`
   - `ACCESS_TOKEN_EXPIRATION=900`, `REFRESH_TOKEN_EXPIRATION=604800`
   - `SEED_ADMIN_EMAIL`, `SEED_ADMIN_PASSWORD` (change-les !)
   - `FRONT_BASE_URL` = l'URL Vercel (pour le CORS)
   > Les migrations s'appliquent **au démarrage** (`alembic upgrade head` dans le `CMD` du Dockerfile),
   > puis l'admin est seedé. Récupère l'URL publique de l'API (ex. `https://xxx.up.railway.app`).

### 2. Vercel — Next.js
1. **Import Project** depuis le repo → *Root Directory* = `apps/frontend`.
2. Variables d'environnement :
   - `API_URL` = l'URL **publique** de l'API Railway (le proxy Next l'appelle côté serveur)
   - `NEXT_PUBLIC_API_URL` = idem (si utilisé côté navigateur)
3. Deploy. Vercel build Next nativement (il **ignore** le Dockerfile).

### 3. Relier
- Vercel `API_URL` → URL Railway. Railway `FRONT_BASE_URL` → URL Vercel.
- C'est tout : le navigateur tape Vercel, qui relaie `/api` vers Railway.

> Clés JWT sur Railway = **contenu PEM en variable** (pas de fichier). Le code lit
> `JWT_PRIVATE_KEY`/`JWT_PUBLIC_KEY` en priorité, sinon les fichiers `*_path`.

---

## Voie B — VPS (Docker Compose + nginx)

Pré-requis : un VPS avec **Docker** + **Docker Compose**, le repo cloné, clés RSA générées.

```bash
# 1. Config
cp .env.example .env
#   -> renseigner POSTGRES_*, SEED_ADMIN_* (change le mot de passe !),
#      NEXT_PUBLIC_API_URL et FRONT_BASE_URL (ton domaine), HTTP_PORT si besoin.

# 2. Clés RSA (si pas déjà fait) — montées en lecture seule dans le conteneur backend
cd apps/backend && python scripts/generate_keys.py && cd ../..

# 3. Build + démarrage (nginx + frontend + backend + postgres)
docker compose -f docker-compose.prod.yml up -d --build

# Migrations + seed admin = automatiques au démarrage du backend.
# nginx expose le port HTTP_PORT (défaut 80) ; frontend/backend restent internes.
```

**Mises à jour** :
```bash
git pull && docker compose -f docker-compose.prod.yml up -d --build
```

### HTTPS sur le VPS
nginx (dans le compose) sert en **HTTP**. Pour le TLS, deux options simples :
- **Cloudflare devant** (le plus simple) : DNS du domaine → IP du VPS, proxy activé → HTTPS gratuit, rien à installer.
- **certbot sur l'hôte** : un nginx/`certbot` au niveau de l'hôte qui termine le TLS et proxy vers `HTTP_PORT`.

> Base de données : par défaut le conteneur `postgres`. Pour une base **managée** (Neon, Supabase, RDS…),
> laisse `postgres` de côté et renseigne `DATABASE_URL` dans `.env` (il prend le dessus sur les `POSTGRES_*`).

---

## Récap des variables sensibles à changer en prod
`POSTGRES_PASSWORD` · `SEED_ADMIN_PASSWORD` · les **clés RSA** (uniques par projet) · `SENTRY_URL` (optionnel).
