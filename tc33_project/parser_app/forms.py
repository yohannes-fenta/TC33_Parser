# parser_app/forms.py

from django import forms

class UploadFileForm(forms.Form):
    file = forms.FileField(label='Select a TC-33 ASCII File (.txt, .ascii)')