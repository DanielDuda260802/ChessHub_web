import os
import sys
import django

def setup_django():
    script_path = os.path.dirname(os.path.abspath(__file__)) 
    project_path = os.path.abspath(os.path.join(script_path, "../../"))
    sys.path.append(project_path) 
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chesshub_project.settings")
    django.setup()
