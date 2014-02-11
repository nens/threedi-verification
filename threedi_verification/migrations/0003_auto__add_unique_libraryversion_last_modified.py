# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding unique constraint on 'LibraryVersion', fields ['last_modified']
        db.create_unique(u'threedi_verification_libraryversion', ['last_modified'])


    def backwards(self, orm):
        # Removing unique constraint on 'LibraryVersion', fields ['last_modified']
        db.delete_unique(u'threedi_verification_libraryversion', ['last_modified'])


    models = {
        u'threedi_verification.libraryversion': {
            'Meta': {'ordering': "['-last_modified']", 'object_name': 'LibraryVersion'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'unique': 'True', 'blank': 'True'})
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