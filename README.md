# get-data-from-gmail

Small function to connect to a gmail account and download all attachments that have been sent from autonomous buoys through the Iridium satellite network.

## Usage

This function requires a file called `credential.json` to be present in the directory. Follow instructions on https://thepythoncode.com/article/use-gmail-api-in-python on how to obtain this file for access to your gmail account.

Once this is set up, add something like the contents of [`to_crontab`](to_crontab) to your crontab in order to automatically check your gmail account every day for new email with attachments from the Iridium satellite network. The cron job will execute [`get-buoy-data.sh`](get-buoy-data.sh), which will load the required python environment (can be found in [`environment.yml`](environment.yml)) and run [`get-buoy-data.py`](get-buoy-data.py) which will do all the work. Note that, when run for the first time, the script will check all email since `1970/01/01 00:00:00` and download all matching attachements. If you do not want this to happen, specify another time in the format `YYYY/MM/DD hh:mm:ss` in a file called `last_access`, the script will then download only attachemnts received after that time.
