# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'TestRun.has_crashed'
        db.add_column(u'threedi_verification_testrun', 'has_crashed',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'TestRun.result'
        db.add_column(u'threedi_verification_testrun', 'result',
                      self.gf('jsonfield.fields.JSONField')(default={}),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'TestRun.has_crashed'
        db.delete_column(u'threedi_verification_testrun', 'has_crashed')

        # Deleting field 'TestRun.result'
        db.delete_column(u'threedi_verification_testrun', 'result')


    models = {
        u'threedi_verification.libraryversion': {
            'Meta': {'ordering': "[u'-last_modified']", 'object_name': 'LibraryVersion'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'unique': 'True'}),
            'num_test_cases': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'threedi_verification.testcase': {
            'Meta': {'ordering': "[u'filename']", 'object_name': 'TestCase'},
            'filename': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'threedi_verification.testrun': {
            'Meta': {'ordering': "[u'-run_started']", 'object_name': 'TestRun'},
            'duration': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'has_crashed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'library_version': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'test_runs'", 'to': u"orm['threedi_verification.LibraryVersion']"}),
            'report': ('jsonfield.fields.JSONField', [], {'default': '{}'}),
            'result': ('jsonfield.fields.JSONField', [], {'default': '{}'}),
            'run_started': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'test_case': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'test_runs'", 'to': u"orm['threedi_verification.TestCase']"})
        }
    }

    complete_apps = ['threedi_verification']