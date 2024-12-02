from .helpers import get_env_variable 

class Service:
    HOST = get_env_variable("SERVICE_HOST")
    PORT = int(get_env_variable("SERVICE_PORT"))
