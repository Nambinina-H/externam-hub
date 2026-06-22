"""Point d'entrée serveur pour le dev local.

Lit le port depuis la config (`API_PORT`, défaut 8000) — pratique pour changer de port
sans toucher au code si 8000 est déjà occupé. Le reload n'est actif qu'en environnement `local`.

En conteneur / PaaS, c'est le Dockerfile qui lance l'app (`fastapi run --port ${PORT:-8000}`),
pas ce fichier.
"""

import uvicorn

from app.core.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.api_port,
        reload=settings.environment == "local",
    )
