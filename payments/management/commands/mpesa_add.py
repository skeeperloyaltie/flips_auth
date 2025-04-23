from django.core.management.base import BaseCommand
from payments.models import MpesaCredential


class Command(BaseCommand):
    help = "Add Mpesa paybill and till number"

    def add_arguments(self, parser):
        parser.add_argument("paybill_number", type=str, help="Paybill number")
        parser.add_argument("till_number", type=str, help="Till number")
        parser.add_argument("account_number", type=str, help="Account number")

    def handle(self, *args, **kwargs):
        paybill_number = kwargs["paybill_number"]
        till_number = kwargs["till_number"]
        account_number = kwargs["account_number"]

        MpesaCredential.objects.create(
            paybill_number=paybill_number,
            till_number=till_number,
            account_number=account_number,
        )
        self.stdout.write(self.style.SUCCESS("Successfully added Mpesa credentials"))
