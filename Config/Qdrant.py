from .helpers import get_env_variable

class Qdrant:
    QDRANT_URL = get_env_variable("QDRANT_URL")
    QDRANT_API_KEY = get_env_variable("QDRANT_API_KEY")
    QDRANT_COLLECTION = get_env_variable("QDRANT_COLLECTION")




  