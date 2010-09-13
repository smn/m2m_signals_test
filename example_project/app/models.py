from django.db import models
from django.db.models import F
from django.db.models.signals import post_save
from dirtyfields import DirtyFieldsMixin
from history.models import HistoricalRecords

class Node(DirtyFieldsMixin, models.Model):
    """
    A node is an entity in the network to which any associated data can be
    pushed. In this contrived example, another Node is the only associated data
    possible.
    """
    # these can be arbitrary fields
    title = models.CharField(max_length=255)
    slaves = models.ManyToManyField('Node', through='Propagation')
    active = models.BooleanField(default=True)
    # internal MVCC counter
    version = models.IntegerField(default=0)
    
    # track history of the model
    history = HistoricalRecords()
    
    def __unicode__(self):
        return "<Node %s@v%s>" % (self.title, self.version)
    
    def save(self, *args, **kwargs):
        # only save if our state has actually changed
        if self.is_dirty():
            # check if we're supposed to propagate this changes to other nodes
            # or if this save() is considered a final destination, by default
            # do not do this
            propagate = kwargs.pop('propagate', False)
            
            # first save the record
            super(Node, self).save(*args, **kwargs)
            
            if propagate:
                # Update the versioning based on the DBs current value of the field
                # hopefully avoid some nasty race conditions, it's slightly ugly
                # since I'm doing a filter that will always only return a single record
                Node.objects.filter(pk=self.pk).update(version=F('version') + 1)
            
                # *HERE BE DRAGONS*
                # Update the propagation object, get whatever version our database
                # thinking the previous version + 1 is. Doing all this hoopla
                # to prevent nasty race conditions, hopefully.
                saved_node = Node.objects.get(pk=self.pk)
                for propagation in Propagation.objects.filter(master=self):
                    propagation.master_version = saved_node.version
                    # make sure we do an actual save() here so the 
                    # signals are triggered
                    propagation.save()
            
        

class PropagationManager(models.Manager):
    def to_push(self):
        return self.get_query_set().extra(where=["master_version > slave_version"])
    

class Propagation(models.Model):
    master = models.ForeignKey('Node', related_name='master_set')
    slave = models.ForeignKey('Node', related_name='slave_set')
    # keep track of which version is where, could do a join but
    # this is cheaper.
    master_version = models.IntegerField(default=0)
    slave_version = models.IntegerField(default=0)
    
    objects = models.Manager()
    changes = PropagationManager()
    
    def __unicode__(self):
        return "<Propagation of Node:%s v%s -> v%s >" % (
            self.node.pk,
            self.master_version,
            self.slave_version
        )
    
    @classmethod
    def summary_of_changes(klass):
        log = []
        for change in klass.changes.to_push():
            master_version = change.master
            historical_slave_version = master_version.history.get(version=change.slave_version)
            slave_version = historical_slave_version.history_object
            log.extend([
                "Got a change:",
                "\tMaster version number is: %s" % change.master_version,
                "\t\tfield values: %s" % master_version._as_dict(),
                "\tSlave version number is: %s" % change.slave_version,
                "\t\tfield values: %s" % slave_version._as_dict(),
            ])
            
            slave = change.slave
            # _as_dict() is provided by dirtyfields
            for field, value in change.master._as_dict().items():
                setattr(slave, field, value)
            # saving the slave, note the propagate=False keyword
            # added, it avoids crazy recursive signal calling
            slave.save(using="node1", propagate=False)
                
        return '\n'.join(log)

def print_change_summary(sender, **kwargs):
    print Propagation.summary_of_changes()

post_save.connect(print_change_summary, sender=Propagation)