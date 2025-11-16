from django import template

register = template.Library()


@register.filter
def mul(value, arg):
    """Multiplica el valor por el argumento"""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def div(value, arg):
    """Divide el valor por el argumento"""
    try:
        return int(value) / int(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter
def add_value(value, arg):
    """Suma el valor y el argumento"""
    try:
        return int(value) + int(arg)
    except (ValueError, TypeError):
        return 0
