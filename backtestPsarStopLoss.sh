#!/bin/bash
 ./env/bin/python3 -u ./backtesting.py ./test/strategy/param_files/previousPsarStopLossUsed.json 2>&1 | tee ./test/strategy/generated/previousPsarStopLossUsed.out.txt
echo "This output is written to ./test/strategy/generated/previousPsarStopLossUsed.out.txt. You find the generated chart at ./test/strategy/generated/bnb-usdt-15m-prev-psar-sl.png"