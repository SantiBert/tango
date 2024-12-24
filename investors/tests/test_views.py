import pytest

from rest_framework.test import APIClient
from rest_framework import status

from django.urls import reverse

from users.tests.fixtures import (
    common_user_token, 
    common_user_founder
    )
from startups.tests.fixtures import (
    common_startup, 
    common_secondary_startup,
    common_third_startup
    )

from startups.models import StartupCategory
from pjbackend.constants import INDUSTRIES_CATEGORIES

from investors.models import (InvestmentRound, InvestorUser, InversorTemporal, FavoriteInvestorsTemporal)

TEMPORAL_INVESTORS = [{
    "email":"arunas.chesonis@safar.partners",
    "first_name":"Arunas",
    "last_name":"Chesonis",
    "firm_name":"Safar Partners",
    "website":"http://www.safar.partners",
    "founding_year": 2019,
    "description":"Safar Partners is a seed- to growth-stage venture fund.",
    "fund_stage":"Seed,Pre-Seed,Series A,Series B,Series C,Series D",
    "fund_type":"Venture Fund",
    "linkedin_link":"https://www.linkedin.com/company/safar-partners/",
    "witter_link":"",
    "city":"Cambridge",
    "state":"Texas",
    "country":"United States",
    "location":"Cambridge",
    "industry":"Health,AI & Machine Learning,Climate & Impact,Software & Internet,Infrastructure",
    "status":"Verified",
    "test":"checked"
},{
    "email":"venk@montavc.com",
    "first_name":"Venktesh",
    "last_name":"Shukla",
    "firm_name":"Monta Vista Capital",
    "website":"http://www.montavc.com",
    "founding_year": 2014,
    "description":"Monta Vista Capital is an investment company focused on early stage B2B companies.",
    "fund_stage":"Seed,Pre-Seed,Series A",
    "fund_type":"Venture Fund",
    "linkedin_link":"https://www.linkedin.com/company-beta/4861438/",
    "witter_link":"https://twitter.com/MontaVC",
    "city":"Mountain View",
    "state":"California",
    "country":"United States",
    "location":"Mountain View",
    "industry":"Hardware,Logistics,Software & Internet,Infrastructure,AI & Machine Learning",
    "status":"Verified",
    "test":"checked"
}]

main_user_token = common_user_token
second_user = common_user_founder
main_startup = common_startup
second_startup = common_secondary_startup
third_startup = common_third_startup

FAKE_UUID = 'a8098c1a-f86e-11da-bd1a-00112444be1e'

def create_investor(investor_data):
    return InversorTemporal.objects.create(
        email=investor_data.get("email"),
        first_name=investor_data.get("first_name", "")[:100],
        last_name=investor_data.get("last_name", "")[:100],
        firm_name=investor_data.get("firm_name", "")[:100],
        website=investor_data.get("website", "")[:100],
        founding_year=str(investor_data.get("founding_year")),
        description=investor_data.get("description", ""),
        fund_stage=investor_data.get("fund_stage", "")[:100],
        fund_type=investor_data.get("fund_type", "")[:100],
        linkedin_link=investor_data.get("linkedin_link", "")[:100],
        twitter_link=investor_data.get("twitter_link", "")[:100],
        city=investor_data.get("city", "")[:100],
        state=investor_data.get("state", "")[:100],
        country=investor_data.get("country", "")[:100],
        location=investor_data.get("location", "")[:100],
        industry=investor_data.get("industry", "")[:100],
        status=investor_data.get("status", "pending"),
        test=investor_data.get("test", "")[:50],
    )

