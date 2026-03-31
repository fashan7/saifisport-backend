from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.views import MeView, UserListView, UserDetailView
from apps.catalog.views      import CategoryViewSet, ProductViewSet
from apps.media.views        import MediaFileViewSet
from apps.leads.views        import LeadViewSet
from apps.content.views      import PageViewSet, BannerViewSet, EmailTemplateViewSet
from apps.subscribers.views  import SubscriberViewSet
from apps.integrations.views import SiteSettingsView, HolidayStatusView

router = DefaultRouter()
router.register('categories',      CategoryViewSet,      basename='category')
router.register('products',        ProductViewSet,       basename='product')
router.register('media',           MediaFileViewSet,     basename='media')
router.register('leads',           LeadViewSet,          basename='lead')
router.register('pages',           PageViewSet,          basename='page')
router.register('banners',         BannerViewSet,        basename='banner')
router.register('email-templates', EmailTemplateViewSet, basename='emailtemplate')
router.register('subscribers',     SubscriberViewSet,    basename='subscriber')

# Aliases — match what the Lovable frontend already calls
router.register('quotes',          LeadViewSet,          basename='quote')
router.register('subcategories',   CategoryViewSet,      basename='subcategory')

urlpatterns = [
     path('', include(router.urls)),

     path('auth/me/',          MeView.as_view(),        name='me'),
     path('users/',            UserListView.as_view(),  name='users'),
     path('users/<int:pk>/',   UserDetailView.as_view(), name='user-detail'),
     # Auth
     path('auth/login/',   TokenObtainPairView.as_view(), name='token_obtain'),
     path('auth/refresh/', TokenRefreshView.as_view(),    name='token_refresh'),

     # Settings
     path('settings/',              SiteSettingsView.as_view(),   name='site-settings'),
     path('settings/holiday-mode/', HolidayStatusView.as_view(),  name='holiday-status'),

     # Newsletter aliases
     path('newsletter/subscribe/',
         SubscriberViewSet.as_view({'post': 'create'}),          name='newsletter-subscribe'),
     path('newsletter/subscribers/',
         SubscriberViewSet.as_view({'get': 'list'}),             name='newsletter-subscribers'),
     path('newsletter/subscribers/export/',
         SubscriberViewSet.as_view({'get': 'export'}),           name='newsletter-export'),
     path('newsletter/blast/',
         SubscriberViewSet.as_view({'post': 'send_newsletter'}), name='newsletter-blast'),
]

"""
curl -X POST http://127.0.0.1:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"fashanzak4@gmail.com","password":"Nahsaf#1997"}'
  
  curl http://127.0.0.1:8000/api/v1/products/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzc0ODYyODY4LCJpYXQiOjE3NzQ4NjEwNjgsImp0aSI6IjBjZmRhMjgyOThmNjRlMTFhYjlhZTNkMzIyYzUyNjgwIiwidXNlcl9pZCI6IjEifQ.83LHQ0xNT-lsfpmifBOf5p_J03U6vf-nhzhYSeggoOU"
"""
