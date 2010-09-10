from django.test import TestCase
from app.models import Node, Clip, Propagation

class AppTestCase(TestCase):
    
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    def test_propagation_tracking(self):
        node = Node.objects.create(title="Node 1")
        clip1 = Clip.objects.create(title="Clip 1")
        clip2 = Clip.objects.create(title="Clip 2")
        
        Propagation.objects.create(node=node, clip=clip1)
        Propagation.objects.create(node=node, clip=clip2)
