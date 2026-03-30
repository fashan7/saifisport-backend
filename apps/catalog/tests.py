import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.catalog.models import Category, Product

User = get_user_model()


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        email='admin@test.com', username='admin', password='testpass123'
    )


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def auth_client(client, admin_user):
    res = client.post('/api/v1/auth/login/', {
        'email': 'admin@test.com', 'password': 'testpass123'
    }, format='json')
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {res.data["access"]}')
    return client


@pytest.fixture
def parent_category(db):
    return Category.objects.create(
        name={'fr': 'Fight Gear', 'en': 'Fight Gear'},
        slug='fight-gear', level=1
    )


@pytest.fixture
def sub_category(db, parent_category):
    return Category.objects.create(
        name={'fr': 'Gants', 'en': 'Gloves'},
        slug='gants', level=2, parent=parent_category
    )


class TestCategoryAPI:

    def test_list_public(self, client, parent_category):
        res = client.get('/api/v1/categories/')
        assert res.status_code == 200
        assert len(res.data) == 1

    def test_create_requires_auth(self, client, db):
        # ← add format='json' because name is a nested dict
        res = client.post('/api/v1/categories/', {
            'name': {'fr': 'Test'}, 'slug': 'test', 'level': 1
        }, format='json')
        assert res.status_code == 401

    def test_create_as_admin(self, auth_client):
        res = auth_client.post('/api/v1/categories/', {
            'name': {'fr': 'Uniformes', 'en': 'Uniforms'},
            'slug': 'uniforms', 'level': 1
        }, format='json')
        assert res.status_code == 201
        assert Category.objects.filter(slug='uniforms').exists()

    def test_delete_blocked_when_has_children(self, auth_client, parent_category, sub_category):
        res = auth_client.delete(f'/api/v1/categories/{parent_category.id}/')
        assert res.status_code == 400
        assert 'subcategories exist' in res.data['error']

    def test_delete_blocked_when_has_products(self, auth_client, db, parent_category):
        Product.objects.create(
            sku='SS-TEST-001',
            name={'fr': 'Test', 'en': 'Test'},
            material={'fr': '', 'en': ''},
            description={'fr': '', 'en': ''},
            moq=10,
            category=parent_category
        )
        res = auth_client.delete(f'/api/v1/categories/{parent_category.id}/')
        assert res.status_code == 400
        assert 'products are linked' in res.data['error']

    def test_delete_allowed_when_empty(self, auth_client, db):
        cat = Category.objects.create(
            name={'fr': 'Empty'}, slug='empty-cat', level=1
        )
        res = auth_client.delete(f'/api/v1/categories/{cat.id}/')
        assert res.status_code == 204


class TestProductAPI:

    def test_list_empty(self, auth_client):
        res = auth_client.get('/api/v1/products/')
        assert res.status_code == 200
        assert res.data == []

    def test_create_product(self, auth_client, parent_category):
        res = auth_client.post('/api/v1/products/', {
            'sku': 'SS-BG-001',
            'name': {'fr': 'Gants Pro', 'en': 'Pro Gloves'},
            'material': {'fr': 'Cuir', 'en': 'Leather'},
            'description': {'fr': 'Description', 'en': 'Description'},
            'moq': 50,
            'featured': True,        # ← 'featured' not 'is_featured' (serializer field name)
            'category': parent_category.id,
        }, format='json')
        assert res.status_code == 201
        assert Product.objects.filter(sku='SS-BG-001').exists()

    def test_sku_unique(self, auth_client, parent_category):
        data = {
            'sku': 'SS-DUP-001',
            'name': {'fr': 'A', 'en': 'A'},
            'material': {'fr': '', 'en': ''},
            'description': {'fr': '', 'en': ''},
            'moq': 10,
            'category': parent_category.id,
        }
        auth_client.post('/api/v1/products/', data, format='json')
        res = auth_client.post('/api/v1/products/', data, format='json')
        assert res.status_code == 400

    def test_featured_field_returned(self, auth_client, db, parent_category):
        Product.objects.create(
            sku='SS-FT-001',
            name={'fr': 'F', 'en': 'F'},
            material={'fr': '', 'en': ''},
            description={'fr': '', 'en': ''},
            moq=10,
            is_featured=True,
            category=parent_category
        )
        res = auth_client.get('/api/v1/products/')
        assert res.data[0]['featured'] is True  # serializer returns 'featured' not 'is_featured'

    def test_delete_product(self, auth_client, db, parent_category):
        p = Product.objects.create(
            sku='SS-DEL-001',
            name={'fr': 'Del', 'en': 'Del'},
            material={'fr': '', 'en': ''},
            description={'fr': '', 'en': ''},
            moq=10,
            category=parent_category
        )
        res = auth_client.delete(f'/api/v1/products/{p.id}/')
        assert res.status_code == 204
        assert not Product.objects.filter(id=p.id).exists()