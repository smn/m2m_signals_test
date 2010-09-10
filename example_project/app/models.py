from django.db import models

class Node(models.Model):
    title = models.CharField(max_length=255)
    clips = models.ManyToManyField('Clip', through='Propagation')
    version = models.IntegerField(default=0)
    
    def save(self, *args, **kwargs):
        self.version += 1
        super(Node, self).save(*args, **kwargs)

class Propagation(models.Model):
    node = models.ForeignKey('Node')
    clip = models.ForeignKey('Clip')    
    master_version = models.IntegerField(default=0)
    slave_version = models.IntegerField(default=0)

class Clip(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    version = models.IntegerField(default=0)
    
    def save(self, *args, **kwargs):
        self.version += 1
        super(Clip, self).save(*args, **kwargs)

