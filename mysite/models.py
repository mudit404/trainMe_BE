from django.db import models

# Create your models here.
class User(models.Model):
    email = models.EmailField(unique=True, max_length=255)
    password = models.CharField(max_length=255)
    username = models.CharField(unique=True, max_length=255)
    courses = models.ForeignKey('Course', on_delete=models.SET_NULL, null=True, blank=True)
    refresh_token = models.TextField(null=True)
    access_token = models.TextField(null=True)

    def __str__(self):
        return self.name
    
class Course(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    image_url = models.URLField(max_length=2083, blank=True, null=True)

    def __str__(self):
        return self.title
    
# class Subscription(models.Model):
#     title = models.CharField(max_length=255)
#     price = models.DecimalField(max_digits=10, decimal_places=2)
#     valid_till = models.DateField(blank=True, null=True)
#     description = models.TextField(blank=True, null=True)
#     course = models.ForeignKey(Course, on_delete=models.CASCADE)

#     def __str__(self):
#         return self.title
    
# class CourseContent(models.Model):
#     course = models.ForeignKey(Course, on_delete=models.CASCADE)
#     title = models.CharField(max_length=255)
#     image_url = models.URLField(max_length=2083, blank=True, null=True)
#     content = models.TextField()

#     def __str__(self):
#         return self.title