# Generated by Django 1.11.7 on 2017-11-28 13:03
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("django_orghierarchy", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="organization",
            name="replaced_by",
            field=models.OneToOneField(
                blank=True,
                help_text="The organization that replaces this organization",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="replaced_organization",
                to="django_orghierarchy.Organization",
            ),
        ),
    ]
