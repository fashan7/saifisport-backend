from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticatedOrReadOnly
from .models import Page, Banner, EmailTemplate
from .serializers import PageSerializer, BannerSerializer, EmailTemplateSerializer


class PageViewSet(viewsets.ModelViewSet):
    queryset         = Page.objects.all()
    serializer_class = PageSerializer
    lookup_field     = 'slug'

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticatedOrReadOnly()]
        return [IsAdminUser()]


class BannerViewSet(viewsets.ModelViewSet):
    serializer_class = BannerSerializer

    def get_queryset(self):
        qs = Banner.objects.all()
        # Public frontend only sees active banners
        if not self.request.user.is_authenticated:
            return qs.filter(is_active=True)
        return qs

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticatedOrReadOnly()]
        return [IsAdminUser()]


class EmailTemplateViewSet(viewsets.ModelViewSet):
    queryset         = EmailTemplate.objects.all()
    serializer_class = EmailTemplateSerializer

    def get_permissions(self):
        return [IsAdminUser()]