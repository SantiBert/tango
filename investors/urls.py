from django.urls import path
from .views import (
    InvestmentRoundView,
    InvestmentBanksView,
    InvestmentChangeAmountView,
    InvestmentChangeRaisedAmountView,
    InvestmentRoundConfirmView,
    DeleteInvestmentRound,
    EditInvestorinParticularRound,
    AddInvestorinParticularRound,
    DeleteInvestorinParticularRound,
    EditParticularInvestmentRound,
    InversorTemporalListView,
    FavoriteInvestorsListViews,
    FavoriteInvestorsViews,
    GetEmailInvestorViews
    )

urlpatterns = [
    path('startup/<str:startupId>/investments/',InvestmentRoundView.as_view(),name="investments"),
    path('startup/<str:startupId>/investments/banks/',InvestmentBanksView.as_view(),name="investments-banks"),
    path('startup/<str:startupId>/investments/<int:userInvestmentId>/confirm/', InvestmentRoundConfirmView.as_view(), name="investments-confirm"),
    path('startup/<str:startupId>/investments/<int:investmentId>/change-amount/',InvestmentChangeAmountView.as_view(),name="investments-change-amount"),
    path('startup/<str:startupId>/investments/<int:investmentId>/change-raised-amount/',InvestmentChangeRaisedAmountView.as_view(),name="investments-change-raised-amount"),
    path('startup/<str:startupId>/investments/<int:roundId>/delete/',DeleteInvestmentRound.as_view(),name="investments-delete"),
    path('startup/<str:startupId>/investments/<int:investmentId>/edit-investor/<int:investorId>',EditInvestorinParticularRound.as_view(),name="investor-edit"),
    path('startup/<str:startupId>/investments/<int:investmentId>/add-investor/', AddInvestorinParticularRound.as_view(),name="investor-add"),
    path('startup/<str:startupId>/investments/<int:investmentId>/delete-investor/<int:investorId>', DeleteInvestorinParticularRound.as_view(),name="investor-delete"),
    path('startup/<str:startupId>/investments/<int:investmentId>/edit/', EditParticularInvestmentRound.as_view(),name="investment-edit"),
    path('startup/<str:startupId>/temporal-investors/', InversorTemporalListView.as_view(),name="temporal-investors"),
    path('startup/<str:startupId>/investments/favorites/', FavoriteInvestorsListViews.as_view(), name='favorites-investors'),
    path('startup/<str:startupId>/investments/favorites/<int:investorId>/edit/', FavoriteInvestorsViews.as_view(), name='favorites-investors-edit'),
    path('startup/<str:startupId>/investments/favorites/<int:investorId>/get-email/', GetEmailInvestorViews.as_view(), name='investors-get-email'),
]   
