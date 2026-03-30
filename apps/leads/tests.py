import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.leads.models import Lead

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


@pytest.fixture
def sample_lead(db):
    return Lead.objects.create(
        club_name='Boxing Club Lyon',
        full_name='Jean Martin',
        email='jean@boxinglyon.fr',
        country='France',
        country_code='FR',
        category='fightGear',
        quantity='500',
    )


class TestLeadAPI:

    def test_public_can_submit_quote(self, client, db):  # ← add db fixture
        res = client.post('/api/v1/quotes/', {
            'club_name': 'MMA Paris',
            'full_name': 'Pierre Dupont',
            'email': 'pierre@mmaparis.fr',
            'country': 'France',
            'country_code': 'FR',
            'category': 'fightGear',
            'quantity': '100',
            'custom_branding': False,
        })
        assert res.status_code == 201
        assert Lead.objects.filter(email='pierre@mmaparis.fr').exists()

    def test_public_cannot_list_leads(self, client):
        res = client.get('/api/v1/quotes/')
        assert res.status_code == 401

    def test_admin_can_list_leads(self, auth_client, sample_lead):
        res = auth_client.get('/api/v1/quotes/')
        assert res.status_code == 200
        assert len(res.data) == 1

    def test_patch_status(self, auth_client, sample_lead):
        res = auth_client.patch(
            f'/api/v1/quotes/{sample_lead.id}/',
            {'status': 'contacted'},
            format='json'
        )
        assert res.status_code == 200
        sample_lead.refresh_from_db()
        assert sample_lead.status == 'contacted'

    def test_patch_invalid_status(self, auth_client, sample_lead):
        res = auth_client.patch(
            f'/api/v1/quotes/{sample_lead.id}/',
            {'status': 'invalid_status'},
            format='json'
        )
        assert res.status_code == 400

    def test_stats_endpoint(self, auth_client, sample_lead):
        res = auth_client.get('/api/v1/leads/stats/')
        assert res.status_code == 200
        assert 'total' in res.data
        assert 'pending' in res.data
        assert 'leads_this_month' in res.data

    def test_csv_export(self, auth_client, sample_lead):
        # ← Don't set Accept header — just test the endpoint returns 200
        res = auth_client.get('/api/v1/quotes/export/')
        assert res.status_code == 200
        assert b'Boxing Club Lyon' in res.content


class TestLeadValidation:

    def test_email_required(self, client, db):
        res = client.post('/api/v1/quotes/', {
            'club_name': 'Test Club',
            'country': 'FR',
            'category': 'fightGear',
            'quantity': '100',
        })
        assert res.status_code == 400

    def test_category_required(self, client, db):
        res = client.post('/api/v1/quotes/', {
            'club_name': 'Test Club',
            'email': 'test@test.com',
            'country': 'FR',
            'quantity': '100',
        })
        assert res.status_code == 400