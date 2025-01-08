from django.urls import path
from . import views

app_name = 'main'  

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path("add-move/", views.add_move, name="add_move"),
    path("validate_move/", views.validate_move, name="validate_move"),
    path("prev-move/", views.prev_move, name="prev_move"),
    path("next-move/", views.next_move, name="next_move"),
    path("current_state/", views.current_state, name="current_state"),
    path("choose-variation/", views.choose_variation, name="choose_variation"),
]
