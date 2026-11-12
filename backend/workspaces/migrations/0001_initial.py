import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('market', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Workspace',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=160)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='workspaces', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at', 'id'],
            },
        ),
        migrations.CreateModel(
            name='ProjectBrief',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('idea', models.TextField(blank=True, max_length=4000)),
                ('customer_description', models.TextField(blank=True, max_length=2000)),
                ('audience', models.CharField(blank=True, choices=[('consumer', 'Consumer'), ('business', 'Business'), ('both', 'Both')], max_length=16)),
                ('market', models.CharField(blank=True, max_length=120)),
                ('budget_band', models.CharField(blank=True, max_length=120)),
                ('goal', models.CharField(blank=True, choices=[('market', 'Market'), ('competitors', 'Competitors'), ('opportunity', 'Opportunity')], max_length=16)),
                ('goal_note', models.TextField(blank=True, max_length=2000)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('workspace', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='brief', to='workspaces.workspace')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ShopWatch',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('enabled', models.BooleanField(default=True)),
                ('shop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='watch_preferences', to='market.shop')),
                ('workspace', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shop_watches', to='workspaces.workspace')),
            ],
            options={
                'ordering': ['-created_at', 'id'],
                'constraints': [models.UniqueConstraint(fields=('workspace', 'shop'), name='unique_shop_watch')],
            },
        ),
        migrations.CreateModel(
            name='SavedShop',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('shop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bookmarks', to='market.shop')),
                ('workspace', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saved_shops', to='workspaces.workspace')),
            ],
            options={
                'ordering': ['-created_at', 'id'],
                'constraints': [models.UniqueConstraint(fields=('workspace', 'shop'), name='unique_saved_shop')],
            },
        ),
        migrations.CreateModel(
            name='SavedReport',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=160)),
                ('report_type', models.CharField(choices=[('ads', 'Ads'), ('products', 'Products'), ('shops', 'Shops')], max_length=16)),
                ('period_days', models.PositiveSmallIntegerField(choices=[(7, '7'), (30, '30'), (90, '90')], default=30)),
                ('filters', models.JSONField(blank=True, default=dict)),
                ('workspace', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saved_reports', to='workspaces.workspace')),
            ],
            options={
                'ordering': ['-created_at', 'id'],
                'constraints': [models.CheckConstraint(condition=models.Q(('period_days__in', [7, 30, 90])), name='report_supported_period')],
            },
        ),
        migrations.CreateModel(
            name='SavedProduct',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bookmarks', to='market.product')),
                ('workspace', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saved_products', to='workspaces.workspace')),
            ],
            options={
                'ordering': ['-created_at', 'id'],
                'constraints': [models.UniqueConstraint(fields=('workspace', 'product'), name='unique_saved_product')],
            },
        ),
        migrations.CreateModel(
            name='SavedAd',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('ad', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bookmarks', to='market.ad')),
                ('workspace', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saved_ads', to='workspaces.workspace')),
            ],
            options={
                'ordering': ['-created_at', 'id'],
                'constraints': [models.UniqueConstraint(fields=('workspace', 'ad'), name='unique_saved_ad')],
            },
        ),
    ]
