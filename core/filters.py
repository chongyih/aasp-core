# Powered by the django_filters package: https://github.com/carltongibson/django-filter/

import django_filters

from core.models import User, CourseGroup


class CourseStudentFilter(django_filters.FilterSet):

    course_group = django_filters.ModelChoiceFilter(queryset=CourseGroup.objects.none(), label="Course Group", method="filter_group")

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'course_group']

    def __init__(self, course_groups, *args, **kwargs):
        super(CourseStudentFilter, self).__init__(*args, **kwargs)
        self.filters['course_group'].queryset = course_groups
        self.filters['first_name'].lookup_expr = "icontains"
        self.filters['last_name'].lookup_expr = "icontains"
        self.filters['username'].lookup_expr = "iexact"

    @staticmethod
    def filter_group(queryset, name, value):
        return queryset.filter(enrolled_groups=value)
