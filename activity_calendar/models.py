from django.conf import settings
from django.core.validators import MinValueValidator, ValidationError
from django.db import models
from django.utils import timezone

from datetime import datetime

from recurrence.fields import RecurrenceField

from core.models import ExtendedUser as User

# Models related to the Calendar-functionality of the application.
# @since 29 JUN 2019

# The Activity model represents an activity in the calendar
class Activity(models.Model): #TODO: Create testcases
    verbose_name_plural = "activities"

    # The User that created the activity
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
    
    # Possible statuses of an event
    # TODO: These are likely only for meeting requests; Remove them in a future version!
    STATUS_OPTIONS = [
        ("CONFIRMED",   "Confirmed"),
        ("CANCELLED",   "Cancelled"),
        ("TENTATIVE",   "Tentative"),
    ]

    # General information
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    status = models.CharField(max_length=15, choices=STATUS_OPTIONS)
    
    # Creation and last update dates (handled automatically)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated_date = models.DateTimeField(auto_now=True)
    
    # The date at which the activity will become visible for all users
    published_date = models.DateTimeField(default=timezone.now)

    # Start and end times
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(default=timezone.now)

    # Recurrence information (e.g. a weekly event)
    # This means we do not need to store (nor create!) recurring activities separately
    recurrences = RecurrenceField(blank=True)

    # Maximum number of participants/slots
    # -1 denotes unlimited
    max_slots = models.IntegerField(default=-1, validators=[MinValueValidator(-1)],
        help_text="-1 denotes unlimited slots")
    max_participants = models.IntegerField(default=-1, validators=[MinValueValidator(-1)],
        help_text="-1 denotes unlimited participants")

    # Maximum number of slots that someone can create/join
    max_slots_join_per_participant = models.IntegerField(default=-1, validators=[MinValueValidator(-1)],
        help_text="-1 denotes unlimited slots")
    max_slots_create_per_participant = models.IntegerField(default=-1, validators=[MinValueValidator(-1)],
        help_text="-1 denotes unlimited slots")
    

    # Publishes the activity, making it visible for all users
    def publish(self):
        self.published_date = timezone.now()
        self.save()

    # String-representation of an instance of the model
    def __str__(self):
        return "{1} ({0})".format(self.id, self.title)

    
    def clean_fields(self, exclude=None):
        super().clean_fields(exclude=exclude)
        errors = {}

        # Activities must start before they can end
        if self.start_date >= self.end_date:
            errors.update({'start_date': 'Start date must be before the end date'})


        r = self.recurrences
        if r:
            recurrence_errors = []
            current_start_time = self.start_date.time()

            # Attempting to exclude dates if no recurrence is specified
            if not r.rrules and (r.exrules or r.exdates):
                recurrence_errors.append('Cannot exclude dates if the activity is non-recurring')

            # Each EXDATE's time needs to match the event start-time
            # Since there's no possibility to select the time in the UI, we're overriding it here
            r.exdates = list(map(lambda dt: datetime.combine(
                    dt.astimezone(timezone.get_current_timezone()).date(),
                    current_start_time), r.exdates))

            if recurrence_errors:
                errors.update({'recurrences': recurrence_errors})

        if errors:
            raise ValidationError(errors)
        
