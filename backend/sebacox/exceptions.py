from rest_framework.response import Response
from rest_framework.exceptions import APIException


def custom_exception_handler(exc, context):
    from rest_framework.views import exception_handler
    response = exception_handler(exc, context)
    
    if response is not None:
        if response.status_code == 403:
            response.data = {
                'error': 'Permission denied',
                'details': response.data
            }
        elif response.status_code == 404:
            response.data = {
                'error': 'Resource not found',
                'details': response.data
            }
    
    return response
