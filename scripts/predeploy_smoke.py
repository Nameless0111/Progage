"""
Pre-deploy smoke checks for the Progage Django project.

The script uses an isolated SQLite database and temporary backup/export paths,
so it can be run before a VPS push without touching the real local/server data.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from binascii import unhexlify
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TMP_ROOT = Path(os.environ.get("PROGAGE_SMOKE_TMP", ROOT / ".tmp" / "predeploy_smoke")).resolve()
DB_PATH = TMP_ROOT / "smoke.sqlite3"


def configure_environment() -> None:
    TMP_ROOT.mkdir(parents=True, exist_ok=True)

    os.environ.setdefault("LOAD_ENV_LOCAL", "0")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "progage.settings")
    os.environ["DATABASE_URL"] = f"sqlite:///{DB_PATH.as_posix()}"
    os.environ["BACKUP_ROOT"] = str(TMP_ROOT / "backups")
    os.environ["LOG_DIR"] = str(TMP_ROOT / "logs")
    os.environ["DEBUG"] = "1"
    os.environ["ALLOWED_HOSTS"] = "testserver,localhost,127.0.0.1"


def reset_tmp() -> None:
    if TMP_ROOT.exists():
        shutil.rmtree(TMP_ROOT)
    TMP_ROOT.mkdir(parents=True, exist_ok=True)


def check_response(name: str, response, expected=(200,), allow_redirect=False) -> None:
    status = response.status_code
    ok = status in expected or (allow_redirect and 300 <= status < 400)
    if not ok:
        location = response.headers.get("Location", "")
        body = response.content[:500].decode("utf-8", errors="replace")
        raise AssertionError(f"{name}: status {status}, location={location!r}, body={body!r}")


def main() -> int:
    reset_tmp()
    configure_environment()

    sys.path.insert(0, str(ROOT))

    import django
    from django.core.management import call_command
    from django.test import Client
    from django.urls import reverse
    from django_otp.oath import TOTP

    django.setup()

    from accounts.models import Notification, Profile, User, UserNotifications, UserPrivacy
    from adminpanel.models import ErrorLog
    from chat.models import Message, SupportChat
    from courses.models import (
        Category,
        CodeSubmission,
        Course,
        CourseEnrollment,
        CourseLike,
        CourseReview,
        Lesson,
        PracticeAssignment,
        TestAnswer,
        TestQuestion,
        TestSubmission,
    )

    call_command("migrate", verbosity=0, interactive=False)

    def user(username: str, role: str, **extra):
        instance = User.objects.create_user(
            username=username,
            email=f"{username}@example.test",
            password="StrongPass123",
            first_name=extra.get("first_name", username.title()),
            last_name=extra.get("last_name", "Smoke"),
            role=role,
            is_staff=role == "admin",
            is_superuser=role == "admin",
        )
        Profile.objects.get_or_create(user=instance)
        UserNotifications.objects.get_or_create(user=instance)
        UserPrivacy.objects.get_or_create(user=instance)
        return instance

    admin = user("smoke_admin", "admin", first_name="Admin")
    teacher = user("smoke_teacher", "teacher", first_name="Teacher")
    hidden_teacher = user("smoke_hidden_teacher", "teacher", first_name="Hidden")
    student = user("smoke_student", "student", first_name="Student")
    fresh_student = user("smoke_fresh_student", "student", first_name="Fresh")
    security_student = user("smoke_security", "student", first_name="Security")

    hidden_privacy = hidden_teacher.privacy_settings
    hidden_privacy.show_in_teachers_list = False
    hidden_privacy.save()

    category = Category.objects.create(name="Python", description="Smoke category")
    course = Course.objects.create(
        title="Smoke Python Course",
        description="Course used by predeploy smoke checks.",
        instructor=teacher,
        category=category,
        level="beginner",
        price=999,
        is_published=False,
    )
    assert course.price == 0 and course.is_published is True

    lecture = Lesson.objects.create(course=course, title="Lecture", lesson_type="lecture", content="Text", order=1)
    test_lesson = Lesson.objects.create(course=course, title="Test", lesson_type="test", content="Test", order=2)
    practice_lesson = Lesson.objects.create(course=course, title="Practice", lesson_type="practice", content="Practice", order=3)
    assert lecture.is_free and test_lesson.is_free and practice_lesson.is_free

    question = TestQuestion.objects.create(
        lesson=test_lesson,
        question_text="2 + 2?",
        question_type="single",
        points=5,
        order=1,
    )
    wrong = TestAnswer.objects.create(question=question, answer_text="5", is_correct=False, order=1)
    correct = TestAnswer.objects.create(question=question, answer_text="4", is_correct=True, order=2)

    assignment = PracticeAssignment.objects.create(
        lesson=practice_lesson,
        title="Print",
        description="Print text",
        requirements="Print OK",
        programming_language="python",
        starter_code="print('OK')",
        expected_output="OK",
        test_cases=[{"expected_output": "OK"}],
        max_attempts=3,
    )

    CourseEnrollment.objects.create(user=student, course=course)
    Notification.objects.create(user=student, notification_type="system", title="Smoke", message="Notification")

    anonymous_student = user("smoke_anon", "student", first_name="Anon")
    anon_privacy = anonymous_student.privacy_settings
    anon_privacy.anonymous_mode = True
    anon_privacy.public_profile = True
    anon_privacy.show_email = True
    anon_privacy.save()
    assert anonymous_student.public_display_name == "Аноним"

    anonymous_teacher = user("smoke_anon_teacher", "teacher", first_name="AnonTeacher")
    anon_teacher_privacy = anonymous_teacher.privacy_settings
    anon_teacher_privacy.anonymous_mode = True
    anon_teacher_privacy.show_in_teachers_list = True
    anon_teacher_privacy.save()
    Course.objects.create(
        title="Anonymous teacher course",
        description="Visible anonymous teacher course.",
        instructor=anonymous_teacher,
        category=category,
        level="beginner",
    )

    anon = Client()
    check_response("home", anon.get(reverse("home")))
    check_response("course list", anon.get(reverse("courses:course_list")))
    check_response("course detail", anon.get(reverse("courses:course_detail", args=[course.id])))
    check_response("login page", anon.get(reverse("accounts:login")))
    check_response("register page", anon.get(reverse("accounts:register")))
    check_response("teachers list", anon.get(reverse("accounts:teachers_list")))
    check_response("teacher profile", anon.get(reverse("accounts:teacher_profile", args=[teacher.id])))
    check_response("api test page", anon.get(reverse("courses:api_test_page")))
    api_response = anon.post(
        reverse("courses:test_code_api"),
        data=json.dumps({"language": "python", "code": "print('OK')"}),
        content_type="application/json",
    )
    check_response("api code test", api_response)
    assert "success" in api_response.json()

    fresh_client = Client()
    assert fresh_client.login(username=fresh_student.username, password="StrongPass123")
    check_response("fresh student enroll", fresh_client.post(reverse("courses:enroll_course", args=[course.id]), follow=True))
    check_response("fresh student duplicate enroll", fresh_client.post(reverse("courses:enroll_course", args=[course.id]), follow=True))

    security_client = Client()
    assert security_client.login(username=security_student.username, password="StrongPass123")
    check_response("security 2fa setup page", security_client.get(reverse("accounts:two_factor_setup")))
    two_factor_response = security_client.post(
        reverse("accounts:generate_2fa_secret"),
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    check_response("security generate 2fa secret", two_factor_response)
    assert two_factor_response.json()["success"] is True
    secret = security_client.session["2fa_secret"]
    token = str(TOTP(unhexlify(secret)).token()).zfill(6)
    verify_response = security_client.post(
        reverse("accounts:verify_2fa_setup"),
        data=json.dumps({"code": token}),
        content_type="application/json",
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    check_response("security verify 2fa setup", verify_response)
    assert verify_response.json()["success"] is True
    enable_response = security_client.post(
        reverse("accounts:enable_2fa"),
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    check_response("security enable 2fa", enable_response)
    assert enable_response.json()["success"] is True
    disable_response = security_client.post(reverse("accounts:disable_2fa"), follow=True)
    check_response("security disable 2fa", disable_response)
    wrong_password_response = security_client.post(
        reverse("accounts:change_password"),
        {
            "current_password": "wrong",
            "new_password": "NewStrongPass123",
            "confirm_password": "NewStrongPass123",
        },
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    check_response("security wrong password change", wrong_password_response)
    assert wrong_password_response.json()["success"] is False
    password_response = security_client.post(
        reverse("accounts:change_password"),
        {
            "current_password": "StrongPass123",
            "new_password": "NewStrongPass123",
            "confirm_password": "NewStrongPass123",
        },
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    check_response("security password change", password_response)
    assert password_response.json()["success"] is True
    relogin_client = Client()
    assert relogin_client.login(username=security_student.username, password="NewStrongPass123")

    email_login = Client()
    check_response(
        "login by email",
        email_login.post(
            reverse("accounts:login"),
            {"username": student.email, "password": "StrongPass123"},
            follow=True,
        ),
    )

    student_client = Client()
    assert student_client.login(username=student.username, password="StrongPass123")
    check_response("student dashboard", student_client.get(reverse("accounts:dashboard")))
    check_response("student profile", student_client.get(reverse("accounts:profile")))
    check_response("student settings", student_client.get(reverse("accounts:settings")))
    check_response("student notifications", student_client.get(reverse("accounts:notifications")))
    check_response("student certificates", student_client.get(reverse("accounts:certificates")))
    check_response(
        "student mark notification",
        student_client.post(reverse("accounts:mark_notification_read", args=[Notification.objects.filter(user=student).first().id]), follow=True),
    )
    check_response("student mark all notifications", student_client.post(reverse("accounts:notifications"), {"mark_all_read": "1"}, follow=True))
    update_notifications_response = student_client.post(
        reverse("accounts:update_notifications"),
        {"support_messages": "on"},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    check_response("student update notifications", update_notifications_response)
    assert update_notifications_response.json()["success"] is True
    update_privacy_response = student_client.post(
        reverse("accounts:update_privacy"),
        {"anonymous_mode": "on", "public_profile": "on", "show_email": "on", "show_progress": "on"},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    check_response("student update privacy", update_privacy_response)
    student.refresh_from_db()
    assert student.privacy_settings.anonymous_mode is True
    assert student.privacy_settings.public_profile is False
    check_response("student chat list", student_client.get(reverse("chat:chat_list")))
    check_response("student start chat page", student_client.get(reverse("chat:start_chat")))
    check_response("student start chat post", student_client.post(reverse("chat:start_chat"), {"subject": "Need help"}, follow=True))
    chat = SupportChat.objects.get(user=student, subject="Need help")
    check_response("student send message", student_client.post(reverse("chat:send_message", args=[chat.id]), {"content": "Hello"}, follow=True))
    check_response("student refresh chat", student_client.get(reverse("chat:refresh_chat", args=[chat.id])))
    check_response("student lesson", student_client.get(reverse("courses:lesson_view", args=[course.id, lecture.id])))
    check_response("student complete lesson", student_client.post(reverse("courses:complete_lesson", args=[course.id, lecture.id]), follow=True))
    check_response("student add comment", student_client.post(reverse("courses:add_comment", args=[course.id, lecture.id]), {"content": "Good"}, follow=True))
    check_response("student like course", student_client.post(reverse("courses:toggle_like", args=[course.id])))
    check_response("student review course", student_client.post(reverse("courses:submit_review", args=[course.id]), {"rating": "5", "comment": "Useful"}, follow=True))
    check_response("student take test", student_client.get(reverse("courses:take_test", args=[test_lesson.id])))
    check_response(
        "student submit test",
        student_client.post(reverse("courses:submit_test", args=[test_lesson.id]), {f"question_{question.id}": str(correct.id)}),
    )
    submission = TestSubmission.objects.get(user=student, lesson=test_lesson)
    check_response("student test result", student_client.get(reverse("courses:test_result", args=[test_lesson.id, submission.id])))
    check_response(
        "student duplicate submit test",
        student_client.post(reverse("courses:submit_test", args=[test_lesson.id]), {f"question_{question.id}": str(wrong.id)}),
    )
    check_response("student practice lesson", student_client.get(reverse("courses:lesson_view", args=[course.id, practice_lesson.id])))
    check_response("student submit code", student_client.post(reverse("courses:submit_code", args=[practice_lesson.id]), {"code": "print('OK')"}, follow=True))
    assert CodeSubmission.objects.filter(assignment=assignment, user=student).exists()

    teacher_client = Client()
    assert teacher_client.login(username=teacher.username, password="StrongPass123")
    check_response("teacher dashboard", teacher_client.get(reverse("courses:teacher_dashboard")))
    check_response(
        "teacher create course post",
        teacher_client.post(
            reverse("courses:teacher_create_course"),
            {
                "title": "Smoke teacher created course",
                "description": "Created through teacher CRUD smoke.",
                "category": str(category.id),
                "level": "beginner",
                "programming_language": "Python",
            },
            follow=True,
        ),
    )
    teacher_created_course = Course.objects.get(title="Smoke teacher created course")
    check_response(
        "teacher edit created course",
        teacher_client.post(
            reverse("courses:teacher_edit_course", args=[teacher_created_course.id]),
            {
                "title": "Smoke teacher edited course",
                "description": "Edited through teacher CRUD smoke.",
                "category": str(category.id),
                "level": "intermediate",
                "programming_language": "Python",
            },
            follow=True,
        ),
    )
    teacher_created_course.refresh_from_db()
    check_response(
        "teacher create lesson",
        teacher_client.post(
            reverse("courses:teacher_create_lesson", args=[teacher_created_course.id]),
            {
                "title": "Smoke created lesson",
                "lesson_type": "lecture",
                "content": "Teacher-created lesson content.",
                "order": "1",
            },
            follow=True,
        ),
    )
    created_lesson = Lesson.objects.get(course=teacher_created_course, title="Smoke created lesson")
    check_response(
        "teacher edit lesson",
        teacher_client.post(
            reverse("courses:teacher_edit_lesson", args=[teacher_created_course.id, created_lesson.id]),
            {
                "title": "Smoke edited lesson",
                "lesson_type": "lecture",
                "content": "Edited lesson content.",
                "order": "1",
            },
            follow=True,
        ),
    )
    check_response("teacher course lessons", teacher_client.get(reverse("courses:teacher_course_lessons", args=[course.id])))
    check_response("teacher create course page", teacher_client.get(reverse("courses:teacher_create_course")))
    check_response("teacher edit course page", teacher_client.get(reverse("courses:teacher_edit_course", args=[course.id])))
    check_response("teacher test constructor", teacher_client.get(reverse("courses:test_constructor", args=[test_lesson.id])))
    check_response(
        "teacher add test question",
        teacher_client.post(
            reverse("courses:test_constructor", args=[test_lesson.id]),
            {
                "question_text": "Smoke new question?",
                "question_type": "single",
                "points": "1",
                "explanation": "",
                "is_required": "on",
                "answers[]": ["yes", "no"],
                "correct_answer": "0",
            },
            follow=True,
        ),
    )
    new_question = TestQuestion.objects.filter(lesson=test_lesson, question_text="Smoke new question?").latest("id")
    check_response("teacher edit test question page", teacher_client.get(reverse("courses:edit_test_question", args=[test_lesson.id, new_question.id])))
    check_response("teacher delete test question page", teacher_client.get(reverse("courses:delete_test_question", args=[test_lesson.id, new_question.id])))
    check_response("teacher delete test question", teacher_client.post(reverse("courses:delete_test_question", args=[test_lesson.id, new_question.id]), follow=True))
    check_response("teacher practice assignment", teacher_client.get(reverse("courses:practice_assignment", args=[practice_lesson.id])))
    check_response(
        "teacher save practice assignment",
        teacher_client.post(
            reverse("courses:practice_assignment", args=[practice_lesson.id]),
            {
                "title": "Print",
                "description": "Print text",
                "requirements": "Print OK",
                "programming_language": "python",
                "starter_code": "print('OK')",
                "expected_output": "OK",
                "time_limit": "5",
                "memory_limit": "256",
                "max_attempts": "3",
                "max_grade": "100",
                "is_published": "on",
                "test_output_0": "OK",
            },
            follow=True,
        ),
    )
    code_submission = CodeSubmission.objects.filter(assignment=assignment, user=student).first()
    check_response("teacher review submission", teacher_client.get(reverse("courses:review_submission", args=[code_submission.id])))
    check_response(
        "teacher approve submission",
        teacher_client.post(
            reverse("courses:review_submission", args=[code_submission.id]),
            {"action": "approve", "grade": "100", "feedback": "Accepted"},
            follow=True,
        ),
    )
    check_response("teacher delete lesson", teacher_client.post(reverse("courses:teacher_delete_lesson", args=[teacher_created_course.id, created_lesson.id]), follow=True))
    check_response("teacher delete course", teacher_client.post(reverse("courses:teacher_delete_course", args=[teacher_created_course.id]), follow=True))

    admin_client = Client()
    assert admin_client.login(username=admin.username, password="StrongPass123")
    admin_pages = [
        ("admin dashboard", reverse("adminpanel:dashboard")),
        ("admin users", reverse("adminpanel:user_list")),
        ("admin courses", reverse("adminpanel:course_list")),
        ("admin enrollments", reverse("adminpanel:enrollment_list")),
        ("admin likes", reverse("adminpanel:like_list")),
        ("admin reviews", reverse("adminpanel:review_list")),
        ("admin comments", reverse("adminpanel:comment_list")),
        ("admin statistics", reverse("adminpanel:statistics")),
        ("admin activity logs", reverse("adminpanel:activity_logs")),
        ("admin system logs", reverse("adminpanel:system_logs")),
        ("admin error logs", reverse("adminpanel:error_logs")),
        ("admin sessions", reverse("adminpanel:user_sessions")),
        ("admin popular content", reverse("adminpanel:popular_content")),
        ("admin backup logs", reverse("adminpanel:backup_logs")),
        ("admin chats", reverse("adminpanel:chat_management")),
    ]
    for name, url in admin_pages:
        check_response(name, admin_client.get(url))

    check_response("admin user create page", admin_client.get(reverse("adminpanel:user_create")))
    check_response(
        "admin user create",
        admin_client.post(
            reverse("adminpanel:user_create"),
            {
                "username": "smoke_admin_created",
                "email": "smoke_admin_created@example.test",
                "first_name": "Created",
                "last_name": "User",
                "role": "student",
                "is_active": "on",
                "password": "StrongPass123",
            },
            follow=True,
        ),
    )
    admin_created_user = User.objects.get(username="smoke_admin_created")
    check_response("admin user edit page", admin_client.get(reverse("adminpanel:user_edit", args=[admin_created_user.id])))
    check_response(
        "admin user edit",
        admin_client.post(
            reverse("adminpanel:user_edit", args=[admin_created_user.id]),
            {
                "username": admin_created_user.username,
                "email": admin_created_user.email,
                "first_name": "Edited",
                "last_name": "User",
                "role": "student",
                "is_active": "on",
                "password": "",
            },
            follow=True,
        ),
    )
    check_response("admin user delete page", admin_client.get(reverse("adminpanel:user_delete", args=[admin_created_user.id])))
    check_response("admin user delete", admin_client.post(reverse("adminpanel:user_delete", args=[admin_created_user.id]), follow=True))
    check_response("admin course create page", admin_client.get(reverse("adminpanel:course_create")))
    check_response(
        "admin course create",
        admin_client.post(
            reverse("adminpanel:course_create"),
            {
                "title": "Smoke admin course",
                "description": "Created by admin smoke.",
                "instructor": str(teacher.id),
                "category": str(category.id),
                "level": "beginner",
            },
            follow=True,
        ),
    )
    admin_course = Course.objects.get(title="Smoke admin course")
    check_response("admin course edit page", admin_client.get(reverse("adminpanel:course_edit", args=[admin_course.id])))
    check_response(
        "admin course edit",
        admin_client.post(
            reverse("adminpanel:course_edit", args=[admin_course.id]),
            {
                "title": "Smoke admin course edited",
                "description": "Edited by admin smoke.",
                "instructor": str(teacher.id),
                "category": str(category.id),
                "level": "advanced",
            },
            follow=True,
        ),
    )
    check_response("admin course delete page", admin_client.get(reverse("adminpanel:course_delete", args=[admin_course.id])))
    check_response("admin course delete", admin_client.post(reverse("adminpanel:course_delete", args=[admin_course.id]), follow=True))
    check_response("admin export json", admin_client.get(reverse("adminpanel:export_data", args=["json"])))
    check_response("admin export csv", admin_client.get(reverse("adminpanel:export_data", args=["csv"])))
    check_response("admin create backup", admin_client.post(reverse("adminpanel:create_backup"), follow=True))
    backup_file = next((item["filename"] for item in __import__("adminpanel.backup_utils", fromlist=["SystemBackup"]).SystemBackup().list_backups()), None)
    if backup_file:
        check_response("admin download backup", admin_client.get(reverse("adminpanel:download_backup", args=[backup_file])), expected=(200,))
        check_response("admin restore backup page", admin_client.get(reverse("adminpanel:restore_backup", args=[backup_file])))
        check_response("admin delete backup", admin_client.post(reverse("adminpanel:delete_backup", args=[backup_file]), follow=True))
    check_response("admin close chat", admin_client.post(reverse("chat:close_chat", args=[chat.id]), follow=True))
    check_response("admin reopen chat", admin_client.post(reverse("adminpanel:reopen_chat", args=[chat.id]), follow=True))

    delete_enrollment = CourseEnrollment.objects.create(user=security_student, course=course)
    delete_like = CourseLike.objects.create(user=fresh_student, course=course)
    delete_review = CourseReview.objects.create(user=fresh_student, course=course, rating=4, comment="Admin delete smoke")
    check_response("admin enrollment delete page", admin_client.get(reverse("adminpanel:enrollment_delete", args=[delete_enrollment.id])))
    check_response("admin enrollment delete", admin_client.post(reverse("adminpanel:enrollment_delete", args=[delete_enrollment.id]), follow=True))
    check_response("admin like delete page", admin_client.get(reverse("adminpanel:like_delete", args=[delete_like.id])))
    check_response("admin like delete", admin_client.post(reverse("adminpanel:like_delete", args=[delete_like.id]), follow=True))
    check_response("admin review delete page", admin_client.get(reverse("adminpanel:review_delete", args=[delete_review.id])))
    check_response("admin review delete", admin_client.post(reverse("adminpanel:review_delete", args=[delete_review.id]), follow=True))

    error = ErrorLog.objects.create(error_type="other", message="Smoke", url="http://testserver/smoke/")
    check_response("admin resolve error", admin_client.post(reverse("adminpanel:resolve_error", args=[error.id]), follow=True))

    print("OK: Progage predeploy smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
