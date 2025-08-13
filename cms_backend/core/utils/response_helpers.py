from rest_framework.response import Response
from rest_framework import status

def success_response(data=None, message="Success", http_status=status.HTTP_200_OK):
    """
    Returns a standardized success response.
    """
    return Response({
        "success": True,
        "message": message,
        "data": data or []
    }, status=http_status)

def error_response(message="Something went wrong", data=None, http_status=status.HTTP_400_BAD_REQUEST):
    """
    Returns a standardized error response.
    """
    return Response({
        "success": False,
        "message": message,
        "data": data or []
    }, status=http_status)
