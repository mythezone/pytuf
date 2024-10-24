from django import template

register = template.Library()

def replace_slash(value):
    value = value.replace("/", "_")
    value = value.replace("?","+")
    value = value.replace("=","-")
    return value

def replace_back_slash(value):
    value = value.replace("\\", "/")
    return value

register.filter("replace_slash",replace_slash)
register.filter("replace_back_slash",replace_back_slash)