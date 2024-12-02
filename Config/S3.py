from .helpers import get_env_variable

class S3:
    S3_BUCKET_NAME= get_env_variable("S3_BUCKET_NAME")
    REGION_NAME = get_env_variable("AWS_REGION_NAME")
    S3_FAQ_DIRECTORY = get_env_variable("S3_FAQ_DIRECTORY")
    S3_BLOGS_DIRECTORY = get_env_variable("S3_BLOGS_DIRECTORY")
    S3_PRODUCTS_DIRECTORY = get_env_variable("S3_PRODUCTS_DIRECTORY")
    S3_BACKUP_DIRECTORY = get_env_variable("S3_BACKUP_DIRECTORY")