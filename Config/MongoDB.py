from .helpers import get_env_variable 

class MongoDB:
    MONGODB_URI = get_env_variable("MONGODB_URI")
    DATABASE = get_env_variable("MONGODB_DATABASE")
    DEFAULT_LIMIT = int(get_env_variable("MONGODB_DEFAULT_LIMIT", default = "60"))
    FAQ_COLLECTION = get_env_variable("MONGODB_FAQ_COLLECTION")
    BLOGS_COLLECTION = get_env_variable("MONGODB_BLOGS_COLLECTION")


