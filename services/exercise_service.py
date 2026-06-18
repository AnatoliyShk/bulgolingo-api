from django.conf import settings
from learning_paths import Exercise, Lesson
from services.gemini_service import GeminiService

class ExerciseService:
    def __init__(self, gemini_service: GeminiService):
        self.gemini_service = gemini_service


    def get_incomplete_lesson(self):
        return (
            Lesson.objects.filter(exercises__is_completed=False)
            .order_by('created_at')
            .first()
        )

    def get_exercise(self, exercise_id: int):
        return Exercise.objects.select_related('lesson').get(pk=exercise_id)

    def complete_exercise(self, exercise: Exercise):
        exercise.is_completed = True
        exercise.save(update_fields=['is_completed'])
        return exercise

    def get_uncompleted_fill_in_the_blank(self, lesson: Lesson):
        exercises = [
            e for e in lesson.exercises.all()
            if e.decision_type == 'fill_in_the_blank' and not e.is_completed
        ]
        if not exercises:
            return None
        return min(exercises, key=lambda e: e.created_at)

    def create_exercise(self, decision_type: str) -> Exercise:
        exercise_data = self.gemini_service.generate_exercise()
        exercise = Exercise.objects.create(
            name=f"Exercise for clause '{exercise_data['clause']['sentence']}'",
            clause=exercise_data,
            decision_type=decision_type,
        )
        return exercise