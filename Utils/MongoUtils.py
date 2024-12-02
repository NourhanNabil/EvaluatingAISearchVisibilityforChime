from typing import List, Dict
from pymongo import MongoClient
from Config.MongoDB import MongoDB
from pymongo import InsertOne, UpdateOne


class MongoUtils:
    def __init__(self, connection_string:str = '' , database: str = ''):
        
        self.default_limit = int(MongoDB.DEFAULT_LIMIT)

        self.connection_string_scheme = connection_string if connection_string else MongoDB.MONGODB_URI
        
        self.database = database if database else MongoDB.DATABASE
        
        self.database_client = None
        self.database_collection_set = {}

    def connect(self):
        try:
            if self.database_client != None:
                return self.database_client

            client = MongoClient(MongoDB.MONGODB_URI)

            self.database_client = client[self.database]

            ping_result = self.database_client.command('ping')

            if ping_result['ok'] == 1:
                self.update_database_collection_set()
                
            else:
                raise ConnectionError("Invalid database connection information, failed to connect to mongodb.")
            
        except Exception as e:
            print(f"Error occurred while connecting to MongoDB: {e}")


    def update_database_collection_set(self):
        if self.database_client is not None:
            self.database_collection_set = set(self.database_client.list_collection_names())
            
    def convert_query_to_mongo_filter(self, filters: List[Dict[str, List[str]]] = []):
        result = []
        for filter in filters:
            if len(filter) > 0:
                query = {}
                key = list(filter.keys())[0]
                value = filter[key]
                if isinstance(value, list) and len(value) > 1:
                    if '$or' not in query:
                        query['$or'] = []
                    for option in value:
                        query['$or'].append({key: option})
                elif isinstance(value, list) and len(value) == 1:
                    query[key] = value[0]
                elif not isinstance(value, list):
                    query[key] = value
                result.append(query)
        if result:
            return result[0] if len(result) == 1 else {"$and": result}
        else:
            return {}

    def create_collection(self, collection_name: str):
        try:
            if self.database_client is None:
                self.connect()

            if self.collection_exists(collection_name):
                print(f"Collection '{collection_name}' already exists.")
                return

            self.database_client.create_collection(collection_name)
            self.update_database_collection_set()
            print(f"Collection '{collection_name}' created successfully.")
        except Exception as e:
            print(f"Error occurred while creating collection '{collection_name}': {e}")


    def collection_exists(self, collection_name: str):
        if collection_name not in self.database_collection_set:
            self.update_database_collection_set()
        
        return collection_name in self.database_collection_set
    
    
    def connect_to_collection(self, collection_name):
        if not self.collection_exists(collection_name):
            print(f"Error mongo collection not found. collection:{collection_name}, database:{self.database}, host: {self.host}.")
            print("maybe the username and password used have no access to the collection requested.")
            return None
    
        return self.database_client[collection_name]
    
    def insert_items(self, collection_name: str, data: List) -> bool:
        try:  
            if self.database_client is None:
                self.connect()

            if self.database_client is None:
                return False
        
            collection = self.connect_to_collection(collection_name)
            
            if collection is None:
                return False
            
            records = data.to_dict(orient='records')
            bulk_operations = [InsertOne(record) for record in records]
            insertion_result = collection.bulk_write(bulk_operations, ordered=False)

            if insertion_result.acknowledged:
                return True
            else:
                return False

        except Exception as e:
            False
        
    def query_collection(self, collection: str,  filters:  List[Dict[str, List[str]]]= [], selected_fields: List[str]= [], projection: Dict[str, int] = {}, skip = 0, limit = None):
        try:  
            if self.database_client is None:
                self.connect()
            
            if self.database_client is None:
                return []
            
            collection_obj = self.connect_to_collection(collection)
            if collection_obj is None:
                return []
            
            query = self.convert_query_to_mongo_filter(filters)
            
            selected_fields_stage = {"_id": 1} #modify to 1 
            
            if selected_fields:
                for field in selected_fields:
                    selected_fields_stage[field] = 1

            if projection:
                selected_fields_stage.update(projection)
            
                         
            find_query = collection_obj.find(query, selected_fields_stage).max_time_ms(90000000)
        
            if skip != 0:
                find_query = find_query.skip(skip)
            if limit is not None:
                find_query = find_query.limit(limit)

            results = find_query
            
            return list(results)
        except Exception as e:
            print(f"Error occurred during query: {e}")
            return []

    def bulk_update_documents(self, collection: str, updates: List[Dict[str, any]]):
        try:
            if self.database_client is None:
                self.connect()
            
            if self.database_client is None:
                return None
            
            collection_obj = self.connect_to_collection(collection)
            if collection_obj is None:
                return None
            bulk_ops = [UpdateOne({'_id': update['filter']['_id']}, {'$set': update['update_fields']}) for update in updates]
            
            update_result = collection_obj.bulk_write(bulk_ops, ordered=False) 

            return {
                "modified_count": update_result.modified_count,
            }

        except Exception as e:
            print(f"Error occurred during bulk update: {e}")
            return None