from django.db import models

class MediaFile(models.Model):
    class AspectRatio(models.TextChoices):
        SQUARE = '1:1',   'Square (products)'
        WIDE   = '16:9',  'Wide (site gallery)'
        BANNER = '21:9',  'Banner (hero)'

    url          = models.URLField(max_length=500)
    public_id    = models.CharField(max_length=255, blank=True)  # Cloudinary public_id
    filename     = models.CharField(max_length=255)
    alt_text     = models.CharField(max_length=255, blank=True)
    aspect_ratio = models.CharField(
        max_length=10, choices=AspectRatio.choices, default=AspectRatio.SQUARE
    )
    file_size_kb = models.PositiveIntegerField(default=0)
    width        = models.PositiveIntegerField(default=0)
    height       = models.PositiveIntegerField(default=0)
    uploaded_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.filename


class ProductImage(models.Model):
    product    = models.ForeignKey(
        'catalog.Product', on_delete=models.CASCADE, related_name='images'
    )
    media_file = models.ForeignKey(
        MediaFile, on_delete=models.PROTECT, related_name='product_uses'
    )
    order      = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ['order']