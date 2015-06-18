
class Error(Exception):
    """
    A generic Exception with status_code
    """
    def __init__(self, *args, **kw):
        Exception.__init__(self, *args, **kw)


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
