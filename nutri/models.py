from django.db import models

class NutriUser(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    age = models.IntegerField()
    gender = models.CharField(max_length=50)
    health_conditions = models.TextField()
    weight = models.FloatField()
    height = models.FloatField()
    dietary_preferences = models.TextField()
    goal = models.CharField(max_length=255)

    @property
    def bmi(self):
        return self.weight / (self.height / 100) ** 2

    class Meta:
        db_table = 'nutriusers'