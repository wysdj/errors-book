import os
os.system('mkdir -p /opt/errorbook/backups')
cron = '0 3 * * * cp /opt/errorbook/errors.db /opt/errorbook/backups/errors_$(date +\\%Y\\%m\\%d).db'
with open('/tmp/cron_entry', 'w') as f:
    f.write(cron + '\n')
os.system('crontab /tmp/cron_entry')
os.system('crontab -l')
