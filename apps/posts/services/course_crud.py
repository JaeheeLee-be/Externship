from django.shortcuts import get_object_or_404
from apps.posts.models.course import Course
from apps.posts.exceptions import CourseAlreadyExistsError


def get_course_list():
    # 과정 목록조회 검증
    return Course.objects.all().order_by("id")


def get_course_detail(course_id: int) -> Course:
    # 과정 상세조회 검증
    return get_object_or_404(Course, id=course_id)


def create_course(validated_data: dict) -> Course:
    # 과정 등록 검증
    name = validated_data["name"]

    if Course.objects.filter(name=name).exists():
        raise CourseAlreadyExistsError("이미 등록된 과정명입니다.")

    return Course.objects.create(**validated_data)


def update_course(course_id: int, validated_data: dict) -> Course:
    # 과정 수정 검증
    course = get_object_or_404(Course, id=course_id)

    for field, value in validated_data.items():
        setattr(course, field, value)

    course.save()
    return course


def delete_course(course_id: int) -> None:
    # 과정 삭제 검증
    course = get_object_or_404(Course, id=course_id)

    # 추후 기수/유저 연결되면 추가

    course.delete()
