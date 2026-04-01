from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticatedOrReadOnly, IsAuthenticated
from .models import Page, Banner, EmailTemplate
from .serializers import PageSerializer, BannerSerializer, EmailTemplateSerializer


class PageViewSet(viewsets.ModelViewSet):
    queryset = Page.objects.filter(is_published=True)
    serializer_class = PageSerializer
    lookup_field = 'slug'

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return []                 
        return [IsAuthenticated()] 

    def get_queryset(self):
        qs = super().get_queryset()
        # Only show published pages to public
        if not self.request.user.is_authenticated:
            return qs.filter(is_published=True)
        return Page.objects.all()


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
            return []             
        return [IsAuthenticated()]   


class EmailTemplateViewSet(viewsets.ModelViewSet):
    queryset         = EmailTemplate.objects.all()
    serializer_class = EmailTemplateSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()] 
        return [IsAdminUser()]        