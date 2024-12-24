from django.urls import path

from .views import (    
    ChangePasswordView,
    DeleteAccountView,
    ForgotPasswordView,
    LoginView,
    SignUpView,
    UpdateUserProfileView,
    UserEditFirstNameProfileView,
    UserEditLastNameProfileView,
    UserEditBioProfileView,
    UserEditSocialMediaProfileView,
    UserProfileView,
    UserEditTagLineProfileView,
    UserProfileProfessionalHistoryView,
    UserProfilePictureView,
    VerificateSignupCodeView,
    ResendVerificationCodeView
)

urlpatterns = [
    path(
        "auth/verificate-code/",
        VerificateSignupCodeView.as_view(),
        name="verificate-code",
    ),
    path(
        "auth/resend-code/",
        ResendVerificationCodeView.as_view(),
        name="resend-code",
    ),
    path(
        "auth/signup/",
        SignUpView.as_view(),
        name="signup",
    ),
    path(
        "auth/login/",
        LoginView.as_view(),
        name="login",
    ),
    path(
        "auth/change-password/",
        ChangePasswordView.as_view(),
        name="change-password",
    ),
    path(
        "auth/forgot-password/",
        ForgotPasswordView.as_view(),
        name="forgot-password",
    ),
     path(
        "auth/delete-account/",
        DeleteAccountView.as_view(),
        name="delete-account",
    ),
    path(
        "profile/change-first-name/",
        UserEditFirstNameProfileView.as_view(),
        name="profile-first-name-change",
    ),
    path(
        "profile/change-last-name/",
        UserEditLastNameProfileView.as_view(),
        name="profile-last-name-change",
    ),
     path(
        "profile/change-bio/",
        UserEditBioProfileView.as_view(),
        name="profile-bio-change"
        ),
    path(
        "profile/change-social-media/",
        UserEditSocialMediaProfileView.as_view(),
        name="profile-social-media-change",
    ),
    path(
        "profile",
        UserProfileView.as_view(),
        name = "profile"
    ),
    path(
        "profile/update/",
        UpdateUserProfileView.as_view(),
        name = "profile-update"
    ),
    path(
        "profile/change-tag-line/",
        UserEditTagLineProfileView.as_view(),
        name="profile-tag-line-change",
    ),
    path(
        "profile/professional-history/",
        UserProfileProfessionalHistoryView.as_view(),
        name="profile-professional-history",
    ),
    path(
        "profile/change-profile-image/",
        UserProfilePictureView.as_view(),
        name="profile-image",
    )
]

