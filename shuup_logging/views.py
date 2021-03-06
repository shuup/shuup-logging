# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from dictdiffer import diff
from django.utils.translation import ugettext_lazy as _
from shuup.admin.utils.picotable import (
    ChoicesFilter, Column, DateRangeFilter, TextFilter
)
from shuup.admin.utils.urls import get_model_url
from shuup.admin.utils.views import PicotableListView
from shuup.utils.analog import LogEntryKind


class BaseLogListView(PicotableListView):
    model = None
    user_search_field = "user__username"
    target_search_field = None  # Define in parent class
    hide_extra = False
    hide_extra_changed = False

    default_columns = [
        Column(
            "created_on", _("Created on"), ordering=1, sortable=True,
            filter_config=DateRangeFilter()
        ),
        Column(
            "user", _("User"), ordering=2, sortable=True, display="format_user", raw=True,
            filter_config=TextFilter(filter_field=user_search_field, placeholder=_("Filter by user..."))
        ),
        Column(
            "target", _("Target"), ordering=3, sortable=True, display="format_target", raw=True,
            filter_config=TextFilter(filter_field=target_search_field, placeholder=_("Filter by target..."))
        ),
        Column(
            "message", _("Message"), ordering=4, sortable=True,
            filter_config=TextFilter(filter_field="message", placeholder=_("Filter by message..."))
        ),
        Column(
            "kind", _("Kind"), ordering=5, sortable=True,
            filter_config=ChoicesFilter(choices=LogEntryKind.choices)
        ),
        Column(
            "identifier", _("Identifier"), ordering=6, sortable=True,
            filter_config=TextFilter(filter_field="identifier", placeholder=_("Filter by identifier..."))
        ),
        Column("extra", _("Extra"), ordering=7, sortable=True),
        Column("extra_changed", _("Change in extra"), ordering=8, sortable=True, display="get_extra_change", raw=True)
    ]

    def __init__(self):
        super(BaseLogListView, self).__init__()
        self.columns = self.default_columns
        if self.hide_extra:
            self.columns = [column for column in self.default_columns if column.id != "extra"]

        if self.hide_extra_changed:
            self.columns = [column for column in self.default_columns if column.id != "extra_changed"]


    def format_user(self, instance, *args, **kwargs):
        if instance.user:
            return '<a href=%s target="_blank">%s</a>' % (get_model_url(instance.user), instance.user)
        return "-"

    def format_target(self, instance, *args, **kwargs):
        if instance.target:
            try:
                return '<a href=%s target="_blank">%s</a>' % (get_model_url(instance.target), instance.target)
            except Exception as e:
                return instance.target.pk
        return "-"

    def get_extra_change(self, instance, *args, **kwargs):
        if not instance.extra:
            return "-"

        previous_item = self.model.objects.filter(
            pk__lt=instance.pk,
            target_id=instance.target_id,
            identifier=instance.identifier
        ).order_by("-id").first()

        if previous_item and previous_item.extra:
            changes = []
            for action, attr, value_change in diff(previous_item.extra, instance.extra):

                if isinstance(attr, list):
                    attr = ".".join(str(v) for v in attr)

                if action == "remove":
                    changes.append(
                        '{} <code>{}</code> <em style="color: red;">{}</em>'.format(
                            action.capitalize(),
                            attr,
                            value_change,
                        )
                    )
                elif action == "add":
                    changes.append(
                        '{} <code>{}</code> <em style="color: green;">{}</em>'.format(
                            action.capitalize(),
                            attr,
                            value_change,
                        )
                    )
                elif action == "change":
                    row_fmt = (
                        '{} <code>{}</code> from <em style="color: red;">{}</em> to <em style="color: green;">{}</em>'
                    )
                    changes.append(
                        row_fmt.format(
                            action.capitalize(),
                            attr,
                            value_change[0] if value_change[0] is not None else "-",
                            value_change[1] if value_change[1] is not None else "-"
                        )
                    )
            return "<br>".join(changes)
        return "-"

    def get_queryset(self):
        return self.model.objects.all().order_by("-created_on")
