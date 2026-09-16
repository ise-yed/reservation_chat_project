from django.urls import path

from apps.authentication.api.v1.views import (
    LoginView,
    LogoutView,
    MeView,
    PasswordChangeConfirmView,
    PasswordChangeRequestView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RefreshTokenView,
    RegisterView,
)

app_name = "authentication"

urlpatterns = [
  
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("refresh/", RefreshTokenView.as_view(), name="auth-token-refresh"),
    path("me/", MeView.as_view(), name="me"),
    
    path("password/reset/request-otp/", PasswordResetRequestView.as_view(), name="password_reset_request"),
    path("password/reset/confirm/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    
    path("password/change/request-otp/", PasswordChangeRequestView.as_view(), name="password_change_request"),
    path("password/change/confirm/", PasswordChangeConfirmView.as_view(), name="password_change_confirm"),
]