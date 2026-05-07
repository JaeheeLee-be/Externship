class SubjectNotFoundError(Exception):
    pass


class SubjectPermissionDeniedError(Exception):
    pass


class SubjectDuplicateTitleError(Exception):
    pass


class CourseNotFoundError(Exception):
    pass


class CourseDeleteDeniedError(Exception):
    pass


class CourseAlreadyExistsError(Exception):
    pass


class CourseBusinessError(Exception):  # 비즈니스 로직 에러용
    pass
