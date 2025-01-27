from django.urls import path
from . import views
from django.contrib.auth.views import LoginView
from django.contrib.auth import views as auth_views
scope = "openid profile email"

urlpatterns = [
    # Login sahifasi (admin uchun login va parol)
       
    path('callback/', views.callback, name='callback'),
    path('', views.LoginView, name='login'),  
    path('home/', views.HomeView, name='home'),
    path('applications/<str:username>/', views.HomeView, name='applications'),
    path('applications/', views.admin_applicationfilter, name='applications'),
    path('sciences/', views.SciencesView, name="sciences"),
    path('groups/', views.GroupsView, name="groups"),
    path('adminapplications/', views.admin_applicationfilter, name='adminapplications'),
    #path('generate_word/', views.generate_word, name='generate_word'),
    path('archive/', views.ArchiveView, name="archive"),
    path('export_excel/', views.export_excel, name='export_excel'),
    path('export_excelgroup/', views.export_excelgroup, name='export_excelgroup'),
    path('update_status/<int:pk>/', views.update_status, name='update_status'),

    path('download_certificate/<int:application_id>/', views.download_certificate, name='download_certificate'),
    path('review/<int:application_id>/', views.application_review, name='application_review'),
]
