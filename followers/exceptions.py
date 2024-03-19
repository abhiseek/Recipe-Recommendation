from django.db import IntegrityError


class AlreadyExistsError(IntegrityError):
    pass


class AlreadyFollowingError(IntegrityError):
    pass
