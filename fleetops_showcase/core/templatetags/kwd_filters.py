from django import template
from decimal import Decimal, InvalidOperation

register = template.Library()


@register.filter
def kwd(value):
    """Format a decimal value as Kuwaiti Dinar with 3 decimal places.
    
    Usage: {{ invoice.cash|kwd }} → "1,234.500 KD"
    """
    try:
        d = Decimal(str(value))
        formatted = f"{d:,.3f}"
        return f"{formatted} KD"
    except (InvalidOperation, TypeError, ValueError):
        return "0.000 KD"


@register.filter
def format_hours(value):
    """Format decimal hours as Xh Ym.
    
    Usage: {{ total_hours|format_hours }} → "168h 30m"
    """
    try:
        total = float(value)
        hours = int(total)
        minutes = int((total - hours) * 60)
        return f"{hours}h {minutes}m"
    except (TypeError, ValueError):
        return "0h 0m"
