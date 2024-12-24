import stripe
import random
import string

from twilio.rest import Client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To

from django.conf import settings
from django.core.files.storage import default_storage
from django.contrib.auth.password_validation import validate_password, ValidationError as PasswordValidationError


def generate_temp_password():
    temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    while True:
        try:
            validate_password(temp_password)
            break
        except PasswordValidationError:
            temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    return temp_password

def get_lifetime_token():
    return settings.SIMPLE_JWT.get("ACCESS_TOKEN_LIFETIME").total_seconds() * 1000

def generate_verification_code(code_length: int) -> str:
    return "".join([str(random.randint(0, 9)) for x in range(code_length)])

def upload_file_to_s3(file):
    file_name = default_storage.get_available_name(file.name)
    
    file_path = default_storage.save(file_name, file)
    
    file_url = default_storage.url(file_path)
    
    return file_url


def send_email(subject, to_email, content=None, template_id=None, template_vars=None):
    sg = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
    from_email = Email(settings.SENDGRID_EMAIL)
    to_email = To(to_email)
    
    mail = Mail(from_email=from_email, to_emails=to_email, subject=subject)
    
    if template_id and template_vars:
        mail.template_id = template_id
        print(template_vars)
        mail.dynamic_template_data = template_vars
    else:
        mail.plain_text_content = content
    
    try:
        response = sg.send(mail)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e)

def send_welcome_email(to_email, name):
    subject="Welcome to PomJuice"
    template_id = "d-0dd4dcc23fcd4f26aab384a4ea754892"
    template_vars = {"firstName": name }
    send_email(subject=subject, to_email=to_email, template_id=template_id, template_vars=template_vars)

def send_cofounder_invite_email(to_email, name, company_name, invite_link):
    subject="You have been invited to join PomJuice"
    template_id = "d-28701fcde221430c84108a697f8414de"
    template_vars = {
        "firstName": name,
        "companyName": company_name,
        "inviteLink": invite_link or "https://pomjuice.com"
    }
    send_email(subject=subject, to_email=to_email, template_id=template_id, template_vars=template_vars)
    
def send_investors_invite_email(
    to_email, 
    company_name, 
    first_name, 
    last_name, 
    firm_name,
    invested_type,
    amount_invested,
    amount,
    industry,
    accept_link,
    decline_link
    ):
    subject="You have been invited to be a investor in join PomJuice"
    template_id = "d-f5b3a12a0e604440bf4ba680214fecc2"
    template_vars = {
        "InvestorFirstName": first_name,
        "companyName": company_name,
        "InvestorFullName": f"{first_name} {last_name}",
        "InvestorEmail":to_email,
        "InvestmentAmount":amount_invested,
        "InvestmentInstrument":invested_type,
        "FirmName":firm_name,
        "FirmWebsite":"#",
        "Industry":industry,
        "BusinessType":invested_type,
        "ApproveLink":accept_link,
        "DeclineLink":decline_link
    }
    send_email(subject=subject, to_email=to_email, template_id=template_id, template_vars=template_vars)

def send_forgot_password_email(to_email, name, temp_password):
    subject="Reset your PomJuice password"
    template_id ="d-ae1fa8275ad047cf8e1c446642d85c2a"
    template_vars = {
        "firstName": name,
        "tempPassword": temp_password
    }
    send_email(subject=subject, to_email=to_email, template_id=template_id, template_vars=template_vars)  
def startup_profile_shared_email(to_email, name, company_name, shared_by, company_profile_url):
    subject="Your PomJuice profile has been shared"
    template_id = "d-30e70876247740fea3d518ff8cb8a6c3"
    template_vars = {
        "firstName": name,
        "companyName": company_name,
        "sharedBy": shared_by,
        "companyLink": company_profile_url
    }
    send_email(subject=subject, to_email=to_email, template_id=template_id, template_vars=template_vars)

# Nedd Investor Investment Email ENdpoint
# Need another email endpoint for the foundersd to get weekly anlaytics

def send_sms(to, body):
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=to
        )
        return message.sid
    except Exception as e:
        print(e)


def cancel_stripe_subscription(stripe_subscription_id):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        # Cancela la suscripción en Stripe
        stripe.Subscription.delete(stripe_subscription_id)
        return True
    except stripe.error.StripeError:
        return False