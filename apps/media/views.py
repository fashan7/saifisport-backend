from rest_framework import viewsets, parsers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticatedOrReadOnly
import cloudinary.uploader
from .models import MediaFile
from .serializers import MediaFileSerializer


class MediaFileViewSet(viewsets.ModelViewSet):
    queryset         = MediaFile.objects.all()
    serializer_class = MediaFileSerializer
    filterset_fields = ['aspect_ratio']
    search_fields    = ['filename', 'alt_text']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticatedOrReadOnly()]
        return [IsAdminUser()]

    def destroy(self, request, *args, **kwargs):
        media = self.get_object()
        if media.product_uses.exists():
            products = list(media.product_uses.values_list('product__sku', flat=True))
            return Response(
                {'error': f'Image is used by products: {", ".join(products)}. Remove from products first.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Delete from Cloudinary too
        if media.public_id:
            cloudinary.uploader.destroy(media.public_id)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    def usage(self, request, pk=None):
        media    = self.get_object()
        pi_qs    = media.product_uses.select_related('product').all()
        return Response({
            'in_use':   pi_qs.exists(),
            'products': [pi.product.sku for pi in pi_qs]
        })

    @action(detail=False, methods=['post'], parser_classes=[parsers.MultiPartParser])
    def upload(self, request):
        file         = request.FILES.get('file')
        aspect_ratio = request.data.get('aspect_ratio', '1:1')

        if not file:
            return Response({'error': 'No file provided.'}, status=400)

        allowed_types = ['image/jpeg', 'image/png', 'image/webp']
        if file.content_type not in allowed_types:
            return Response({'error': 'Only JPEG, PNG and WebP allowed.'}, status=400)

        if file.size > 10 * 1024 * 1024:  # 10MB
            return Response({'error': 'File too large. Max 10MB.'}, status=400)

        crop_map = {
            '1:1':  {'width': 800,  'height': 800,  'crop': 'fill'},
            '16:9': {'width': 1280, 'height': 720,  'crop': 'fill'},
            '21:9': {'width': 1920, 'height': 823,  'crop': 'fill'},
        }
        transform = crop_map.get(aspect_ratio, crop_map['1:1'])

        result = cloudinary.uploader.upload(
            file,
            folder         = 'saifisport',
            transformation = transform,
            quality        = 'auto',
            fetch_format   = 'auto',
        )

        media = MediaFile.objects.create(
            url          = result['secure_url'],
            public_id    = result['public_id'],
            filename     = file.name,
            aspect_ratio = aspect_ratio,
            file_size_kb = result.get('bytes', 0) // 1024,
            width        = result.get('width', 0),
            height       = result.get('height', 0),
        )
        return Response(MediaFileSerializer(media).data, status=201)