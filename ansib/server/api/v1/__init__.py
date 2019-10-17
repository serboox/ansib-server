import flask_restplus

from ansib.server.api.v1 import ansible


VERSION = '1'


api = flask_restplus.Api(title='Managed instance API',
                         version=VERSION,
                         description='API for Ansible execution')


for namespace in (
        ansible,
):
    for resource_api in namespace.APIs:
        resource_api.register_to_api(api, version=VERSION)
