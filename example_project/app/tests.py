from django.test import TestCase
from app.models import Node, Clip, Propagation


class AppTestCase(TestCase):
    
    def create_nodes_and_clips(self):
        self.node = Node(title="Node 1")
        self.node.save()
        
        self.clip1 = Clip(title="Clip 1")
        self.clip1.save()
        self.clip2 = Clip(title="Clip 2")
        self.clip2.save()
        
        # This setup requires explicite creation of M2M objects
        # node.clips.create & node.clips.add doesn't work
        Propagation(node=self.node, clip=self.clip1).save()
        Propagation(node=self.node, clip=self.clip2).save()
        
        # reload these manually, tests are throwing things off
        self.node = Node.objects.get(pk=self.node.pk)
        self.clip1 = Clip.objects.get(pk=self.clip1.pk)
        self.clip2 = Clip.objects.get(pk=self.clip2.pk)
        
    
    def test_dirtyfields(self):
        """Make sure the dirty fields actually work"""
        self.create_nodes_and_clips()
        self.node.active = False
        self.assertTrue(self.node.is_dirty())
        # check the dirty fields, returning the original state as in the DB
        self.assertEquals(self.node.get_dirty_fields(), {'active': True})
    
    def test_propagation_tracking(self):
        """Check the propagation of changes from node to clips"""
        self.create_nodes_and_clips()
        self.assertEquals(Propagation.changes.to_push().count(), 0)
        
        self.node.title="Changed title"
        self.node.save()
        
        # the clips versions are behind and should be pushed
        self.assertEquals(Propagation.changes.to_push().count(), 2)
        
    def test_no_propagation_when_nothings_changed(self):
        """Nothing should be changed if no fields have changed"""
        self.create_nodes_and_clips()
        self.assertFalse(self.node.is_dirty())
        self.node.save()
        self.assertEquals(Propagation.changes.to_push().count(), 0)
    
    def test_changes_being_propagated(self):
        """Using the History we should be able to see what's changed"""
        self.create_nodes_and_clips()
        self.node.title="Changed Title"
        self.node.save()
        
        # print Propagation.summary_of_changes()
        