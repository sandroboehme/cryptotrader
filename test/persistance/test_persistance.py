import ast
import json
import os
import unittest
from random import randint

from google.cloud import storage

from cryptotrader.persistance.g_cloud_storage_persistance import GCloudStoragePersistance
from cryptotrader.persistance.persistance import Persistance
from definitions import ROOT_PATH


class TestPersistance(unittest.TestCase):

    @classmethod
    def setUp(self):
        pass


    def test_get_gcloud_main_folder(self):
        gcloud_persistance = GCloudStoragePersistance()
        gcloud_persistance.delete_main_folder()
        gcloud_persistance.save_candle_state('binance', 'BNBUSDT', 2019, 4, 26, 1,
                                                                   {'aKey': 'aValue'})
        candle_state, path = gcloud_persistance.get_last_candle_state('binance', 'BNBUSDT', 2019, 4, 26, 1)
        assert candle_state == {'aKey': 'aValue'}
        assert path == 'trades/binance/BNBUSDT/2019/4/26/1/1.json'

        gcloud_persistance.save_candle_state('binance', 'BNBUSDT', 2019, 4, 26, 1,
                                                                   {'aKey2': 'aValue2'})
        candle_state, path = gcloud_persistance.get_last_candle_state('binance', 'BNBUSDT', 2019, 4, 26, 1)
        assert candle_state == {'aKey2': 'aValue2'}
        assert path == 'trades/binance/BNBUSDT/2019/4/26/1/2.json'


if __name__ == '__main__':
    unittest.main()
