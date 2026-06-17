from django.contrib import admin

from .models import Exercise, Lesson


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'is_completed', 'created_at')
    list_filter = ('is_completed',)


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'lesson', 'decision_type', 'is_completed', 'created_at')
    list_filter = ('is_completed', 'decision_type')
