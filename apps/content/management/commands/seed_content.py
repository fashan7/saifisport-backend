from django.core.management.base import BaseCommand
from apps.content.models import Page, Banner, EmailTemplate


class Command(BaseCommand):
    help = 'Seed initial Pages, Banners and Email Templates'

    def handle(self, *args, **kwargs):
        self._seed_pages()
        self._seed_banners()
        self._seed_email_templates()
        self.stdout.write(self.style.SUCCESS('Content seeded successfully.'))

    def _seed_pages(self):
        pages = [
            {
                'slug': 'privacy',
                'title': {
                    'fr': 'Politique de Confidentialité',
                    'en': 'Privacy Policy',
                    'de': 'Datenschutzrichtlinie',
                    'es': 'Política de Privacidad',
                    'sv': 'Integritetspolicy',
                },
                'content': {'fr': '', 'en': '', 'de': '', 'es': '', 'sv': ''},
                'is_published': True,
            },
            {
                'slug': 'terms',
                'title': {
                    'fr': 'Conditions Générales',
                    'en': 'Terms & Conditions',
                    'de': 'Allgemeine Geschäftsbedingungen',
                    'es': 'Términos y Condiciones',
                    'sv': 'Villkor',
                },
                'content': {'fr': '', 'en': '', 'de': '', 'es': '', 'sv': ''},
                'is_published': True,
            },
            {
                'slug': 'shipping',
                'title': {
                    'fr': 'Expédition et Retours',
                    'en': 'Shipping & Returns',
                    'de': 'Versand & Rücksendungen',
                    'es': 'Envío y Devoluciones',
                    'sv': 'Frakt & Returer',
                },
                'content': {'fr': '', 'en': '', 'de': '', 'es': '', 'sv': ''},
                'is_published': True,
            },
        ]
        for data in pages:
            Page.objects.get_or_create(slug=data['slug'], defaults=data)
        self.stdout.write('  ✓ Pages seeded')

    def _seed_banners(self):
        banners = [
            {
                'order': 1,
                'title':       {'fr': 'Équipement de Combat Premium', 'en': 'Premium Combat Equipment', 'de': 'Premium-Kampfausrüstung', 'es': 'Equipo de Combate Premium', 'sv': 'Premium Kampingutrustning'},
                'subtitle':    {'fr': 'Direct usine de Sialkot à votre salle', 'en': 'Factory-direct from Sialkot to your gym', 'de': 'Direkt ab Werk von Sialkot', 'es': 'Directo de fábrica desde Sialkot', 'sv': 'Direkt från fabriken i Sialkot'},
                'button_text': {'fr': 'Parcourir le Catalogue', 'en': 'Browse Catalog', 'de': 'Katalog durchsuchen', 'es': 'Ver Catálogo', 'sv': 'Bläddra i katalog'},
                'button_link': '/fight-gear',
                'is_active':   True,
            },
            {
                'order': 2,
                'title':       {'fr': 'Personnalisation Disponible', 'en': 'Custom Branding Available', 'de': 'Individuelle Markengestaltung', 'es': 'Personalización Disponible', 'sv': 'Anpassad varumärkning'},
                'subtitle':    {'fr': 'Votre logo, vos couleurs, notre savoir-faire', 'en': 'Your logo, your colors, our craftsmanship', 'de': 'Ihr Logo, Ihre Farben, unser Handwerk', 'es': 'Tu logo, tus colores, nuestra artesanía', 'sv': 'Din logotyp, dina färger, vårt hantverk'},
                'button_text': {'fr': 'Demander un Devis', 'en': 'Request Quote', 'de': 'Angebot anfordern', 'es': 'Solicitar Presupuesto', 'sv': 'Begär offert'},
                'button_link': '/contact',
                'is_active':   True,
            },
            {
                'order': 3,
                'title':       {'fr': 'Nouvelle Collection Boxe', 'en': 'New Boxing Collection', 'de': 'Neue Boxkollektion', 'es': 'Nueva Colección de Boxeo', 'sv': 'Ny boxningskollektion'},
                'subtitle':    {'fr': 'Gants et équipements professionnels', 'en': 'Professional grade gloves & gear', 'de': 'Professionelle Handschuhe & Ausrüstung', 'es': 'Guantes y equipos profesionales', 'sv': 'Professionella handskar och utrustning'},
                'button_text': {'fr': 'Acheter Maintenant', 'en': 'Shop Now', 'de': 'Jetzt kaufen', 'es': 'Comprar Ahora', 'sv': 'Handla nu'},
                'button_link': '/fight-gear',
                'is_active':   False,
            },
        ]
        for data in banners:
            Banner.objects.get_or_create(order=data['order'], defaults=data)
        self.stdout.write('  ✓ Banners seeded')

    def _seed_email_templates(self):
        templates = [
            {
                'name': 'Quote Confirmation (User)',
                'type': 'transactional',
                'subject': {
                    'fr': 'Votre demande de devis #{{quote_id}} — Saifi Sport',
                    'en': 'Your Quote Request #{{quote_id}} — Saifi Sport',
                },
                'body': {
                    'fr': 'Cher {{user_name}},\n\nMerci pour votre demande de devis pour {{product_name}}.\nNotre équipe vous répondra dans les 24 heures.\n\nID Devis: {{quote_id}}\nCatégorie: {{category}}\nQuantité: {{quantity}}\n\nCordialement,\nL\'équipe Saifi Sport',
                    'en': 'Dear {{user_name}},\n\nThank you for your quote request for {{product_name}}.\nOur team will get back to you within 24 hours.\n\nQuote ID: {{quote_id}}\nCategory: {{category}}\nQuantity: {{quantity}}\n\nBest regards,\nThe Saifi Sport Team',
                },
            },
            {
                'name': 'New Lead Alert (Admin)',
                'type': 'notification',
                'subject': {
                    'fr': '🔔 Nouveau Lead: {{club_name}} — {{category}}',
                    'en': '🔔 New Lead: {{club_name}} — {{category}}',
                },
                'body': {
                    'fr': 'Nouveau lead reçu:\n\nClub: {{club_name}}\nCatégorie: {{category}}\nQuantité: {{quantity}}\nPays: {{country}}',
                    'en': 'New lead received:\n\nClub: {{club_name}}\nCategory: {{category}}\nQuantity: {{quantity}}\nCountry: {{country}}',
                },
            },
            {
                'name': 'General Newsletter',
                'type': 'marketing',
                'subject': {
                    'fr': '{{subject_line}}',
                    'en': '{{subject_line}}',
                },
                'body': {
                    'fr': '',
                    'en': '',
                },
            },
        ]
        for data in templates:
            EmailTemplate.objects.get_or_create(name=data['name'], defaults=data)
        self.stdout.write('  ✓ Email templates seeded')