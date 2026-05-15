from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.models import Profile, UserNotifications, UserPrivacy
from courses.models import Category, Course, Lesson, PracticeAssignment, TestAnswer, TestQuestion


class Command(BaseCommand):
    help = "Create a small local demo dataset for the flash-drive launch package."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset-passwords",
            action="store_true",
            help="Reset demo account passwords to the documented values.",
        )

    def handle(self, *args, **options):
        User = get_user_model()
        accounts = [
            {
                "username": "admin",
                "email": "admin@progage.local",
                "password": "Admin12345!",
                "role": "admin",
                "first_name": "Администратор",
                "last_name": "Progage",
                "is_staff": True,
                "is_superuser": True,
            },
            {
                "username": "teacher",
                "email": "teacher@progage.local",
                "password": "Teacher12345!",
                "role": "teacher",
                "first_name": "Преподаватель",
                "last_name": "Progage",
                "is_staff": False,
                "is_superuser": False,
            },
            {
                "username": "student",
                "email": "student@progage.local",
                "password": "Student12345!",
                "role": "student",
                "first_name": "Студент",
                "last_name": "Progage",
                "is_staff": False,
                "is_superuser": False,
            },
        ]

        users = {}
        for data in accounts:
            password = data.pop("password")
            user, created = User.objects.get_or_create(
                username=data["username"],
                defaults=data,
            )
            if created or options["reset_passwords"]:
                user.set_password(password)
            for field, value in data.items():
                setattr(user, field, value)
            user.save()

            Profile.objects.get_or_create(user=user)
            UserNotifications.objects.get_or_create(user=user)
            UserPrivacy.objects.get_or_create(user=user)
            users[user.username] = user

        category, _ = Category.objects.get_or_create(
            name="Программирование",
            defaults={"description": "Практические курсы по программированию."},
        )

        course, _ = Course.objects.get_or_create(
            title="Демонстрационный курс Python",
            instructor=users["teacher"],
            defaults={
                "description": "Короткий курс для проверки запуска платформы Progage.",
                "category": category,
                "level": "beginner",
                "programming_language": "Python",
            },
        )

        lecture, _ = Lesson.objects.get_or_create(
            course=course,
            title="Вводная лекция",
            defaults={
                "lesson_type": "lecture",
                "content": "Это демонстрационная лекция для локальной проверки проекта.",
                "order": 1,
            },
        )

        test_lesson, _ = Lesson.objects.get_or_create(
            course=course,
            title="Проверочный тест",
            defaults={
                "lesson_type": "test",
                "content": "Ответьте на вопрос, чтобы проверить работу тестирования.",
                "order": 2,
            },
        )
        question, _ = TestQuestion.objects.get_or_create(
            lesson=test_lesson,
            order=1,
            defaults={
                "question_text": "Что выводит команда print('OK')?",
                "question_type": "single",
                "points": 1,
            },
        )
        TestAnswer.objects.get_or_create(
            question=question,
            answer_text="OK",
            defaults={"is_correct": True, "order": 1},
        )
        TestAnswer.objects.get_or_create(
            question=question,
            answer_text="Ошибка",
            defaults={"is_correct": False, "order": 2},
        )

        practice_lesson, _ = Lesson.objects.get_or_create(
            course=course,
            title="Практическое задание",
            defaults={
                "lesson_type": "practice",
                "content": "Напишите программу, которая выводит OK.",
                "order": 3,
            },
        )
        PracticeAssignment.objects.get_or_create(
            lesson=practice_lesson,
            defaults={
                "title": "Вывод строки",
                "description": "Напишите программу, которая выводит строку OK.",
                "requirements": "Программа должна вывести ровно OK.",
                "programming_language": "python",
                "starter_code": "print('OK')",
                "expected_output": "OK",
                "test_cases": [{"expected_output": "OK"}],
            },
        )

        self.stdout.write(self.style.SUCCESS("Demo data is ready."))
