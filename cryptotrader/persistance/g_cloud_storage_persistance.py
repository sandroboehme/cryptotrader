import json
import os
from abc import ABC, abstractmethod

from google.cloud import storage

from cryptotrader.persistance.persistance import Persistance
from definitions import ROOT_PATH


class GCloudStoragePersistance(Persistance):

    def __init__(self):
        auth_file_path = os.path.join(ROOT_PATH, 'auth.json')
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = auth_file_path
        # Instantiates a client
        self.storage_client = storage.Client()

    def get_or_create_sub_folders(self, folders=[]):
        pass

    def get_last_file_id(self, folder):
        bucket = self.storage_client.lookup_bucket(Persistance.FOLDER_NAME_MAIN)
        last_file_id = self.get_last_file_id_by_bucket(bucket, folder) if bucket else None
        return last_file_id

    def get_last_file_id_by_bucket(self, bucket, folder):
        blobs = bucket.list_blobs(prefix=folder + '/')
        file_count = 0
        # just use the file count as the next_file_id
        for blob in blobs:
            file_count += 1
        return None if file_count == 0 else file_count

    def save_candle_state_with_id(self, folder, next_file_id, candle_state):
        bucket = self.storage_client.lookup_bucket(Persistance.FOLDER_NAME_MAIN)
        bucket = bucket if bucket else self.create_bucket()
        json_string = json.dumps(candle_state)
        path = f"{folder}/{next_file_id}.json"
        bucket.blob(path).upload_from_string(json_string)
        return path

    def get_last_candle_state_with_id(self, folder, last_file_id):
        bucket = self.storage_client.lookup_bucket(Persistance.FOLDER_NAME_MAIN)
        if bucket is None:
            return None
        path = f"{folder}/{last_file_id}.json"
        blob = bucket.blob(path)
        candle_state = json.loads(blob.download_as_string())
        return candle_state, path

    def get_or_create_main_sub_folders(self, folders='path/name'):
        bucket = self.storage_client.lookup_bucket(Persistance.FOLDER_NAME_MAIN)
        bucket = bucket if bucket else self.create_main_folder()
        return bucket.blob(folders).upload_from_string('{}')

    def create_bucket(self):
        return self.storage_client.create_bucket(Persistance.FOLDER_NAME_MAIN)

    def delete_main_folder(self):
        bucket = self.storage_client.lookup_bucket(Persistance.FOLDER_NAME_MAIN)
        if bucket:
            bucket.delete(force=True)
