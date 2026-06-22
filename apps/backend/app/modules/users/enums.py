import enum


class UserRoleEnum(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"
    SUPERADMIN = "SUPERADMIN"
    META_ADS_EXPERT = "META_ADS_EXPERT"
