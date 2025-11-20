from rest_framework.renderers import JSONRenderer
import time

class CustomJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        status_code = renderer_context['response'].status_code
        success = status_code < 400
        message = "Request successful" if success else "Request failed"
        
        if isinstance(data, dict):
            if 'message' in data:
                message = data.pop('message')
            
            if 'error' in data:
                message = data.pop('error')
                success = False
                
            if 'detail' in data:
                message = data.pop('detail')
                success = False

        response_data = {
            "success": success,
            "code": status_code,
            "message": message,
            "timestamp": int(time.time()),
            "data": data if data else None 
        }

        if not response_data['data']:
            response_data['data'] = None

        return super(CustomJSONRenderer, self).render(response_data, accepted_media_type, renderer_context)