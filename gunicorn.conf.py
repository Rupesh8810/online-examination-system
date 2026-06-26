import multiprocessing

# For 100-200 concurrent students:
# workers = 2*CPU+1, threads=4 gives ~(workers*threads) concurrent requests
bind             = "0.0.0.0:8000"
workers          = multiprocessing.cpu_count() * 2 + 1
worker_class     = "gthread"
threads          = 4
timeout          = 120
keepalive        = 5
max_requests     = 1000      # restart worker after N requests (prevents memory bloat)
max_requests_jitter = 100    # randomize restart to avoid thundering herd
accesslog        = "-"
errorlog         = "-"
loglevel         = "info"
preload_app      = True      # share memory across workers (lower RAM per worker)
worker_tmp_dir   = "/dev/shm"  # use RAM for temp files (faster on Linux)
