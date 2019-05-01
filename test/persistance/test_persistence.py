import json
import os
import unittest

from cryptotrader.persistence.persistence import Persistence
from cryptotrader.persistence.persistence_factory import PersistenceFactory
from cryptotrader.persistence.filesystem_persistence import FilesystemPersistence
from cryptotrader.persistence.firestore_persistence import FirestorePersistence
from cryptotrader.persistence.persistence_type import PersistenceType
from definitions import ROOT_PATH


class TestPersistence(unittest.TestCase):

    def setUp(self):
        abs_param_file = os.path.join(ROOT_PATH, 'test/backtestBNBPsarSL.json')
        with open(abs_param_file, 'r') as f:
            trade_setup = json.load(f)
            self.trade_parameter = dict(exchange=trade_setup['exchange'],
                                        pair=trade_setup['symbol'],
                                        year=trade_setup['fromdate']['year'],
                                        month=trade_setup['fromdate']['month'],
                                        day=trade_setup['fromdate']['day'],
                                        trade_id=trade_setup['name'])
        self.trade_setup_path = Persistence.get_path('binance', 'bnb/usdt')

    def test_trade_setup_filesystem_persistence(self):
        persistence_imp = PersistenceFactory.get_persistance(PersistenceType.FS,
                                                             self.trade_setup_path,
                                                             name='backtestBNBPsarSL',
                                                             root_path=ROOT_PATH)
        self.trade_setup_persistence_test(persistence_imp)

    def test_trade_setup_firestore_persistence(self):
        persistence_imp = PersistenceFactory.get_persistance(PersistenceType.GOOGLE_FIRESTORE,
                                                             self.trade_setup_path,
                                                             name='backtestBNBPsarSL')
        self.trade_setup_persistence_test(persistence_imp)

    def trade_setup_persistence_test(self, persistence):
        abs_param_file = os.path.join(ROOT_PATH, 'test/backtestBNBPsarSL.json')

        persistence.delete_setup()

        with open(abs_param_file, 'r') as f:
            trade_setup = json.load(f)
            trade_setup['event_stop'] = False
            persistence.save_setup(trade_setup)
            retrieved_setup = persistence.get_setup()
            assert retrieved_setup == trade_setup
            persistence.end_setup()
            retrieved_setup = persistence.get_setup()
            assert retrieved_setup['event_stop']

    def test_persistence_type_handling(self):
        assert 'fs' == PersistenceType.FS.value
        assert 'google_cloud_storage' == PersistenceType.GOOGLE_CLOUD_STORAGE.value
        assert PersistenceType.FS == PersistenceType('fs')
        assert PersistenceType.GOOGLE_CLOUD_STORAGE == PersistenceType('google_cloud_storage')

    def test_file_system_persistence(self):
        persistence_imp = PersistenceFactory.get_cs_persistance(PersistenceType.FS,
                                                                  **self.trade_parameter,
                                                                  root_path=ROOT_PATH)
        self.persistence_impl_test(persistence_imp)

    def test_gcloud_storage_persistence(self):
        persistence_imp = PersistenceFactory.get_cs_persistance(PersistenceType.GOOGLE_CLOUD_STORAGE,
                                                                  **self.trade_parameter)
        self.persistence_impl_test(persistence_imp)

    def persistence_impl_test(self, persistence_imp):
        """
        Tests if it's possible to store the candle state initially when no trade folder is there yet and in
        subsequent cases when there is a previous candle state.
        :param persistence_imp:
        :param trade_parameter:
        :return:
        """
        persistence_imp.delete_trade_folder()
        persistence_imp.save_candle_state(candle_state={'aKey': 'aValue'})
        candle_state, path = persistence_imp.get_last_candle_state()
        assert candle_state == {'aKey': 'aValue'}
        assert path == 'trades/binance/bnbusdt/2019/1/28/trailing_sl/1.json'

        persistence_imp.save_candle_state(candle_state={'aKey2': 'aValue2'})
        candle_state, path = persistence_imp.get_last_candle_state()
        assert candle_state == {'aKey2': 'aValue2'}
        assert path == 'trades/binance/bnbusdt/2019/1/28/trailing_sl/2.json'


if __name__ == '__main__':
    unittest.main()
