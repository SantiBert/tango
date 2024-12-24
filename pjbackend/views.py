from django.http import JsonResponse

def health_check(request):
    data = {
        "status": "ok",
        "message": "Service is running",
    }
    return JsonResponse(data)
