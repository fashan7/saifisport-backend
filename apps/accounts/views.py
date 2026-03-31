from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import serializers, status
from django.contrib.auth import get_user_model

User = get_user_model()


class MeView(APIView):
    """Returns current user info — frontend calls this to validate session."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            'id':       request.user.id,
            'email':    request.user.email,
            'username': request.user.username,
            'role':     request.user.role,
        })


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model  = User
        fields = ['id', 'email', 'username', 'role', 'is_active', 'password', 'date_joined']
        read_only_fields = ['id', 'date_joined']

    def validate_email(self, value):
        return value.lower().strip()

    def validate_role(self, value):
        allowed = [r.value for r in User.Role]
        if value not in allowed:
            raise serializers.ValidationError(f"Role must be one of {allowed}")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)   # hashed — never stored plain
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class UserListView(APIView):
    """List + create users — superadmin only."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        # Only superadmin can see all users
        if request.user.role != 'superadmin':
            return Response({'error': 'Forbidden'}, status=403)
        users = User.objects.all().order_by('-date_joined')
        return Response(UserSerializer(users, many=True).data)

    def post(self, request):
        if request.user.role != 'superadmin':
            return Response({'error': 'Forbidden'}, status=403)
        ser = UserSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data, status=201)


class UserDetailView(APIView):
    """Get, update, delete single user — superadmin only."""
    permission_classes = [IsAdminUser]

    def get_object(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            return None

    def get(self, request, pk):
        user = self.get_object(pk)
        if not user:
            return Response({'error': 'Not found'}, status=404)
        return Response(UserSerializer(user).data)

    def patch(self, request, pk):
        if request.user.role != 'superadmin':
            return Response({'error': 'Forbidden'}, status=403)
        user = self.get_object(pk)
        if not user:
            return Response({'error': 'Not found'}, status=404)
        # Prevent demoting yourself
        if user.pk == request.user.pk and request.data.get('role') != 'superadmin':
            return Response({'error': 'Cannot change your own role'}, status=400)
        ser = UserSerializer(user, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)

    def delete(self, request, pk):
        if request.user.role != 'superadmin':
            return Response({'error': 'Forbidden'}, status=403)
        user = self.get_object(pk)
        if not user:
            return Response({'error': 'Not found'}, status=404)
        if user.pk == request.user.pk:
            return Response({'error': 'Cannot delete your own account'}, status=400)
        user.delete()
        return Response(status=204)