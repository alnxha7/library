# Generated by Django 5.1.4 on 2024-12-27 10:33

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('book', '0002_borrrow'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Borrrow',
            new_name='Borrow',
        ),
    ]