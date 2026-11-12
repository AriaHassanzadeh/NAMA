from django.db import transaction
from rest_framework import serializers

from .models import ProjectBrief, SavedReport, Workspace


class WorkspaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workspace
        fields = ["id", "name", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    @transaction.atomic
    def create(self, validated_data):
        workspace = super().create(validated_data)
        ProjectBrief.objects.create(workspace=workspace)
        return workspace


class ProjectBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectBrief
        fields = [
            "id", "workspace", "idea", "customer_description", "audience", "market", "budget_band",
            "goal", "goal_note", "completed_at", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "workspace", "completed_at", "created_at", "updated_at"]

    def update(self, instance, validated_data):
        if any(getattr(instance, key) != value for key, value in validated_data.items()):
            instance.completed_at = None
        return super().update(instance, validated_data)

    def validate(self, attrs):
        if self.context.get("complete"):
            value = lambda key: attrs.get(key, getattr(self.instance, key, ""))
            errors = {}
            if len(value("idea").strip()) < 5:
                errors["idea"] = "Describe the idea using at least five characters."
            if not value("audience") and len(value("customer_description").strip()) < 3:
                errors["customer_description"] = "Select an audience or describe the customer."
            if not value("goal"):
                errors["goal"] = "Choose a project goal."
            if errors:
                raise serializers.ValidationError(errors)
        return attrs


class SavedReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedReport
        fields = ["id", "workspace", "name", "report_type", "period_days", "filters", "created_at", "updated_at"]
        read_only_fields = ["id", "workspace", "created_at", "updated_at"]

    def validate_filters(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Filters must be an object.")
        if "page" in value or "page_size" in value:
            raise serializers.ValidationError("Report filters do not contain pagination.")
        return value

    def validate(self, attrs):
        from market.api import FILTERS
        report_type = attrs.get("report_type", getattr(self.instance, "report_type", "ads"))
        values = attrs.get("filters", getattr(self.instance, "filters", {}))
        validator = FILTERS[report_type](data=values)
        validator.is_valid(raise_exception=True)
        if "filters" in attrs:
            attrs["filters"] = {key: validator.data[key] for key in values}
        return attrs


class ShopWatchInputSerializer(serializers.Serializer):
    enabled = serializers.BooleanField(default=True)
