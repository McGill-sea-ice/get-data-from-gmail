#!/bin/bash
# to be run each day, checking for new emails from sbd.iridium.com
# and downloading and categorizing the attachments
echo "---------- get-buoy-data.sh -----------"
echo " "
date

# load conda environment
source /aos/home/jrieck/miniconda3/etc/profile.d/conda.sh
conda activate buoy-data

python3 /storage2/common/get-buoy-data/get-buoy-data.py
