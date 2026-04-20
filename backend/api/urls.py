"""
URL configuration for API app.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('test/', views.test_json, name='test_json'),
    # Run simulation (slow - runs prediction)
    path('simulate/run/', views.run_simulation, name='run_simulation'),
    # Database query endpoints (fast - reads saved data)
    path('simulation/latest/', views.get_latest_simulation, name='get_latest_simulation'),
    path('matches/', views.get_matches, name='get_matches'),
    path('standings/', views.get_standings, name='get_standings'),
    path('teams/stats/', views.get_team_stats, name='get_team_stats'),
    path('results/full/', views.get_full_results, name='get_full_results'),
]
