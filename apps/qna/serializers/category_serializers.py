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
            raise serializers.ValidationError("카테고리 종류와 이름은 필수 입력값입니다.")
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        category_type = attrs.get("category_type")
        parent_id = attrs.get("parent_id")
        name = attrs.get("name")

        parent = None

        # 대분류는 부모를 가질 수 없음
        if category_type == "large":
            if parent_id is not None:
                raise serializers.ValidationError(
                    "대분류는 parent_id를 가질 수 없습니다.",
                    code="large_has_parent",
                )

        # 중/소분류는 부모가 필요함
        if category_type in ["middle", "small"]:
            if parent_id is None:
                raise serializers.ValidationError(
                    "부모 카테고리를 찾을 수 없습니다.",
                    code="parent_not_found",
                )

            try:
                parent = QuestionCategory.objects.get(id=parent_id)
            except QuestionCategory.DoesNotExist:
                raise serializers.ValidationError(
                    "부모 카테고리를 찾을 수 없습니다.",
                    code="parent_not_found",
                )

            parent_depth = get_category_depth(parent)

            # 중분류의 부모는 대분류
            if category_type == "middle" and parent_depth != 1:
                raise serializers.ValidationError(
                    "중분류의 부모는 대분류여야 합니다.",
                    code="invalid_middle_parent",
                )

            # 소분류의 부모는 중분류
            if category_type == "small" and parent_depth != 2:
                raise serializers.ValidationError(
                    "소분류의 부모는 중분류여야 합니다.",
                    code="invalid_small_parent",
                )

        # 같은 부모 아래 동일 이름 중복 방지
        if QuestionCategory.objects.filter(parent=parent, name=name).exists():
            raise serializers.ValidationError(
                "동일한 이름의 카테고리가 이미 존재합니다.",
                code="duplicate_category",
            )

        attrs["parent"] = parent
        return attrs

    def get_error_detail(self) -> str:
        first_error = next(iter(self.errors.values()))

        if isinstance(first_error, list):
            return str(first_error[0])

        return str(first_error)

    def get_error_code(self) -> str:
        first_error = next(iter(self.errors.values()))

        if isinstance(first_error, list):
            return getattr(first_error[0], "code", "invalid")

        return getattr(first_error, "code", "invalid")


# 카테고리 생성 응답
class AdminCategoryCreateResponseSerializer(serializers.ModelSerializer[QuestionCategory]):
    category_id = serializers.IntegerField(source="id")
    parent_id = serializers.IntegerField(source="parent.id", allow_null=True)
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
