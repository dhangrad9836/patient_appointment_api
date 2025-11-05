from rest_framework import serializers
from .models import Patient, Appointment
from django.utils import timezone


class PatientSerializer(serializers.ModelSerializer):
    """
    Serializer for Patient model.
    Includes computed fields and custom validation.
    """
    full_name = serializers.ReadOnlyField()
    age = serializers.ReadOnlyField()
    appointment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Patient
        fields = [
            'id',
            'patient_id',
            'first_name',
            'last_name',
            'full_name',
            'date_of_birth',
            'age',
            'phone',
            'email',
            'appointment_count',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_appointment_count(self, obj):
        """Return total number of appointments for this patient"""
        return obj.appointments.count()
    
    def validate_patient_id(self, value):
        """Ensure patient_id follows correct format"""
        if not value.startswith('PT'):
            raise serializers.ValidationError(
                "Patient ID must start with 'PT' (e.g., PT001)"
            )
        return value
    
    def validate_date_of_birth(self, value):
        """Ensure date of birth is not in the future"""
        if value > timezone.now().date():
            raise serializers.ValidationError(
                "Date of birth cannot be in the future"
            )
        return value


class AppointmentSerializer(serializers.ModelSerializer):
    """
    Serializer for Appointment model.
    Includes nested patient data and validation logic.
    """
    patient_details = PatientSerializer(source='patient', read_only=True)
    patient_id = serializers.CharField(write_only=True)
    exam_type_display = serializers.CharField(
        source='get_exam_type_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    is_past = serializers.ReadOnlyField()
    is_today = serializers.ReadOnlyField()
    
    class Meta:
        model = Appointment
        fields = [
            'id',
            'patient',
            'patient_id',
            'patient_details',
            'appointment_date',
            'exam_type',
            'exam_type_display',
            'status',
            'status_display',
            'referring_physician',
            'clinical_indication',
            'special_instructions',
            'duration_minutes',
            'room_number',
            'is_past',
            'is_today',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'patient', 'created_at', 'updated_at']
    
    def validate_patient_id(self, value):
        """Ensure patient exists"""
        try:
            patient = Patient.objects.get(patient_id=value)
            return patient.patient_id
        except Patient.DoesNotExist:
            raise serializers.ValidationError(
                f"Patient with ID '{value}' does not exist"
            )
    
    def validate_appointment_date(self, value):
        """Ensure appointment is not in the past"""
        if value < timezone.now():
            raise serializers.ValidationError(
                "Cannot schedule appointments in the past"
            )
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        # Check for double-booking if we have all required fields
        if 'patient_id' in data and 'appointment_date' in data:
            patient = Patient.objects.get(patient_id=data['patient_id'])
            
            # Check for existing appointments on same day
            existing = Appointment.objects.filter(
                patient=patient,
                appointment_date__date=data['appointment_date'].date(),
                status__in=['SCHEDULED', 'CONFIRMED', 'CHECKED_IN']
            )
            
            # Exclude current appointment if updating
            if self.instance:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise serializers.ValidationError(
                    f"Patient {data['patient_id']} already has an appointment on "
                    f"{data['appointment_date'].date()}"
                )
        
        return data
    
    def create(self, validated_data):
        """Custom create to handle patient_id lookup"""
        patient_id = validated_data.pop('patient_id')
        patient = Patient.objects.get(patient_id=patient_id)
        validated_data['patient'] = patient
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Custom update to handle patient_id lookup"""
        if 'patient_id' in validated_data:
            patient_id = validated_data.pop('patient_id')
            patient = Patient.objects.get(patient_id=patient_id)
            validated_data['patient'] = patient
        return super().update(instance, validated_data)


class AppointmentListSerializer(serializers.ModelSerializer):
    """
    serializer for listing appointments.
    Reduces payload size for list views.
    """
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    patient_id = serializers.CharField(source='patient.patient_id', read_only=True)
    exam_type_display = serializers.CharField(source='get_exam_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id',
            'patient_id',
            'patient_name',
            'appointment_date',
            'exam_type_display',
            'status_display',
            'referring_physician'
        ]