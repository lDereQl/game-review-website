# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('account/<int:user_id>/', views.account_details, name='account_details'),
    path('game/<int:game_id>/', views.game_detail, name='game_detail'),
    path('games/', views.game_list, name='game_list'),
    path('game/create/', views.create_game, name='create_game'),
    path('game/edit/<int:game_id>/', views.edit_game, name='edit_game'),
    path('game/delete/<int:game_id>', views.delete_game, name='delete_game'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('critic/edit/', views.edit_critic, name='edit_critic'),
    path('critic/delete/', views.delete_critic, name='delete_critic'),
    path('critic/delete_confirm/', views.delete_critic_confirm, name='delete_critic_confirm'), 
    path('critic/verify/', views.verify_critic, name='verify_critic'), 
    path('critic/dashboard/', views.critic_dashboard, name='critic_dashboard'),
    path('game/<int:game_id>/all_reviews/', views.all_reviews, name='all_reviews'),
    path('game/<int:game_id>/create_review/', views.create_review, name='create_review'),
    path('adminas/user_list/', views.user_list, name='user_list'),
    path('adminas/update_role/<int:user_id>/', views.update_user_role, name='update_user_role'),
    path('upload/', views.upload_file, name='upload_file'),
    path('comments/edit/<int:comment_id>/', views.edit_comment, name='edit_comment'),
    path('comments/<int:comment_id>/like/', views.like_comment, name='like_comment'),
    path('game/<int:game_id>/import_steam_comments/', views.import_steam_comments, name='import_steam_comments'),
    path('game/hide/<int:game_id>/', views.hide_game, name='hide_game'),
    path('game/delete/<int:game_id>/', views.delete_game, name='delete_game'),
    path('game/toggle_visibility/<int:game_id>/', views.toggle_game_visibility, name='toggle_game_visibility'),
]
