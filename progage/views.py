from django.shortcuts import render

def home_view(request):
    context = {
        'current_year': 2026,
        'users_count': 1000,
        'courses_count': 50,
        'instructors_count': 25,
        'certificates_count': 500,
    }
    return render(request, 'home.html', context)
