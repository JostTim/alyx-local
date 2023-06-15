# Generated by Django 4.1.3 on 2023-06-14 19:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0017_data_repository_inclusion_chain'),
        ('subjects', '0011_migrating_dataset_type_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='default_data_repository',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='data.datarepository'),
        ),
    ]
