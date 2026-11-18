import json

from cryptography.fernet import InvalidToken
from django.core.management.base import BaseCommand, CommandError

from storage.drive import DriveClient, DriveError, drive_credentials
from storage.models import DriveAccount, StorageLocation
from storage.oauth import client_for_owner, token_cipher
from storage.reconcile import probe_location, reconcile_location
from storage.service import DRIVE_PROVIDER


def _read_only_client(owner_id):
    account = DriveAccount.objects.filter(
        owner_id=owner_id, state=DriveAccount.State.CONNECTED
    ).first()
    if account is None:
        raise DriveError("drive_not_connected")
    try:
        token = (
            token_cipher().decrypt(account.refresh_token_ciphertext.encode()).decode()
        )
    except (InvalidToken, UnicodeError):
        raise DriveError("drive_reauthorize") from None
    return DriveClient(drive_credentials(token)), account


class Command(BaseCommand):
    help = "Inspect one owner-scoped batch of Drive locations. Default mode leaves the database unchanged."

    def add_arguments(self, parser):
        parser.add_argument("--owner-id", type=int, required=True)
        parser.add_argument("--after-location", type=int, default=0)
        parser.add_argument("--limit", type=int, default=25)
        parser.add_argument("--apply", action="store_true")

    def handle(self, *args, **opts):
        limit = opts["limit"]
        if not 1 <= limit <= 100 or opts["after_location"] < 0:
            raise CommandError("Use a limit of 1 through 100 and a nonnegative cursor.")

        owner_id = opts["owner_id"]
        apply = opts["apply"]
        client_factory = client_for_owner if apply else _read_only_client
        operation = reconcile_location if apply else probe_location
        try:
            client, account = client_factory(owner_id)
        except DriveError as error:
            raise CommandError(error.code) from None

        batch = list(
            StorageLocation.objects.filter(
                asset__item__owner_id=owner_id,
                provider=DRIVE_PROVIDER,
                pk__gt=opts["after_location"],
            )
            .select_related("asset__item")
            .order_by("pk")[: limit + 1]
        )
        results = []
        for location in batch[:limit]:
            try:
                result = operation(location, client=client, account=account)
            except DriveError as error:
                if error.retryable:
                    raise CommandError(error.code) from None
                outcome = {
                    "outcome": "probe_failed",
                    "detail": error.code,
                    "applied": False,
                }
            else:
                outcome = {
                    "status": result.status,
                    "outcome": result.outcome,
                    "detail": result.detail,
                    "applied": result.applied,
                }
            results.append(
                {
                    "location_id": location.pk,
                    "asset_id": str(location.asset_id),
                    **outcome,
                }
            )

        self.stdout.write(
            json.dumps(
                {
                    "results": results,
                    "next_after_location": batch[limit - 1].pk
                    if len(batch) > limit
                    else None,
                }
            )
        )
