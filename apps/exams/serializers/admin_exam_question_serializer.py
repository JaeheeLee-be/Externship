from rest_framework import serializers

from apps.exams.models import ExamQuestion


class QuestionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamQuestion
        fields = ["exam_id", "question", "prompt", "blank_count", "options_json", "answer", "point", "explanation"]
        read_only_fields = ["exam_id"]

    def validate(self, data):
        if data["point"] <= 0:
            raise serializers.ValidationError("배점은 0보다 작거나 같을 수 없습니다.")
        return data


class QuestionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamQuestion
        fields = [
            "id",
            "exam_id",
            "question",
            "prompt",
            "blank_count",
            "options_json",
            "answer",
            "point",
            "explanation",
        ]
        read_only_fields = ["id", "exam_id"]

    def validate(self, data):
        point = data.get("point")
        if point is not None and point <= 0:
            raise serializers.ValidationError("배점은 0보다 작거나 같을 수 없습니다.")
        return data


class QuestionDeleteResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamQuestion
        fields = [
            "id",
            "exam_id",
        ]
        read_only_fields = ["id", "exam_id"]
