
import unittest

from test import backtesting


class TestTrailingStopLoss(unittest.TestCase):

    def setUp(self):
        self.param_file_path_prefix = 'test/strategy/param_files/'

    def test_previousPsarStopLossUsed(self):
        backtesting.main([self.param_file_path_prefix + 'previousPsarStopLossUsed.json'])

    @unittest.skip("For some reason the psar gets lower here. From my understanding that shouldn't happen. Debug here.")
    def test_lowerPsarBug(self):
        backtesting.main([self.param_file_path_prefix + 'lowerPsarBug.json'])

    def test_fallBackStopLoss(self):
        backtesting.main([self.param_file_path_prefix + 'fallbackStopLossUsed.json'])

    @unittest.skip("Change the params depending on the current market price and remove the skip function. ")
    def test_live(self):
        backtesting.main([self.param_file_path_prefix + 'liveBNBBacktesting.json'])

    @unittest.skip("Needs the stopLoss strategy to be configured.")
    def test_simple_stop_loss(self):
        backtesting.main([self.param_file_path_prefix + 'stopLoss.json'])


if __name__ == '__main__':
    unittest.main()
