from typing import Any

from rest_framework import serializers

from apps.exams.models import ExamSubmission, Exam, ExamQuestion


class ExamNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = ["id", "title", "thumbnail_img_url"]
        read_only_fields = ["id", "title", "thumbnail_img_url"]

class QuestionsNestedSerializer(serializers.ModelSerializer):
    options = serializers.JSONField(required=False, source="options_json")
    is_correct = serializers.SerializerMethodField()
    submitted_answer = serializers.SerializerMethodField()

    def get_is_correct(self, obj):
        answer_json = self.context.get("answer_json", {})
        return answer_json.get(str(obj.id), []) == obj.answer

    def get_submitted_answer(self, obj):
        answer_json = self.context.get("answer_json", {})
        return answer_json.get(str(obj.id), [])


    class Meta:
        model = ExamQuestion
        fields = [
            "id",
            "question",
            "prompt",
            "blank_count",
            "options",
            "type",
            "answer",
            "point",
            "explanation",
            "is_correct",
            "submitted_answer",
        ]




class UserExamSubmissionGetSerializer(serializers.ModelSerializer[ExamSubmission]):
    exam = ExamNestedSerializer(source="deployment.exam")
    questions = serializers.SerializerMethodField()
    total_score = serializers.SerializerMethodField()
    submitted_at = serializers.DateTimeField(source="created_at")
    elapsed_time = serializers.SerializerMethodField()

    def get_questions(self, obj):
        queryset = ExamQuestion.objects.filter(exam=obj.deployment.exam)
        return QuestionsNestedSerializer(
            queryset,
            many=True,
            context={"answer_json": obj.answer_json}
        ).data

    def get_total_score(self, obj):
        questions = obj.deployment.questions_snapshot_json
        return sum(q.get("point", 0) for q in questions)

    def get_elapsed_time(self, obj):
        return int((obj.created_at - obj.started_at).total_seconds())



    class Meta:
        model = ExamSubmission
        fields = [
            "id",
            "submitter_id",
            "deployment_id",
            "exam",
            "questions",
            "cheating_count",
            "score",
            "total_score",
            "correct_answer_count",
            "elapsed_time",
            "started_at",
            "submitted_at",
        ]



class QuestionsSchemaSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    question = serializers.CharField()
    prompt = serializers.CharField()
    blank_count = serializers.IntegerField()
    options = serializers.ListField(child=serializers.CharField())
    type = serializers.CharField()
    answer = serializers.ListField(child=serializers.CharField())
    point = serializers.IntegerField()
    explanation = serializers.CharField()
    is_correct = serializers.BooleanField()
    submitted_answer = serializers.ListField(child=serializers.CharField())


class UserExamSubmissionExtendSchemaSerializer(serializers.Serializer[Any]):
    id = serializers.IntegerField()
    submitter_id = serializers.IntegerField()
    deployment_id = serializers.IntegerField()
    exam = ExamNestedSerializer()
    questions = QuestionsSchemaSerializer(many=True)
    cheating_count = serializers.IntegerField()
    score = serializers.IntegerField()
    total_score = serializers.IntegerField()
    correct_answer_count = serializers.IntegerField()
    elapsed_time = serializers.IntegerField()
    started_at = serializers.DateTimeField()
    submitted_at = serializers.DateTimeField()