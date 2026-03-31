from django.db import models


class PageVisit(models.Model):
    ip_hash     = models.CharField(max_length=64, db_index=True)  # SHA256, never store raw IP
    country     = models.CharField(max_length=2, blank=True)       # ISO code: FR, DE, etc.
    country_name= models.CharField(max_length=100, blank=True)
    city        = models.CharField(max_length=100, blank=True)
    path        = models.CharField(max_length=500)
    referrer    = models.CharField(max_length=500, blank=True)
    user_agent  = models.CharField(max_length=500, blank=True)
    language    = models.CharField(max_length=10, blank=True)
    visited_at  = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['ip_hash', 'path', 'visited_at']),
            models.Index(fields=['country']),
        ]

    def __str__(self):
        return f"{self.country} {self.path} {self.visited_at:%Y-%m-%d}"


class DailyStats(models.Model):
    """Pre-aggregated daily stats for fast dashboard queries."""
    date          = models.DateField(unique=True, db_index=True)
    unique_visits = models.IntegerField(default=0)
    total_hits    = models.IntegerField(default=0)
    top_country   = models.CharField(max_length=2, blank=True)

    class Meta:
        ordering = ['-date']