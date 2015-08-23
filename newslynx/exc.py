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


# Sous Chef Errors #

class SousChefSchemaError(Exception):

    """
    An error that's thrown when a SousChef has an invalid schema.
    """
    status_code = 400


class SousChefInstallError(Exception):

    """
    An error that's thrown when a SousChef cannot be installed.
    """
    status_code = 400


class SousChefInitError(Exception):

    """
    An error that's thrown when a SousChef is not properly initialized.
    """
    status_code = 400


class SousChefDocError(Exception):

    """
    An error that's thrown when generating Sous Chef documentation.
    """
    status_code = 400


class SousChefExecError(Exception):

    """
    An error that's thrown when a SousChef is not properly executed.
    """
    status_code = 400


class SousChefModuleInitError(Exception):

    """
    An error that's thrown when a SousChef module is not properly initialized.
    """
    status_code = 400


class SousChefImportError(Exception):

    """
    An error that's thrown when a SousChef cannot be imported.
    """
    status_code = 400


# Merlynne Errors #

class MerlynneError(Exception):

    """
    An error that's thrown when a Merlynne is not properly initialized.
    """
    status_code = 400

# Recipe Errors #


class RecipeSchemaError(Exception):

    """
    An error that's thrown when a Recipe has an invalid schema
    according to it's SousChef.
    """
    status_code = 400

# Search String Errors #


class SearchStringError(Exception):

    """
    An error that's thrown when a search string is invalid.
    """
    status_code = 400

# config.yaml Errors #


class ConfigError(Exception):

    """
    An error that's thrown when something is wrong with the config file.
    """
    status_code = 400

# newslynx.client Errors #


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
    "SousChefImportError": SousChefImportError,
    "SousChefExecError": SousChefExecError,
    "SousChefDocError": SousChefDocError,
    "SousChefModuleInitError": SousChefModuleInitError,
    "SousChefInstallError": SousChefInstallError,
    "MerlynneError": MerlynneError,
    "RecipeSchemaError": RecipeSchemaError,
    "SearchStringError": SearchStringError,
    "ConfigError": ConfigError,
    "ClientError": ClientError
}
