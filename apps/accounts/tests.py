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