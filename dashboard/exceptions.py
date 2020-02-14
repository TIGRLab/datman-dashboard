class InvalidDataException(Exception):
    """An exception for attempts to add incorrect data to the database.
    """


class RedcapException(Exception):
    """An exception for REDCap interface issues.
    """


class MonitorException(Exception):
    """An exception for scheduled jobs that have encountered problems.
    """
    pass


class SchedulerException(Exception):
    """An exception for problems while interacting with the scheduler.
    """
    pass


class InvalidUsage(Exception):
    """An exception for incorrect usage of the URL endpoints.
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