import os
from yggdrasil.services import IntegrationServiceManager


services_file = os.environ.get('INTEGRATION_SERVICES', 'services.yml')

x = IntegrationServiceManager(is_app=True)
if 'photosynthesis' not in x.registry.registry:
    x.registry.add(name=services_file)
port = int(os.environ.get('PORT', 5000))
app = x.app


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
