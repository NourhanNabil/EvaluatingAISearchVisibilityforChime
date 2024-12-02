from .helpers import get_env_variable

class AWS:
    ACCESS_KEY_ID = get_env_variable("AWS_ACCESS_KEY_ID")
    ACCESS_KEY_SECRET = get_env_variable("AWS_ACCESS_KEY_SECRET")
   