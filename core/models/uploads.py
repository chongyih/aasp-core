from django.db import models
from core.models import User, Assessment

def snapshots_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/<course>/<test_name>/<username>/<filename>
    return '{0}/{1}/{2}/{3}'.format(instance.course, instance.test_name, instance.username, filename)

class UploadFile(models.Model):
    username = models.CharField(max_length=100)
    course = models.CharField(max_length=500)
    test_name = models.CharField(max_length=100)
    timestamp = models.CharField(max_length=200)
    image = models.ImageField(null=True, blank=True, upload_to=snapshots_directory_path)
    
    