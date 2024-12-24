import pytest
from startups.models import (
    StartupCategory,
    StartupSubcategory,
    StartupTechSector,
    Startup, 
    StartupVideo, 
    StartupImage, 
    StartupSlidedeck, 
    StartupBusinessTraction, 
    StartupTopCustomer,
    Founder)
from users.tests.fixtures import common_user_token, common_user_founder

main_user_token = common_user_token
user_founder = common_user_founder

FAKE_CATEGORY_DATA = {"name": "Software & Internet", "code": "software&internet"}
FAKE_SUBCATEGORY_DATA =  {"name": "Computer Games", "code": "software&internet_1"}

FAKE_SECOND_CATEGORY_DATA = {"name": "Finance & Crypto", "code": "finance&crypto"}
FAKE_SECOND_SUBCATEGORY_DATA =  {"name": "Accounting", "code": "finance&crypto_1"}

FAKE_THIRD_CATEGORY_DATA = {"name": "Energy", "code": "energy"}
FAKE_THIRD_SUBCATEGORY_DATA =  {"name": "Oil & Energy", "code": "energy_1"}

FAKE_TECH_SECTOR = {"name":"AI/ML"}

FAKE_STARTUP_DATA = {
    "name": "Tech Innovations Inc.",
    "description": "A cutting-edge technology startup specializing in artificial intelligence solutions.",
    "location": "Bessemer, Alabama, United States",
    "industry": "Information Technology",
    "website_url": "https://www.techinnovations.com",
    "stage": Startup.SEED,
    "employee_count": Startup.ONE_TO_TEN,
    "video_url": "https://www.youtube.com/watch?v=1w7OgIMMRc4&ab_channel=GunsNRosesVEVO",
    "image_url": "https://i.ytimg.com/vi/1w7OgIMMRc4/maxresdefault.jpg",
    "slidedeck_url": "https://example.com/slidedeck",
    "business_model": StartupBusinessTraction.PRODUCT_SALES,
    "business_revenue_sources": StartupBusinessTraction.B2B,
    "mrr": 10000,
    "top_customer_name": "Uber",
    "top_customer_image": "https://d3i4yxtzktqr9n.cloudfront.net/uber-sites/f452c7aefd72a6f52b36705c8015464e.jpg",
    "top_customer_url": "https://d3i4yxtzktqr9n.cloudfront.net/uber-sites/f452c7aefd72a6f52b36705c8015464e.jpg"
} 

@pytest.fixture
def common_startup(main_user_token):
    category = StartupCategory.objects.create(
        name = FAKE_CATEGORY_DATA['name'],
        code = FAKE_CATEGORY_DATA['code']
        )
    subcategory = StartupSubcategory.objects.create(
        name = FAKE_SUBCATEGORY_DATA['name'],
        code = FAKE_SUBCATEGORY_DATA['name'],
        category = category 
    )
    tech_sector = StartupTechSector.objects.create(
        name = FAKE_TECH_SECTOR['name']
    )
    main_user = main_user_token['user']
    founder_user = main_user_token['secondary_user']
    startup = Startup.create_startup_for_test(
        name=FAKE_STARTUP_DATA["name"],
        main_founder=main_user,
        description=FAKE_STARTUP_DATA["description"],
        location=FAKE_STARTUP_DATA["location"],
        industry_category=subcategory,
        tech_sector=tech_sector,
        website_url=FAKE_STARTUP_DATA["website_url"],
        stage=FAKE_STARTUP_DATA["stage"],
        employee_count=FAKE_STARTUP_DATA["employee_count"],
        is_active=True
    )

    StartupVideo.objects.create(startup=startup, url=FAKE_STARTUP_DATA["video_url"], is_active=True)
    StartupImage.objects.create(startup=startup, url=FAKE_STARTUP_DATA["image_url"], is_active=True)
    StartupSlidedeck.objects.create(startup=startup, url=FAKE_STARTUP_DATA["slidedeck_url"])

    business_traction = StartupBusinessTraction.objects.create(
        startup=startup,
        business_model=FAKE_STARTUP_DATA["business_model"],
        business_revenue_sources=FAKE_STARTUP_DATA["business_revenue_sources"],
        mrr=FAKE_STARTUP_DATA["mrr"]
    )

    StartupTopCustomer.objects.create(
        startup=startup,
        business_traction =business_traction,
        name=FAKE_STARTUP_DATA["top_customer_name"],
        image=FAKE_STARTUP_DATA["top_customer_image"],
        url=FAKE_STARTUP_DATA["top_customer_url"]
    )
    
    Founder.objects.create(
        user=founder_user,
        startup=startup,
        is_confirmed=True
    )
    
    return startup

