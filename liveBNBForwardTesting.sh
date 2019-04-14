#!/bin/bash
 ./env/bin/python3 -u ./backtesting.py ./test/strategy/param_files/liveBNBForwardTesting.json 2>&1 | tee ./test/strategy/generated/liveBNBForwardTesting.out.txt
echo "This output is written to ./test/strategy/generated/liveBNBForwardTesting.out.txt. You find the generated chart at ./test/strategy/generated/bnb-usdt-1m-live.png"
