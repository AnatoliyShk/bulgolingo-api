import json

from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import Lesson


@method_decorator(csrf_exempt, name='dispatch')
class LessonListView(View):
    def get(self, request):
        lessons = list(Lesson.objects.values('id', 'name', 'description'))
        return JsonResponse(lessons, safe=False)

    def post(self, request):
        data = json.loads(request.body)
        lesson = Lesson.objects.create(
            name=data['name'],
            description=data.get('description', ''),
        )
        return JsonResponse(
            {'id': lesson.id, 'name': lesson.name, 'description': lesson.description},
            status=201,
        )


@method_decorator(csrf_exempt, name='dispatch')
class LessonDetailView(View):
    def get(self, request, lesson_id):
        try:
            lesson = Lesson.objects.get(pk=lesson_id)
        except Lesson.DoesNotExist:
            return JsonResponse({'detail': 'Lesson not found'}, status=404)
        return JsonResponse({'id': lesson.id, 'name': lesson.name, 'description': lesson.description})

    def delete(self, request, lesson_id):
        try:
            lesson = Lesson.objects.get(pk=lesson_id)
        except Lesson.DoesNotExist:
            return JsonResponse({'detail': 'Lesson not found'}, status=404)
        lesson.delete()
        return JsonResponse({}, status=204)
