from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """
    Template filter to get value from dictionary by key
    Usage: {{ my_dict|lookup:key }}
    """
    return dictionary.get(key, 0)

@register.filter
def mul(value, arg):
    """
    Template filter to multiply values
    Usage: {{ value|mul:arg }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def div(value, arg):
    """
    Template filter to divide values
    Usage: {{ value|div:arg }}
    """
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def question_type_color(question_type):
    """
    Returns Bootstrap color class for question type
    """
    colors = {
        'single': 'primary',
        'multiple': 'success',
        'text': 'warning',
        'essay': 'dark'
    }
    return colors.get(question_type, 'secondary')

@register.filter
def submission_color(status):
    """
    Returns Bootstrap color class for submission status
    """
    colors = {
        'pending': 'secondary',
        'running': 'info',
        'success': 'success',
        'error': 'danger',
        'timeout': 'warning',
        'memory': 'danger',
        'wrong': 'danger'
    }
    return colors.get(status, 'secondary')
