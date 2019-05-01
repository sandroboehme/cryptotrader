import json
import os
import shutil

from cryptotrader.persistence.cs_persistence import CSPersistence


class FSCSPersistence(CSPersistence):
    """
    Stores the candle state in the file system.
    """
    FOLDER_NAME_CANDLE_STATES = 'candle_states'

    def __init__(self, exchange, pair, year, month, day, trade_id, root):
        CSPersistence.__init__(self, exchange, pair, year, month, day, trade_id)
        self.abs_cs_folder = os.path.join(root, FSCSPersistence.FOLDER_NAME_CANDLE_STATES)

    def get_last_file_id_by_folder(self, folder):
        try:
            abs_folder = os.path.join(self.abs_cs_folder, folder)
            if not os.path.exists(abs_folder) or len(os.listdir(abs_folder)) == 0:
                last_file_id = None
            else:
                last_file_id = len(os.listdir(abs_folder))

        except OSError:
            print ('Error reading directory ' + abs_folder)

        return last_file_id

    def save_candle_state_with_id(self, folder, next_file_id, candle_state):
        try:
            abs_folder = os.path.join(self.abs_cs_folder, folder)
            if not os.path.exists(abs_folder):
                os.makedirs(abs_folder)
        except OSError:
            print('Error creating directory ' + abs_folder)
        try:
            abs_file_path = os.path.join(abs_folder, str(next_file_id) + '.json')
            with open(abs_file_path, "w") as candle_state_file:
                candle_state_file.write(json.dumps(candle_state, indent=4))
        except OSError:
            print('Error creating file ' + abs_file_path)
        return abs_file_path

    def delete_folder(self, folder):
        try:
            abs_folder = os.path.join(self.abs_cs_folder, folder)
            shutil.rmtree(abs_folder, ignore_errors=True)
        except OSError:
            print('Error deleting folder ' + abs_folder)

    def get_last_candle_state_with_id(self, folder, last_file_id):
        try:
            abs_folder = os.path.join(self.abs_cs_folder, folder)
            file_name = str(last_file_id) + '.json'
            abs_file_path = os.path.join(abs_folder, file_name)
            with open(abs_file_path, 'r') as f:
                candle_state = json.load(f)
        except OSError:
            print('Error loading ' + abs_file_path)
        return candle_state, os.path.join(folder, file_name)
