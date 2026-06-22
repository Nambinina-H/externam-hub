"""Vérif côte-à-côte : génère l'APERÇU du rapport d'un vrai client (pour comparer avec
Meta Ads Manager). ⚠️ AUCUN email n'est envoyé — c'est de la lecture seule.

- Sans argument         : liste les clients prêts (DB seulement, AUCUN appel Meta).
- Avec un `client_id`   : génère l'aperçu de ce client (appel Meta en lecture seule).

Usage :
    python -m app.scripts.verify_report
    python -m app.scripts.verify_report 12
"""

import sys
from datetime import date

from app.db.session import SessionLocal
from app.modules.clients.models import Client
from app.modules.reports.service import _managed_reports, _reports_text, previous_week_range


def list_ready(db) -> list[Client]:
    clients = db.query(Client).order_by(Client.name).all()
    ready = [c for c in clients if c.meta_business_id and (c.managed_campaign_ids or [])]
    print(f"{len(clients)} client(s) en base ; {len(ready)} prêt(s) (portefeuille lié + campagnes cochées)\n")
    for c in ready:
        print(f"  #{c.id}  {c.name}  | portefeuille {c.meta_business_id} | {len(c.managed_campaign_ids)} campagne(s) cochée(s)")
    if not ready:
        print("  (aucun) — il faut : lier un portefeuille à un client, puis cocher des campagnes gérées.")
    return ready


def preview_one(db, client_id: int) -> None:
    client = db.get(Client, client_id)
    if client is None:
        print(f"Client #{client_id} introuvable.")
        return
    start, end = previous_week_range(date.today())
    print(f"=== APERÇU (SANS ENVOI) — {client.name} ===")
    print(f"Semaine {start:%d/%m/%Y} -> {end:%d/%m/%Y}  ·  attribution 7 j clic + 1 j vue · clics sur un lien\n")
    reports = _managed_reports(db, client, start, end)  # lit Meta en lecture seule
    if not reports:
        print("Aucune campagne gérée trouvée pour ce client (ou aucune diffusion sur la semaine).")
        return
    print(_reports_text(reports))
    print("\n--- À comparer dans Ads Manager (mêmes réglages) ---")
    print("• Période : la semaine ci-dessus (lundi → dimanche)")
    print("• Colonnes : « Clics sur un lien », « CTR (clics sur un lien) »")
    print("• Attribution : « 7 jours clic ou 1 jour vue »")
    print("• Filtre : uniquement les campagnes cochées")


def main() -> None:
    db = SessionLocal()
    try:
        if len(sys.argv) > 1:
            preview_one(db, int(sys.argv[1]))
        else:
            list_ready(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
