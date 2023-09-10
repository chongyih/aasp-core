from django import template

register = template.Library()


@register.filter(name='has_group')
def has_group(user, group_name):
    if group_name == "educator":
        return user.is_superuser or user.groups.filter(name=group_name).exists()
    return user.groups.filter(name=group_name).exists()


@register.simple_tag(takes_context=True)
def param_replace(context, **kwargs):
    # https://www.caktusgroup.com/blog/2018/10/18/filtering-and-pagination-django/
    d = context['request'].GET.copy()
    for k, v in kwargs.items():
        d[k] = v
    for k in [k for k, v in d.items() if not v]:
        del d[k]
    return d.urlencode()

@register.filter(name='add_class')
def add_class(field, css):
    return field.as_widget(attrs={"class": css})