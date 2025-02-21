from django.urls import path
from . import views
from django.contrib.auth.views import LoginView
from django.contrib.auth import views as auth_views
scope = "openid profile email"

urlpatterns = [
    # Login sahifasi (admin uchun login va parol)
       
    path('callback/', views.callback, name='callback'),
    path('', views.LoginView, name='login'),
    path('logout/', views.logout, name='logout'),
    path('home/', views.HomeView, name='home'),
    # Foydalanuvchi uchun ariza ko'rish
    path('applications/', views.admin_applicationfilter_user, name='applications'), 
    # Admin uchun arizalarni filtrlash
    path('adminapplications/', views.admin_applicationfilter_admin, name='admin_applications'),

    path('sciences/', views.SciencesView, name="sciences"),
    path('groups/', views.GroupsView, name="groups"),
    
    path('archive/', views.ArchiveView, name="archive"),
    path('export_excel/', views.export_excel, name='export_excel'),
    path('export_excelgroup/', views.export_excelgroup, name='export_excelgroup'),
    path('update_status/<int:pk>/', views.update_status, name='update_status'),
    path('generate-certificate/<int:result_id>/', views.generate_certificate, name='generate_certificate'),
    path('verify/<int:result_id>/', views.verify_certificate, name='verify_certificate'),
    path('curriculum/', views.curriculum_view, name='curriculum_view'),
    path('curriculum_user/', views.curriculum_user, name='curriculum_user'),
]
