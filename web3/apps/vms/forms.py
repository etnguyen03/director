import re
import uuid

from raven.contrib.django.raven_compat.models import client

from django import forms
from django.core.cache import cache

from ..sites.models import Site
from ..users.models import User
from .helpers import call_api
from .models import VirtualMachine, VirtualMachineHost


class VirtualMachineForm(forms.ModelForm):
    name = forms.CharField(
        max_length=255, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    description = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}), required=False
    )
    users = forms.ModelMultipleChoiceField(
        required=False, queryset=User.objects.filter(service=False)
    )
    site = forms.ModelChoiceField(
        required=False, queryset=Site.objects.filter(category="vm")
    )
    owner = forms.ModelChoiceField(
        required=True, queryset=User.objects.filter(service=False)
    )
    host = forms.ModelChoiceField(
        required=True,
        queryset=VirtualMachineHost.objects.all(),
        widget=forms.RadioSelect(),
        empty_label=None,
    )

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        name_re = "^{}$".format(
            re.escape(name.lower().replace("-", " ")).replace("\\\\-", "[- ]")
        )
        existing = VirtualMachine.objects.filter(name__iregex=name_re)
        if existing.exists():
            if self.instance and self.instance.pk:
                if not existing.first() == self.instance:
                    raise forms.ValidationError(
                        "A virtual machine with this name already exists!"
                    )
            else:
                raise forms.ValidationError(
                    "A virtual machine with this name already exists!"
                )
        return name

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super(VirtualMachineForm, self).__init__(*args, **kwargs)
        self.fields["host"].initial = VirtualMachineHost.objects.first().id
        self.fields["owner"].initial = self.user.id
        if not self.user.is_superuser:
            self.fields["owner"].queryset = User.objects.filter(id=self.user.id)
            self.fields["owner"].disabled = True
            self.fields["site"].queryset = Site.objects.filter(
                group__users=self.user, category="vm"
            )
        if self.instance and self.instance.pk:
            self.old_hostname = self.instance.hostname
        else:
            vm_key = "vm:templates"
            vm_templates = cache.get(vm_key)
            if not vm_templates:
                vm_templates = call_api("container.templates")
                cache.set(vm_key, vm_templates)
            if vm_templates:
                self.fields["template"] = forms.ChoiceField(
                    choices=[(x, x.title()) for x in vm_templates],
                    widget=forms.Select(attrs={"class": "form-control"}),
                )

    def save(self, commit=True):
        instance = forms.ModelForm.save(self, commit=False)
        hostname = instance.hostname

        if commit:
            editing = bool(instance.pk)
            instance.save()
            self.save_m2m()
            instance.users.remove(instance.owner)
            if not editing:
                ret = call_api(
                    "container.create",
                    name=hostname,
                    template=self.cleaned_data.get("template", "debian"),
                )
                if ret is None or ret[0] == 1:
                    client.captureMessage("Failed to create VM: {}".format(ret))
                    instance.delete()
                    return None
                else:
                    if ret[0] != 2:
                        instance.uuid = uuid.UUID(ret[1].split("\n")[-1])
                        instance.save()
            elif not self.old_hostname == hostname:
                if "name" in self.changed_data:
                    ret = call_api(
                        "container.set_hostname",
                        name=str(instance.uuid),
                        old_hostname=self.old_hostname,
                        new_hostname=hostname,
                    )
                    if ret is None or ret != 0:
                        client.captureMessage(
                            "Failed to change VM hostname: {}".format(ret)
                        )
                        return instance

        return instance

    class Meta:
        model = VirtualMachine
        fields = ["name", "description", "owner", "users", "site", "host"]
