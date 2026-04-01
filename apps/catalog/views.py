from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response 
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    throttle_classes = [] 
    queryset         = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['level', 'parent']
    search_fields    = ['slug']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticatedOrReadOnly()]
        return [IsAdminUser()]

    def destroy(self, request, *args, **kwargs):
        category = self.get_object()
        # Block deletion if products are linked
        if category.products_l1.exists() or category.products_l2.exists() or category.products_l3.exists():
            return Response(
                {'error': 'Cannot delete — products are linked to this category.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Block deletion if subcategories exist
        if category.children.exists():
            return Response(
                {'error': 'Cannot delete — subcategories exist. Delete them first.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'subcategory', 'product_type', 'is_featured']
    search_fields    = ['sku']
    ordering_fields  = ['created_at', 'moq']
    ordering         = ['id']
    throttle_classes = [] 

    def get_queryset(self):
        return Product.objects.select_related(
            'category', 'subcategory', 'product_type'
        ).prefetch_related('images__media_file')

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticatedOrReadOnly()]
        return [IsAdminUser()]

    def destroy(self, request, *args, **kwargs):
        product = self.get_object()
        # Delete linked product images first
        product.images.all().delete()
        return super().destroy(request, *args, **kwargs)