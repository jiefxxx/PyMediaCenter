
class ConfigLoadError(Exception):
    def __init__(self, message):
        Exception.__init__(self, "pyconfig : "+message)

