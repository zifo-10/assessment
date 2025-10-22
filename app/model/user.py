# app/models/user.py
import enum

class Role(str, enum.Enum):
    super_admin = "super_admin"
    admin = "admin"
    user = "user"
