from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    """Wrap DRF's exception handler to produce a normalized JSON error shape.

    Normalized shape examples:
      - Validation errors: { field: [..], ... }
      - Other errors: { "detail": "message" }
    """
    response = drf_exception_handler(exc, context)
    if response is None:
        # Unhandled exceptions: provide a safe generic message
        return Response({'detail': 'An unexpected error occurred.'}, status=500)

    data = response.data
    # If data is already a dict of fields or contains 'detail', leave as-is
    if isinstance(data, dict):
        # Convert list-like top-level errors to 'detail'
        if 'detail' in data:
            return response
        # If data looks like {'error': '...'} convert to {'detail': '...'}
        if 'error' in data and isinstance(data['error'], str):
            response.data = {'detail': data['error']}
            return response
        return response

    # Fallback: ensure a detail message
    response.data = {'detail': str(data)}
    return response
