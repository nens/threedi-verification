# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'TestRun'
        db.create_table(u'threedi_verification_testrun', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('test_case', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['threedi_verification.TestCase'])),
            ('library_version', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['threedi_verification.LibraryVersion'])),
            ('run_started', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('duration', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'threedi_verification', ['TestRun'])

        # Adding model 'TestCase'
        db.create_table(u'threedi_verification_testcase', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('filename', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'threedi_verification', ['TestCase'])

        # Adding model 'LibraryVersion'
        db.create_table(u'threedi_verification_libraryversion', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'threedi_verification', ['LibraryVersion'])


    def backwards(self, orm):
        # Deleting model 'TestRun'
        db.delete_table(u'threedi_verification_testrun')

        # Deleting model 'TestCase'
        db.delete_table(u'threedi_verification_testcase')

        # Deleting model 'LibraryVersion'
        db.delete_table(u'threedi_verification_libraryversion')


    models = {
        u'threedi_verification.libraryversion': {
            'Meta': {'ordering': "['-last_modified']", 'object_name': 'LibraryVersion'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        u'threedi_verification.testcase': {
            'Meta': {'ordering': "['filename']", 'object_name': 'TestCase'},
            'filename': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        u'threedi_verification.testrun': {
            'Meta': {'ordering': "['-run_started']", 'object_name': 'TestRun'},
            'duration': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'library_version': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['threedi_verification.LibraryVersion']"}),
            'run_started': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'test_case': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['threedi_verification.TestCase']"})
        }
    }

    complete_apps = ['threedi_verification']