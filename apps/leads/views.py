import csv
from django.http import HttpResponse
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from .models import Lead
from .serializers import LeadSerializer


class LeadViewSet(viewsets.ModelViewSet):
    queryset         = Lead.objects.all()
    serializer_class = LeadSerializer
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'priority', 'country', 'category']
    search_fields    = ['club_name', 'email', 'full_name']
    ordering_fields  = ['created_at', 'priority']
    parser_classes   = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAdminUser()]

    @action(detail=False, methods=['get'])
    def stats(self, request):
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Count
        now   = timezone.now()
        month = now - timedelta(days=30)
        qs    = self.get_queryset()
        top   = (qs.values('category')
                   .annotate(n=Count('id'))
                   .order_by('-n')
                   .first())
        return Response({
            'total':            qs.count(),
            'leads_this_month': qs.filter(created_at__gte=month).count(),
            'pending':          qs.filter(status='pending').count(),
            'contacted':        qs.filter(status='contacted').count(),
            'top_category':     top['category'] if top else None,
        })

    @action(detail=False, methods=['get'], url_path='export')
    def export(self, request):
        """CSV export — matches frontend exportQuotesCSV()"""
        qs = self.get_queryset()
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="leads.csv"'
        writer = csv.writer(response)
        writer.writerow([
            'Date', 'Club Name', 'Full Name', 'Email', 'Phone',
            'Country', 'Category', 'Quantity', 'Custom Branding',
            'VAT Number', 'Status', 'Priority'
        ])
        for lead in qs:
            writer.writerow([
                lead.created_at.strftime('%Y-%m-%d'),
                lead.club_name, lead.full_name, lead.email, lead.phone,
                lead.country, lead.category, lead.quantity,
                lead.custom_branding, lead.vat_number,
                lead.status, lead.priority,
            ])
        return response