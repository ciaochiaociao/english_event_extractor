import logging
import time


def setup_logger(name, log_file, level=logging.INFO):
    """Function setup as many loggers as you want"""
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(module)s %(funcName)s %(message)s')

    handler = logging.FileHandler(log_file)        
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


def logtime(logger_name):
    def timeit(method):
        def timed(*args, **kw):
            ts = time.time()
            logging.getLogger(logger_name).info("Running function {}".format(method.__name__))
            result = method(*args, **kw)
            te = time.time()
            logging.getLogger(logger_name).info("function {} ran in {}s".format(method.__name__, round(te - ts, 2)))
            return result
        return timed
    return timeit


def lprint(*args, **kwargs):
    import inspect
    import os
    import sys
    callerFrame = inspect.stack()[1]  # 0 represents this line
    myInfo = inspect.getframeinfo(callerFrame[0])
    myFilename = os.path.basename(myInfo.filename)
    print('{}({}):'.format(myFilename, myInfo.lineno), *args, flush=True, file=sys.stderr, **kwargs)
