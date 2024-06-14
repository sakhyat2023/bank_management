from typing import Any
from django import forms
from django.db import models
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .constants import gender_type, account_type
from .models import UserBankAccount, UserAddress


class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    email = forms.EmailField()
    birth_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    account_type = forms.ChoiceField(choices=account_type)
    gender = forms.ChoiceField(choices=gender_type)
    street_address = forms.CharField(max_length=100)
    city = forms.CharField(max_length=100)
    postal_code = forms.IntegerField()
    country = forms.CharField(max_length=100)

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
            "birth_date",
            "account_type",
            "gender",
            "street_address",
            "city",
            "postal_code",
            "country",
        ]

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit == True:
            user.save()
            birth_date = self.cleaned_data.get("birth_date")
            account_type = self.cleaned_data.get("account_type")
            gender = self.cleaned_data.get("gender")
            postal_code = self.cleaned_data.get("postal_code")
            country = self.cleaned_data.get("country")
            city = self.cleaned_data.get("city")
            street_address = self.cleaned_data.get("street_address")

            UserAddress.objects.create(
                user=user,
                street_address=street_address,
                city=city,
                postal_code=postal_code,
                country=country,
            )

            UserBankAccount.objects.create(
                user=user,
                account_number=143590 + user.id,
                account_type=account_type,
                birth_date=birth_date,
                gender=gender,
            )

            return user

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        for field in self.fields:
            self.fields[field].widget.attrs.update({"class": "form-control w-100"})


class UpdateUserForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    email = forms.EmailField()
    birth_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    account_type = forms.ChoiceField(choices=account_type)
    gender = forms.ChoiceField(choices=gender_type)
    street_address = forms.CharField(max_length=100)
    city = forms.CharField(max_length=100)
    postal_code = forms.IntegerField()
    country = forms.CharField(max_length=100)

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
        ]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        for field in self.fields:
            self.fields[field].widget.attrs.update({"class": "form-control w-100"})

        if self.instance:
            try:
                user_account = self.instance.account
                user_address = self.instance.address
            except UserBankAccount.DoesNotExist:
                user_account = None
                user_address = None

            if user_account:
                self.fields["account_type"].initial = user_account.account_type
                self.fields["gender"].initial = user_account.gender
                self.fields["birth_date"].initial = user_account.birth_date
                self.fields["street_address"].initial = user_address.street_address
                self.fields["city"].initial = user_address.city
                self.fields["postal_code"].initial = user_address.postal_code
                self.fields["country"].initial = user_address.country

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            user_account, created = UserBankAccount.objects.get_or_create(user=user)
            user_address, created = UserAddress.objects.get_or_create(user=user)
            user_account.account_type = self.cleaned_data["account_type"]
            user_account.gender = self.cleaned_data["gender"]
            user_account.birth_date = self.cleaned_data["birth_date"]
            user_account.save()

            user_address.street_address = self.cleaned_data["street_address"]
            user_address.city = self.cleaned_data["city"]
            user_address.postal_code = self.cleaned_data["postal_code"]
            user_address.country = self.cleaned_data["country"]
            user_address.save()

            return user
