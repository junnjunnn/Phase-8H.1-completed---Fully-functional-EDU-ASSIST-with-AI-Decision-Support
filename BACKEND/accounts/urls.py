from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    CurrentUserView,
    LoginView,
    LogoutView,
    UserListCreateView,
    UserRetrieveUpdateView,
    activate_user,
    deactivate_user,
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='auth-login'),
    path('me/', CurrentUserView.as_view(), name='auth-me'),
    path('logout/', LogoutView.as_view(), name='auth-logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('users/', UserListCreateView.as_view(), name='auth-user-list'),
    path('users/<int:pk>/', UserRetrieveUpdateView.as_view(), name='auth-user-detail'),
    path('users/<int:pk>/activate/', activate_user, name='auth-user-activate'),
    path('users/<int:pk>/deactivate/', deactivate_user, name='auth-user-deactivate'),
]
