# car-sharing-app
A car sharing webapp for managing fuel costs and planning car trips



## Migrating

- To create a new migration version run `pipenv run flask db migrate` from `src` directory
- To migrate to a new migration version run `pipenv run flask db upgrade` from `src` directory
- Depending on your current revision, you may need to disable the scheduler in `app.py` to run migration commands successfully as the Scheduler is invoked when executing a migration and depends on tables or columns which may not yet exist.

## Issue tracking

- For easier issue tracking, all Carbulator issues are collected in the client project: https://github.com/Carbulator/carbulator-client/issues