from apps.posts.models.category import PostCategory
from apps.courses.models.cohort import *
from apps.posts.models.comment import PostComment, PostCommentTag
from apps.courses.models.course import Course
from apps.posts.models.like import Like
from apps.posts.models.post import Post
from apps.courses.models.subject import Subject

__all__ = ["PostCategory", "Post", "PostComment", "PostCommentTag", "Like", "Subject", "Course", "Cohort"]
