import datetime
from abc import ABC, abstractmethod


class Persistence(ABC):

    FOLDER_NAME_MAIN = 'cryptotrader-com'
    FOLDER_NAME_TRADES = 'trades'
    FOLDER_NAME_SETUPS = 'setups'

    def __init__(self, path, name):
        self.path = path
        self.name = name

    def save_setup(self, setup):
        self.save_setup_impl(self.path, self.name, setup)

    def get_setup(self):
        return self.get_setup_impl(self.path, self.name)

    def delete_setup(self):
        return self.delete_setup_impl(self.path, self.name)

    def end_setup(self):
        self.update_setup_impl(self.path, self.name, {'event_stop': True})

    def update_setup(self, setup2change):
        self.update_setup_impl(self.path, self.name, setup2change)

    @staticmethod
    def get_week_path():
        today = datetime.datetime.today()
        return f"{Persistence.FOLDER_NAME_MAIN}/{today.year}/{today.month}/{today.isocalendar()[1]}"

    @staticmethod
    def get_path(exchange, pair):
        week_path = Persistence.get_week_path()
        exchange = exchange.lower()
        pair = pair.replace('/', '').lower()
        path = f'{week_path}/{Persistence.FOLDER_NAME_SETUPS}/{exchange}/{pair}'
        return path

    @abstractmethod
    def get_setup_impl(self, path, name):
        pass

    @abstractmethod
    def save_setup_impl(self, path, name, setup):
        pass

    @abstractmethod
    def delete_setup_impl(self, path, name):
        pass

    @abstractmethod
    def update_setup_impl(self, path, name, setup):
        pass
