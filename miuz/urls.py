from django.urls import path
from . import views
from django.contrib.auth.views import LoginView
from django.contrib.auth import views as auth_views
scope = "openid profile email"

urlpatterns = [

    path('login/', views.oneid_login, name='oneid_login'),
    path('callback/', views.oneid_callback, name='oneid_callback'),
    path('', LoginView.as_view(template_name='login.html'), name='login'),
    path('redirect/', views.LoginRedirectView, name='redirect'),  # Yo'naltiruvchi view
    path('account/', views.HomeView, name='home'),  # Admin uchun sahifa
    path('register/', views.LoginRedirectView, name='register'),  # Admin uchun sahifa
    path('sciences/', views.SciencesView, name="sciences"),
    path('groups/', views.GroupsView, name="groups"),
    path('adminapplications/', views.admin_applicationfilter, name='adminapplications'),
    # path('adminapplications/create/', views.application_create_view, name='application_create'),
    path('applications/', views.admin_applicationfilter, name='applications'),
    path('archive/', views.ArchiveView, name="archive"),
    path('export_excel/', views.export_excel, name='export_excel'),
    path('export_excelgroup/', views.export_excelgroup, name='export_excelgroup'),
    path('update_status/<int:pk>/', views.update_status, name='update_status'),  # Statusni yangilash
    # path('adminapplications/comissions/', views.comissions_view, name='adminapplications_comissions'),  # Statusni yangilash

]
