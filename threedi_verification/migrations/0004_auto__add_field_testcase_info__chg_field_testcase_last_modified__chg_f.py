# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'TestCase.info'
        db.add_column(u'threedi_verification_testcase', 'info',
                      self.gf('django.db.models.fields.TextField')(null=True, blank=True),
                      keep_default=False)


        # Changing field 'TestCase.last_modified'
        db.alter_column(u'threedi_verification_testcase', 'last_modified', self.gf('django.db.models.fields.DateTimeField')())

        # Changing field 'LibraryVersion.last_modified'
        db.alter_column(u'threedi_verification_libraryversion', 'last_modified', self.gf('django.db.models.fields.DateTimeField')(unique=True))

        # Changing field 'TestRun.run_started'
        db.alter_column(u'threedi_verification_testrun', 'run_started', self.gf('django.db.models.fields.DateTimeField')())

    def backwards(self, orm):
        # Deleting field 'TestCase.info'
        db.delete_column(u'threedi_verification_testcase', 'info')


        # Changing field 'TestCase.last_modified'
        db.alter_column(u'threedi_verification_testcase', 'last_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'LibraryVersion.last_modified'
        db.alter_column(u'threedi_verification_libraryversion', 'last_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, unique=True))

        # Changing field 'TestRun.run_started'
        db.alter_column(u'threedi_verification_testrun', 'run_started', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

    models = {
        u'threedi_verification.libraryversion': {
            'Meta': {'ordering': "[u'-last_modified']", 'object_name': 'LibraryVersion'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'unique': 'True'})
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
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'library_version': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['threedi_verification.LibraryVersion']"}),
            'run_started': ('django.db.models.fields.DateTimeField', [], {}),
            'test_case': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['threedi_verification.TestCase']"})
        }
    }

    complete_apps = ['threedi_verification']