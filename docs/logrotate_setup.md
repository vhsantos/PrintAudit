# Logrotate Setup for PrintAudit

Configure logrotate to automatically generate PrintAudit reports when CUPS logs are rotated.

## Important: Use prerotate

Reports must be generated in `prerotate` (before rotation), not `postrotate`. Once logs are rotated, `page_log` is replaced with an empty file.

## Weekly Rotation

```bash
/etc/logrotate.d/cups-daemon
/var/log/cups/*log {
        weekly
        missingok
        rotate 4
        sharedscripts
        prerotate
                /usr/local/bin/printaudit -c /etc/printaudit/printaudit.conf \
                --outputs html,email
        endscript
        postrotate
                invoke-rc.d --quiet cups restart > /dev/null
        endscript
        compress
        delaycompress
        notifempty
        create
}
```

## Monthly Rotation

```bash
/etc/logrotate.d/cups-daemon
/var/log/cups/*log {
        monthly
        missingok
        rotate 7
        sharedscripts
        prerotate
                /usr/local/bin/printaudit -c /etc/printaudit/printaudit.conf \
                --outputs html,email
        endscript
        postrotate
                invoke-rc.d --quiet cups restart > /dev/null
        endscript
        compress
        delaycompress
        notifempty
        create
}
```

Configure email settings in `/etc/printaudit/printaudit.conf` under `[email]` section.

## Testing

Test your configuration:

```bash
sudo logrotate -d /etc/logrotate.d/cups-daemon
```

Force a test rotation:

```bash
sudo logrotate -f /etc/logrotate.d/cups-daemon
```

## Troubleshooting

**PrintAudit not found**: Use full path or find it with `which printaudit`

**Email not working**: Check email configuration in `/etc/printaudit/printaudit.conf` under `[email]` section
