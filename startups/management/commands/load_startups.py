from django.core.management.base import BaseCommand
from startups.models import (
  StartupSubcategory,
  Startup, 
  Founder,
  StartupVideo,
  StartupImage,
  StartupTopCustomer,
  StartupBusinessTraction)
from users.models import CustomUser
from pjbackend.constants import (
  STARTUP_ONE_MAIN_FOUNDER,
  STARTUP_ONE_CO_FOUNDER,
  STARTUP_TWO_MAIN_FOUNDER,
  STARTUP_TWO_CO_FOUNDER,
  STARTUP_THREE_MAIN_FOUNDER,
  STARTUP_THREE_CO_FOUNDER
)

class Command(BaseCommand):
    
    startups = [
    {
      "name": "Tech Innovations Inc.",
      "main_founder":STARTUP_ONE_MAIN_FOUNDER,
      "co_founder":STARTUP_ONE_CO_FOUNDER,
      "description": "A cutting-edge technology startup specializing in artificial intelligence solutions.",
      "industry": "Information Technology",
      "employee_count": Startup.FIFTY_TO_TWOHUNDREDFIFTY,
      "location":"Bessemer, Alabama, United States",
      "website_url": "https://www.techinnovations.com",
      "image_url": "https://i.ytimg.com/vi/1w7OgIMMRc4/maxresdefault.jpg",
      "video_url": "https://www.youtube.com/watch?v=1w7OgIMMRc4&ab_channel=GunsNRosesVEVO",
      "business_traction": {
        "business_model": StartupBusinessTraction.PLATFORM,
        "business_revenue_sources": StartupBusinessTraction.B2B,
        "mrr": 10000
        },
      "top_customer":{
        "name":"Uber",
        "url":"https://d3i4yxtzktqr9n.cloudfront.net/uber-sites/f452c7aefd72a6f52b36705c8015464e.jpg"
      }
    },
    {
      "name": "EcoGreen Solutions",
      "main_founder":STARTUP_TWO_MAIN_FOUNDER,
      "co_founder":STARTUP_TWO_CO_FOUNDER,
      "description": "An environmentally friendly startup focused on renewable energy and sustainability.",
      "industry": "Clean Energy",
      "employee_count": Startup.TEN_TO_FIFTY,
      "location":"Bessemer, Alabama, United States",
      "website_url": "https://www.ecogreensolutions.com",
      "image_url": "https://i.ytimg.com/vi/3s3bQM7hmMc/hqdefault.jpg",
      "video_url": "https://www.youtube.com/watch?v=l482T0yNkeo&ab_channel=acdcVEVO",
      "business_traction": {
        "business_model": StartupBusinessTraction.E_COMMERCE,
        "business_revenue_sources": StartupBusinessTraction.B2C,
        "mrr": 5000
        },
      "top_customer":{
        "name":"amazon",
        "url":"https://1000logos.net/wp-content/uploads/2016/10/Amazon-Logo.png"
      }
    },
    {
      "name": "HealthTech Solutions",
      "main_founder":STARTUP_THREE_MAIN_FOUNDER,
      "co_founder":STARTUP_THREE_CO_FOUNDER,
      "description": "A healthcare technology startup revolutionizing patient care with digital health tools.",
      "industry": "Healthcare",
      "employee_count": Startup.ONE_TO_TEN,
      "location":"Bessemer, Alabama, United States",
      "website_url": "https://www.healthtechsolutions.com",
      "image_url": "https://i.ytimg.com/vi/O4irXQhgMqg/maxresdefault.jpg",
      "video_url": "https://www.youtube.com/watch?v=O4irXQhgMqg&ab_channel=ABKCOVEVO",
      "business_traction": {
        "business_model": StartupBusinessTraction.SAAS,
        "business_revenue_sources": StartupBusinessTraction.B2B2C,
        "mrr": 15000
        },
      "top_customer":{
        "name":"AT&T",
        "url":"https://upload.wikimedia.org/wikipedia/commons/thumb/3/31/AT%26T_logo_2016.svg/320px-AT%26T_logo_2016.svg.png"
      }
    }
  ]
        
    help = 'Create some startups for testing environment'
    
    def handle(self, *args, **options):
      for startup_data in self.startups:
          startup_name = startup_data['name']
          if not Startup.objects.filter(name=startup_name).exists():
              startup = self.create_startup(startup_data)
              self.stdout.write(self.style.SUCCESS(f'Startup "{startup.name}" created successfully'))
          else:
              self.stdout.write(self.style.WARNING(f'Startup "{startup_name}" already exists'))

    def create_startup(self, startup_data):
        main_founder = CustomUser.objects.get(email=startup_data['main_founder'])
        if main_founder:
            industry_category = StartupSubcategory.objects.all().first()
            startup = Startup.create_startup_for_test(
                name=startup_data['name'],
                description=startup_data['description'],
                location=startup_data['location'],
                industry_category=industry_category,
                tech_sector = industry_category,
                employee_count=startup_data['employee_count'],
                website_url=startup_data['website_url'],
                main_founder=main_founder
            )

            # Get a second user to create another founder for the startup
            video_url = startup_data['video_url']
            if video_url:
              self.create_startup_video(startup, video_url)
              
            image_url = startup_data['image_url']
            if image_url:
              self.create_startup_image(startup, image_url)
              
            business_traction_data = startup_data['business_traction']
            top_customer_data = startup_data['top_customer']
            
            if business_traction_data and top_customer_data:
              self.create_business_traction_and_top_customer(startup, business_traction_data, top_customer_data)
            
            
            co_founder = CustomUser.objects.get(email=startup_data['co_founder'])
            if co_founder:
                self.create_founder(startup,co_founder)
                return startup
            else:
                self.stdout.write(self.style.ERROR('There are no additional users available to assign as a founder.'))
                return None
        else:
            self.stdout.write(self.style.ERROR('There are no users available to assign as a primary founder.'))
            return None

    def create_founder(self,startup,founder):
      Founder.objects.create(user=founder,email=founder.email,first_name=founder.first_name,last_name=founder.last_name,startup=startup, is_confirmed=True)
    
    def create_startup_video(self, startup, video_url):
      StartupVideo.objects.create(startup=startup, url=video_url)

    def create_startup_image(self, startup, image_url):
      StartupImage.objects.create(startup=startup, url=image_url)
      
    def create_business_traction_and_top_customer(self, startup, business_traction_data, top_customer_data):
      business_traction = StartupBusinessTraction.objects.create(
        startup=startup,
        business_model=business_traction_data['business_model'],
        business_revenue_sources=business_traction_data['business_revenue_sources'],
        mrr=business_traction_data['mrr']
        )
      StartupTopCustomer.objects.create(
        startup=startup,
        business_traction =business_traction,
        name=top_customer_data["name"],
        url=top_customer_data["url"]
      )