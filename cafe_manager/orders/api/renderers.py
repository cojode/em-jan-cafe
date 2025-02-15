from rest_framework import status
from rest_framework.renderers import JSONRenderer


class CustomRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        """API response customizer."""
        response = renderer_context["response"]

        is_success = status.is_success(response.status_code)

        response_data = {
            "success": is_success,
            "data": data if is_success else None,
            "error": data if not is_success else None,
        }
        return super().render(response_data, accepted_media_type, renderer_context)
