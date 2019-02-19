#!/bin/bash
 ./env/bin/python3 -u ./backtesting.py ./test/strategy/param_files/liveBNBBacktesting.json 2>&1 | tee ./test/strategy/generated/liveBNBBacktesting.out.txt
echo "This output is written to ./test/strategy/generated/liveBNBBacktesting.out.txt. You find the generated chart at ./test/strategy/generated/bnb-usdt-1m-live.png"