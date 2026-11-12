import uuid

from django.conf import settings
from django.db import models


class TimestampedModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Workspace(TimestampedModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="workspaces")
    name = models.CharField(max_length=160)

    class Meta:
        ordering = ["-created_at", "id"]

    def __str__(self):
        return self.name


class ProjectBrief(TimestampedModel):
    class Audience(models.TextChoices):
        CONSUMER = "consumer", "Consumer"
        BUSINESS = "business", "Business"
        BOTH = "both", "Both"

    class Goal(models.TextChoices):
        MARKET = "market", "Market"
        COMPETITORS = "competitors", "Competitors"
        OPPORTUNITY = "opportunity", "Opportunity"

    workspace = models.OneToOneField(Workspace, on_delete=models.CASCADE, related_name="brief")
    idea = models.TextField(blank=True, max_length=4000)
    customer_description = models.TextField(blank=True, max_length=2000)
    audience = models.CharField(max_length=16, choices=Audience.choices, blank=True)
    market = models.CharField(max_length=120, blank=True)
    budget_band = models.CharField(max_length=120, blank=True)
    goal = models.CharField(max_length=16, choices=Goal.choices, blank=True)
    goal_note = models.TextField(blank=True, max_length=2000)
    completed_at = models.DateTimeField(null=True, blank=True)


class SavedAd(TimestampedModel):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="saved_ads")
    ad = models.ForeignKey("market.Ad", on_delete=models.CASCADE, related_name="bookmarks")

    class Meta:
        ordering = ["-created_at", "id"]
        constraints = [models.UniqueConstraint(fields=["workspace", "ad"], name="unique_saved_ad")]


class SavedProduct(TimestampedModel):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="saved_products")
    product = models.ForeignKey("market.Product", on_delete=models.CASCADE, related_name="bookmarks")

    class Meta:
        ordering = ["-created_at", "id"]
        constraints = [models.UniqueConstraint(fields=["workspace", "product"], name="unique_saved_product")]


class SavedShop(TimestampedModel):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="saved_shops")
    shop = models.ForeignKey("market.Shop", on_delete=models.CASCADE, related_name="bookmarks")

    class Meta:
        ordering = ["-created_at", "id"]
        constraints = [models.UniqueConstraint(fields=["workspace", "shop"], name="unique_saved_shop")]


class ShopWatch(TimestampedModel):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="shop_watches")
    shop = models.ForeignKey("market.Shop", on_delete=models.CASCADE, related_name="watch_preferences")
    enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at", "id"]
        constraints = [models.UniqueConstraint(fields=["workspace", "shop"], name="unique_shop_watch")]


class SavedReport(TimestampedModel):
    class ReportType(models.TextChoices):
        ADS = "ads", "Ads"
        PRODUCTS = "products", "Products"
        SHOPS = "shops", "Shops"

    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="saved_reports")
    name = models.CharField(max_length=160)
    report_type = models.CharField(max_length=16, choices=ReportType.choices)
    period_days = models.PositiveSmallIntegerField(choices=[(7, "7"), (30, "30"), (90, "90")], default=30)
    filters = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at", "id"]
        constraints = [models.CheckConstraint(condition=models.Q(period_days__in=[7, 30, 90]), name="report_supported_period")]
