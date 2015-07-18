"""
Everything errors.
"""


# API Errors #
class JobError(Exception):
    pass


class RequestError(Exception):
    status_code = 400


class AuthError(Exception):
    status_code = 401


class ForbiddenError(Exception):
    status_code = 403


class NotFoundError(Exception):
    status_code = 404


class ConflictError(Exception):
    status_code = 409


class UnprocessableEntityError(Exception):
    status_code = 422


class InternalServerError(Exception):
    status_code = 500


# Internal Errors #

class SousChefSchemaError(Exception):
    """
    An error that's thrown when a SousChef has an invalid schema.
    """
    status_code = 400


class SousChefInitError(Exception):
    """
    An error that's thrown when a SousChef is not properly initialized.
    """
    status_code = 400


class MerlynneError(Exception):
    """
    An error that's thrown when a Merlynne is not properly initialized.
    """
    status_code = 400


class RecipeSchemaError(Exception):
    """
    An error that's thrown when a Recipe has an invalid schema
    according to it's SousChef.
    """
    status_code = 400


class SearchStringError(Exception):
    """
    An error that's thrown when a search string is invalid.
    """
    status_code = 400


class ConfigError(Exception):
    """
    An error that's thrown when something is wrong with the config file.
    """
    status_code = 400


class ClientError(Exception):
    """
    An error that's thrown when something is wrong on the API Client side.
    """
    status_code = 500


# a lookup of all errors
ERRORS = {
    "RequestError": RequestError,
    "AuthError": AuthError,
    "ForbiddenError": ForbiddenError,
    "NotFoundError": NotFoundError,
    "ConflictError": ConflictError,
    "UnprocessableEntityError": UnprocessableEntityError,
    "InternalServerError": InternalServerError,
    "SousChefSchemaError": SousChefSchemaError,
    "RecipeSchemaError": RecipeSchemaError,
    "SearchStringError": SearchStringError,
    "ConfigError": ConfigError,
    "ClientError": ClientError
}
