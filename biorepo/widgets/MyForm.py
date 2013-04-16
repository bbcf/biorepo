from tw2.forms.fields import FormField, ContainerMixin, SubmitButton, Form
from tw2.api import lazystring
import logging
log = logging.getLogger(__name__)

__all__ = ["MyForm"]
_ = lazystring


class MyForm(Form):
    """
    A base class for all forms.

    Use this class as a base for your custom form. You should override it's
    template because it's a dummy one which does not display errors, help text
    or anything besides it's fields.

    The form will take care of setting its ``enctype`` if it contains any
    FileField
    """
    template = "biorepo.templates.MyForm"
