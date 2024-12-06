# Generated by Django 5.1.3 on 2024-12-06 17:46

import alyx.base.base
import alyx.data.models
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0024_filerec_relative_path_not_necessary'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datarepository',
            name='timezone',
            field=models.CharField(blank=True, default='Etc/UTC', help_text='Timezone of the server (see https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)', max_length=64),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='data_format',
            field=models.ForeignKey(default=alyx.data.models.default_data_format, on_delete=django.db.models.deletion.PROTECT, to='data.dataformat'),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='dataset_type',
            field=models.ForeignKey(default=alyx.data.models.default_dataset_type, on_delete=django.db.models.deletion.PROTECT, to='data.datasettype'),
        ),
        migrations.AlterField(
            model_name='datasettype',
            name='filename_pattern',
            field=alyx.base.base.CharNullField(blank=True, help_text="File name pattern (with wildcards) for this file in ALF naming convention. E.g. 'spikes.times.*' or '*.timestamps.*', or 'spikes.*.*' for a DataCollection, which would include all files starting with the word 'spikes'. NB: Case-insensitive matching.If null, the name field must match the object.attribute part of the filename.", max_length=255, null=True, unique=True),
        ),
    ]
