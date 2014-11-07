# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ImportHistory'
        db.create_table(u'dip_importhistory', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('job', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dip.Job'])),
            ('timestamp', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('import_rows', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('ignore_row', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('status', self.gf('django.db.models.fields.SmallIntegerField')()),
            ('import_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
        ))
        db.send_create_signal(u'dip', ['ImportHistory'])

        # Adding model 'Job'
        db.create_table(u'dip_job', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'import_jobs', to=orm['auth.User'])),
            ('database', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Database'])),
            ('table', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('dip_id', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('dip_alias', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('interval', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('fields', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'dip', ['Job'])


    def backwards(self, orm):
        # Deleting model 'ImportHistory'
        db.delete_table(u'dip_importhistory')

        # Deleting model 'Job'
        db.delete_table(u'dip_job')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'core.database': {
            'Meta': {'object_name': 'Database'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'dbs'", 'to': u"orm['auth.User']"}),
            'engine': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'host': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'port': ('django.db.models.fields.PositiveIntegerField', [], {'default': '3306'}),
            'user': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'dip.importhistory': {
            'Meta': {'object_name': 'ImportHistory'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignore_row': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'import_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'import_rows': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'job': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dip.Job']"}),
            'status': ('django.db.models.fields.SmallIntegerField', [], {}),
            'timestamp': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        u'dip.job': {
            'Meta': {'object_name': 'Job'},
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'import_jobs'", 'to': u"orm['auth.User']"}),
            'database': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Database']"}),
            'dip_alias': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'dip_id': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'fields': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interval': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'table': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['dip']