from abc import ABC, abstractmethod


class CSPersistence(ABC):
    FOLDER_NAME_MAIN = 'cryptotrader-com'
    FOLDER_NAME_TRADES = 'trades'
    FOLDER_NAME_CANDLE_STATE = 'candle-state'

    def __init__(self, exchange, pair, year, month, day, trade_id):
        self.folder = self.get_folder(exchange, pair, year, month, day, trade_id)

    def save_candle_state(self, candle_state):
        last_file_id = self.get_last_file_id_by_folder(self.folder)
        next_file_id = last_file_id + 1 if last_file_id is not None else 1
        return self.save_candle_state_with_id(self.folder, next_file_id, candle_state)

    def get_last_candle_state(self):
        last_file_id = self.get_last_file_id_by_folder(self.folder)
        return self.get_last_candle_state_with_id(self.folder, last_file_id)

    def delete_trade_folder(self):
        self.delete_folder(self.folder)

    def get_folder(self, exchange, pair, year, month, day, trade_id):
        exchange = exchange.lower()
        pair = pair.replace('/','').lower()
        trade_id = trade_id
        folder = f"{CSPersistence.FOLDER_NAME_TRADES}/{exchange}/{pair}/{year}/{month}/{day}/{trade_id}"
        return folder

    def get_last_file_id(self):
        return self.get_last_file_id_by_folder(self.folder)

    @abstractmethod
    def get_last_file_id_by_folder(self, folder):
        pass

    @abstractmethod
    def save_candle_state_with_id(self, folder, next_file_id, candle_state):
        pass

    @abstractmethod
    def get_last_candle_state_with_id(self, folder, last_file_id):
        pass

    @abstractmethod
    def delete_folder(self, folder):
        pass
