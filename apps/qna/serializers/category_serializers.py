from typing import Any

from rest_framework import serializers

from apps.qna.models.question_models import QuestionCategory


# 카테고리 depth 계산 함수
def get_category_depth(category: QuestionCategory) -> int:
    depth = 1
    current_depth = category.parent
    while current_depth:
        depth += 1
        current_depth = current_depth.parent
    return depth

# 카테고리 depth -> type 변환
def get_category_type(category: QuestionCategory) -> str | None:
    mapping = {
        1: "large",
        2: "middle",
        3: "small",
    }
    return mapping.get(get_category_depth(category))


# 어드민 카테고리 생성
class AdminCategoryCreateSerializer(serializers.Serializer[Any]):
    category_type = serializers.ChoiceField(
        choices=["large", "middle", "small"],
        error_messages={
            "required": "카테고리 종류와 이름은 필수 입력값입니다.",
            "invalid_choice": "카테고리 종류와 이름은 필수 입력값입니다.",
        },
    )
    name = serializers.CharField(
        max_length=15,
        error_messages={
            "required": "카테고리 종류와 이름은 필수 입력값입니다.",
            "blank": "카테고리 종류와 이름은 필수 입력값입니다.",
        },
    )
    parent_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_name(self, value: str) -> str:
        value = value.strip()
        if not value:
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        category_type = attrs.get("category_type")
        parent_id = attrs.get("parent_id")
        name = attrs.get("name")

        parent = None

        # 대분류는 부모를 가질 수 없음
        if category_type == "large":
            if parent_id is not None:

        # 중/소분류는 부모가 필요함
        if category_type in ["middle", "small"]:
            if parent_id is None:

            try:
                parent = QuestionCategory.objects.get(id=parent_id)
            except QuestionCategory.DoesNotExist:

            parent_depth = get_category_depth(parent)

            # 중분류의 부모는 대분류
            if category_type == "middle" and parent_depth != 1:

            # 소분류의 부모는 중분류
            if category_type == "small" and parent_depth != 2:

        # 같은 부모 아래 동일 이름 중복 방지
        if QuestionCategory.objects.filter(parent=parent, name=name).exists():

        attrs["parent"] = parent
        return attrs


# 카테고리 생성 응답
class AdminCategoryCreateResponseSerializer(serializers.ModelSerializer[QuestionCategory]):
    category_id = serializers.IntegerField(source="id")
    parent_id = serializers.SerializerMethodField()
    category_type = serializers.SerializerMethodField()

    class Meta:
        model = QuestionCategory
        fields = [
            "category_id",
            "name",
            "parent_id",
            "category_type",
            "created_at",
        ]

    def get_category_type(self, obj: QuestionCategory) -> str | None:
        depth = get_category_depth(obj)

        mapping = {
            1: "large",
            2: "middle",
            3: "small",
        }
        return mapping.get(depth)

    def get_parent_id(self, obj: QuestionCategory) -> int | None:
        return obj.parent_id

# 어드민 카테고리 목록 조회 응답
class AdminCategoryListSerializer(serializers.ModelSerializer[QuestionCategory]):
    category_id = serializers.IntegerField(source="id")
    category_type = serializers.SerializerMethodField()
    parent_name = serializers.SerializerMethodField()
    child_names = serializers.SerializerMethodField()

    class Meta:
        model = QuestionCategory
        fields = [
            "category_id",
            "name",
            "category_type",
            "parent_name",
            "child_names",
            "created_at",
            "updated_at",
        ]

    def get_category_type(self, obj: QuestionCategory) -> str | None:
        return get_category_type(obj)

    def get_parent_name(self, obj: QuestionCategory) -> str | None:
        if obj.parent is None:
            return None
        return obj.parent.name

    def get_child_names(self, obj: QuestionCategory) -> list[str]:
        return [child.name for child in obj.children.all()]