from django.test import TestCase
from apps.users.models import User
from apps.projects_and_clients.models import Client, Project
from apps.finances.models import FinGroup


class TestProjectFinGroupSignal(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            name="siguser",
            email="sig@test.com",
            password="pass",
            phone="5584000000000"
        )
        self.client = Client.objects.create(
            user=self.user, name="C1", cpf="11122233344"
        )

    def test_fingroup_created_automatically(self):
        # Create Project
        project = Project.objects.create(
            user=self.user,
            client=self.client,
            name="Signal Project",
            estimated_deadline="2026-12-31",
            estimated_cost=500.00,
            status="OPEN"
        )
        
        # Check if FinGroup exists
        fingroup = FinGroup.objects.filter(
            user=self.user,
            related_to=project.id,
            relation="PROJECT"
        ).first()
        
        self.assertIsNotNone(fingroup)
        self.assertEqual(fingroup.name, f"Finanças: {project.name}")
