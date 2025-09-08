from rest_framework.response import Response
from rest_framework import status


def flatten_errors(errors):
    """
    Convert DRF serializer errors into a simple list of error strings,
    keeping field names for clarity.
    """
    flat_errors = []

    if isinstance(errors, dict):
        for field, msgs in errors.items():
            if isinstance(msgs, list):
                for msg in msgs:
                    flat_errors.append(f"{field}: {msg}")
            elif isinstance(msgs, dict):
                # recursively flatten nested errors
                nested_errors = flatten_errors(msgs)
                for err in nested_errors:
                    flat_errors.append(f"{field}: {err}")
            else:
                flat_errors.append(f"{field}: {msgs}")
    elif isinstance(errors, list):
        for err in errors:
            if isinstance(err, dict):
                flat_errors.extend(flatten_errors(err))
            else:
                flat_errors.append(str(err))
    else:
        flat_errors.append(str(errors))

    return flat_errors

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
    Returns a standardized error response with flattened errors.
    """
    flat_errors = flatten_errors(data) if data else []
    return Response({
        "success": False,
        "message": message,
        "errors": flat_errors  # note: changed key to 'errors' instead of 'data'
    }, status=http_status)
