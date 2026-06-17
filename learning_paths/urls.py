from django.urls import path

from . import views

urlpatterns = [
    path('lessons/', views.LessonListView.as_view(), name='lesson-list'),
    path('lessons/<int:lesson_id>/', views.LessonDetailView.as_view(), name='lesson-detail'),
]
