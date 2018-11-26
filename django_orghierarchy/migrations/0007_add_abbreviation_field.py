# Generated by Django 2.1.3 on 2018-11-22 14:36

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import mptt.fields


class Migration(migrations.Migration):

    dependencies = [
        ('django_orghierarchy', '0006_add_user_editable_to_data_source'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='abbreviation',
            field=models.CharField(blank=True, help_text='A commonly used abbreviation', max_length=50, null=True),
        ),
    ]
