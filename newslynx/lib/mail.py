"""
All things related to sending + recieving of emails.
"""
from newslynx.lib.pkg.validate_email import validate_email


def validate(address):
    """
    Validates an email address via regex.
    """
    return validate_email(address, check_mx=False, verify=False)
