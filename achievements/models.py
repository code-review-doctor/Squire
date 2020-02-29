from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

#Setup some constants
maxDescriptionLength = 255
maxNameLength = 31

# Create categories for the Achievements like Boardgames, Roleplay, General
class Category(models.Model):
    class Meta:
        # Enabled proper plurality
        verbose_name_plural = "categories"
        
        # Sort by name. If they are equal, sort by Id
        ordering = ['name','id']

    name = models.CharField(max_length=maxNameLength)
    description = models.TextField(max_length=maxDescriptionLength)

    def __str__(self):
        return self.name

# Gets or creates the default Category
def get_or_create_default_category():  
    return Category.objects.get_or_create(name='General', description='Contains Achievements that do not belong to any other Category.')[0]

# Achievements that can be earned by users
class Achievement(models.Model):
    # Basic Information
    name = models.CharField(max_length=maxNameLength)
    description = models.TextField(max_length=maxDescriptionLength)
    category = models.ForeignKey(Category, on_delete=models.SET(get_or_create_default_category), related_name="related_achievements")

    # An Achievement can be claimed by more members (claimants) and a member can have more achievements.
    claimants = models.ManyToManyField(User, blank=True, through="Claimant", related_name="claimed_achievements")

    # Text used to display unlocked status. Can be used to display extra data for high scores.
    # {0} User
    # {1} Date (Sorted on descending)
    # {2} extra_data_1 (Sorted on ascending)
    # {3} extra_data_2 (Sorted on descending)
    # {4} extra_data_3
    # E.g. {0} unlocked this achievement on {1} with a score of {2}!
    unlocked_text = models.CharField(max_length=127, default="Claimed by {0} on {1}.",
        help_text="{0}: User, {1}: Date (Tertiary Sort, Descending), {2}: Extra Data 1 (Primary Sort, Ascending), {3}: Extra Data 2 (Secondary Sort, Descending), {4}: Extra Data 3")

    class Meta:
        permissions = [
            ("can_view_claimants", "Can view the claimants of Achievements"),
        ]
        ordering = ['name','id']

    def __str__(self):
        return self.name

    # Checks whether a given user can view this achievement's claimants
    @staticmethod
    def user_can_view_claimants(user):
        if user is None:
            return False
        
        # TODO: Work with Permission System
        return user.is_authenticated


# Represents a user earning an achievement
class Claimant(models.Model):
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date_unlocked = models.DateField(default=timezone.now)

    # Extra data fields that can be used to track high-scores
    extra_data_1 = models.CharField(max_length=63, null=True, blank=True)
    extra_data_2 = models.CharField(max_length=63, null=True, blank=True)
    extra_data_3 = models.CharField(max_length=63, null=True, blank=True)

    def __str__(self):
        return f"{self.achievement} unlocked by {self.user}"
    
    class Meta:
        ordering = ['extra_data_1', '-extra_data_2', '-date_unlocked','id']
