
from datetime import datetime

from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from import_export.admin import ExportActionMixin
from import_export.formats.base_formats import CSV

from .forms import AdminMemberForm
from .models import Member, MemberLog, MemberLogField, Room, MemberYear, Membership
from core.admin import EmptyFieldListFilter
from membership_file.export import MemberResource
from utils.forms import RequestUserToFormModelAdminMixin


class HideRelatedNameAdmin(admin.ModelAdmin):
    class Media:
        # Hacky solution to hide the "X was updated: <Y> -> <Z>" text
        # We don't need to edit this information anyways, so it's safe to hide
        # https://stackoverflow.com/a/5556813
        css = {
            'all': ('css/hide_related_model_name.css',),
        }


class DisableModifications():
    # Disable creation
    def has_add_permission(self, request):
        return False

    # Disable editing
    def has_change_permission(self, request, obj=None):
        return False

    # Disable deletion
    def has_delete_permission(self, request, obj=None):
        return False


class RoomInline(admin.TabularInline):
    model = Room.members_with_access.through
    extra = 0


class MemberYearInline(admin.TabularInline):
    model = Membership
    fk_name = 'member'
    extra = 0
    fields = ['year', 'has_paid', 'payment_date']


class MemberLogReadOnlyInline(DisableModifications, admin.TabularInline):
    model = MemberLog
    extra = 0
    readonly_fields = ['date', 'get_url']
    fields = ['log_type', 'user', 'date', 'get_url']
    ordering = ("-date",)

    # Whether the object can be deleted inline
    can_delete = False

    def get_url(self, obj):
        return format_html("<a href='/admin/membership_file/memberlog/{0}/change/'>View Details</a>", obj.id)
    get_url.short_description = 'Details'


@admin.register(Member)
class MemberWithLog(RequestUserToFormModelAdminMixin, ExportActionMixin, HideRelatedNameAdmin):
    ##############################
    #  Export functionality
    resource_class = MemberResource
    formats = (CSV,)

    def has_export_permission(self, request):
        return request.user.has_perm('membership_file.can_export_membership_file')

    def get_export_filename(self, request, queryset, file_format):
        filename_prefix = ""
        if queryset.filter(is_deregistered=True).exists():
            filename_prefix = "HAS_DEREGISTERED_MEMBERS-"

        date_str = datetime.now().strftime('%Y-%m-%d')
        filename = "%sMembershipFile-%s.%s" % (filename_prefix, date_str, file_format.get_extension())

        return filename

    ##############################
    form = AdminMemberForm
    save_on_top = True

    list_display = ('id', 'user', 'first_name', 'tussenvoegsel', 'last_name', 'educational_institution', 'is_deregistered', 'marked_for_deletion')
    list_filter = [
        'memberyear',
        'is_deregistered', 'marked_for_deletion',
        'is_honorary_member',
        'educational_institution',
        ('tue_card_number', EmptyFieldListFilter), ('external_card_number', EmptyFieldListFilter),
        ('key_id', EmptyFieldListFilter), ('phone_number', EmptyFieldListFilter),
    ]
    list_display_links = ('id', 'user', 'first_name')
    search_fields = ['first_name', 'last_name', 'email', 'phone_number', 'tue_card_number', 'external_card_number', 'key_id']

    readonly_fields = ['last_updated_by', 'last_updated_date']

    # Display a search box instead of a dropdown menu
    autocomplete_fields = ['user']

    fieldsets = [
        (None, {'fields':
            ['user', ('first_name', 'tussenvoegsel', 'last_name'),
            'marked_for_deletion',
            ('last_updated_date', 'last_updated_by'),]}),
        ('Membership Status', {'fields':
            ['is_deregistered', 'has_paid_membership_fee', 'is_honorary_member', 'member_since']}),
        ('Contact Details', {'fields':
            ['email', 'phone_number',
            ('street', 'house_number', 'house_number_addition'), ('postal_code', 'city'), 'country']}),
        ('Room Access', {'fields':
            ['key_id', 'tue_card_number',
            ('external_card_number', 'external_card_digits', 'external_card_cluster'),
            'external_card_deposit', 'accessible_rooms']}),
        ('Legal Information', {'fields':
            ['educational_institution', 'student_number',
            'date_of_birth', 'legal_name']}),
        ('Notes', {'fields':
            ['notes']}),
    ]

    inlines = [MemberLogReadOnlyInline, MemberYearInline]

    # Show at most 150 members per page (opposed to 100).
    # Show a "show all" button if <999 members are selected (opposed to 200)
    #   We're increasing these numbers as the board needs to be able to select all members in
    #   order to export & send emails to them. We likely won't go over 150 members, so this
    #   basically gets rid of any chances of forgetting to click the "select all" button,
    #   causing the last few members to not receive emails.
    list_per_page = 150
    list_max_show_all = 999

    # Allow bulk updating has_paid_membership_fee = False
    # TODO: This isn't a clean solution but it'll work for now
    actions = ['mark_as_current_member', ExportActionMixin.export_admin_action]

    # Disable bulk delete
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def mark_as_current_member(self, request, queryset):
        try:
            year = MemberYear.objects.get(is_active=True)
        except MemberYear.MultipleObjectsReturned:
            self.message_user(
                request,
                "There are multiple years active,  only  one should be active",
                level=messages.ERROR
            )
            return
        except MemberYear.DoesNotExist:
            self.message_user(
                request,
                "There is currently no year active, make sure that one is active",
                level=messages.ERROR
            )
            return
        created_count = 0
        for member in queryset:
            member, created = Membership.objects.get_or_create(
                member=member,
                year=year,
            )
            created_count += int(created)

        self.message_user(
            request,
            f"Succesfully created {created_count} new members. {queryset.count() - created_count} instances were already a member",
            level=messages.SUCCESS
        )
    mark_as_current_member.short_description = 'Assign as member of the currently active year'

    # Disable deletion if the member was not marked for deletion
    # Disable deletion for the user that marked the member for deletion
    def has_delete_permission(self, request, obj=None):
        # User is normally allowed to delete these objects
        if obj is None:
            return True

        # If the member was not marked for deletion, disable deletion
        if not obj.marked_for_deletion:
            return False
        # If the member was marked for deletion by the requesting user, disable deletion
        elif (obj.last_updated_by is None) or (obj.last_updated_by.id == request.user.id):
            return False

        # The member was marked for deletion, and is being deleted by another user; enable deletion
        return True


# Prevents MemberLogField creation, edting, or deletion in the Django Admin Panel
class MemberLogFieldReadOnlyInline(DisableModifications, admin.TabularInline):
    model = MemberLogField
    extra = 0

    # Whether the object can be deleted inline
    can_delete = False


# Prevents MemberLog creation, edting, or deletion in the Django Admin Panel
@admin.register(MemberLog)
class MemberLogReadOnly(DisableModifications, HideRelatedNameAdmin):
    # Show the date at which the information was updated as well
    readonly_fields = ['date']
    list_display = ('id', 'log_type', 'user', 'member', 'date')
    list_filter = ['log_type', 'member']
    list_display_links = ('id', 'log_type')

    inlines = [MemberLogFieldReadOnlyInline]


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    model = Room

    list_display = ('id', 'name', 'access')
    list_display_links = ('id', 'name')
    search_fields = ['name', 'access']

    ordering = ("access",)
    filter_horizontal = ('members_with_access',)


@admin.register(MemberYear)
class MemberYearAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'member_count']
    list_filter = ['is_active',]

    def member_count(self, obj):
        return obj.members.count()


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ['member', 'year', 'has_paid', 'payment_date']
    list_filter = ['year', 'has_paid']


