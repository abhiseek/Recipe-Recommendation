from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from .exceptions import AlreadyFollowingError


class FollowingManager(models.Manager):
    """ Friendship manager """

    def get_followers(self, user):
        """ Return a list of all followers """
        qs = (
            Follower.objects.select_related("from_user", "to_user")
                .filter(to_user=user)
                .all()
        )
        followers = [u.from_user for u in qs]

        return followers

    def follow_user(self, user, to_user):
        """ Follow someone """
        if  to_user == user:
            raise ValidationError("Users cannot follow themselves")

        if self.is_following(user, to_user):
            raise AlreadyFollowingError("You are already following this user")

        Follower.objects.create(from_user=user, to_user=to_user)

    def remove_follow(self, user, to_user):
        """ Stop following user """
        try:
            qs = Follower.objects.filter(to_user=to_user, from_user=user)
            qs.delete()
            return True
        except Follower.DoesNotExist:
            return False

    def is_following(self, user, to_user):
        """ Is user1 following user2? """
        try:
            Follower.objects.get(to_user=to_user, from_user=user)
            return True
        except Follower.DoesNotExist:
            return False


class Follower(models.Model):
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='friends')
    from_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    objects = FollowingManager()

    class Meta:
        verbose_name = _("Follower")
        verbose_name_plural = _("Followers")
        unique_together = ("from_user", "to_user")

    def __str__(self):
        return f"User  #{self.from_user_id} is following #{self.to_user_id} "

    def save(self, *args, **kwargs):
        # Ensure users can't be friends with themselves
        if self.to_user == self.from_user:
            raise ValidationError("Users cannot follow themselves.")
        super().save(*args, **kwargs)
