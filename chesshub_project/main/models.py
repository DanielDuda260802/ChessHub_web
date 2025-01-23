from django.db import models
from django.contrib.postgres.indexes import BrinIndex

RESULT_CHOICES = [
    ("1-0", "White Wins"),
    ("0-1", "Black Wins"),
    ("1/2-1/2", "Draw"),
    ("", "Unknown")
]

class Game(models.Model):
    white_player = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    black_player = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    white_FideId = models.IntegerField(blank=True, null=True, db_index=True)
    black_FideId = models.IntegerField(blank=True, null=True, db_index=True)
    white_elo = models.IntegerField(blank=True, null=True, db_index=True)
    black_elo = models.IntegerField(blank=True, null=True, db_index=True)
    white_title = models.CharField(max_length=5, blank=True, null=True)
    black_title = models.CharField(max_length=5, blank=True, null=True)
    result = models.CharField(max_length=10, choices=RESULT_CHOICES, db_index=True, default="")
    date = models.DateField(blank=True, null=True, db_index=True)
    event_date = models.DateField(blank=True, null=True)
    site = models.CharField(max_length=200, blank=True, null=True)
    round = models.CharField(max_length=50, blank=True, null=True)
    eco = models.CharField(max_length=10, blank=True, null=True, db_index=True)
    notation = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.white_player} vs {self.black_player} ({self.date})"

    class Meta:
        indexes = [
            models.Index(fields=['date']),  
            BrinIndex(fields=['date']),  
            models.Index(fields=['white_elo']),
            models.Index(fields=['black_elo']),
            models.Index(fields=['white_elo', 'black_elo']),
            models.Index(fields=['result']),
            models.Index(fields=['eco']),
        ]
        ordering = ['-date']


class FENPosition(models.Model):
    fen_string = models.CharField(max_length=100, db_index=True)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    move_number = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['fen_string']),
            models.Index(fields=['game']),
        ]

    def __str__(self):
        return f"FEN: {self.fen_string} - Game: {self.game_id} - Move: {self.move_number}"


class PGNFile(models.Model):
    file = models.FileField(upload_to='pgn_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name