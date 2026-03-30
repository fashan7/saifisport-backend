from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        SUPERADMIN = 'superadmin', 'Super Admin'
        STAFF      = 'staff',      'Staff'
        VIEWER     = 'viewer',     'Viewer'

    role  = models.CharField(max_length=20, choices=Role.choices, default=Role.SUPERADMIN)
    email = models.EmailField(unique=True)

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email