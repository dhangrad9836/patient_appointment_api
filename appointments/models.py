from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone

class Patient(models.Model):
    """
    Patient model with HIPAA-safe anonymized identifiers.
    Based on real radiology patient management workflows.
    """
    
    # Anonymized patient identifier
    patient_id = models.CharField(
        max_length=20,
        unique=True,
        help_text="Anonymized patient identifier (e.g., PT001)"
    )
    
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    
    # Phone validator (US format)
    phone_regex = RegexValidator(
        regex=r'^\d{3}-\d{3}-\d{4}$',
        message="Phone number must be in format: 555-555-5555"
    )
    phone = models.CharField(validators=[phone_regex], max_length=12)
    
    email = models.EmailField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = "Patient"
        verbose_name_plural = "Patients"
    
    def __str__(self):
        return f"{self.patient_id} - {self.last_name}, {self.first_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        """Calculate patient age from date of birth"""
        today = timezone.now().date()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )


class Appointment(models.Model):
    """
    Appointment model for imaging procedures.
    Includes validation to prevent common scheduling errors.
    """
    
    EXAM_TYPE_CHOICES = [
        ('MRI_BRAIN', 'MRI Brain'),
        ('MRI_SPINE', 'MRI Spine'),
        ('MRI_KNEE', 'MRI Knee'),
        ('MRI_SHOULDER', 'MRI Shoulder'),
        ('MRI_ABDOMEN', 'MRI Abdomen'),
        ('CT_HEAD', 'CT Head'),
        ('CT_CHEST', 'CT Chest'),
        ('CT_ABDOMEN', 'CT Abdomen'),
        ('XRAY_CHEST', 'X-Ray Chest'),
        ('XRAY_SPINE', 'X-Ray Spine'),
        ('ULTRASOUND', 'Ultrasound'),
    ]
    
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('CONFIRMED', 'Confirmed'),
        ('CHECKED_IN', 'Checked In'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('NO_SHOW', 'No Show'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    # Foreign key to Patient
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    
    # Appointment details
    appointment_date = models.DateTimeField()
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPE_CHOICES)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='SCHEDULED'
    )
    
    # Clinical details
    referring_physician = models.CharField(max_length=100)
    clinical_indication = models.TextField(
        help_text="Reason for exam (e.g., 'r/o rotator cuff tear')",
        blank=True
    )
    special_instructions = models.TextField(
        help_text="Special prep or patient needs",
        blank=True
    )
    
    # Scheduling metadata
    duration_minutes = models.IntegerField(
        default=30,
        help_text="Expected appointment duration"
    )
    room_number = models.CharField(max_length=10, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['appointment_date']
        verbose_name = "Appointment"
        verbose_name_plural = "Appointments"
    
    def __str__(self):
        return f"{self.patient.patient_id} - {self.get_exam_type_display()} on {self.appointment_date.date()}"
    
    def clean(self):
        """Validation to prevent scheduling errors"""
        from django.core.exceptions import ValidationError
        
        # Don't allow appointments in the past
        if self.appointment_date and self.appointment_date < timezone.now():
            raise ValidationError("Cannot schedule appointments in the past")
        
        # Check for double-booking (same patient, overlapping time)
        if self.patient_id:
            overlapping = Appointment.objects.filter(
                patient=self.patient,
                appointment_date__date=self.appointment_date.date(),
                status__in=['SCHEDULED', 'CONFIRMED', 'CHECKED_IN']
            ).exclude(pk=self.pk)
            
            if overlapping.exists():
                raise ValidationError(
                    f"Patient {self.patient.patient_id} already has an appointment on this date"
                )
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_past(self):
        """Check if appointment is in the past"""
        return self.appointment_date < timezone.now()
    
    @property
    def is_today(self):
        """Check if appointment is today"""
        return self.appointment_date.date() == timezone.now().date()