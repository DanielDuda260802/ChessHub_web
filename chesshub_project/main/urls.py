from django.urls import path
from . import views
from .views import game_details, get_game_moves, upload_pgn, get_games, filtered_games, reset_game, get_games_by_fen, clear_filters

app_name = 'main'  

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path("add-move/", views.add_move, name="add_move"),
    path("prev-move/", views.prev_move, name="prev_move"),
    path("next-move/", views.next_move, name="next_move"),
    path("current_state/", views.current_state, name="current_state"),
    path("choose-variation/", views.choose_variation, name="choose_variation"),
    path('get_games/', views.get_games, name='get_games'),
    path('game_details/<int:game_id>/', views.game_details, name='game_details'),
    path('get_game_moves/<int:game_id>/', get_game_moves, name='get_game_moves'),
    path('upload-pgn/', upload_pgn, name='upload_pgn'),
    path('task-status/<str:task_id>/', views.check_task_status, name='task_status'),
    path('api/games/', get_games, name='get_games'),
    path('filtered_games/', filtered_games, name='filtered_games'),
    path('reset_game/', views.reset_game, name='reset_game'),
    path('get_games_by_fen/', views.get_games_by_fen, name='get_games_by_fen'),
    path('clear_filters/', views.clear_filters, name='clear_filters')
]