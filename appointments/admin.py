from django.contrib import admin
from .models import Patient, Appointment

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['patient_id', 'first_name', 'last_name', 'date_of_birth', 'phone']
    search_fields = ['patient_id', 'first_name', 'last_name']

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['patient', 'appointment_date', 'exam_type', 'status', 'referring_physician']
    list_filter = ['status', 'exam_type']
    search_fields = ['patient__patient_id', 'referring_physician']
    date_hierarchy = 'appointment_date'