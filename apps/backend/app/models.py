"""Registre des modèles SQLAlchemy pour qu'Alembic les détecte à l'autogénération.

À chaque nouvelle feature, importer ici ses modèles.
"""

from app.modules.ads.models import MetaAdAccount, MetaPortfolio  # noqa: F401
from app.modules.audit.models import AuditLog  # noqa: F401
from app.modules.clients.models import Client  # noqa: F401
from app.modules.reports.models import EmailTemplate  # noqa: F401
from app.modules.settings.models import EmailSettings  # noqa: F401
from app.modules.users.models import User  # noqa: F401

__all__ = ["User", "Client", "MetaPortfolio", "MetaAdAccount", "EmailSettings", "EmailTemplate", "AuditLog"]
