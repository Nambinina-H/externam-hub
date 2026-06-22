"""Écrit l'aperçu HTML du rapport (données d'exemple) dans `apercu_rapport.html`
pour le visualiser dans un navigateur. Usage : python -m app.scripts.render_preview"""

from app.db.session import SessionLocal
from app.modules.reports.schemas import EmailTemplateSchema
from app.modules.reports.service import DEFAULT_TEMPLATE, preview_template

db = SessionLocal()
try:
    out = preview_template(db, None, EmailTemplateSchema(**DEFAULT_TEMPLATE))
finally:
    db.close()

with open("apercu_rapport.html", "w", encoding="utf-8") as f:
    f.write(out["html"])

print("OK — objet :", out["subject"])
print("Taille HTML :", len(out["html"]), "caractères")
print("Fichier : apps/backend/apercu_rapport.html (ouvre-le dans un navigateur)")
