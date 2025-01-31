from django import forms

class DNISearchForm(forms.Form):
    dni = forms.CharField(
        label='',
        max_length=20,
        widget=forms.TextInput(attrs={'placeholder': 'Ingrese su DNI acá'})
    )