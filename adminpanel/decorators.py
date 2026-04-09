from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Необходимо войти в систему.')
            return redirect('accounts:login')
        if request.user.role != 'admin':
            messages.error(request, 'У вас нет доступа к админ-панели.')
            return redirect('courses:course_list')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
