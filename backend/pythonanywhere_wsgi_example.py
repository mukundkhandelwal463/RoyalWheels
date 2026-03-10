"""
PythonAnywhere WSGI configuration example for this repo.

Copy the relevant parts into:
  /var/www/<your_username>_pythonanywhere_com_wsgi.py

IMPORTANT:
- `path` must point to the folder that contains `manage.py`
- The folder name is case-sensitive on Linux (PythonAnywhere)
"""

import os
import sys

# Example:
# path = "/home/mukund462/royalWHeeLs/backend"
path = "/home/<username>/<project_dir>/backend"
if path not in sys.path:
    sys.path.append(path)

os.environ["DJANGO_SETTINGS_MODULE"] = "backend.settings"

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()

