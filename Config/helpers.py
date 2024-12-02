import os
from dotenv import load_dotenv

load_dotenv()

def get_env_variable(env_var_name: str, default = "") -> str:
    return os.getenv(env_var_name, default= default)

