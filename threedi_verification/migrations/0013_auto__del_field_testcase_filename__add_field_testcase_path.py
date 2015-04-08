# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Rename field 'TestCase.filename' to 'TestCase.path'
        db.rename_column(u'threedi_verification_testcase', 'filename', 'path')


    def backwards(self, orm):
        # Rename field  'TestCase.path' to 'TestCase.filename'
        db.rename_column(u'threedi_verification_testcase', 'path', 'filename')


    models = {
        u'threedi_verification.libraryversion': {
            'Meta': {'ordering': "[u'-last_modified']", 'object_name': 'LibraryVersion'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'unique': 'True'}),
            'library': ('django.db.models.fields.CharField', [], {'default': "u'SUBG'", 'max_length': '4'}),
            'num_test_cases': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'threedi_verification.testcase': {
            'Meta': {'ordering': "[u'path']", 'object_name': 'TestCase'},
            'path': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'has_csv': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'library': ('django.db.models.fields.CharField', [], {'default': "u'SUBG'", 'max_length': '4'}),
        },
        u'threedi_verification.testcaseversion': {
            'Meta': {'ordering': "[u'test_case', u'last_modified']", 'object_name': 'TestCaseVersion'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {}),
            'test_case': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'test_case_versions'", 'to': u"orm['threedi_verification.TestCase']"})
        },
        u'threedi_verification.testrun': {
            'Meta': {'ordering': "[u'-run_started']", 'object_name': 'TestRun'},
            'duration': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'library_version': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'test_runs'", 'to': u"orm['threedi_verification.LibraryVersion']"}),
            'report': ('jsonfield.fields.JSONField', [], {'default': '{}'}),
            'run_started': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'test_case_version': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'test_runs'", 'to': u"orm['threedi_verification.TestCaseVersion']"})
        }
    }

    complete_apps = ['threedi_verification']
