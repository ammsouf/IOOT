from django.urls import path
from . import views, api

urlpatterns = [
    path("", views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("graph_temp/", views.graph_temp, name="graph_temp"),
    path("graph_hum/", views.graph_hum, name="graph_hum"),
    path("api/", api.Dlist, name="api_list"),
    path("latest/", api.latest, name="latest"),
    path("history/", api.history, name="history"),
    path("api/post/", api.Dhtviews.as_view(), name="api_post"),
    path('api/endpoint/', views.save_measurements, name='save_measurements'),
    path('archive/', views.incident_archive, name='incident_archive'),
    path('create_incident/', views.create_incident, name='create_incident'),
    path('incident_dashboard/', views.incident_dashboard, name='incident_dashboard'),
    path('incident/<int:incident_id>/', views.incident_detail, name='incident_detail'),
    path('submit_comment/', views.submit_comment, name='submit_comment'),
    path('api/temperature-history/', views.temperature_history, name='temperature_history'),
    path('api/humidity-history/', views.humidity_history, name='humidity_history'),
]
