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
            
            elif 'error' in data:
                message = data.pop('error')
                success = False
                
            elif 'detail' in data:
                message = data.pop('detail')
                success = False
            
            elif not success:
                try:
                    first_key = next(iter(data))
                    error_content = data[first_key]
                    
                    if isinstance(error_content, list) and len(error_content) > 0:
                        message = str(error_content[0])
                    else:
                        message = str(error_content)
                except Exception:
                    pass

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