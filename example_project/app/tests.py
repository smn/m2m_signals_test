from django.test import TestCase
from app.models import Node, Propagation


class AppTestCase(TestCase):
    
    def setUp(self):
        pass
    
    def tearDown(self):
        # Dump the data that's in the node1 database
        print "Summary of what's available in database 2"
        print "=" * 50
        for node in Node.objects.all().using("node1"):
            print "Record:", node, "Fields:", node._as_dict()
        
    
    def create_master_and_slaves(self):
        # master
        self.node = Node(title="Node 1")
        self.node.save(propagate=True)
        
        # slaves
        self.slave_1 = Node(title="Slave 1")
        self.slave_1.save(propagate=False)
        self.slave_2 = Node(title="Slave 2")
        self.slave_2.save(propagate=False)
        
        # This setup requires explicite creation of M2M objects
        # node.slaves.create & node.slaves.add doesn't work
        Propagation(master=self.node, slave=self.slave_1).save()
        Propagation(master=self.node, slave=self.slave_2).save()
        
        # reload these manually, tests are throwing things off
        self.node = Node.objects.get(pk=self.node.pk)
        self.slave_1 = Node.objects.get(pk=self.slave_1.pk)
        self.slave_2 = Node.objects.get(pk=self.slave_2.pk)
        
    
    def test_dirtyfields(self):
        """Make sure the dirty fields actually work"""
        self.create_master_and_slaves()
        self.node.active = False
        self.assertTrue(self.node.is_dirty())
        # check the dirty fields, returning the original state as in the DB
        self.assertEquals(self.node.get_dirty_fields(), {'active': True})
    
    def test_propagation_tracking(self):
        """Check the propagation of changes from master to slaves"""
        self.create_master_and_slaves()
        self.assertEquals(Propagation.changes.to_push().count(), 0)
        
        self.node.title="Changed title"
        self.node.save(propagate=True)
        
        # the slave versions are behind and should be pushed
        self.assertEquals(Propagation.changes.to_push().count(), 2)
        
    def test_no_propagation_when_nothings_changed(self):
        """Nothing should be changed if no fields have changed"""
        self.create_master_and_slaves()
        self.assertFalse(self.node.is_dirty())
        self.node.save(propagate=True)
        self.assertEquals(Propagation.changes.to_push().count(), 0)
    
    def test_changes_being_propagated(self):
        """Using the History we should be able to see what's changed"""
        self.create_master_and_slaves()
        self.node.title="Changed Title"
        self.node.save(propagate=True)
        