@pytest.fixture
def common_secondary_startup(main_user_token):
    category = StartupCategory.objects.create(
        name = FAKE_SECOND_CATEGORY_DATA['name'],
        code = FAKE_SECOND_CATEGORY_DATA['code']
        )
    subcategory = StartupSubcategory.objects.create(
        name = FAKE_SECOND_SUBCATEGORY_DATA['name'],
        code = FAKE_SECOND_SUBCATEGORY_DATA['name'],
        category = category 
    )
    tech_sector = StartupTechSector.objects.create(
        name = FAKE_TECH_SECTOR['name']
    )
    main_user = main_user_token['secondary_user']
    startup = Startup.create_startup_for_test(
        name=FAKE_STARTUP_DATA["name"],
        main_founder=main_user,
        description=FAKE_STARTUP_DATA["description"],
        location=FAKE_STARTUP_DATA["location"],
        industry_category=subcategory,
        tech_sector=tech_sector,
        website_url=FAKE_STARTUP_DATA["website_url"],
        stage=FAKE_STARTUP_DATA["stage"],
        employee_count=FAKE_STARTUP_DATA["employee_count"],
        is_active=True
    )

    StartupVideo.objects.create(startup=startup, url=FAKE_STARTUP_DATA["video_url"], is_active=True)
    StartupImage.objects.create(startup=startup, url=FAKE_STARTUP_DATA["image_url"], is_active=True)
    StartupSlidedeck.objects.create(startup=startup, url=FAKE_STARTUP_DATA["slidedeck_url"])
    
    return startup

@pytest.fixture
def common_third_startup(main_user_token):
    category = StartupCategory.objects.create(
        name = FAKE_THIRD_CATEGORY_DATA['name'],
        code = FAKE_THIRD_CATEGORY_DATA['code']
        )
    subcategory = StartupSubcategory.objects.create(
        name = FAKE_THIRD_SUBCATEGORY_DATA['name'],
        code = FAKE_THIRD_SUBCATEGORY_DATA['name'],
        category = category 
    )
    tech_sector = StartupTechSector.objects.create(
        name = FAKE_TECH_SECTOR['name']
    )
    main_user = main_user_token['user']
    founder_user = main_user_token['secondary_user']
    startup = Startup.create_startup_for_test(
        name=FAKE_STARTUP_DATA["name"],
        main_founder=founder_user,
        description=FAKE_STARTUP_DATA["description"],
        location=FAKE_STARTUP_DATA["location"],
        industry_category=subcategory,
        tech_sector=tech_sector,
        website_url=FAKE_STARTUP_DATA["website_url"],
        stage=FAKE_STARTUP_DATA["stage"],
        employee_count=FAKE_STARTUP_DATA["employee_count"],
        is_active=True
    )

    StartupVideo.objects.create(startup=startup, url=FAKE_STARTUP_DATA["video_url"], is_active=True)
    StartupImage.objects.create(startup=startup, url=FAKE_STARTUP_DATA["image_url"], is_active=True)
    StartupSlidedeck.objects.create(startup=startup, url=FAKE_STARTUP_DATA["slidedeck_url"])
    
    StartupBusinessTraction.objects.create(
        startup=startup,
        business_model=FAKE_STARTUP_DATA["business_model"],
        business_revenue_sources=FAKE_STARTUP_DATA["business_revenue_sources"],
        mrr=FAKE_STARTUP_DATA["mrr"]
    )
    
    Founder.objects.create(
        user=main_user,
        startup=startup,
        is_confirmed=True
    )
    
    return startup
