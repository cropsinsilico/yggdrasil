import os
from yggdrasil.services import IntegrationServiceManager, _service_repo_dir


services_file = os.environ.get('INTEGRATION_SERVICES', 'services.yml')
repo_directory = os.environ.get(_service_repo_dir, None)


x = IntegrationServiceManager(is_app=True)
if 'photosynthesis' not in x.registry.registry:
    x.registry.add(name=services_file)
if repo_directory and os.path.isdir(repo_directory):
    x.registry.add(repo_directory)
port = int(os.environ.get('PORT', 5000))
app = x.app


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
