from django import forms
from django.contrib.auth.forms import UserCreationForm
from store.models import User,Order

class SignUpForm(UserCreationForm):

    class Meta:

        model=User

        fields=["username","email","phone","password1","password2"]

class OtpVerifyForm(forms.Form):

    otp=forms.CharField(max_length=10)


class SignInForm(forms.Form):

    username=forms.CharField()

    password=forms.CharField()

class OrderForm(forms.ModelForm):

    class Meta:

        model=Order

        fields=["address","phone","payment_method"]



