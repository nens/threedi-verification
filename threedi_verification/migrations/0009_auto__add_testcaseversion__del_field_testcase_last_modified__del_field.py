# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'TestCaseVersion'
        db.create_table(u'threedi_verification_testcaseversion', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('test_case', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'test_case_versions', to=orm['threedi_verification.TestCase'])),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal(u'threedi_verification', ['TestCaseVersion'])

        # Deleting field 'TestCase.last_modified'
        db.delete_column(u'threedi_verification_testcase', 'last_modified')

        # Deleting field 'TestRun.test_case'
        db.delete_column(u'threedi_verification_testrun', 'test_case_id')

        # Adding field 'TestRun.test_case_version'
        db.add_column(u'threedi_verification_testrun', 'test_case_version',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=1, related_name=u'test_runs', to=orm['threedi_verification.TestCaseVersion']),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting model 'TestCaseVersion'
        db.delete_table(u'threedi_verification_testcaseversion')


        # User chose to not deal with backwards NULL issues for 'TestCase.last_modified'
        raise RuntimeError("Cannot reverse this migration. 'TestCase.last_modified' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'TestCase.last_modified'
        db.add_column(u'threedi_verification_testcase', 'last_modified',
                      self.gf('django.db.models.fields.DateTimeField')(),
                      keep_default=False)


        # User chose to not deal with backwards NULL issues for 'TestRun.test_case'
        raise RuntimeError("Cannot reverse this migration. 'TestRun.test_case' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'TestRun.test_case'
        db.add_column(u'threedi_verification_testrun', 'test_case',
                      self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'test_runs', to=orm['threedi_verification.TestCase']),
                      keep_default=False)

        # Deleting field 'TestRun.test_case_version'
        db.delete_column(u'threedi_verification_testrun', 'test_case_version_id')


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
            'info': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
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