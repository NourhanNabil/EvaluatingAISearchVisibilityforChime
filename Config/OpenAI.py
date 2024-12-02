from .helpers import get_env_variable

class OpenAI:
    API_KEY = get_env_variable("OPENAI_API_KEY")
    MODEL_NAME = get_env_variable("OPENAI_MODEL_NAME")
    MODEL_NAME_EMBEDDING = get_env_variable("OPENAI_MODEL_NAME_EMBEDDING")



  