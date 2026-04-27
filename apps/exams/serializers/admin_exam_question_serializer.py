from rest_framework import serializers

from apps.exams.models import ExamQuestion


class PointValidateMixin:
    def validate_point(self, value):
        if value <= 0:
            raise serializers.ValidationError("배점은 0보다 작거나 같을 수 없습니다.")
        return value


class QuestionCreateSerializer(PointValidateMixin, serializers.ModelSerializer):
    class Meta:
        model = ExamQuestion
        fields = ["question", "type", "prompt", "blank_count", "options_json", "answer", "point", "explanation"]


class QuestionUpdateSerializer(PointValidateMixin, serializers.ModelSerializer):
    point = serializers.IntegerField(required=False)

    class Meta:
        model = ExamQuestion
        fields = [
            "question",
            "type",
            "prompt",
            "blank_count",
            "options_json",
            "answer",
            "point",
            "explanation",
        ]


class QuestionDeleteResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamQuestion
        fields = [
            "id",
            "exam_id",
        ]
        read_only_fields = ["id", "exam_id"]


class QuestionResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamQuestion
        fields = ["question", "type", "prompt", "blank_count", "options_json", "answer", "point", "explanation"]


class QuestionUpdateResponseSerializer(QuestionResponseSerializer):
    class Meta(QuestionResponseSerializer.Meta):
        fields = ["id"] + QuestionResponseSerializer.Meta.fields


class QuestionCreateResponseSerializer(QuestionResponseSerializer):
    class Meta(QuestionResponseSerializer.Meta):
        fields = ["exam_id"] + QuestionResponseSerializer.Meta.fields
