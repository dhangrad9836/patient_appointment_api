from django.core.management.base import BaseCommand
from appointments.models import Patient, Appointment
from faker import Faker
import random
from datetime import datetime, timedelta
from django.utils import timezone

fake = Faker()

class Command(BaseCommand):
    help = 'Generate sample patients and appointments'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--patients',
            type=int,
            default=50,
            help='Number of patients to generate'
        )
        parser.add_argument(
            '--appointments',
            type=int,
            default=100,
            help='Number of appointments to generate'
        )
    
    def handle(self, *args, **options):
        patient_count = options['patients']
        appointment_count = options['appointments']
        
        # Clear existing data
        self.stdout.write('Clearing existing data...')
        Appointment.objects.all().delete()
        Patient.objects.all().delete()
        
        # Generate patients
        self.stdout.write(f'Generating {patient_count} patients...')
        patients = []
        for i in range(patient_count):
            patient = Patient.objects.create(
                patient_id=f'PT{1000 + i}',
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=90),
                phone=f'{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}',
                email=fake.email() if random.random() > 0.3 else None
            )
            patients.append(patient)
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(patients)} patients'))
        
        # Generate appointments
        self.stdout.write(f'Generating {appointment_count} appointments...')
        
        exam_types = [choice[0] for choice in Appointment.EXAM_TYPE_CHOICES]
        status_choices = [choice[0] for choice in Appointment.STATUS_CHOICES]
        physicians = [
            'Dr. Smith',
            'Dr. Johnson',
            'Dr. Williams',
            'Dr. Brown',
            'Dr. Davis',
            'Dr. Miller',
        ]
        
        clinical_indications = [
            'r/o fracture',
            'chronic pain',
            'follow-up',
            'post-operative evaluation',
            'r/o herniated disc',
            'r/o rotator cuff tear',
            'screening',
            'trauma evaluation',
        ]
        
        # Create appointments spanning from 30 days ago to 60 days ahead
        start_date = timezone.now() - timedelta(days=30)
        end_date = timezone.now() + timedelta(days=60)
        
        appointments = []
        for i in range(appointment_count):
            # Random date within range
            days_offset = random.randint(0, 90) - 30
            appointment_date = start_date + timedelta(days=days_offset)
            
            # Business hours: 7 AM - 6 PM
            hour = random.randint(7, 18)
            minute = random.choice([0, 15, 30, 45])
            appointment_date = appointment_date.replace(
                hour=hour,
                minute=minute,
                second=0,
                microsecond=0
            )
            
            # Determine status based on date
            if appointment_date < timezone.now():
                # Past appointments: mostly completed, some no-shows
                status_weights = {
                    'COMPLETED': 0.85,
                    'NO_SHOW': 0.10,
                    'CANCELLED': 0.05
                }
            else:
                # Future appointments: mostly scheduled/confirmed
                status_weights = {
                    'SCHEDULED': 0.60,
                    'CONFIRMED': 0.35,
                    'CANCELLED': 0.05
                }
            
            status = random.choices(
                list(status_weights.keys()),
                weights=list(status_weights.values())
            )[0]
            
            exam_type = random.choice(exam_types)
            
            # Duration varies by exam type
            if 'MRI' in exam_type:
                duration = random.choice([30, 45, 60])
            elif 'CT' in exam_type:
                duration = random.choice([15, 20, 30])
            else:
                duration = random.choice([10, 15, 20])
            
            appointment = Appointment(
                patient=random.choice(patients),
                appointment_date=appointment_date,
                exam_type=exam_type,
                status=status,
                referring_physician=random.choice(physicians),
                clinical_indication=random.choice(clinical_indications),
                duration_minutes=duration,
                room_number=f'RM-{random.randint(1, 5)}' if random.random() > 0.5 else ''
            )
            appointments.append(appointment)
        
        # Bulk create (skip validation for sample data)
        Appointment.objects.bulk_create(appointments)
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(appointments)} appointments'))
        
        # Print statistics
        self.stdout.write('\n--- Statistics ---')
        self.stdout.write(f'Total patients: {Patient.objects.count()}')
        self.stdout.write(f'Total appointments: {Appointment.objects.count()}')
        
        # Status breakdown
        for status_choice in Appointment.STATUS_CHOICES:
            count = Appointment.objects.filter(status=status_choice[0]).count()
            self.stdout.write(f'{status_choice[1]}: {count}')
        
        # Today's appointments
        today_count = Appointment.objects.filter(
            appointment_date__date=timezone.now().date()
        ).count()
        self.stdout.write(f'Appointments today: {today_count}')
        
        # Upcoming appointments
        upcoming_count = Appointment.objects.filter(
            appointment_date__gte=timezone.now(),
            status__in=['SCHEDULED', 'CONFIRMED']
        ).count()
        self.stdout.write(f'Upcoming appointments: {upcoming_count}')
        
        self.stdout.write(self.style.SUCCESS('\nSample data generation complete!'))