import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        email='admin@test.com', username='admin', password='testpass123'
    )
    
@pytest.fixture
def auth_client(client, admin_user):
    res = client.post('/api/v1/auth/login/', {
        'email': 'admin@test.com', 'password': 'testpass123'
    }, format='json')
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {res.data["access"]}')
    return client


class TestAuth:

    def test_login_with_email(self, client, admin_user):
        res = client.post('/api/v1/auth/login/', {
            'email': 'admin@test.com',
            'password': 'testpass123'
        }, format='json')
        assert res.status_code == 200
        assert 'access' in res.data
        assert 'refresh' in res.data

    def test_login_wrong_password(self, client, admin_user):
        res = client.post('/api/v1/auth/login/', {
            'email': 'admin@test.com',
            'password': 'wrongpassword'
        }, format='json')
        assert res.status_code == 401

    def test_login_unknown_email(self, client, db):
        res = client.post('/api/v1/auth/login/', {
            'email': 'nobody@test.com',
            'password': 'whatever'
        }, format='json')
        assert res.status_code == 401

    def test_refresh_token(self, client, admin_user):
        login = client.post('/api/v1/auth/login/', {
            'email': 'admin@test.com',
            'password': 'testpass123'
        }, format='json')
        refresh = login.data['refresh']
        res = client.post('/api/v1/auth/refresh/', {
            'refresh': refresh
        }, format='json')
        assert res.status_code == 200
        assert 'access' in res.data

    def test_expired_token_rejected(self, client):
        fake_token = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.fake.fake'
        client.credentials(HTTP_AUTHORIZATION=fake_token)
        res = client.get('/api/v1/leads/')
        assert res.status_code == 401

    def test_protected_route_without_token(self, client):
        res = client.get('/api/v1/leads/')
        assert res.status_code == 401
        
@pytest.mark.django_db
class TestSecurity:

    def test_sql_injection_in_email(self, client):
        """SQL injection in login field must not crash — DRF/Django ORM is safe."""
        res = client.post('/api/v1/auth/login/', {
            'email': "' OR '1'='1",
            'password': 'anything'
        }, format='json')
        assert res.status_code == 401   # rejected, not 500

    def test_xss_in_email_rejected(self, client, db):
        """XSS payload in email field must be rejected by email validator."""
        res = client.post('/api/v1/auth/login/', {
            'email': '<script>alert(1)</script>@evil.com',
            'password': 'test'
        }, format='json')
        assert res.status_code == 401

    def test_staff_cannot_access_users(self, client, db):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        staff = User.objects.create_user(
            email='staff@test.com', username='staff',
            password='testpass123', role='staff'
        )
        res = client.post('/api/v1/auth/login/',
                          {'email': 'staff@test.com', 'password': 'testpass123'},
                          format='json')
        token = res.data['access']
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        res2 = client.get('/api/v1/users/')
        assert res2.status_code == 403

    def test_viewer_cannot_write(self, client, db):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        viewer = User.objects.create_user(
            email='viewer@test.com', username='viewer',
            password='testpass123', role='viewer'
        )
        res = client.post('/api/v1/auth/login/',
                          {'email': 'viewer@test.com', 'password': 'testpass123'},
                          format='json')
        token = res.data['access']
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        res2 = client.post('/api/v1/categories/',
                           {'name': {'fr': 'Test'}, 'slug': 'test', 'level': 1},
                           format='json')
        assert res2.status_code == 403

    def test_cannot_delete_own_account(self, auth_client, admin_user):
        res = auth_client.delete(f'/api/v1/users/{admin_user.id}/')
        assert res.status_code == 400

    def test_expired_token_rejected(self, client):
        client.credentials(HTTP_AUTHORIZATION='Bearer fake.token.here')
        res = client.get('/api/v1/leads/')
        assert res.status_code == 401