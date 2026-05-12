from django.shortcuts import render
from django.db.models import Count
from courses.models import Course

def home_view(request):
    from courses.models import Course, Category, CourseLike
    from accounts.models import User
    
    # Получаем все опубликованные курсы
    all_courses = Course.objects.filter(is_published=True).select_related('instructor', 'category')
    
    print(f"DEBUG: Found {all_courses.count()} published courses")
    
    # Проверим есть ли курсы без категорий
    courses_without_category = all_courses.filter(category__isnull=True)
    if courses_without_category.exists():
        print(f"DEBUG: Found {courses_without_category.count()} courses without category")
        # Получаем или создаем категорию
        category, _ = Category.objects.get_or_create(
            name="Программирование",
            defaults={'description': 'Курсы по программированию'}
        )
        # Обновим курсы без категории
        courses_without_category.update(category=category)
        print(f"DEBUG: Updated {courses_without_category.count()} courses with category")
        # Обновляем запрос
        all_courses = Course.objects.filter(is_published=True).select_related('instructor', 'category')
    
        
    # Получаем популярные курсы
    popular_courses = all_courses.annotate(
        like_count=Count('likes')
    ).order_by('-like_count')[:8]
    
    print(f"DEBUG: Popular courses count: {len(popular_courses)}")
    for course in popular_courses:
        print(f"DEBUG: - {course.title} (likes: {getattr(course, 'like_count', 0)})")
    
    context = {
        'current_year': 2026,
        'users_count': 1000,
        'courses_count': 50,
        'instructors_count': 25,
        'certificates_count': 500,
        'popular_courses': popular_courses,
    }
    return render(request, 'index.html', context)
