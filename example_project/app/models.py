from django.db import models
from django.db.models import F
from dirtyfields import DirtyFieldsMixin
from history.models import HistoricalRecords

class Node(DirtyFieldsMixin, models.Model):
    """
    A node is an entity in the network to which any associated data can be
    pushed. In this contrived example, a Clip is the only associated data
    possible.
    """
    title = models.CharField(max_length=255)
    clips = models.ManyToManyField('Clip', through='Propagation')
    active = models.BooleanField(default=True)
    # internal MVCC
    version = models.IntegerField(default=0)
    history = HistoricalRecords()
    
    def __unicode__(self):
        return "<Node %s@v%s>" % (self.title, self.version)
    
    def save(self, *args, **kwargs):
        if self.is_dirty():
            super(Node, self).save(*args, **kwargs)
            # update the versioning based on the DBs current value of the field
            # hopefully avoid some nasty race conditions
            Node.objects.filter(pk=self.pk).update(version=F('version') + 1)
            # Update the propagation object, have Django do the DB lookup through
            # a join and fill in that value.
        
            # Here be dragons
            saved_node = Node.objects.get(pk=self.pk)
            Propagation.objects.filter(node=self).update(master_version=saved_node.version)

class PropagationManager(models.Manager):
    def to_push(self):
        return self.get_query_set().extra(where=["master_version > slave_version"])
    
    def to_pull(self):
        return self.get_query_set().extra(where=["slave_version > master_version"])

class Propagation(models.Model):
    node = models.ForeignKey('Node')
    clip = models.ForeignKey('Clip')    
    # keep track of which version is where.
    master_version = models.IntegerField(default=0)
    slave_version = models.IntegerField(default=0)
    
    objects = models.Manager()
    changes = PropagationManager()
    
    @classmethod
    def summary_of_changes(klass):
        for change in klass.changes.to_push():
            master_version = change.node
            historical_slave_version = master_version.history.get(version=change.slave_version)
            slave_version = historical_slave_version.history_object
            print "Got a change:"
            print "\tMaster version number is: %s" % change.master_version
            print "\tMaster field values: %s" % master_version._as_dict()
            print "\tSlave version number is: %s" % change.slave_version
            print "\tSlave field values: %s" % slave_version._as_dict()
        

class Clip(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    active = models.BooleanField(default=True)
    # internal MVCC
    version = models.IntegerField(default=0)
    
    history = HistoricalRecords()
    
    def __unicode__(self):
        return "<Clip %s@v%s>" % (self.title, self.version)
    
    def save(self, *args, **kwargs):
        self.version += 1
        super(Clip, self).save(*args, **kwargs)

