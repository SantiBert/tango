import csv
import os

from django.core.management.base import BaseCommand
from investors.models import InversorTemporal
from startups.models import StartupCategory
from django.db.models.functions import Lower

class Command(BaseCommand):
    help = 'Create or update investors from a CSV file'

    def handle(self, *args, **kwargs):
        base_dir = os.path.dirname(__file__)
        csv_file = os.path.join(base_dir, 'data.csv')

        with open(csv_file, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                firm_name = row.get('firm_name', '')[:255] 
                website = row.get('website', '')[:255]
                linkedin_link = row.get('linkedin_link', '')[:255]
                twitter_link = row.get('twitter_link', '')[:255]
                location = row.get('location', None)[:255]

                # Buscar o crear el inversor temporal según su email
                inversor, created = InversorTemporal.objects.get_or_create(
                    email=row.get('email'),
                    defaults={  # Solo se usan estos valores si el inversor no existe
                        'first_name': row.get('first_name', '')[:100],
                        'last_name': row.get('last_name', '')[:100],
                        'firm_name': firm_name,
                        'website': website,
                        'founding_year': row.get('founding_year', '')[:20],
                        'description': row.get('description', ''),
                        'fund_stage': row.get('fund_stage', '')[:100],
                        'fund_type': row.get('fund_type', '')[:100],
                        'linkedin_link': linkedin_link,
                        'twitter_link': twitter_link,
                        'city': row.get('city', '')[:100],
                        'state': row.get('state', '')[:100],
                        'country': row.get('country', '')[:100],
                        'location': location,
                        'industry': row.get('industry', '')[:100],
                        'status': row.get('status', 'pending'),
                        'test': row.get('test', '')[:50],
                        'is_active': True,
                    }
                )

                # Obtener las categorías de startups desde el CSV
                category_name = row.get('industry', '')  # Asumiendo que el campo se llama 'categories'
                
                if category_name:
                    # Separar los nombres de las categorías por comas, eliminar espacios y convertir a minúsculas
                    names = [name.strip().lower() for name in category_name.split(',')]
                    
                    # Buscar las categorías por nombre en la base de datos, también eliminando espacios y convirtiendo a minúsculas
                    categories = StartupCategory.objects.annotate(lower_name=Lower('name')).filter(lower_name__in=names)
                    
                    if categories.exists():
                        # Si el inversor ya existe, comprobar si tiene categorías asignadas
                        if inversor.industry_categories.exists():
                            # Agregar nuevas categorías
                            inversor.industry_categories.add(*categories)
                            self.stdout.write(self.style.SUCCESS(f'Added new categories for {inversor.email}.'))
                        else:
                            # Si no tiene categorías, asignar las categorías por primera vez
                            inversor.industry_categories.set(categories)
                            self.stdout.write(self.style.SUCCESS(f'Assigned categories to {inversor.email}.'))

                if created:
                    self.stdout.write(self.style.SUCCESS(f'Investor {row.get("email")} created successfully.'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'Investor {row.get("email")} updated successfully.'))

        self.stdout.write(self.style.SUCCESS('Import process completed.'))
