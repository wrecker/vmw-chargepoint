#!/bin/bash
#

# Check Day of the week. 1=Monday, 5=Friday
dow=$(date +%u)
if [ "$dow" -gt "5" ]
then
  exit
fi

# Check Hour of the day.
# Run only between 8AM & 5PM PST.
# Additionally notify only between 9AM & 4PM PST
# By Default Openshift run on aws-east. So adjust the offsets.
hour=$(date +%-H)
notify=""
if [ "$hour" -lt 11 ] || [ "$hour" -gt 20 ]
then
  exit
fi
if [ "$hour" -ge 12 ] && [ "$hour" -le 19 ]
then
  notify="notify"
fi

# Minute with +2 offset
minute=$(date +%-M)
offset=$((minute + 2))
if [ $(($offset % 4)) -ne 0 ]
then
  exit
fi

echo "Executing @" $(date) $notify >> $OPENSHIFT_PYTHON_LOG_DIR/get_json_cron.log
source $VIRTUAL_ENV/bin/activate
python $OPENSHIFT_REPO_DIR/wsgi/get_json.py $notify >> $OPENSHIFT_PYTHON_LOG_DIR/get_json_cron.log
