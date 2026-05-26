from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from ingestion.models import ActivityRecord, Organization, PlantLookup, UserProfile
from ingestion.services import process_upload

User = get_user_model()


class Command(BaseCommand):
    help = "Seed demo organization, analyst user, and sample ingestion files"

    def handle(self, *args, **options):
        org, _ = Organization.objects.get_or_create(
            slug="acme-corp",
            defaults={"name": "Acme Corporation"},
        )

        user, created = User.objects.get_or_create(
            username="analyst",
            defaults={
                "email": "analyst@acme.example",
                "first_name": "Jordan",
                "last_name": "Lee",
                "is_staff": True,
            },
        )
        if created:
            user.set_password("demo1234")
            user.save()
            self.stdout.write(self.style.SUCCESS("Created analyst / demo1234"))

        UserProfile.objects.get_or_create(user=user, defaults={"organization": org})

        plants = [
            ("1000", "Berlin HQ", "DE"),
            ("2000", "Munich Plant", "DE"),
            ("3000", "Chicago Office", "US"),
        ]
        for code, site, country in plants:
            PlantLookup.objects.get_or_create(
                organization=org,
                plant_code=code,
                defaults={"site_name": site, "country": country},
            )

        if ActivityRecord.objects.filter(organization=org).exists():
            self.stdout.write(
                self.style.WARNING("Sample data already loaded — skipping file ingest.")
            )
            self.stdout.write(self.style.SUCCESS("Demo seed complete."))
            return

        sample_dir = Path(__file__).resolve().parents[4] / "sample_data"
        files = [
            ("sap", "sap_procurement_fuel.csv"),
            ("utility", "utility_electricity.csv"),
            ("travel", "concur_travel_export.csv"),
        ]
        for source_type, filename in files:
            path = sample_dir / filename
            if not path.exists():
                self.stdout.write(self.style.WARNING(f"Skip missing {path}"))
                continue
            data = path.read_bytes()
            run = process_upload(org, source_type, data, filename, user)
            self.stdout.write(
                f"  {source_type}: {run.rows_parsed} parsed, "
                f"{run.rows_failed} failed, {run.rows_suspicious} suspicious"
            )

        self.stdout.write(self.style.SUCCESS("Demo seed complete."))
