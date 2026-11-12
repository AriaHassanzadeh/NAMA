import django.db.models.deletion
import django.db.models.functions.text
import django.utils.timezone
import market.models
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('slug', models.SlugField(max_length=80, primary_key=True, serialize=False)),
                ('label', models.CharField(max_length=120)),
            ],
            options={
                'ordering': ['slug'],
            },
        ),
        migrations.CreateModel(
            name='Country',
            fields=[
                ('code', models.CharField(max_length=2, primary_key=True, serialize=False)),
                ('label', models.CharField(max_length=120)),
                ('flag', models.CharField(blank=True, max_length=8)),
            ],
            options={
                'ordering': ['code'],
            },
        ),
        migrations.CreateModel(
            name='MediaAsset',
            fields=[
                ('key', models.SlugField(max_length=80, primary_key=True, serialize=False)),
                ('path', models.CharField(max_length=500)),
                ('source_width', models.PositiveIntegerField(blank=True, null=True)),
                ('source_height', models.PositiveIntegerField(blank=True, null=True)),
                ('crop_x', models.PositiveIntegerField(blank=True, null=True)),
                ('crop_y', models.PositiveIntegerField(blank=True, null=True)),
                ('crop_width', models.PositiveIntegerField(blank=True, null=True)),
                ('crop_height', models.PositiveIntegerField(blank=True, null=True)),
                ('media_kind', models.CharField(choices=[('image', 'Image'), ('video', 'Video')], default='image', max_length=12)),
                ('video_url', models.URLField(blank=True, max_length=500, null=True)),
            ],
            options={
                'ordering': ['key'],
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('slug', models.SlugField(allow_unicode=True, max_length=100, primary_key=True, serialize=False)),
                ('label', models.CharField(max_length=120)),
            ],
            options={
                'ordering': ['slug'],
            },
        ),
        migrations.CreateModel(
            name='Shop',
            fields=[
                ('source_kind', models.CharField(choices=[('demo', 'Demo'), ('manual', 'Manual'), ('csv', 'CSV'), ('provider', 'Provider')], default='manual', max_length=16)),
                ('source_reference', models.CharField(blank=True, default='', max_length=500)),
                ('observed_on', models.DateField(blank=True, null=True)),
                ('imported_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('external_id', models.CharField(max_length=100)),
                ('name', models.CharField(max_length=200)),
                ('domain', models.CharField(max_length=253, unique=True)),
                ('initial', models.CharField(blank=True, max_length=8)),
                ('color', models.CharField(default='#e7e7ec', max_length=7)),
                ('created_on', models.DateField(blank=True, null=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='shops', to='market.category')),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='shops', to='market.country')),
            ],
            options={
                'ordering': ['name', 'pk'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('source_kind', models.CharField(choices=[('demo', 'Demo'), ('manual', 'Manual'), ('csv', 'CSV'), ('provider', 'Provider')], default='manual', max_length=16)),
                ('source_reference', models.CharField(blank=True, default='', max_length=500)),
                ('observed_on', models.DateField(blank=True, null=True)),
                ('imported_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('external_id', models.CharField(max_length=100)),
                ('name', models.CharField(max_length=200)),
                ('english_name', models.CharField(blank=True, max_length=200)),
                ('description', models.TextField(blank=True)),
                ('published_on', models.DateField(blank=True, null=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='products', to='market.category')),
                ('primary_media', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products', to='market.mediaasset')),
                ('shop', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='products', to='market.shop')),
            ],
            options={
                'ordering': ['name', 'pk'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ShopMedia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.PositiveIntegerField()),
                ('media', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='shop_placements', to='market.mediaasset')),
                ('shop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gallery', to='market.shop')),
            ],
            options={
                'ordering': ['position', 'pk'],
            },
        ),
        migrations.CreateModel(
            name='ShopMetrics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_kind', models.CharField(choices=[('demo', 'Demo'), ('manual', 'Manual'), ('csv', 'CSV'), ('provider', 'Provider')], default='manual', max_length=16)),
                ('source_reference', models.CharField(blank=True, default='', max_length=500)),
                ('observed_on', models.DateField(blank=True, null=True)),
                ('imported_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('value_kind', models.CharField(choices=[('illustrative', 'Illustrative'), ('observed', 'Observed'), ('estimated', 'Estimated')], default='observed', max_length=16)),
                ('currency', models.CharField(default='USD', max_length=3)),
                ('daily_revenue_estimate_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=16, null=True)),
                ('monthly_visits_count', models.PositiveBigIntegerField(blank=True, null=True)),
                ('growth_30d_percent', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('active_ads_count', models.PositiveIntegerField(blank=True, null=True)),
                ('total_ads_count', models.PositiveIntegerField(blank=True, null=True)),
                ('reported_products_count', models.PositiveIntegerField(blank=True, null=True)),
                ('trend', models.JSONField(blank=True, default=list, validators=[market.models.validate_trend])),
                ('shop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='metrics', to='market.shop')),
            ],
            options={
                'ordering': ['-imported_at', '-pk'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Ad',
            fields=[
                ('source_kind', models.CharField(choices=[('demo', 'Demo'), ('manual', 'Manual'), ('csv', 'CSV'), ('provider', 'Provider')], default='manual', max_length=16)),
                ('source_reference', models.CharField(blank=True, default='', max_length=500)),
                ('observed_on', models.DateField(blank=True, null=True)),
                ('imported_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('external_id', models.CharField(max_length=100)),
                ('platform', models.CharField(choices=[('meta', 'Meta'), ('tiktok', 'TikTok'), ('youtube', 'YouTube')], max_length=16)),
                ('format', models.CharField(choices=[('image', 'Image'), ('video', 'Video')], max_length=12)),
                ('title', models.CharField(max_length=250)),
                ('copy', models.TextField(blank=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='ads', to='market.category')),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='ads', to='market.country')),
                ('primary_media', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ads', to='market.mediaasset')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='ads', to='market.product')),
                ('tags', models.ManyToManyField(blank=True, related_name='ads', to='market.tag')),
            ],
            options={
                'ordering': ['title', 'pk'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AdMetrics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_kind', models.CharField(choices=[('demo', 'Demo'), ('manual', 'Manual'), ('csv', 'CSV'), ('provider', 'Provider')], default='manual', max_length=16)),
                ('source_reference', models.CharField(blank=True, default='', max_length=500)),
                ('observed_on', models.DateField(blank=True, null=True)),
                ('imported_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('value_kind', models.CharField(choices=[('illustrative', 'Illustrative'), ('observed', 'Observed'), ('estimated', 'Estimated')], default='observed', max_length=16)),
                ('currency', models.CharField(default='USD', max_length=3)),
                ('active_days', models.PositiveIntegerField(blank=True, null=True)),
                ('reach_count', models.PositiveBigIntegerField(blank=True, null=True)),
                ('likes_count', models.PositiveBigIntegerField(blank=True, null=True)),
                ('spend_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=16, null=True)),
                ('roas_ratio', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('ctr_percent', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('variant_count', models.PositiveIntegerField(blank=True, null=True)),
                ('trend', models.JSONField(blank=True, default=list, validators=[market.models.validate_trend])),
                ('ad', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='metrics', to='market.ad')),
            ],
            options={
                'ordering': ['-imported_at', '-pk'],
                'abstract': False,
                'constraints': [models.UniqueConstraint(fields=('ad', 'source_kind', 'source_reference'), name='market_ad_metrics_source_unique'), models.CheckConstraint(condition=models.Q(('spend_amount__gte', 0)), name='market_ad_spend_nonnegative'), models.CheckConstraint(condition=models.Q(('roas_ratio__gte', 0)), name='market_ad_roas_nonnegative'), models.CheckConstraint(condition=models.Q(('ctr_percent__gte', 0), ('ctr_percent__lte', 100)), name='market_ad_ctr_range')],
            },
        ),
        migrations.CreateModel(
            name='ProductMetrics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_kind', models.CharField(choices=[('demo', 'Demo'), ('manual', 'Manual'), ('csv', 'CSV'), ('provider', 'Provider')], default='manual', max_length=16)),
                ('source_reference', models.CharField(blank=True, default='', max_length=500)),
                ('observed_on', models.DateField(blank=True, null=True)),
                ('imported_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('value_kind', models.CharField(choices=[('illustrative', 'Illustrative'), ('observed', 'Observed'), ('estimated', 'Estimated')], default='observed', max_length=16)),
                ('currency', models.CharField(default='USD', max_length=3)),
                ('price_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=16, null=True)),
                ('active_ads_count', models.PositiveIntegerField(blank=True, null=True)),
                ('growth_percent', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='metrics', to='market.product')),
            ],
            options={
                'ordering': ['-imported_at', '-pk'],
                'abstract': False,
                'constraints': [models.UniqueConstraint(fields=('product', 'source_kind', 'source_reference'), name='market_product_metrics_source_unique'), models.CheckConstraint(condition=models.Q(('price_amount__gte', 0)), name='market_product_price_nonnegative'), models.CheckConstraint(condition=models.Q(('growth_percent__gte', -100)), name='market_product_growth_minimum')],
            },
        ),
        migrations.AddConstraint(
            model_name='shop',
            constraint=models.UniqueConstraint(fields=('source_kind', 'external_id'), name='market_shop_source_external_unique'),
        ),
        migrations.AddConstraint(
            model_name='shop',
            constraint=models.CheckConstraint(condition=models.Q(('domain', django.db.models.functions.text.Lower(django.db.models.functions.text.Trim('domain'))), models.Q(('domain__endswith', '.'), _negated=True)), name='market_shop_domain_normalized'),
        ),
        migrations.AddConstraint(
            model_name='product',
            constraint=models.UniqueConstraint(fields=('source_kind', 'external_id'), name='market_product_source_external_unique'),
        ),
        migrations.AddConstraint(
            model_name='shopmedia',
            constraint=models.UniqueConstraint(fields=('shop', 'position'), name='market_shop_media_position_unique'),
        ),
        migrations.AddConstraint(
            model_name='shopmedia',
            constraint=models.UniqueConstraint(fields=('shop', 'media'), name='market_shop_media_asset_unique'),
        ),
        migrations.AddConstraint(
            model_name='shopmetrics',
            constraint=models.UniqueConstraint(fields=('shop', 'source_kind', 'source_reference'), name='market_shop_metrics_source_unique'),
        ),
        migrations.AddConstraint(
            model_name='shopmetrics',
            constraint=models.CheckConstraint(condition=models.Q(('daily_revenue_estimate_amount__gte', 0)), name='market_shop_revenue_nonnegative'),
        ),
        migrations.AddConstraint(
            model_name='shopmetrics',
            constraint=models.CheckConstraint(condition=models.Q(('growth_30d_percent__gte', -100)), name='market_shop_growth_minimum'),
        ),
        migrations.AddConstraint(
            model_name='ad',
            constraint=models.UniqueConstraint(fields=('source_kind', 'external_id'), name='market_ad_source_external_unique'),
        ),
        migrations.AddConstraint(
            model_name='ad',
            constraint=models.CheckConstraint(condition=models.Q(('platform__in', ['meta', 'tiktok', 'youtube'])), name='market_ad_platform_valid'),
        ),
        migrations.AddConstraint(
            model_name='ad',
            constraint=models.CheckConstraint(condition=models.Q(('format__in', ['image', 'video'])), name='market_ad_format_valid'),
        ),
    ]
