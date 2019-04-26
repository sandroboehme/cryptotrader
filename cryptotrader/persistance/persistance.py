from abc import ABC, abstractmethod


class Persistance(ABC):
    FOLDER_NAME_MAIN = 'cryptotrader-com'
    FOLDER_NAME_TRADES = 'trades'
    FOLDER_NAME_CANDLE_STATE = 'candle-state'

    def save_candle_state(self, exchange, pair, year, month, day, trade_id, candle_state):
        folder = f"{Persistance.FOLDER_NAME_TRADES}/{exchange}/{pair}/{year}/{month}/{day}/{trade_id}"
        last_file_id = self.get_last_file_id(folder)
        next_file_id = last_file_id + 1 if last_file_id is not None else 1
        return self.save_candle_state_with_id(folder, next_file_id, candle_state)

    def get_last_candle_state(self, exchange, pair, year, month, day, trade_id):
        folder = f"{Persistance.FOLDER_NAME_TRADES}/{exchange}/{pair}/{year}/{month}/{day}/{trade_id}"
        last_file_id = self.get_last_file_id(folder)
        return self.get_last_candle_state_with_id(folder, last_file_id)

    # @abstractmethod
    # def get_or_create_sub_folders(self):
    #     pass

    @abstractmethod
    def get_last_file_id(self, folder):
        pass

    @abstractmethod
    def save_candle_state_with_id(self, folder, next_file_id, candle_state):
        pass

    @abstractmethod
    def get_last_candle_state_with_id(self, folder, last_file_id):
        pass


    # @abstractmethod
    # def get_or_create_main_sub_folders(self, folders=[]):
    #     pass

    @abstractmethod
    def delete_main_folder(self):
        pass
