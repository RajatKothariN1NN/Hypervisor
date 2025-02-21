from drf_yasg.inspectors import SwaggerAutoSchema

class JWTSwaggerAutoSchema(SwaggerAutoSchema):
    def get_security_definitions(self):
        return {
            'Bearer': {
                'type': 'apiKey',
                'name': 'Authorization',
                'in': 'header',
            }
        }

    def get_security_requirements(self):
        if self.view.authentication_classes:
            return [{'Bearer': []}]
        return []