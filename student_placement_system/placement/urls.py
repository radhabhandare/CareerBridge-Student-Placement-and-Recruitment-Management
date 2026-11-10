from django.urls import path
from . import views


urlpatterns = [
    # General pages
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('success/', views.success, name='success'),

    # Login, activation and logout
    path('login/', views.login_page, name='login'),
    path(
        'activate/<uid>/<token>/',
        views.activate,
        name='activate'
    ),
    path('logout/', views.logout_page, name='logout'),

    # Student pages
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('jobs/', views.jobs, name='jobs'),
    path(
        'jobs/<int:pk>/',
        views.job_detail,
        name='job_detail'
    ),
    path(
        'jobs/<int:pk>/apply/',
        views.apply,
        name='apply'
    ),
    path('applications/', views.applications, name='applications'),
    path('notifications/', views.notices, name='notices'),

    # Admin pages
    path(
        'placement-admin/',
        views.admin_home,
        name='admin_home'
    ),
    path(
        'placement-admin/students/',
        views.admin_students,
        name='admin_students'
    ),
    path(
        'placement-admin/students/<int:pk>/approve/',
        views.approve,
        name='approve'
    ),
    path(
        'placement-admin/students/<int:pk>/reject/',
        views.reject,
        name='reject'
    ),
    path(
        'placement-admin/students/<int:pk>/resend-activation/',
        views.resend_activation,
        name='resend_activation'
    ),

    # Company and job management
    path(
        'placement-admin/companies/',
        views.companies,
        name='companies'
    ),
    path(
        'placement-admin/jobs/',
        views.jobs_admin,
        name='jobs_admin'
    ),

    # Application management
    path(
        'placement-admin/applications/',
        views.apps_admin,
        name='apps_admin'
    ),
]