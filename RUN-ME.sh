#!/bin/bash

if [[ "$VIRTUAL_ENV" == "" ]]
then
  source venv/bin/activate
fi

if [ $? -eq 0 ]; then
 python3 generate_misp.py;
fi
if [ $? -eq 0 ]; then
  python3 plot_misp.py;
fi
if [ $? -eq 0 ]; then
  bash package_data.sh;
fi
