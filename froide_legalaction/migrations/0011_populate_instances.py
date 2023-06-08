import django.db.models.deletion
from django.db import migrations, models


def create_instances(apps, schema_editor):
    Instance = apps.get_model("froide_legalaction", "Instance")
    Lawsuit = apps.get_model("froide_legalaction", "Lawsuit")

    for lawsuit in Lawsuit.objects.all().select_related("court"):
        first_instance = Instance(
            court=lawsuit.court,
            court_type=lawsuit.court_type,
            start_date=lawsuit.start_date,
            end_date=lawsuit.end_date,
            lawsuit=lawsuit,
        )
        first_instance.save()


class Migration(migrations.Migration):
    dependencies = [
        ("froide_legalaction", "0010_instance"),
    ]

    operations = [
        migrations.RunPython(create_instances, atomic=False),
    ]
