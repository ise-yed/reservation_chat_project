from django.db import models


class UserRoles(models.TextChoices):
    CUSTOMER = "customer", "Customer"
    PROVIDER = "provider", "Provider"
    STAFF = "staff", "Staff"
    ORG_ADMIN = "org_admin", "Organization Admin"
    SUPER_ADMIN = "super_admin", "Super Admin"
