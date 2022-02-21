class MessageNotSend(Exception):
    """Raised when the message cannot sent."""

    def __init__(self, message):
        self.message = message
        super().__init__()

    def __str__(self):
        return f'{self.message}'

class StatusCodeNotOK(Exception):
    """Raised when the status code is not OK."""

    def __init__(self, message):
        self.message = message
        super().__init__()

    def __str__(self):
        return f'{self.message}'

class JSONDecodeError(Exception):
    """Raised when the JSON Decode does not work properly."""

    def __init__(self, message):
        self.message = message
        super().__init__()

    def __str__(self):
        return f'{self.message}'

class ListHWIsNotList(Exception):
    """Raised when the list of homeworks is not a list."""

    def __init__(self, message):
        self.message = message
        super().__init__()

    def __str__(self):
        return f'{self.message}'
