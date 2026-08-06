import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
from django.conf import settings
settings.DATABASES['default'] = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': ':memory:',
}
settings.ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']
import django
django.setup()
from django.test.utils import get_runner
TestRunner = get_runner(settings)
test_runner = TestRunner(verbosity=2)
failures = test_runner.run_tests(['predictions.tests'])
raise SystemExit(bool(failures))
