from django.db import models


class LearningPath(models.Model):
    name = models.CharField(max_length=255)
    language = models.CharField(max_length=255)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'learning_paths'

    def __str__(self):
        return self.name

class Lesson(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'lessons'

    def __str__(self):
        return self.name


class Exercise(models.Model):
    name = models.CharField(max_length=255)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='exercises')
    clause = models.JSONField()
    decision_type = models.CharField(max_length=255, default='fill_in_the_blank')
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'exercises'

    def __str__(self):
        return self.name
