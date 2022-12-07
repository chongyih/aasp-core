from django.forms import models
from core.models import UploadFile

class UploadFileForm(models.ModelForm):
    class Meta:
        model = UploadFile
        fields = ['course', 'test_name', 'timestamp', 'image']