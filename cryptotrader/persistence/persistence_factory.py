from cryptotrader.persistence.filesystem_persistence import FilesystemPersistence
from cryptotrader.persistence.firestore_persistence import FirestorePersistence
from cryptotrader.persistence.fs_cs_persistence import FSCSPersistence
from cryptotrader.persistence.gcloud_storage_cs_persistence import GCloudStorageCSPersistence
from cryptotrader.persistence.persistence_type import PersistenceType


class PersistenceFactory(object):

    @staticmethod
    def get_cs_persistance(persistence_type, exchange, pair, year, month, day, trade_id, root_path=None):
        if persistence_type == PersistenceType.GOOGLE_CLOUD_STORAGE:
            return GCloudStorageCSPersistence(exchange, pair, year, month, day, trade_id)
        else:
            return FSCSPersistence(exchange, pair, year, month, day, trade_id, root_path)

    @staticmethod
    def get_persistance(persistence_type, path, name, root_path=None):
        if persistence_type == PersistenceType.GOOGLE_FIRESTORE:
            return FirestorePersistence(path, name)
        else:
            return FilesystemPersistence(path, name, root_path)
