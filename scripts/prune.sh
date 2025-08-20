#!/bin/bash
# cron job to remove old analyis weekly

log_file="/home/ubuntu/logs/prune.log"
# Delete log file if larger than 10MB
[[ $(stat --printf '%s' "$log_file") -gt 10485760 ]] && rm $log_file

exec >> $log_file
current_date_time="`date +"%Y%m%d %T"`"
echo "pruning analysis: $current_date_time"
source /home/ubuntu/env/bin/activate
python /home/ubuntu/OasisPythonUI/scripts/prune_analysis.py -f --password=$OASIS_PASSWORD -d 7
