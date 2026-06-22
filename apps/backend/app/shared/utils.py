def to_dict(instance) -> dict:
    """Convertit une instance de modèle SQLAlchemy en dictionnaire."""
    if not instance:
        return {}
    return {column.name: getattr(instance, column.name) for column in instance.__table__.columns}
