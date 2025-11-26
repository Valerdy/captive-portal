# Generated manually for FreeRADIUS tables

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('radius', '0001_initial'),
    ]

    operations = [
        # Create radcheck table - User authentication credentials
        migrations.CreateModel(
            name='RadCheck',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(db_index=True, max_length=64)),
                ('attribute', models.CharField(default='Cleartext-Password', max_length=64)),
                ('op', models.CharField(default=':=', max_length=2)),
                ('value', models.CharField(max_length=253)),
            ],
            options={
                'db_table': 'radcheck',
                'ordering': ['username'],
            },
        ),
        # Create radreply table - User reply attributes
        migrations.CreateModel(
            name='RadReply',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(db_index=True, max_length=64)),
                ('attribute', models.CharField(max_length=64)),
                ('op', models.CharField(default='=', max_length=2)),
                ('value', models.CharField(max_length=253)),
            ],
            options={
                'db_table': 'radreply',
                'ordering': ['username'],
            },
        ),
        # Create radgroupcheck table - Group-level checks
        migrations.CreateModel(
            name='RadGroupCheck',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('groupname', models.CharField(db_index=True, max_length=64)),
                ('attribute', models.CharField(max_length=64)),
                ('op', models.CharField(default=':=', max_length=2)),
                ('value', models.CharField(max_length=253)),
            ],
            options={
                'db_table': 'radgroupcheck',
                'ordering': ['groupname'],
            },
        ),
        # Create radgroupreply table - Group-level replies
        migrations.CreateModel(
            name='RadGroupReply',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('groupname', models.CharField(db_index=True, max_length=64)),
                ('attribute', models.CharField(max_length=64)),
                ('op', models.CharField(default='=', max_length=2)),
                ('value', models.CharField(max_length=253)),
                ('priority', models.IntegerField(default=0)),
            ],
            options={
                'db_table': 'radgroupreply',
                'ordering': ['groupname', 'priority'],
            },
        ),
        # Create radusergroup table - User to group mapping
        migrations.CreateModel(
            name='RadUserGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(db_index=True, max_length=64)),
                ('groupname', models.CharField(db_index=True, max_length=64)),
                ('priority', models.IntegerField(default=0)),
            ],
            options={
                'db_table': 'radusergroup',
                'ordering': ['username', 'priority'],
                'unique_together': {('username', 'groupname')},
            },
        ),
        # Create radpostauth table - Post-authentication logging
        migrations.CreateModel(
            name='RadPostAuth',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(db_index=True, max_length=64)),
                ('pass_field', models.CharField(db_column='pass', max_length=64, verbose_name='pass')),
                ('reply', models.CharField(max_length=32)),
                ('authdate', models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                'db_table': 'radpostauth',
                'ordering': ['-authdate'],
            },
        ),
        # Add indexes for radcheck
        migrations.AddIndex(
            model_name='radcheck',
            index=models.Index(fields=['username', 'attribute'], name='radcheck_username_idx'),
        ),
        # Add indexes for radreply
        migrations.AddIndex(
            model_name='radreply',
            index=models.Index(fields=['username', 'attribute'], name='radreply_username_idx'),
        ),
        # Add indexes for radgroupcheck
        migrations.AddIndex(
            model_name='radgroupcheck',
            index=models.Index(fields=['groupname', 'attribute'], name='radgroupcheck_groupname_idx'),
        ),
        # Add indexes for radgroupreply
        migrations.AddIndex(
            model_name='radgroupreply',
            index=models.Index(fields=['groupname', 'attribute'], name='radgroupreply_groupname_idx'),
        ),
        # Add indexes for radusergroup
        migrations.AddIndex(
            model_name='radusergroup',
            index=models.Index(fields=['username', 'priority'], name='radusergroup_username_idx'),
        ),
        migrations.AddIndex(
            model_name='radusergroup',
            index=models.Index(fields=['groupname'], name='radusergroup_groupname_idx'),
        ),
        # Add indexes for radpostauth
        migrations.AddIndex(
            model_name='radpostauth',
            index=models.Index(fields=['username', '-authdate'], name='radpostauth_username_idx'),
        ),
    ]