@pytest.mark.django_db
def test_create_multiple_investments_in_single_round_successfully(mocker, main_user_token, main_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    data = {
        'roundType': 'Seed',
        'amount': 100000,
        'raisedAmount': 2050000,
        'date': '2024-04-26T12:00:00Z',
        'investors': [
            {
                'firstName': 'John',
                'lastName': 'Doe',
                'firmName': 'ABC Ventures',
                'email': 'john.doe@example.com',
                'amountInvested': 50000,
                'investedType': 'Equity'
            },
            {
                'firstName': "Roelof",
                'lastName': 'Botha',
                'firmName': 'Sequoia Ventures',
                'email': 'early-rb@sequoiacap.com',
                'amountInvested': 1000000,
                'investedType':'Equilty'
            },
            {
                 'firstName': "Zach",
                'lastName': 'Cohen',
                'firmName': 'andressen horowitz',
                'email': ' zachcohen@a16z.com',
                'amountInvested': 1000000,
                'investedType':'Equilty' 
            }
        ]
        }
    url = reverse('investments', kwargs={"startupId": main_startup.id})
    mocker.patch("pjbackend.utils.send_investors_invite_email", return_value=True)
    response = client.put(url, data, format='json')
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.django_db
def test_create_multiple_as_cofounder_investments_in_single_round_successfully(mocker, main_user_token, third_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    data = {
        'roundType': 'Seed',
        'amount': 100000,
        'raisedAmount': 2050000,
        'date': '2024-04-26T12:00:00Z',
        'investors': [
            {
                'firstName': 'John',
                'lastName': 'Doe',
                'firmName': 'ABC Ventures',
                'email': 'john.doe@example.com',
                'amountInvested': 50000,
                'investedType': 'Equity'
            },
            {
                'firstName': "Roelof",
                'lastName': 'Botha',
                'firmName': 'Sequoia Ventures',
                'email': 'early-rb@sequoiacap.com',
                'amountInvested': 1000000,
                'investedType':'Equilty'
            },
            {
                 'firstName': "Zach",
                'lastName': 'Cohen',
                'firmName': 'andressen horowitz',
                'email': ' zachcohen@a16z.com',
                'amountInvested': 1000000,
                'investedType':'Equilty' 
            }
        ]
        }
    url = reverse('investments', kwargs={"startupId": third_startup.id})
    mocker.patch("pjbackend.utils.send_investors_invite_email", return_value=True)
    response = client.put(url, data, format='json')
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.django_db
def test_create_investment_round_successfully(mocker, main_user_token,main_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    data = {
        'roundType': 'Seed',
        'amount': 100000,
        'raisedAmount': 50000,
        'date': '2024-04-26T12:00:00Z',
        'investors': [
            {
                'firstName': 'John',
                'lastName': 'Doe',
                'firmName': 'ABC Ventures',
                'email': 'john.doe@example.com',
                'amountInvested': 50000,
                'investedType': 'Equity'
            }
        ]
    }
    url = reverse('investments', kwargs={"startupId": main_startup.id})
    mocker.patch("pjbackend.utils.send_investors_invite_email", return_value=True)
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_201_CREATED

@pytest.mark.django_db
def test_create_investment_as_cofounder_round_successfully(mocker, main_user_token,third_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    data = {
        'roundType': 'Seed',
        'amount': 100000,
        'raisedAmount': 50000,
        'date': '2024-04-26T12:00:00Z',
        'investors': [
            {
                'firstName': 'John',
                'lastName': 'Doe',
                'firmName': 'ABC Ventures',
                'email': 'john.doe@example.com',
                'amountInvested': 50000,
                'investedType': 'Equity'
            }
        ]
    }
    url = reverse('investments', kwargs={"startupId": third_startup.id})
    mocker.patch("pjbackend.utils.send_investors_invite_email", return_value=True)
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_201_CREATED

@pytest.mark.django_db
def test_create_investment_round_wrong_id(mocker, main_user_token):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
   
    data = {
        'roundType': 'Seed',
        'amount': 100000,
        'raisedAmount': 50000,
        'date': '2024-04-26T12:00:00Z',
        'investors': [
            {
                'firstName': 'John',
                'lastName': 'Doe',
                'firmName': 'ABC Ventures',
                'email': 'john.doe@example.com',
                'amountInvested': 50000,
                'investedType': 'Equity'
            }
        ]
    }
    url = reverse('investments', kwargs={"startupId":FAKE_UUID})
    mocker.patch("pjbackend.utils.send_investors_invite_email", return_value=True)
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
def test_create_investment_round_not_authorized(mocker, main_user_token,second_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    data = {
        'roundType': 'Seed',
        'amount': 100000,
        'raisedAmount': 50000,
        'date': '2024-04-26T12:00:00Z',
        'investors': [
            {
                'firstName': 'John',
                'lastName': 'Doe',
                'firmName': 'ABC Ventures',
                'email': 'john.doe@example.com',
                'amountInvested': 50000,
                'investedType': 'Equity'
            }
        ]
    }
    url = reverse('investments', kwargs={"startupId": second_startup.id})
    response = client.post(url, data, format='json')
    mocker.patch("pjbackend.utils.send_investors_invite_email", return_value=True)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    
@pytest.mark.django_db
def test_create_investment_round_anonymous_user(main_startup):
    client = APIClient()
    
    data = {
        'roundType': 'Seed',
        'amount': 100000,
        'raisedAmount': 50000,
        'date': '2024-04-26T12:00:00Z',
        'investors': [
            {
                'firstName': 'John',
                'lastName': 'Doe',
                'firmName': 'ABC Ventures',
                'email': 'john.doe@example.com',
                'amountInvested': 50000,
                'investedType': 'Equity'
            }
        ]
    }
    url = reverse('investments', kwargs={"startupId": main_startup.id})
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
@pytest.mark.django_db
def test_get_investment_round_successfully(main_user_token,main_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    investment_round = InvestmentRound.objects.create(startup=main_startup,round_type='Seed', amount=100000, raised_amount=50000)
    InvestorUser.objects.create(
        round=investment_round,
        first_name='John',
        last_name='Doe',
        firm_name='ABC Ventures',
        email='john.doe@example.com',
        amount_invested=50000,
        invested_type='Equity'
    )
    url = reverse('investments', kwargs={"startupId": main_startup.id})
    response = client.get(url)
    
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.django_db
def test_get_investment_round_as_cofounder_successfully(main_user_token,third_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    investment_round = InvestmentRound.objects.create(startup=third_startup,round_type='Seed', amount=100000, raised_amount=50000)
    InvestorUser.objects.create(
        round=investment_round,
        first_name='John',
        last_name='Doe',
        firm_name='ABC Ventures',
        email='john.doe@example.com',
        amount_invested=50000,
        invested_type='Equity'
    )
    url = reverse('investments', kwargs={"startupId": third_startup.id})
    response = client.get(url)
    
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.django_db
def test_get_investment_round_round_wrong_id(main_user_token,main_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    investment_round = InvestmentRound.objects.create(startup=main_startup,round_type='Seed', amount=100000, raised_amount=50000)
    InvestorUser.objects.create(
        round=investment_round,
        first_name='John',
        last_name='Doe',
        firm_name='ABC Ventures',
        email='john.doe@example.com',
        amount_invested=50000,
        invested_type='Equity'
    )
    url = reverse('investments', kwargs={"startupId": FAKE_UUID})
    response = client.get(url)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    
@pytest.mark.django_db
def test_get_investment_round_not_authorized(main_user_token,main_startup, second_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    investment_round = InvestmentRound.objects.create(startup=main_startup,round_type='Seed', amount=100000, raised_amount=50000)
    InvestorUser.objects.create(
        round=investment_round,
        first_name='John',
        last_name='Doe',
        firm_name='ABC Ventures',
        email='john.doe@example.com',
        amount_invested=50000,
        invested_type='Equity'
    )
    url = reverse('investments', kwargs={"startupId": second_startup.id})
    response = client.get(url)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    
@pytest.mark.django_db
def test_get_investment_round_anonymous_user(main_startup):
    client = APIClient()
    investment_round = InvestmentRound.objects.create(startup=main_startup,round_type='Seed', amount=100000, raised_amount=50000)
    InvestorUser.objects.create(
        round=investment_round,
        first_name='John',
        last_name='Doe',
        firm_name='ABC Ventures',
        email='john.doe@example.com',
        amount_invested=50000,
        invested_type='Equity'
    )
    url = reverse('investments', kwargs={"startupId": main_startup.id})
    response = client.get(url)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_change_investment_round_amount(main_user_token,main_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    investment_round = InvestmentRound.objects.create(startup=main_startup,round_type='Seed', amount=100000, raised_amount=50000)
    InvestorUser.objects.create(
        round=investment_round,
        first_name='John',
        last_name='Doe',
        firm_name='ABC Ventures',
        email='john.doe@example.com',
        amount_invested=50000,
        invested_type='Equity'
    )
    
    url = reverse('investments-change-amount',args=(main_startup.id, investment_round.id))  
    
    data = {'amount': 150000}
    
    response = client.put(url, data, format='json')
    
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.django_db
def test_change_investment_round_amount_as_cofounder(main_user_token,third_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    investment_round = InvestmentRound.objects.create(startup=third_startup,round_type='Seed', amount=100000, raised_amount=50000)
    InvestorUser.objects.create(
        round=investment_round,
        first_name='John',
        last_name='Doe',
        firm_name='ABC Ventures',
        email='john.doe@example.com',
        amount_invested=50000,
        invested_type='Equity'
    )
    
    url = reverse('investments-change-amount',args=(third_startup.id, investment_round.id))  
    
    data = {'amount': 150000}
    
    response = client.put(url, data, format='json')
    
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.django_db
def test_change_investment_round_raised_amount(main_user_token,main_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    investment_round = InvestmentRound.objects.create(startup=main_startup,round_type='Seed', amount=100000, raised_amount=50000)
    InvestorUser.objects.create(
        round=investment_round,
        first_name='John',
        last_name='Doe',
        firm_name='ABC Ventures',
        email='john.doe@example.com',
        amount_invested=50000,
        invested_type='Equity'
    )
    
    url = reverse('investments-change-raised-amount', args=(main_startup.id, investment_round.id))
    
    data = {'raisedAmount': 75000}
    
    response = client.put(url, data, format='json')
    
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_update_investor_details_inparticular_round(main_user_token,main_startup):
    client = APIClient()
    token = main_user_token.get("token")
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)

    investment_round = InvestmentRound.objects.create(startup=main_startup, round_type='Seed', amount=100000, raised_amount=50000)
    investor = InvestorUser.objects.create(
        round=investment_round,
        first_name='John',
        last_name='Doe',
        firm_name='ABC Ventures',
        amount_invested=50000,
        invested_type='Equity'
    )

    #data for updating
    url = reverse('investor-edit', args=(main_startup.id, investment_round.id, investor.id))
    updated_data = {
        'firstName': 'Jane',
        'lastName': 'Doe',
        'firmName': 'XYZ Ventures',
        'email': 'jane.doe@example.com',
        'amountInvested': 75000,
        'investedType': 'Equity'
    }
    response = client.put(url, updated_data, format='json')
    assert response.status_code == status.HTTP_200_OK
    investor.refresh_from_db()
    assert investor.first_name == 'Jane'
    assert investor.last_name == 'Doe'
    assert investor.firm_name == 'XYZ Ventures'
    assert investor.email == 'jane.doe@example.com'
    assert investor.amount_invested == 75000
    assert investor.invested_type == 'Equity'    


@pytest.mark.django_db
def test_update_investor_details_as_cofounder_inparticular_round(main_user_token,third_startup):
    client = APIClient()
    token = main_user_token.get("token")
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)

    investment_round = InvestmentRound.objects.create(startup=third_startup, round_type='Seed', amount=100000, raised_amount=50000)
    investor = InvestorUser.objects.create(
        round=investment_round,
        first_name='John',
        last_name='Doe',
        firm_name='ABC Ventures',
        amount_invested=50000,
        invested_type='Equity'
    )

    #data for updating
    url = reverse('investor-edit', args=(third_startup.id, investment_round.id, investor.id))
    updated_data = {
        'firstName': 'Jane',
        'lastName': 'Doe',
        'firmName': 'XYZ Ventures',
        'email': 'jane.doe@example.com',
        'amountInvested': 75000,
        'investedType': 'Equity'
    }
    response = client.put(url, updated_data, format='json')
    assert response.status_code == status.HTTP_200_OK
    investor.refresh_from_db()
    assert investor.first_name == 'Jane'
    assert investor.last_name == 'Doe'
    assert investor.firm_name == 'XYZ Ventures'
    assert investor.email == 'jane.doe@example.com'
    assert investor.amount_invested == 75000
    assert investor.invested_type == 'Equity'    

@pytest.mark.django_db
def test_update_investor_details_inparticular_round_wrong_id(main_user_token,main_startup):
    client = APIClient()
    token = main_user_token.get("token")
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    investment_round = InvestmentRound.objects.create(startup=main_startup, round_type='Seed', amount=100000, raised_amount=50000)
    url = reverse('investor-edit', args=(main_startup.id, investment_round.id, 999))
    updated_data = {
        'firstName': 'Jane',
        'lastName': 'Doe',
        'firmName': 'XYZ Ventures',
        'email': 'jane.doe@example.com',
        'amountInvested': 75000,    
        'investedType': 'Equity'
    }
    response = client.put(url, updated_data, format='json')  
    assert response.status_code == status.HTTP_404_NOT_FOUND
    
@pytest.mark.django_db
def test_update_investor_details_inparticular_round_not_authorized(main_startup):
    client = APIClient()
    investment_round = InvestmentRound.objects.create(startup=main_startup, round_type='Seed', amount=100000, raised_amount=50000)
    investor = InvestorUser.objects.create(
        round=investment_round,
        first_name='John',
        last_name='Doe',
        firm_name='ABC Ventures',
        amount_invested=50000,
        invested_type='Equity'
    )
    url = reverse('investor-edit', args=(main_startup.id, investment_round.id, investor.id))
    updated_data = {
        'firstName': 'Jane',
        'lastName': 'Doe',
        'firmName': 'XYZ Ventures',
        'email': 'jane.doe@example.com',
        'amountInvested': 75000,
        'investedType': 'Equity'
    }
    response = client.put(url, updated_data, format='json')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_delete_investment_round(main_user_token,main_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    investment_round = InvestmentRound.objects.create(startup=main_startup,round_type='Seed', amount=100000, raised_amount=50000)
    InvestorUser.objects.create(
        round=investment_round,
        first_name='John',
        last_name='Doe',
        firm_name='ABC Ventures',
        amount_invested=50000,
        invested_type='Equity'
    )
    url = reverse('investments-delete', args=(main_startup.id, investment_round.id))
    response = client.delete(url)
    print(response.data)
    print(investment_round)
    print(InvestorUser.objects.all())
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.django_db
def test_delete_investment_as_cofounder_round(main_user_token,third_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    investment_round = InvestmentRound.objects.create(startup=third_startup,round_type='Seed', amount=100000, raised_amount=50000)
    InvestorUser.objects.create(
        round=investment_round,
        first_name='John',
        last_name='Doe',
        firm_name='ABC Ventures',
        amount_invested=50000,
        invested_type='Equity'
    )
    url = reverse('investments-delete', args=(third_startup.id, investment_round.id))
    response = client.delete(url)
    print(response.data)
    print(investment_round)
    print(InvestorUser.objects.all())
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.django_db
def test_delete_investment_round_with_multiple_investors(main_user_token, main_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
   
    investment_round = InvestmentRound.objects.create(
        startup=main_startup,
        round_type='Seed',
        amount=100000,
        raised_amount=50000,
        is_active=True  
    )
    investors_data = [
        {'first_name': 'John', 'last_name': 'Doe', 'firm_name': 'ABC Ventures', 'amount_invested': 50000, 'invested_type': 'Equity'},
        {'first_name': 'Jane', 'last_name': 'Smith', 'firm_name': 'XYZ Capital', 'amount_invested': 30000, 'invested_type': 'Debt'},
        {'first_name': 'Jim', 'last_name': 'Beam', 'firm_name': 'DEF Partners', 'amount_invested': 20000, 'invested_type': 'Equity'},
    ]
    for investor in investors_data:
        InvestorUser.objects.create(
            round=investment_round,
            first_name=investor['first_name'],
            last_name=investor['last_name'],
            firm_name=investor['firm_name'],
            amount_invested=investor['amount_invested'],
            invested_type=investor['invested_type']
        )
    url = reverse('investments-delete', args=(main_startup.id, investment_round.id))
    response = client.delete(url)

    assert response.status_code == 200
    investment_round.refresh_from_db()
    assert investment_round.is_active == False
    assert InvestorUser.objects.filter(round=investment_round).exists() == True

@pytest.mark.django_db
def test_delete_investment_round_wrong_id(main_user_token,main_startup):
    token = main_user_token.get("token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    investment_round = InvestmentRound.objects.create(startup=main_startup,round_type='Seed', amount=100000, raised_amount=50000)
    InvestorUser.objects.create(
        round=investment_round,
        first_name='John',
        last_name='Doe',
        firm_name='ABC Ventures',
        amount_invested=50000,
        invested_type='Equity'
    )
    url = reverse('investments-delete', args=(main_startup.id, 999))
    response = client.delete(url)
    assert response.status_code == 404

@pytest.mark.django_db
def test_delete_investment_round_not_authorized(main_startup):
    client = APIClient()
    investment_round = InvestmentRound.objects.create(startup=main_startup,round_type='Seed', amount=100000, raised_amount=50000)
    InvestorUser.objects.create(
        round=investment_round,
        first_name='John',
        last_name='Doe',
        firm_name='ABC Ventures',
        amount_invested=50000,
        invested_type='Equity'
    )
    url = reverse('investments-delete', args=(main_startup.id, investment_round.id))
    response = client.delete(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_delete_investor_inparticular_round(main_user_token,main_startup):
    client = APIClient()
    token = main_user_token.get("token")
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    investment_round = InvestmentRound.objects.create(startup=main_startup, round_type='Seed', amount=100000, raised_amount=50000)
    investor = InvestorUser.objects.create(
        round=investment_round,
        first_name='John',
        last_name='Doe',
        firm_name='ABC Ventures',
        amount_invested=50000,
        invested_type='Equity'
    )
    url = reverse('investor-delete', args=(main_startup.id, investment_round.id, investor.id))
    response = client.delete(url)
    assert response.status_code == status.HTTP_200_OK
    investor.refresh_from_db()
    assert investor.is_active == False

@pytest.mark.django_db
def test_delete_as_cofunder_investor_inparticular_round(main_user_token,third_startup):
    client = APIClient()
    token = main_user_token.get("token")
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    investment_round = InvestmentRound.objects.create(startup=third_startup, round_type='Seed', amount=100000, raised_amount=50000)
    investor = InvestorUser.objects.create(
        round=investment_round,
        first_name='John',
        last_name='Doe',
        firm_name='ABC Ventures',
        amount_invested=50000,
        invested_type='Equity'
    )
    url = reverse('investor-delete', args=(third_startup.id, investment_round.id, investor.id))
    response = client.delete(url)
    assert response.status_code == status.HTTP_200_OK
    investor.refresh_from_db()
    assert investor.is_active == False


@pytest.mark.django_db
def test_delete_investor_inparticular_round_wrong_id(main_user_token,main_startup):
    client = APIClient()
    token = main_user_token.get("token")
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    investment_round = InvestmentRound.objects.create(startup=main_startup, round_type='Seed', amount=100000, raised_amount=50000)
    url = reverse('investor-delete', args=(main_startup.id, investment_round.id, 999))
    response = client.delete(url)
    assert response.status_code == 404

@pytest.mark.django_db
def test_delete_investor_inparticular_round_not_authorized(main_startup):
    client = APIClient()
    investment_round = InvestmentRound.objects.create(startup=main_startup, round_type='Seed', amount=100000, raised_amount=50000)
    investor = InvestorUser.objects.create(
        round=investment_round,
        first_name='John',
        last_name='Doe',
        firm_name='ABC Ventures',
        amount_invested=50000,
        invested_type='Equity'
    )
    url = reverse('investor-delete', args=(main_startup.id, investment_round.id, investor.id))
    response = client.delete(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_add_investor_inparticular_round(main_user_token,main_startup):
    client = APIClient()
    token = main_user_token.get("token")
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    investment_round = InvestmentRound.objects.create(startup=main_startup, round_type='Seed', amount=100000, raised_amount=50000)
    url = reverse('investor-add', args=(main_startup.id, investment_round.id))
    data = {
        'firstName': 'John',
        'lastName': 'Doe',
        'firmName': 'ABC Ventures',
        'email': 'john.doe@gmail.com',
        'amountInvested': 50000,
        'investedType': 'Equity'
    }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_201_CREATED
    assert InvestorUser.objects.filter(round=investment_round).count() == 1


@pytest.mark.django_db
def test_add_investor_as_cofounder_inparticular_round(main_user_token,third_startup):
    client = APIClient()
    token = main_user_token.get("token")
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    investment_round = InvestmentRound.objects.create(startup=third_startup, round_type='Seed', amount=100000, raised_amount=50000)
    url = reverse('investor-add', args=(third_startup.id, investment_round.id))
    data = {
        'firstName': 'John',
        'lastName': 'Doe',
        'firmName': 'ABC Ventures',
        'email': 'john.doe@gmail.com',
        'amountInvested': 50000,
        'investedType': 'Equity'
    }
    response = client.post(url, data, format='json')
    assert response.status_code == 201
    assert InvestorUser.objects.filter(round=investment_round).count() == 1

@pytest.mark.django_db
def test_add_investor_inparticular_round_wrong_id(main_user_token,main_startup):
    client = APIClient()
    token = main_user_token.get("token")
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    url = reverse('investor-add', args=(main_startup.id, 999))
    data = {
        'firstName': 'John',
        'lastName': 'Doe',
        'firmName': 'ABC Ventures',
        'email': 'john.doe@gmail.com',
        'amountInvested': 50000,
        'investedType': 'Equity'
    }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db  
def test_add_investor_inparticular_round_not_authorized(main_startup):
    client = APIClient()
    investment_round = InvestmentRound.objects.create(startup=main_startup, round_type='Seed', amount=100000, raised_amount=50000)
    url = reverse('investor-add', args=(main_startup.id, investment_round.id))
    data = {
        'firstName': 'John',
        'lastName': 'Doe',
        'firmName': 'ABC Ventures',
        'email':  'john.doe@gmail.com',
        'amountInvested': 50000,
        'investedType': 'Equity'
    }
    response = client.post(url, data, format='json')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_edit_investment_round(main_user_token,main_startup):
    client = APIClient()
    token = main_user_token.get("token")
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    investment_round = InvestmentRound.objects.create(startup=main_startup, round_type='Seed', amount=100000, raised_amount=50000)
    url = reverse('investment-edit', args=(main_startup.id, investment_round.id))
    data = {
        'roundType': 'Series A',
        'amount': 200000,
        'raisedAmount': 100000,
        'date': '2024-04-26T12:00:00Z'
    }
    response = client.put(url, data, format='json')
    assert response.status_code == 200
    investment_round.refresh_from_db()
    assert investment_round.round_type == 'Series A'
    assert investment_round.amount == 200000
    assert investment_round.raised_amount == 100000
    assert investment_round.date.strftime('%Y-%m-%dT%H:%M:%SZ') == '2024-04-26T12:00:00Z'

@pytest.mark.django_db
def test_edit_investment_round_as_cofounder(main_user_token,third_startup):
    client = APIClient()
    token = main_user_token.get("token")
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    investment_round = InvestmentRound.objects.create(startup=third_startup, round_type='Seed', amount=100000, raised_amount=50000)
    url = reverse('investment-edit', args=(third_startup.id, investment_round.id))
    data = {
        'roundType': 'Series A',
        'amount': 200000,
        'raisedAmount': 100000,
        'date': '2024-04-26T12:00:00Z'
    }
    response = client.put(url, data, format='json')
    assert response.status_code == status.HTTP_200_OK
    investment_round.refresh_from_db()
    assert investment_round.round_type == 'Series A'
    assert investment_round.amount == 200000
    assert investment_round.raised_amount == 100000
    assert investment_round.date.strftime('%Y-%m-%dT%H:%M:%SZ') == '2024-04-26T12:00:00Z'

@pytest.mark.django_db
def test_edit_investment_round_wrong_id(main_user_token,main_startup):
    client = APIClient()
    token = main_user_token.get("token")
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    url = reverse('investment-edit', args=(main_startup.id, 999))
    data = {
        'roundType': 'Series A',
        'amount': 200000,
        'raisedAmount': 100000,
        'date': '2024-04-26T12:00:00Z'
    }
    response = client.put(url, data, format='json')
    assert response.status_code == status.HTTP_404_NOT_FOUND       

@pytest.mark.django_db
def test_edit_investment_round_not_authorized(main_startup):
    client = APIClient()
    investment_round = InvestmentRound.objects.create(startup=main_startup, round_type='Seed', amount=100000, raised_amount=50000)
    url = reverse('investment-edit', args=(main_startup.id, investment_round.id))
    data = {
        'roundType': 'Series A',
        'amount': 200000,
        'raisedAmount': 100000,
        'date': '2024-04-26T12:00:00Z'
    }
    response = client.put(url, data, format='json')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
@pytest.mark.django_db
def test_inversor_temporal(main_user_token, main_startup):
    client = APIClient()
    token = main_user_token.get("token")
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    url = reverse('temporal-investors',kwargs={"startupId": main_startup.id})
    response = client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert 'count' in response.data
    assert 'total_pages' in response.data
    assert 'next' in response.data
    assert 'previous' in response.data
    assert 'results' in response.data

@pytest.mark.django_db
def test_get_favorite_investors(main_user_token, main_startup):
    client = APIClient()
    token = main_user_token.get("token")
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
   # Create investors
    investor_1 = create_investor(TEMPORAL_INVESTORS[0])
    investor_2 = create_investor(TEMPORAL_INVESTORS[1])

    # Associate investors with the startup
    FavoriteInvestorsTemporal.objects.bulk_create([
        FavoriteInvestorsTemporal(startup=main_startup, investor=investor_1),
        FavoriteInvestorsTemporal(startup=main_startup, investor=investor_2)
    ])
    
    category = StartupCategory.objects.create(
        name = INDUSTRIES_CATEGORIES[4].get("name"),
        code = INDUSTRIES_CATEGORIES[4].get("code")
    )
    
    investor_1.industry_categories.add(category)
    
    url = reverse('favorites-investors', kwargs={"startupId": main_startup.id})
    response = client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 2
    
@pytest.mark.django_db
def test_get_favorite_investors_wrong_id(main_user_token, main_startup):
    client = APIClient()
    token = main_user_token.get("token")
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
   # Create investors
    investor_1 = create_investor(TEMPORAL_INVESTORS[0])
    investor_2 = create_investor(TEMPORAL_INVESTORS[1])

    # Associate investors with the startup
    FavoriteInvestorsTemporal.objects.bulk_create([
        FavoriteInvestorsTemporal(startup=main_startup, investor=investor_1),
        FavoriteInvestorsTemporal(startup=main_startup, investor=investor_2)
    ])
    
    url = reverse('favorites-investors', kwargs={"startupId":FAKE_UUID})
    response = client.get(url)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    
@pytest.mark.django_db
def test_get_favorite_investors_not_authorized(main_startup):
    client = APIClient()
    
   # Create investors
    investor_1 = create_investor(TEMPORAL_INVESTORS[0])
    investor_2 = create_investor(TEMPORAL_INVESTORS[1])

    # Associate investors with the startup
    FavoriteInvestorsTemporal.objects.bulk_create([
        FavoriteInvestorsTemporal(startup=main_startup, investor=investor_1),
        FavoriteInvestorsTemporal(startup=main_startup, investor=investor_2)
    ])
    
    url = reverse('favorites-investors', kwargs={"startupId": main_startup.id})
    response = client.get(url)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    

@pytest.mark.django_db
def test_create_favorite_investors(main_user_token, main_startup):
    client = APIClient()
    token = main_user_token.get("token")
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
   # Create investors
    investor_1 = create_investor(TEMPORAL_INVESTORS[0])
    
    url = reverse('favorites-investors-edit', kwargs={"startupId": main_startup.id,"investorId":investor_1.id})
    response = client.post(url)
    
    assert response.status_code == status.HTTP_201_CREATED
    
    favorite_url = reverse('favorites-investors', kwargs={"startupId": main_startup.id})
    favorite_response = client.get(favorite_url)
    assert favorite_response.status_code == status.HTTP_200_OK
    assert len(favorite_response.json()) == 1
    
@pytest.mark.django_db
def test_create_favorite_investors_wrong_startup_id(main_user_token):
    client = APIClient()
    token = main_user_token.get("token")
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
   # Create investors
    investor_1 = create_investor(TEMPORAL_INVESTORS[0])
    
    url = reverse('favorites-investors-edit', kwargs={"startupId": FAKE_UUID,"investorId":investor_1.id})
    response = client.post(url)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    
@pytest.mark.django_db
def test_create_favorite_investors_wrong_investor_id(main_user_token, main_startup):
    client = APIClient()
    token = main_user_token.get("token")
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
   # Create investors
    create_investor(TEMPORAL_INVESTORS[0])
    
    url = reverse('favorites-investors-edit', kwargs={"startupId": main_startup.id,"investorId":9999})
    response = client.post(url)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
def test_create_favorite_investors_not_authorized(main_startup):
    client = APIClient()
    
   # Create investors
    investor_1 = create_investor(TEMPORAL_INVESTORS[0])
    
    url = reverse('favorites-investors-edit', kwargs={"startupId": main_startup.id,"investorId":investor_1.id})
    response = client.post(url)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
@pytest.mark.django_db
def test_delete_favorite_investors(main_user_token, main_startup):
    client = APIClient()
    token = main_user_token.get("token")
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
   # Create investors
    investor_1 = create_investor(TEMPORAL_INVESTORS[0])
    investor_2 = create_investor(TEMPORAL_INVESTORS[1])

    # Associate investors with the startup
    FavoriteInvestorsTemporal.objects.create(startup=main_startup, investor=investor_1)
    FavoriteInvestorsTemporal.objects.create(startup=main_startup, investor=investor_2)
    
    url = reverse('favorites-investors-edit', kwargs={"startupId": main_startup.id,"investorId":investor_1.id})
    response = client.delete(url)
    
    assert response.status_code == status.HTTP_200_OK
    favorite_url = reverse('favorites-investors', kwargs={"startupId": main_startup.id})
    favorite_response = client.get(favorite_url)
    assert favorite_response.status_code == status.HTTP_200_OK
    assert len(favorite_response.json()) == 1
    

@pytest.mark.django_db
def test_delete_favorite_investors_wrong_startup_id(main_user_token, main_startup):
    client = APIClient()
    token = main_user_token.get("token")
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
   # Create investors
    investor_1 = create_investor(TEMPORAL_INVESTORS[0])
    investor_2 = create_investor(TEMPORAL_INVESTORS[1])

    # Associate investors with the startup
    FavoriteInvestorsTemporal.objects.create(startup=main_startup, investor=investor_1)
    FavoriteInvestorsTemporal.objects.create(startup=main_startup, investor=investor_2)
    
    url = reverse('favorites-investors-edit', kwargs={"startupId": FAKE_UUID,"investorId":investor_1.id})
    response = client.delete(url)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    
@pytest.mark.django_db
def test_delete_favorite_investors_wrong_investor_id(main_user_token, main_startup):
    client = APIClient()
    token = main_user_token.get("token")
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
   # Create investors
    investor_1 = create_investor(TEMPORAL_INVESTORS[0])
    investor_2 = create_investor(TEMPORAL_INVESTORS[1])

    # Associate investors with the startup
    FavoriteInvestorsTemporal.objects.create(startup=main_startup, investor=investor_1)
    FavoriteInvestorsTemporal.objects.create(startup=main_startup, investor=investor_2)
    
    url = reverse('favorites-investors-edit', kwargs={"startupId": main_startup.id,"investorId":9999})
    response = client.delete(url)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    
@pytest.mark.django_db
def test_delete_favorite_investors_not_authorized(main_startup):
    client = APIClient()
    
   # Create investors
    investor_1 = create_investor(TEMPORAL_INVESTORS[0])
    investor_2 = create_investor(TEMPORAL_INVESTORS[1])

    # Associate investors with the startup
    FavoriteInvestorsTemporal.objects.create(startup=main_startup, investor=investor_1)
    FavoriteInvestorsTemporal.objects.create(startup=main_startup, investor=investor_2)
    
    url = reverse('favorites-investors-edit', kwargs={"startupId": main_startup.id,"investorId":investor_1.id})
    response = client.delete(url)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_get_favorite_investor_get_email(main_user_token, main_startup):
    client = APIClient()
    token = main_user_token.get("token")
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
   # Create investors
    investor_1 = create_investor(TEMPORAL_INVESTORS[0])
    investor_2 = create_investor(TEMPORAL_INVESTORS[1])

    # Associate investors with the startup
    FavoriteInvestorsTemporal.objects.bulk_create([
        FavoriteInvestorsTemporal(startup=main_startup, investor=investor_1),
        FavoriteInvestorsTemporal(startup=main_startup, investor=investor_2)
    ])
    url_result_1 = f"mailto:{investor_1.email}"
    url_result_2 = f"mailto:{investor_2.email}"
    
    url_1 = reverse('investors-get-email', kwargs={"startupId": main_startup.id,"investorId":investor_1.id})
    response_1 = client.get(url_1)
    
    assert response_1.status_code == status.HTTP_200_OK
    assert response_1.json().get("url") == url_result_1
    
    url_2 = reverse('investors-get-email', kwargs={"startupId": main_startup.id,"investorId":investor_2.id})
    response_2 = client.get(url_2)
    
    assert response_2.status_code == status.HTTP_200_OK
    assert response_2.json().get("url") == url_result_2

@pytest.mark.django_db
def test_get_favorite_investor_get_email_wrong_startup_id(main_user_token, main_startup):
    client = APIClient()
    token = main_user_token.get("token")
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
   # Create investors
    investor = create_investor(TEMPORAL_INVESTORS[0])

    # Associate investors with the startup
    FavoriteInvestorsTemporal.objects.create(
        startup=main_startup, 
        investor=investor
    )
    
    url = reverse('investors-get-email', kwargs={"startupId": FAKE_UUID,"investorId":investor.id})
    response = client.get(url)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
def test_get_favorite_investor_get_email_wrong_investor_id(main_user_token, main_startup):
    client = APIClient()
    token = main_user_token.get("token")
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
   # Create investors
    investor = create_investor(TEMPORAL_INVESTORS[0])

    # Associate investors with the startup
    FavoriteInvestorsTemporal.objects.create(
        startup=main_startup, 
        investor=investor
    )
    
    url = reverse('investors-get-email', kwargs={"startupId": main_startup.id,"investorId":9999})
    response = client.get(url)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    


@pytest.mark.django_db
def test_get_favorite_investor_get_email_not_authorized(main_startup):
    client = APIClient()

   # Create investors
    investor = create_investor(TEMPORAL_INVESTORS[0])

    # Associate investors with the startup
    FavoriteInvestorsTemporal.objects.create(
        startup=main_startup, 
        investor=investor
    )
    
    url = reverse('investors-get-email', kwargs={"startupId": main_startup.id,"investorId":investor.id})
    response = client.get(url)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_investment_banks_view_success(main_user_token, main_startup):
    client = APIClient()
    token = main_user_token.get("token")
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    url = reverse('investments-banks', kwargs={"startupId": main_startup.id})

    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data == {"ECLLabsMatch": False, "stennMatch": False}

@pytest.mark.django_db
def test_investment_banks_view_no_access(main_user_token):
    client = APIClient()
    token = main_user_token.get("token")
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    
    url = reverse('investments-banks', kwargs={"startupId": FAKE_UUID})

    response = client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data == {"error": "Startup does not exist"}
    
@pytest.mark.django_db
def test_investment_banks_view_not_authorized(main_startup):
    client = APIClient()
    
    url = reverse('investments-banks', kwargs={"startupId": main_startup.id})

    response = client.get(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED