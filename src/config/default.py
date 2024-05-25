class DefaultConfig(object):
    SQLALCHEMY_DATABASE_URI = 'mysql://root:@localhost/carbulator'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'thisKeyIsNotSecretChangeIt'
    JWT_SECRET_KEY = 'thisKeyIsNotSecretChangeIt'
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']
    ERROR_404_HELP = False
    SYSTEM_EMAIL = 'YOUR_SYSTEM_EMAIL'
    SMTP_HOST = 'YOUR_SMTP_HOST'
    SMTP_USER = 'YOUR_SMTP_USER'
    SMTP_PASSWORD = 'YOUR_SMTP_PASSWORD'
    SMTP_PORT = 'YOUR_SMTP_PORT'
    FRONTEND_HOST = 'https://example.com'
