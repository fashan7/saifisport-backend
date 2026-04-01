import os
from rest_framework import viewsets, parsers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.views import APIView
import cloudinary.uploader

from .models import MediaFile
from .serializers import MediaFileSerializer
from ..leads.utils import validate_upload


class MediaFileViewSet(viewsets.ModelViewSet):
    """
    Handles all media operations.
    Upload endpoint: POST /api/v1/media/upload/
      - file         (required) — the image file
      - aspect_ratio (optional) — '1:1' | '16:9' | '21:9', defaults to '1:1'
    
    aspect_ratio determines the type:
      1:1  → Product Images  → saifisport/products/ folder
      16:9 → Site Gallery    → saifisport/gallery/ folder
      21:9 → Banners         → saifisport/banners/ folder
    """
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
                {'error': f'Image is used by products: {", ".join(str(p) for p in products)}. Remove from products first.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Delete from Cloudinary
        if media.public_id:
            try:
                cloudinary.uploader.destroy(media.public_id)
            except Exception:
                pass  # Don't block DB deletion if Cloudinary fails
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    def usage(self, request, pk=None):
        """GET /api/v1/media/{pk}/usage/ — which products use this image."""
        media = self.get_object()
        pi_qs = media.product_uses.select_related('product').all()
        return Response({
            'in_use':   pi_qs.exists(),
            'products': [pi.product.sku for pi in pi_qs]
        })

    @action(detail=False, methods=['post'], parser_classes=[parsers.MultiPartParser])
    def upload(self, request):
        """
        POST /api/v1/media/upload/
        The single upload endpoint for ALL image types.
        Send aspect_ratio to determine where it goes:
          - 1:1  → product image
          - 16:9 → site gallery (homepage)
          - 21:9 → banner
        """
        file         = request.FILES.get('file')
        aspect_ratio = request.data.get('aspect_ratio', '1:1')

        # ── Validation ────────────────────────────────────────────────────
        if not file:
            return Response({'error': 'No file provided.'}, status=400)

        if aspect_ratio not in ['1:1', '16:9', '21:9']:
            aspect_ratio = '1:1'

        # File type check
        allowed_types = ['image/jpeg', 'image/png', 'image/webp']
        if file.content_type not in allowed_types:
            return Response({'error': 'Only JPEG, PNG and WebP allowed.'}, status=400)

        # File size check (10MB)
        if file.size > 10 * 1024 * 1024:
            return Response({'error': 'File too large. Max 10MB.'}, status=400)

        # Magic bytes security check
        try:
            validate_upload(file)
        except Exception as e:
            return Response({'error': str(e)}, status=400)

        # ── Cloudinary config ─────────────────────────────────────────────
        folder_map = {
            '1:1':  'saifisport/products',
            '16:9': 'saifisport/gallery',
            '21:9': 'saifisport/banners',
        }
        crop_map = {
            '1:1':  {'width': 800,  'height': 800,  'crop': 'fill'},
            '16:9': {'width': 1280, 'height': 720,  'crop': 'fill'},
            '21:9': {'width': 1920, 'height': 823,  'crop': 'fill'},
        }

        folder    = folder_map[aspect_ratio]
        transform = crop_map[aspect_ratio]

        # ── Upload to Cloudinary ──────────────────────────────────────────
        try:
            result = cloudinary.uploader.upload(
                file,
                folder         = folder,
                quality        = 'auto',
                fetch_format   = 'auto',
            )
        except Exception as e:
            return Response(
                {'error': f'Cloudinary upload failed: {str(e)}'},
                status=500
            )

        # Verify we got a URL back
        url = result.get('secure_url', '')
        if not url:
            return Response(
                {'error': 'Cloudinary did not return a URL.'},
                status=500
            )

        # ── Save to DB ────────────────────────────────────────────────────
        media = MediaFile.objects.create(
            url          = url,
            public_id    = result.get('public_id', ''),
            filename     = os.path.splitext(file.name)[0] or file.name,
            aspect_ratio = aspect_ratio,
            file_size_kb = result.get('bytes', 0) // 1024,
            width        = result.get('width', 0),
            height       = result.get('height', 0),
            alt_text     = '',
        )

        return Response(MediaFileSerializer(media).data, status=201)


class PublicGalleryView(APIView):
    """
    GET /api/v1/gallery/
    Public — no auth needed.
    Returns site gallery images (16:9) for the homepage.
    Max 12 images, newest first.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        lang  = request.query_params.get('lang', 'fr')
        limit = int(request.query_params.get('limit', 12))
        limit = min(limit, 50)  # cap at 50

        images = (
            MediaFile.objects
            .filter(aspect_ratio='16:9')
            .order_by('-uploaded_at')[:limit]
        )

        def resolve(field, fallback=''):
            if isinstance(field, dict):
                return field.get(lang) or field.get('fr') or field.get('en') or fallback
            return field or fallback

        return Response([
            {
                'id':    img.id,
                'url':   img.url,
                'alt':   resolve(img.alt_text),
                'title': resolve(img.title, img.filename),
            }
            for img in images
        ])