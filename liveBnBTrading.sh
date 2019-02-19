#!/bin/bash
 ./env/bin/python3 -u ./livetrading.py ./param_files/liveBNBTrading.json 2>&1 | tee ./generated/liveBNBTrading.out.txt
echo "This output is written to ./generated/liveBNBTrading.out.txt. You find the generated chart at ./generated/bnb-usdt-1m-live.png"