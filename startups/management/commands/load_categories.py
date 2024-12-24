from django.core.management.base import BaseCommand
from startups.models import StartupCategory, StartupSubcategory, StartupTechSector

from pjbackend.constants import INDUSTRIES_CATEGORIES, INDUSTRIES_SUBCATEGORIES, TECH_SECTOR

class Command(BaseCommand):        
    help = 'Create all categories and subcategories for the industries of startups'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Creating industry categories.'))
        for category_data in INDUSTRIES_CATEGORIES:
            category_code = category_data['code']
            category_name = category_data['name']
            if not StartupCategory.objects.filter(code=category_code).exists():
                StartupCategory.objects.create(
                    name = category_name,
                    code = category_code
                )
                self.stdout.write(self.style.SUCCESS(f'Category "{category_name}" created successfully'))
            else:
                self.stdout.write(self.style.WARNING(f'Category "{category_name}" already exists'))
        self.stdout.write(self.style.SUCCESS('All industry categories have been created.'))
        self.stdout.write(self.style.WARNING('Creating industry sub-categories.'))
        for category_data in INDUSTRIES_CATEGORIES:
            category_code = category_data['code']
            category_name = category_data['name']
            category_object = StartupCategory.objects.get(code=category_code)
            self.stdout.write(self.style.WARNING(f'Creating the subcategories of the {category_name} category'))
            subcategories = INDUSTRIES_SUBCATEGORIES.get(category_code)
            for subcategory_data in subcategories:
                subcategory_code = subcategory_data['code']
                subcategory_name = subcategory_data['name']
                if not StartupSubcategory.objects.filter(code=subcategory_code).exists():
                    StartupSubcategory.objects.create(
                        name = subcategory_name,
                        code = subcategory_code,
                        category = category_object
                    )
                    self.stdout.write(self.style.SUCCESS(f'Subcategory "{subcategory_name}" created successfully'))
                else:
                    self.stdout.write(self.style.WARNING(f'Subcategory "{subcategory_name}" already exists'))
            self.stdout.write(self.style.WARNING(f'All subcategories of the {category_name} category have been created'))
        self.stdout.write(self.style.SUCCESS('All industry subcategories have been created.'))
        
        for tech_sector_data in TECH_SECTOR:
            tech_sector_name = tech_sector_data['name']
            if not StartupTechSector.objects.filter(name=tech_sector_name).exists():
                StartupTechSector.objects.create(
                    name=tech_sector_name
                )
                self.stdout.write(self.style.SUCCESS(f'Tech Sector "{tech_sector_name}" created successfully'))
            else:
                self.stdout.write(self.style.WARNING(f'Tech Sector "{tech_sector_name}" already exists'))
        
        self.stdout.write(self.style.SUCCESS('All industry categories and subcategories have been created.'))