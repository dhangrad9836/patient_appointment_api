from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import timedelta

from .models import Patient, Appointment
from .serializers import (
    PatientSerializer,
    AppointmentSerializer,
    AppointmentListSerializer
)


class PatientViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing patients.
    
    Provides standard CRUD operations plus custom actions for:
    - Retrieving patient's appointments
    - Patient search
    """
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['patient_id', 'first_name', 'last_name', 'phone']
    ordering_fields = ['last_name', 'created_at']
    ordering = ['last_name']
    
    @action(detail=True, methods=['get'])
    def appointments(self, request, pk=None):
        """
        Get all appointments for a specific patient.
        
        GET /api/patients/{id}/appointments/
        """
        patient = self.get_object()
        appointments = patient.appointments.all()
        
        # Optional filtering by status
        status_filter = request.query_params.get('status')
        if status_filter:
            appointments = appointments.filter(status=status_filter)
        
        serializer = AppointmentListSerializer(appointments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def upcoming_appointments(self, request, pk=None):
        """
        Get upcoming appointments for a patient.
        
        GET /api/patients/{id}/upcoming_appointments/
        """
        patient = self.get_object()
        upcoming = patient.appointments.filter(
            appointment_date__gte=timezone.now(),
            status__in=['SCHEDULED', 'CONFIRMED']
        ).order_by('appointment_date')
        
        serializer = AppointmentListSerializer(upcoming, many=True)
        return Response(serializer.data)


class AppointmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing appointments.
    
    Provides full CRUD operations with additional features:
    - Filtering by date, status, exam type
    - Today's appointments
    - Upcoming appointments
    - Appointment statistics
    """
    queryset = Appointment.objects.select_related('patient').all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'exam_type', 'patient']
    search_fields = ['patient__patient_id', 'patient__last_name', 'referring_physician']
    ordering_fields = ['appointment_date', 'created_at']
    ordering = ['appointment_date']
    
    def get_serializer_class(self):
        """Use lightweight serializer for list view"""
        if self.action == 'list':
            return AppointmentListSerializer
        return AppointmentSerializer
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """
        Get all appointments scheduled for today.
        
        GET /api/appointments/today/
        """
        today = timezone.now().date()
        today_appointments = self.queryset.filter(
            appointment_date__date=today
        ).order_by('appointment_date')
        
        serializer = AppointmentListSerializer(today_appointments, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """
        Get upcoming appointments (next 7 days).
        
        GET /api/appointments/upcoming/
        Query params:
        - days: number of days ahead (default: 7)
        """
        days = int(request.query_params.get('days', 7))
        end_date = timezone.now() + timedelta(days=days)
        
        upcoming = self.queryset.filter(
            appointment_date__range=[timezone.now(), end_date],
            status__in=['SCHEDULED', 'CONFIRMED']
        ).order_by('appointment_date')
        
        serializer = AppointmentListSerializer(upcoming, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get appointment statistics.
        
        GET /api/appointments/statistics/
        """
        from django.db.models import Count
        
        total = self.queryset.count()
        by_status = dict(
            self.queryset.values('status').annotate(count=Count('id')).values_list('status', 'count')
        )
        by_exam_type = dict(
            self.queryset.values('exam_type').annotate(count=Count('id')).values_list('exam_type', 'count')
        )
        
        today_count = self.queryset.filter(
            appointment_date__date=timezone.now().date()
        ).count()
        
        upcoming_count = self.queryset.filter(
            appointment_date__gte=timezone.now(),
            status__in=['SCHEDULED', 'CONFIRMED']
        ).count()
        
        stats = {
            'total_appointments': total,
            'today': today_count,
            'upcoming': upcoming_count,
            'by_status': by_status,
            'by_exam_type': by_exam_type
        }
        
        return Response(stats)
    
    @action(detail=True, methods=['post'])
    def check_in(self, request, pk=None):
        """
        Check in a patient for their appointment.
        
        POST /api/appointments/{id}/check_in/
        """
        appointment = self.get_object()
        
        if appointment.status != 'CONFIRMED':
            return Response(
                {'error': 'Can only check in confirmed appointments'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        appointment.status = 'CHECKED_IN'
        appointment.save()
        
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Mark appointment as completed.
        
        POST /api/appointments/{id}/complete/
        """
        appointment = self.get_object()
        
        if appointment.status not in ['CHECKED_IN', 'IN_PROGRESS']:
            return Response(
                {'error': 'Can only complete checked-in or in-progress appointments'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        appointment.status = 'COMPLETED'
        appointment.save()
        
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel an appointment.
        
        POST /api/appointments/{id}/cancel/
        """
        appointment = self.get_object()
        
        if appointment.status == 'COMPLETED':
            return Response(
                {'error': 'Cannot cancel completed appointments'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        appointment.status = 'CANCELLED'
        appointment.save()
        
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)