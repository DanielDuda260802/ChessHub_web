from django.db import models

class Game(models.Model):
    white_player = models.CharField(max_length=100, blank=True, null=True)
    black_player = models.CharField(max_length=100, blank=True, null=True)
    white_FideId = models.IntegerField(blank=True, null=True)
    black_FideId = models.IntegerField(blank=True, null=True)
    white_elo = models.IntegerField(blank=True, null=True)
    black_elo = models.IntegerField(blank=True, null=True)
    white_title = models.CharField(max_length=5, blank=True, null=True)
    black_title = models.CharField(max_length=5, blank=True, null=True)
    result = models.CharField(max_length=10, blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    event_date = models.DateField(blank=True, null=True)
    site = models.CharField(max_length=200, blank=True, null=True)
    round = models.CharField(max_length=50, blank=True, null=True)
    eco = models.CharField(max_length=10, blank=True, null=True)
    notation = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.white} vs {self.black} ({self.date})"
