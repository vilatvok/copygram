from django.core import validators


class UsernameValidator(validators.RegexValidator):
    regex = r'^(?=.*[a-zA-Z])[a-zA-Z0-9._]+$'
    message = (
        "Enter a valid username. This value may contain at least one character, "
        "numbers, and ./_ characters."
    )
    flags = 0
