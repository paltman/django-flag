import re

from django import template
from django.utils.translation import ugettext as _

from django.contrib.contenttypes.models import ContentType

from flag.models import FlaggedContent


register = template.Library()


@register.inclusion_tag("flag/flag_form.html", takes_context=True)
def flag(context, content_object, creator_field):
    content_type = ContentType.objects.get(
        app_label = content_object._meta.app_label,
        model = content_object._meta.module_name
    )
    return {
        "content_type": content_type.id,
        "object_id": content_object.id,
        "creator_field": creator_field,
        "request": context["request"],
        "user": context["user"],
    }


@register.tag
def set_is_flagged(parser, token):
    try:
        tag_name, args = token.contents.split(None, 1)
    except ValueError:
        msg = _("%r tag requires exactly 1 argument" % token.contents.split()[0])
        raise template.TemplateSyntaxError, msg
    m = re.search(r'(.*?) as (\w+)', args)
    if not m:
        msg = _("%r tag had invalid arguments" % tag_name)
        raise template.TemplateSyntaxError, msg
    obj, name = m.groups()
    return ProcessIsFlaggedNode(obj, name)


class ProcessIsFlaggedNode(template.Node):
    def __init__(self, obj, name):
        self.context_object = template.Variable(obj)
        self.variable_name = name

    def _is_flagged(self, obj):
        try:
            ct = ContentType.objects.get_for_model(obj)
            flags = FlaggedContent.objects.filter(
                content_type=ct, object_id=obj.id, status='1')
            return len(flags) > 0
        except Exception:
            pass
        return False

    def render(self, context):
        obj = self.context_object.resolve(context)
        context[self.variable_name] = self._is_flagged(obj)
        return ''
