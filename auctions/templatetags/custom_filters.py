from django import template

register = template.Library()

@register.filter(name='hide_middle_chars')
def hide_middle_chars(username):
    if len(username) > 2:
        return username[0] + '*'*(len(username)-2) + username[-1]
    else:
        return username
