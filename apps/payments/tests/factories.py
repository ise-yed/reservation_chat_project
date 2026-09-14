import factory

from apps.payments.enums import PaymentMethod, PaymentStatus
from apps.payments.models import Payment, PaymentTransaction


class PaymentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Payment

    appointment = None

    @factory.lazy_attribute
    def organization(self):
        return self.appointment.organization

    @factory.lazy_attribute
    def payer(self):
        return self.appointment.customer

    @factory.lazy_attribute
    def created_by(self):
        return self.payer

    @factory.lazy_attribute
    def amount(self):
        return self.appointment.price

    currency = "IRR"
    status = PaymentStatus.PENDING
    method = PaymentMethod.MOCK
    idempotency_key = factory.Sequence(lambda n: f"test-payment-{n}")


class PaymentTransactionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PaymentTransaction

    payment = factory.SubFactory(PaymentFactory)
    transaction_type = "initiated"
    amount = factory.LazyAttribute(lambda obj: obj.payment.amount)
    status = "success"
