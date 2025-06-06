# Generated by Django 5.1.4 on 2025-01-08 07:51

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ChessGame',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('white_player', models.CharField(max_length=100)),
                ('black_player', models.CharField(max_length=100)),
                ('white_elo', models.IntegerField(blank=True, null=True)),
                ('black_elo', models.IntegerField(blank=True, null=True)),
                ('result', models.CharField(max_length=7)),
                ('event', models.CharField(blank=True, max_length=200, null=True)),
                ('site', models.CharField(blank=True, max_length=200, null=True)),
                ('date', models.DateField(blank=True, null=True)),
                ('round', models.CharField(blank=True, max_length=50, null=True)),
                ('pgn', models.TextField()),
            ],
        ),
    ]
