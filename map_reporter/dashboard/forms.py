from django import forms
from django.core.mail import send_mail
from django.core.mail import EmailMessage
from bootstrap_daterangepicker import widgets, fields
from datetime import date, datetime, timedelta
from collections import OrderedDict
from dateutil import relativedelta


class DatePicker(forms.Form):
    # # Date Picker Fields
    # date_single_normal = fields.DateField()
    # date_single_with_format = fields.DateField(
    #     input_formats=['%d/%m/%Y'],
    #     widget=widgets.DatePickerWidget(
    #         format='%d/%m/%Y'
    #     )
    # )
    # date_single_clearable = fields.DateField(required=False)

    # # Date Range Fields
    # date_range_normal = fields.DateRangeField()

    # date_range_with_format = fields.DateRangeField(
    #     input_formats=['%d/%m/%Y'],
    #     widget=widgets.DateRangeWidget(
    #         format='%d/%m/%Y',
    #     )
    # )

    date_range_with_predefined_ranges = fields.DateRangeField(
        input_formats=["%d/%m/%Y"],
        widget=widgets.DateRangeWidget(
            picker_options={
                "locale": {
                    "format": "DD/MM/YYYY",
                },
                "ranges": widgets.common_dates("%d/%m/%Y"),
                "alwaysShowCalendars": True,
            },
        ),
    )

    # date_range_with_predefined_ranges = fields.DateRangeField(
    #     # input_formats=['%d/%m/%Y'],
    #     widget=widgets.DateRangeWidget(
    #         picker_options={
    #             # 'format':'%d/%m/%Y',
    #             'ranges': widgets.common_dates(),
    #             'alwaysShowCalendars': True,
    #             },
    #     )
    # )

    # date_range_with_predefined_ranges = fields.DateRangeField(
    #     input_formats=['%d/%m/%Y'],
    #     widget=widgets.DateRangeWidget(
    #         picker_options={
    #             'ranges': widgets.common_dates(),
    #             'alwaysShowCalendars': True,
    #             },
    #         format='%d/%m/%Y',
    #     )
    # )

    # date_range_clearable = fields.DateRangeField(required=False)

    # # DateTime Range Fields
    # datetime_range_normal = fields.DateTimeRangeField()
    # datetime_range_with_format = fields.DateTimeRangeField(
    #     input_formats=['%d/%m/%Y (%I:%M:%S)'],
    #     widget=widgets.DateTimeRangeWidget(
    #         format='%d/%m/%Y (%I:%M:%S)'
    #     )
    # )
    # datetime_range_clearable = fields.DateTimeRangeField(required=False)


# name = forms.CharField(
#     widget=forms.TextInput(
#         attrs={"placeholder": "Name", "style": "width: 300px;", "class": "form-control"}
#     )
# )


class FeedbackForm(forms.Form):
    subjects = [
        ("feature", "Αίτημα νέας λειτουργίας"),
        ("bug", "Αίτημα υποστήρηξης"),
    ]
    subject = forms.CharField(
        label="Επιλέξτε θέμα",
        widget=forms.Select(
            choices=subjects,
            attrs={
                "class": "form-select m-2",
            },
        ),
    )
    message = forms.CharField(
        label="Περιγραφή",
        widget=forms.Textarea(
            attrs={
                "class": "form-control m-2",
            }
        ),
    )
    cc_myself = forms.BooleanField(
        label="Κοινοποίηση μηνύματος σε εμένα",
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
            }
        ),
    )
    file_field = forms.FileField(
        label="Προσθήκη αρχείων",
        widget=forms.ClearableFileInput(
            attrs={
                "multiple": True,
                "class": "form-control m-2",
            }
        ),
        required=False,
    )
