#!/bin/bash
 ./env/bin/python3 -u ./backtesting.py ./test/strategy/param_files/fallbackStopLossUsed.json 2>&1 | tee ./test/strategy/generated/fallbackStopLossUsed.out.txt
echo "This output is written to ./test/strategy/generated/fallbackStopLossUsed.out.txt. You find the generated chart at ./test/strategy/generated/bnb-usdt-15m-fallback-sl.png"