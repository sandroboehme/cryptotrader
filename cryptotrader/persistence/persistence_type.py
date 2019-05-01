from enum import Enum


class PersistenceType(Enum):
    FS = 'fs'
    GOOGLE_CLOUD_STORAGE = 'google_cloud_storage'
    GOOGLE_FIRESTORE = 'google_firestore'

