from django.db import models
#공통베이스모델 참조예정

class PostCategory(models.Model):
    name = models.CharField(max_length=20)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "post_category"

    def __str__(self) -> str:
        return self.name
