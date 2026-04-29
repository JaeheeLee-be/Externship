from typing import Any

from rest_framework import serializers

from apps.posts.models.course import Course


# 001+004 과정 등록 및 수정 시 사용할 데이터 규격
class CourseRequestSerializer(serializers.ModelSerializer[Course]):
    class Meta:
        model = Course
        # 요구사항에 맞춰 과정명, 태그, 소개, 썸네일 로고 기재
        fields = ["name", "tag", "description", "thumbnail_img_url"]


# 002 과정 목록 조회 시 사용할 데이터 규격
class CourseListResponseSerializer(serializers.ModelSerializer[Course]):
    active_cohort_count = serializers.IntegerField()
    total_student_count = serializers.IntegerField()

    class Meta:
        model = Course
        # 요구사항: ID, 과정명, 운영기수, 총인원, 등록일, 수정일
        fields = ["id", "name", "active_cohort_count", "total_student_count", "created_at", "updated_at"]


# 003 과정 상세 조회 사용 데이터 규격
class CourseDetailResponseSerializer(serializers.ModelSerializer[Course]):
    class Meta:
        model = Course
        fields = ["id", "name", "tag", "description", "thumbnail_img_url", "created_at", "updated_at"]


class CourseActionResponseSerializer(serializers.Serializer[Any]):
    detail = serializers.CharField(help_text="응답 메시지")
