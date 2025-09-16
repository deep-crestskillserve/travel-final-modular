import sys
import json
import logging
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        """ Format log records as JSON """
        log_data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'message': record.getMessage(),
            'module': record.module,
            'line': record.lineno
        }
        if hasattr(record, 'extra_data'):
            log_data['extra'] = record.extra_data
        return json.dumps(log_data)

def get_logger(name='app_logger', level=logging.DEBUG):
    """ Return a logger that outputs JSON formatted logs to stdout. """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    logger.handlers = []
    logger.addHandler(console_handler)
    return logger


# # Example with DEBUG level
# if __name__ == "__main__":
#     logger = setup_logger()
#     debug_data = {"function": "calculate_metrics", "input_values": [1, 2, 3], "status": "processing"}
#     logger.debug("Detailed calculation step", extra={"extra_data": debug_data})