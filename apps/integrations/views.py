from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticatedOrReadOnly
from .models import SiteSettings
from .serializers import SiteSettingsSerializer


class SiteSettingsView(APIView):
    """Single-object view — no router needed, always operates on row id=1."""

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticatedOrReadOnly()]
        return [IsAdminUser()]

    def get(self, request):
        settings_obj = SiteSettings.get()
        return Response(SiteSettingsSerializer(settings_obj, context={'request': request}).data)

    def patch(self, request):
        settings_obj = SiteSettings.get()
        serializer   = SiteSettingsSerializer(settings_obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    
class HolidayStatusView(APIView):
    permission_classes = []  # Public — frontend shows holiday banner

    def get(self, request):
        s = SiteSettings.get()
        data = {'is_holiday': s.holiday_mode}
        if s.holiday_mode:
            lang = request.query_params.get('lang', 'fr')
            data['message'] = s.holiday_message.get(lang) or s.holiday_message.get('fr', '')
        return Response(data)