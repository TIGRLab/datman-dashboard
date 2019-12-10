class InvalidDataException(Exception):
    """
    Default exception when user tries to insert something obviously wrong.
    """


class RedcapException(Exception):
    """Generic error for recap interface"""


class MonitorException(Exception):
    pass


class SchedulerException(Exception):
    pass


class InvalidUsage(Exception):
    """
    Generic exception for API
    """
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


class TimeoutError(Exception):
    pass
