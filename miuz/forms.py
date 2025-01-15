from django import forms
from django.contrib.auth.models import Group

from .models import Applications, Sciences, Groups
from django.core.exceptions import ValidationError
from .models import Groups, Applications, Edutype


class ApplicationForm(forms.ModelForm):
    directions = forms.ModelChoiceField(queryset=Groups.objects.all(), required=True, empty_label="Tanlang",
                                        label="Ixtisoslik nomi")
    edutype = forms.ModelChoiceField(queryset=Edutype.objects.all(), required=True, empty_label="Tanlang",
                                        label="Ta'lim turi")
    class Meta:
        model = Applications
        fields = ['first_name', 'last_name', 'father_name', 'directions',
            'sciences', 'type_edu', 'organization', 'number',
            'oak_decision', 'work_order', 'reference_letter', 'application']


class ScienceForm(forms.ModelForm):
    class Meta:
        model = Sciences
        fields = ['name', 'directions']


class GroupForm(forms.ModelForm):
    class Meta:
        model = Groups
        fields = ['directions', 'comission',]


class EdutypeForm(forms.ModelForm):

    class Meta:
        model = Edutype  # To'g'ri modelni ko'rsatamiz
        fields = ['name']  # Edutype modelining mavjud maydonlari
