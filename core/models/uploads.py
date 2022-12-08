from django.db import models


def snapshots_directory_path(instance, filename):
    course = instance.course.replace(' ', '_').replace('/', '-')
    test_name = instance.test_name.replace('/', '_')

    # file will be uploaded to MEDIA_ROOT/<course>/<test_name>/<username>/<filename>
    return '{0}/{1}/{2}/{3}'.format(course, test_name, instance.candidate.username, filename)

class UploadFile(models.Model):
    candidate = models.ForeignKey("User", null=False, blank=False, on_delete=models.PROTECT)
    course = models.CharField(max_length=500)
    test_name = models.CharField(max_length=100)
    timestamp = models.CharField(max_length=200)
    image = models.ImageField(null=True, blank=True, upload_to=snapshots_directory_path)    
    