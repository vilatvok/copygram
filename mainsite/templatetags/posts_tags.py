from django import template

from taggit.models import Tag

register = template.Library()

@register.inclusion_tag('mainsite/includes/tags.html')
def get_tags():
    tags = Tag.objects.all()
    return {'tags': tags}