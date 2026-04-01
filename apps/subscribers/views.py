from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, AllowAny, IsAuthenticated
from rest_framework.renderers import BaseRenderer
from django.conf import settings
from .models import Subscriber, NewsletterSend
from .serializers import SubscriberSerializer, NewsletterSendSerializer

class PassthroughRenderer(BaseRenderer):
    media_type = '*/*'
    format = 'csv'
    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data

class SubscriberViewSet(viewsets.ModelViewSet):
    queryset         = Subscriber.objects.all()
    serializer_class = SubscriberSerializer
    search_fields    = ['email']
    filterset_fields = ['is_active', 'preferred_lang']

    def get_permissions(self):
        if self.action == 'create':
            return []                  
        return [IsAuthenticated()]      

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def send_newsletter(self, request):
        subject = request.data.get('subject')
        body    = request.data.get('body')

        if not subject or not body:
            return Response({'error': 'Subject and body are required.'}, status=400)

        active_subscribers = Subscriber.objects.filter(is_active=True, gdpr_consent=True)
        count = active_subscribers.count()

        NewsletterSend.objects.create(
            subject         = subject if isinstance(subject, dict) else {'fr': subject},
            body            = body if isinstance(body, dict) else {'fr': body},
            recipient_count = count,
        )
        # Frontend expects exactly: { sent_to: number }
        return Response({'sent_to': count}, status=201)

    @action(detail=False, methods=['get'], url_path='unsubscribe/(?P<token>[^/.]+)', permission_classes=[AllowAny])
    def unsubscribe(self, request, token=None):
        try:
            sub = Subscriber.objects.get(unsubscribe_token=token)
            sub.is_active = False
            sub.save()
            return Response({'message': 'Unsubscribed successfully.'})
        except Subscriber.DoesNotExist:
            return Response({'error': 'Invalid token.'}, status=404)
        
        
    @action(detail=False, methods=['get'], renderer_classes=[PassthroughRenderer])
    def export(self, request):
        import csv
        from django.http import HttpResponse
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="subscribers.csv"'
        writer = csv.writer(response)
        writer.writerow(['Email', 'Language', 'Status', 'Subscribed At'])
        for sub in Subscriber.objects.all():
            writer.writerow([
                sub.email,
                sub.preferred_lang,
                'active' if sub.is_active else 'unsubscribed',
                sub.subscribed_at.strftime('%Y-%m-%d'),
            ])
        return response
