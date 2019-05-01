import os

from google.cloud import firestore

from cryptotrader.persistence.persistence import Persistence
from definitions import ROOT_PATH


class FirestorePersistence(Persistence):

    def __init__(self, path, name):
        Persistence.__init__(self, path, name)
        os.environ['GRPC_DNS_RESOLVER'] = 'native'
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.join(ROOT_PATH, 'auth.json')
        self.db = firestore.Client()

    def save_setup_impl(self, path, name, setup):
        doc_ref = self.db.document(path, name)
        doc_ref.set(setup)

    def update_setup_impl(self, path, name, setup):
        doc_ref = self.db.document(path, name)
        doc_ref.update(setup)

    def get_setup_impl(self, path, name):
        doc = self.db.document(path, name)
        return doc.get().to_dict()

    def delete_setup_impl(self, path, name):
        doc = self.db.document(path, name)
        doc.delete()
