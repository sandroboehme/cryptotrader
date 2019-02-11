# cryptotrader
Currently this project is work in progress.

The goal is to have a trailing stop loss in 1min candles or at higher timeframes based on the Parabolic SAR.

The ParabolicSL used in the code is an adapted ParabolicSAR that resets on a long trade.

It is planned to work on the Binance exchange.

## Requirements
Python 3

## Installation
```
virtualenv --python python3 env
source env/bin/activate
pip3 install -r requirements.txt
```

## Run
``` 
./backtestPsarStopLoss.sh
```

## Exit virtualenv
``` 
deactivate
```