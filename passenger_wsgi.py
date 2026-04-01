import sys
import os

# 1. Force the app root directory into the Python path
BASE_DIR = os.path.dirname(__file__)
sys.path.insert(0, BASE_DIR)

# 2. Set the Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'prairiewealth_project.settings'

# 3. Import the actual Django application
try:
    from prairiewealth_project.wsgi import application
except Exception:
    import traceback
    def application(environ, start_response):
        start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
        return [traceback.format_exc().encode()]
