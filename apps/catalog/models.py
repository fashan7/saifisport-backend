from django.db import models
from django.conf import settings

def translated_default():
    return {code: '' for code in settings.LANGUAGE_CODES}


class Category(models.Model):
    class Level(models.IntegerChoices):
        PARENT = 1, 'Parent'
        SUB    = 2, 'Subcategory'
        TYPE   = 3, 'Type'

    name   = models.JSONField(default=translated_default)  
    slug   = models.SlugField(max_length=100, unique=True)
    level  = models.IntegerField(choices=Level.choices)
    parent = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.CASCADE, related_name='children'
    )
    order  = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']
        verbose_name_plural = 'Categories'

    def get_name(self, lang=None):
        lang = lang or settings.DEFAULT_LANGUAGE
        return self.name.get(lang) or self.name.get(settings.DEFAULT_LANGUAGE, '')

    def __str__(self):
        return self.get_name()


class Product(models.Model):
    sku         = models.CharField(max_length=50, unique=True)
    name        = models.JSONField(default=translated_default)
    material    = models.JSONField(default=dict)
    description = models.JSONField(default=translated_default)
    moq         = models.PositiveIntegerField(default=1, help_text='Minimum order quantity')
    is_featured = models.BooleanField(default=False)
    available_materials = models.JSONField(
        default=list,
        help_text='List of available materials: cowhide, buffalo, pu, pvc'
    )

    category     = models.ForeignKey(
        Category, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='products_l1'
    )
    subcategory  = models.ForeignKey(
        Category, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='products_l2'
    )
    product_type = models.ForeignKey(
        Category, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='products_l3'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def get_name(self, lang=None):
        lang = lang or settings.DEFAULT_LANGUAGE
        return self.name.get(lang) or self.name.get(settings.DEFAULT_LANGUAGE, '')

    def __str__(self):
        return f"{self.sku} — {self.get_name()}"