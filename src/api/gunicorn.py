import logging.config

workers = 2
accesslog = '/srv/logs/gunicorn_access.log'
errorlog = ' /srv/logs/gunicorn_errors.log'
preload_app = True
worker_class = 'gevent'

# max_requests = 10000
# max_requests_jitter = int(max_requests / 2)

logging.config.dictConfig({
   'version': 1,
   'disable_existing_loggers': False,
   'formatters': {
       'verbose': {
           'format': '[%(levelname)s %(asctime)s %(module)s.%(funcName)s] %(message)s',
           'datefmt': '%Y-%m-%d %H:%M:%S',
       },
   },
   'handlers': {
       'default': {
           'class': 'logging.StreamHandler',
           'formatter': 'verbose'
       },
       'file': {
           'class': 'logging.FileHandler',
           'filename': '/var/log/gunicorn/service.log',
           'formatter': 'verbose'
       },
   },
   'loggers': {
       '': {
           'handlers': ['default', 'file'],
           'level': 'WARN',
           'propagate': True,
       },
   }
})

logger = logging.getLogger(__name__)


