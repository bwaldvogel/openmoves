import sys
sys.path.insert(0, '.')

activate_this = 'virtualenv/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

import webapp
application = webapp.init(configFile='openmoves.cfg')

assert 'ADMINS' in application.config, 'no admins configured'
admins = application.config['ADMINS']

assert 'SYSTEM_SENDER_ADDRESS' in application.config, 'no system sender address configured'
systemSenderAddress = application.config['SYSTEM_SENDER_ADDRESS']

smtpServer = application.config['SMTP_SERVER']

# http://flask.pocoo.org/docs/errorhandling/
if not application.debug:
    import logging
    from logging.handlers import SMTPHandler
    mail_handler = SMTPHandler(smtpServer, systemSenderAddress, admins, 'openmoves.net application error')
    mail_handler.setLevel(logging.ERROR)
    application.logger.addHandler(mail_handler)
