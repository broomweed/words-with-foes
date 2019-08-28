from django import template

register = template.Library()

@register.filter(expects_localtime=True)
def datefmt(date):
    """ Formats a date... classily ("aug 7 2016") """
    if date is None:
        date = "never"
    else:
        date = "{dt:%b} {dt.day} {dt:%Y}".format(dt=date).lower()
    return date

@register.filter(expects_localtime=True)
def datetimefmt(date):
    """ Formats a date... classily ("aug 7 2016 09:30")
        this version includes time!"""
    if date is None:
        date = "never"
    else:
        date = "{dt:%b} {dt.day} {dt:%Y} {dt:%H}:{dt:%M}".format(dt=date).lower()
    return date

@register.filter(expects_localtime=True)
def datefmt0(date):
    """ Formats a date... classily, but with leading zero on day,
        for columns and such ("aug 07 2016") """
    if date is None:
        date = "never"
    else:
        date = "{dt:%b} {dt:%d} {dt:%Y}".format(dt=date).lower()
    return date
