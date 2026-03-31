import hashlib
import json
from datetime import timedelta, date

import requests
from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncDate, TruncMonth
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from .models import PageVisit


def get_ip(request):
    """Extract real IP respecting proxies."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def hash_ip(ip: str) -> str:
    """Hash IP for privacy — never store raw IP."""
    return hashlib.sha256(ip.encode()).hexdigest()


def lookup_country(ip: str) -> dict:
    """
    Geo-locate IP using free ip-api.com (45 req/min free).
    Returns dict with country, countryCode, city.
    """
    if ip in ('127.0.0.1', 'localhost', '::1', ''):
        return {'country': 'Local', 'countryCode': 'LC', 'city': 'Local'}
    try:
        res = requests.get(
            f'http://ip-api.com/json/{ip}?fields=country,countryCode,city',
            timeout=2
        )
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return {'country': '', 'countryCode': '', 'city': ''}


class TrackVisitView(APIView):
    """
    POST /api/v1/analytics/track/
    Called by frontend on page load.
    Deduplicates: same IP + same path within 30 minutes = no new record.
    """
    permission_classes = [AllowAny]
    throttle_classes   = []  # handled by dedup logic below

    def post(self, request):
        ip     = get_ip(request)
        ip_h   = hash_ip(ip)
        path   = request.data.get('path', '/')[:500]
        ref    = request.data.get('referrer', '')[:500]
        ua     = request.META.get('HTTP_USER_AGENT', '')[:500]
        lang   = request.data.get('language', '')[:10]

        # Dedup: if same IP hash visited same path in last 30 minutes → skip
        cutoff = timezone.now() - timedelta(minutes=30)
        already = PageVisit.objects.filter(
            ip_hash=ip_h,
            path=path,
            visited_at__gte=cutoff
        ).exists()

        if already:
            return Response({'recorded': False, 'reason': 'duplicate'})

        # Geo-lookup (async would be better in prod, fine for now)
        geo = lookup_country(ip)

        PageVisit.objects.create(
            ip_hash      = ip_h,
            country      = geo.get('countryCode', ''),
            country_name = geo.get('country', ''),
            city         = geo.get('city', ''),
            path         = path,
            referrer     = ref,
            user_agent   = ua,
            language     = lang,
        )
        return Response({'recorded': True})


class AnalyticsSummaryView(APIView):
    """GET /api/v1/analytics/summary/ — CMS dashboard stats."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now   = timezone.now()
        today = now.date()

        # Date ranges
        last_30 = today - timedelta(days=30)
        last_7  = today - timedelta(days=7)
        yesterday = today - timedelta(days=1)

        base = PageVisit.objects.all()

        # ── Totals ──────────────────────────────────────────────
        total_unique = base.values('ip_hash').distinct().count()
        total_hits   = base.count()

        # ── Last 30 days ─────────────────────────────────────────
        last30 = base.filter(visited_at__date__gte=last_30)
        visits_30d        = last30.values('ip_hash').distinct().count()
        visits_7d         = base.filter(visited_at__date__gte=last_7).values('ip_hash').distinct().count()
        visits_today      = base.filter(visited_at__date=today).values('ip_hash').distinct().count()
        visits_yesterday  = base.filter(visited_at__date=yesterday).values('ip_hash').distinct().count()

        # ── Daily breakdown (last 30 days) ────────────────────────
        daily = (
            last30
            .annotate(day=TruncDate('visited_at'))
            .values('day')
            .annotate(
                unique=Count('ip_hash', distinct=True),
                hits=Count('id')
            )
            .order_by('day')
        )

        # ── Top countries ─────────────────────────────────────────
        countries = (
            last30
            .exclude(country='')
            .values('country', 'country_name')
            .annotate(unique=Count('ip_hash', distinct=True))
            .order_by('-unique')[:15]
        )

        # ── Top pages ─────────────────────────────────────────────
        top_pages = (
            last30
            .values('path')
            .annotate(hits=Count('id'), unique=Count('ip_hash', distinct=True))
            .order_by('-unique')[:10]
        )

        # ── Recent visits (last 50) ───────────────────────────────
        recent = (
            base
            .values('country', 'country_name', 'city', 'path', 'language', 'visited_at')
            .order_by('-visited_at')[:50]
        )

        return Response({
            'totals': {
                'all_time_unique': total_unique,
                'all_time_hits':   total_hits,
                'last_30d_unique': visits_30d,
                'last_7d_unique':  visits_7d,
                'today_unique':    visits_today,
                'yesterday_unique':visits_yesterday,
            },
            'daily':     list(daily),
            'countries': list(countries),
            'top_pages': list(top_pages),
            'recent':    list(recent),
        })