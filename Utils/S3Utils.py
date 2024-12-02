import os
import boto3
from pandas import DataFrame
import pandas as pd
from io import StringIO
import json

from .StringUtils import StringUtils

from Config.AWS import AWS
from Config.S3 import S3

class S3Utils:
    default_client = boto3.client(
            's3',
            aws_access_key_id=AWS.ACCESS_KEY_ID,
            aws_secret_access_key=AWS.ACCESS_KEY_SECRET,
            region_name = S3.REGION_NAME
        )
    bucket_name = S3.S3_BUCKET_NAME
    @classmethod
    def Connect(cls, aws_access_key_id : str = '', aws_secret_access_key : str = '', aws_region_name : str = ''):
        if StringUtils.is_None_or_whitespace(aws_access_key_id):
            aws_access_key_id = AWS.ACCESS_KEY_ID
        
        if StringUtils.is_None_or_whitespace(aws_secret_access_key):
            aws_access_key_id = AWS.ACCESS_KEY_SECRET

        if StringUtils.is_None_or_whitespace(aws_region_name):
            aws_region_name = AWS.REGION_NAME
        
        return boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name = aws_region_name
        )
    
    @classmethod
    def Upload(cls, folder_name, file_name, data):
        if isinstance(data, DataFrame):
            csv_data = data.to_csv(index=False)
            data = csv_data.encode('utf-8')
        elif isinstance(data, bytes):
            data = data.decode('utf-8')
        elif isinstance(data, str):
            data = data
        elif isinstance(data, dict):
            data = json.dumps(data).encode('utf-8')
        elif isinstance(data, list):
            data = data
        else:
            print("Invalid file format to be uploaded...")
            return False

        key = folder_name + file_name
        cls.default_client.put_object(Bucket=cls.bucket_name, Key=key, Body=data)
        return True
    
    @classmethod
    def file_exists(cls,bucket_name, file_path):
        try:
            cls.default_client.head_object(Bucket=bucket_name, Key=file_path)
            return True
        except:
            return False
        
    @classmethod
    def read_file(cls, file_path):
        _, file_extension = os.path.splitext(file_path)
        file_extension = file_extension.lower()

        response = cls.default_client.get_object(Bucket=cls.bucket_name, Key=file_path)
        file_content = response['Body'].read().decode('utf-8')

        if file_extension == '.json':
            return json.loads(file_content)
        elif file_extension == '.csv' or file_extension == '.txt':
            return pd.read_csv(StringIO(file_content))
        else:
            raise ValueError(f"Unsupported file extension: {file_extension}")
    
    @classmethod
    def delete_s3_file(cls, file_key):
        if cls.file_exists(cls.bucket_name,file_key):
            cls.default_client.delete_object(Bucket=cls.bucket_name, Key=file_key)
    
    @classmethod
    def list_csv_files_in_s3(cls, folder):
        """Lists all CSV files in the specified S3 bucket and folder, handling pagination."""
        files = []
        try:
            continuation_token = None
            while True:
                kwargs = {'Bucket': cls.bucket_name, 'Prefix': folder}
                if continuation_token:
                    kwargs['ContinuationToken'] = continuation_token

                response = cls.default_client.list_objects_v2(**kwargs)
                if 'Contents' in response:
                    files.extend([obj['Key'] for obj in response['Contents']
                                if obj['Key'].endswith('.csv') ])
                if response.get('IsTruncated'): 
                    continuation_token = response.get('NextContinuationToken')
                else:
                    break

            return files
        except Exception as e:
            print(f"Failed to list .csv files in S3: {e}")
            raise


  