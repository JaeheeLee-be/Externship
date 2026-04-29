class PostNotFoundError(Exception):
    pass


class PostPermissionDeniedError(Exception):
    pass


class CommentNotFoundError(Exception):
    pass


class CommentPermissionDeniedError(Exception):
    pass


class SubjectNotFoundError(Exception):
    pass


class SubjectPermissionDeniedError(Exception):
    pass


class SubjectDuplicateTitleError(Exception):
    pass
