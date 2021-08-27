
from django.contrib import messages
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, TemplateView, UpdateView, FormView

from boardgames.models import BoardGame
from inventory.forms import FilterOwnershipThroughRelatedItems
from inventory.models import Ownership, Item, MiscellaneousItem
from inventory.views import OwnershipMixin
from roleplaying.models import RoleplayingItem
from utils.views import SearchFormMixin, PostOnlyFormViewMixin

from membership_file.util import user_to_member

from committees.forms import *
from committees.models import AssociationGroup, AssociationGroupMembership
from committees.utils import user_in_association_group


class AssocGroupOverview(ListView):
    context_object_name = 'association_groups'
    group_type = None
    tab_name = None

    def get_queryset(self):
        return AssociationGroup.objects.filter(type=self.group_type, is_public=True)

    def get_context_data(self, *args, **kwargs):
        context = super(AssocGroupOverview, self).get_context_data(*args, **kwargs)
        context[self.tab_name] = True
        return context


class CommitteeOverview(AssocGroupOverview):
    template_name = "committees/overview_committees.html"
    group_type = AssociationGroup.COMMITTEE
    tab_name = 'tab_committee'


class GuildOverview(AssocGroupOverview):
    template_name = "committees/overview_guilds.html"
    group_type = AssociationGroup.GUILD
    tab_name = 'tab_guild'


class BoardOverview(AssocGroupOverview):
    template_name = "committees/overview_boards.html"
    group_type = AssociationGroup.BOARD
    tab_name = 'tab_boards'


class AssociationGroupMixin:
    """ Mixin that stores the retrieved group from the url group_id keyword. Also verifies user is part of that group """
    association_group = None
    config_class = None

    def dispatch(self, request, *args, **kwargs):
        self.association_group = get_object_or_404(AssociationGroup, id=self.kwargs['group_id'])
        if not user_in_association_group(self.request.user, self.association_group):
            raise PermissionDenied()

        if self.config_class and not self.config_class.is_valid_for_group(self.association_group):
            raise PermissionDenied()

        return super(AssociationGroupMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(AssociationGroupMixin, self).get_context_data(**kwargs)
        context['association_group'] = self.association_group
        return context


class AssociationGroupDetailView(AssociationGroupMixin, TemplateView):
    template_name = "committees/group_detail_info.html"

    def get_context_data(self, **kwargs):
        context = super(AssociationGroupDetailView, self).get_context_data(**kwargs)
        context['tab_overview'] = True
        context['quicklinks_internal'] = self.construct_internal_links(self.association_group.site_group)
        context['quicklinks_external'] = self.association_group.shortcut_set.all()
        return context

    @staticmethod
    def construct_internal_links(group):
        links = []
        if group.permissions.filter(codename='maintain_ownerships_for_boardgame').exists():
            links.append({
                'url': reverse_lazy('inventory:catalogue', kwargs={'type_id': BoardGame}),
                'name': "Boardgame catalogue",
            })
        if group.permissions.filter(codename='maintain_ownerships_for_roleplayingitem').exists():
            links.append({
                'url': reverse_lazy('inventory:catalogue',  kwargs={'type_id': RoleplayingItem}),
                'name': "Roleplaying catalogue",
            })
        if group.permissions.filter(codename='maintain_ownerships_for_miscellaneousitem').exists():
            links.append({
                'url': reverse_lazy('inventory:catalogue',  kwargs={'type_id': MiscellaneousItem}),
                'name': "Misc item catalogue",
            })
        return links


class AssociationGroupQuickLinksView(AssociationGroupMixin, FormView):
    template_name = "committees/group_detail_quicklinks.html"
    form_class = AddOrUpdateExternalUrlForm

    def get_form_kwargs(self):
        form_kwargs = super(AssociationGroupQuickLinksView, self).get_form_kwargs()
        form_kwargs['association_group'] = self.association_group
        return form_kwargs

    def form_valid(self, form):
        instance, created = form.save()
        if created:
            msg = f'{instance.name} has been added'
        else:
            msg = f'{instance.name} has been updated'
        messages.success(self.request, msg)

        return super(AssociationGroupQuickLinksView, self).form_valid(form)

    def get_success_url(self):
        return self.request.path

    def get_context_data(self, **kwargs):
        return super(AssociationGroupQuickLinksView, self).get_context_data(tab_overview=True, **kwargs)


class AssociationGroupQuickLinksDeleteView(AssociationGroupMixin, PostOnlyFormViewMixin, FormView):
    form_class = DeleteGroupExternalUrlForm
    form_success_method_name = 'delete'

    def get_form_kwargs(self):
        quicklink = self.association_group.shortcut_set.filter(id=self.kwargs.get('quicklink_id', None))
        if not quicklink.exists():
            raise Http404("This shortcut does not exist")

        form_kwargs = super(AssociationGroupQuickLinksDeleteView, self).get_form_kwargs()
        form_kwargs['instance'] = quicklink.first()
        return form_kwargs

    def get_success_url(self):
        return reverse_lazy("committees:group_quicklinks", kwargs={'group_id': self.association_group.id})

    def get_success_message(self, form):
        return f'{form.instance.name} has been removed'


class AssociationGroupUpdateView(AssociationGroupMixin, FormView):
    form_class = AssociationGroupUpdateForm
    template_name = "committees/group_detail_info_edit.html"

    def get_form_kwargs(self):
        form_kwargs = super(AssociationGroupUpdateView, self).get_form_kwargs()
        form_kwargs['instance'] = self.association_group
        return form_kwargs

    def get_context_data(self, **kwargs):
        return super(AssociationGroupUpdateView, self).get_context_data(
            tab_overview=True,
            **kwargs
        )

    def form_valid(self, form):
        form.save()
        return super(AssociationGroupUpdateView, self).form_valid(form)

    def get_success_url(self):
        return reverse_lazy('committees:group_general', kwargs={'group_id': self.association_group.id})


class AssociationGroupMembersView(AssociationGroupMixin, FormView):
    template_name = "committees/group_detail_members.html"
    form_class = AssociationGroupMembershipForm

    def get_form_kwargs(self):
        form_kwargs = super(AssociationGroupMembersView, self).get_form_kwargs()
        form_kwargs['association_group'] = self.association_group
        return form_kwargs

    def form_valid(self, form):
        instance = form.save()
        msg = f'{instance.member} has been updated'
        messages.success(self.request, msg)

        return super(AssociationGroupMembersView, self).form_valid(form)

    def get_success_url(self):
        return self.request.path

    def get_context_data(self, **kwargs):
        return super(AssociationGroupMembersView, self).get_context_data(
            tab_overview=True,
            member_links=self.association_group.associationgroupmembership_set.all(),
            **kwargs)


