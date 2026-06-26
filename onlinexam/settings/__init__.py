import os

# Load .env file if present (for local development)
try:
    from pathlib import Path
    env_file = Path(__file__).resolve().parent.parent.parent / '.env'
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())
except Exception:
    pass

env = os.environ.get('DJANGO_ENV', 'development')
if env == 'production':
    from .production import *
else:
    from .development import *
