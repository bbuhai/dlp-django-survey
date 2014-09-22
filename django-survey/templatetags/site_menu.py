from django import template

register = template.Library()


@register.inclusion_tag('menu.html')
def site_menu(item):
    return {'item': item}