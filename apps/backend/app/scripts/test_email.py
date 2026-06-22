"""Test isolé de la configuration SMTP.

Envoie UN seul email à une adresse de test dédiée — ne lit JAMAIS la base de données
ni les adresses des clients réels (garde-fou : on ne spamme pas de vrais clients).

Usage :
    python -m app.scripts.test_email [destinataire]

Sans argument, l'email part vers l'adresse de test par défaut.
"""

import sys

from app.core.config import get_settings
from app.core.email import send_email

# Destinataire de test dédié (jamais une adresse de la base).
DEFAULT_TEST_RECIPIENT = "nambininahasinarasoanaivo@gmail.com"


def main() -> None:
    to = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TEST_RECIPIENT
    settings = get_settings()

    print(f"SMTP      : {settings.smtp_host}:{settings.smtp_port}")
    print(f"SMTP_USER : {settings.smtp_user or '(vide)'}")
    print(f"FROM      : {settings.from_email}")
    print(f"-> envoi de test a : {to}")
    if not settings.smtp_user:
        print("SMTP_USER vide -> mode dry-run (rien n'est reellement envoye).")

    html = (
        "<h2>Externam Studio Hub - email de test</h2>"
        "<p>Si tu lis ceci, la configuration SMTP fonctionne. ✅</p>"
        "<p>Ceci est un test isole, sans rapport avec un client reel.</p>"
    )
    send_email(to, "Externam Hub - test SMTP", html)
    print("Termine (voir le log ci-dessus pour confirmation d'envoi).")


if __name__ == "__main__":
    main()
