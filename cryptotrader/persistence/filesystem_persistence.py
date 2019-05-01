import json
import os

from google.cloud import firestore

from cryptotrader.persistence.persistence import Persistence
from definitions import ROOT_PATH


class FilesystemPersistence(Persistence):

    def __init__(self, path, name, root):
        Persistence.__init__(self, path, name)
        os.environ['GRPC_DNS_RESOLVER'] = 'native'
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.join(ROOT_PATH, 'auth.json')
        self.db = firestore.Client()
        self.root = root

    def save_setup_impl(self, path, name, setup):
        try:
            abs_folder = os.path.join(self.root, path)
            if not os.path.exists(abs_folder):
                os.makedirs(abs_folder)
        except OSError:
            print('Error creating directory ' + abs_folder)
        try:
            abs_file_path = f'{abs_folder}/{name}.json'
            with open(abs_file_path, "w") as trade_setup_file:
                trade_setup_file.write(json.dumps(setup, indent=4))
        except OSError:
            print('Error creating file ' + abs_file_path)
        return abs_file_path

    def update_setup_impl(self, path, name, setup_2update):
        trade_setup = self.get_setup_impl(path, name)
        for key in setup_2update:
            trade_setup[key] = setup_2update.get(key)
        self.save_setup_impl(path, name, trade_setup)

    def get_setup_impl(self, path, name):
        try:
            abs_file_path = self.get_file_path(path, name)
            with open(abs_file_path, "r") as trade_setup_file:
                return json.load(trade_setup_file)
        except OSError:
            print('Error creating file ' + abs_file_path)
        return None

    def get_file_path(self, path, name):
        abs_folder = os.path.join(self.root, path)
        abs_file_path = f'{abs_folder}/{name}.json'
        return abs_file_path

    def delete_setup_impl(self, path, name):
        try:
            abs_file_path = self.get_file_path(path, name)
            os.remove(abs_file_path)
        except OSError:
            print('Error deleting ' + abs_file_path)
