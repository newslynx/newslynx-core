
# API ERRORS #


class APIError(Exception):

    """
    A generic error for throwing api errors.
    """

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = str(self.message)
        rv['error'] = self.__class__.__name__
        rv['status_code'] = self.status_code
        return rv


class RequestError(APIError):
    status_code = 400


class AuthError(APIError):
    status_code = 401


class ForbiddenError(APIError):
    status_code = 403


class NotFoundError(APIError):
    status_code = 404


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
    An error in the API Client.
    """
    status_code = 500
