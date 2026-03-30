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

    @action(detail=False, methods=['post'], parser_classes=[parsers.MultiPartParser])
    def upload(self, request):
        file         = request.FILES.get('file')
        aspect_ratio = request.data.get('aspect_ratio', '1:1')

        if not file:
            return Response({'error': 'No file provided.'}, status=400)

        # Map aspect ratio to Cloudinary crop settings
        crop_map = {
            '1:1':  {'width': 800,  'height': 800,  'crop': 'fill'},
            '16:9': {'width': 1280, 'height': 720,  'crop': 'fill'},
            '21:9': {'width': 1920, 'height': 823,  'crop': 'fill'},
        }
        transform = crop_map.get(aspect_ratio, crop_map['1:1'])

        result = cloudinary.uploader.upload(
            file,
            folder       = 'saifisport',
            transformation = transform,
            quality      = 'auto',
            fetch_format = 'auto',
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
    
    @action(detail=True, methods=['get'])
    def usage(self, request, pk=None):
        media = self.get_object()
        product_images = media.product_uses.select_related('product').all()
        in_use   = product_images.exists()
        products = [pi.product.get_name() for pi in product_images]
        return Response({'in_use': in_use, 'products': products})