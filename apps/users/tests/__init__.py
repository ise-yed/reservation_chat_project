import factory

from apps.users.models import User, UserRoles


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = "Test"
    last_name = "User"
    phone_number = factory.Sequence(lambda n: f"091200000{n}")
    role = UserRoles.CUSTOMER
    is_active = True
    is_verified = False

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        raw_password = extracted or "StrongPass123!"
        obj.set_password(raw_password)
        if create:
            obj.save()
