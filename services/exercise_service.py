from django.conf import settings
from learning_paths import Exercise, Lesson

class ExerciseService:
    @staticmethod
    def get_incomplete_lesson():
        return (
            Lesson.objects.filter(exercises__is_completed=False)
            .order_by('created_at')
            .first()
        )

    @staticmethod
    def get_exercise(exercise_id: int):
        return Exercise.objects.select_related('lesson').get(pk=exercise_id)

    @staticmethod
    def complete_exercise(exercise: Exercise):
        exercise.is_completed = True
        exercise.save(update_fields=['is_completed'])
        return exercise

    @staticmethod
    def get_uncompleted_fill_in_the_blank(lesson: Lesson):
        exercises = [
            e for e in lesson.exercises.all()
            if e.decision_type == 'fill_in_the_blank' and not e.is_completed
        ]
        if not exercises:
            return None
        return min(exercises, key=lambda e: e.created_at)