To run the server do the followings (assumption: OS is linux/macos):

1. Create virtualenv: virtualenv venv
2. Activate it: source venv/bin/activate
3. Install dependencies: pip install -r requirements.txt
4. Create Postgres DB locally and put connection url to .env
   ie: DATABASE_URL=postgresql://kayadev:kayapass@localhost/kayadb
5. Migrate tables to the db
   flask db init
   flask db migrate
   flask db upgrade
6. Migrate data into tables
   Copy and paste the excel file with data into main directory of the system and rename it Kaya_data.xlsx
   Run: python import_data.py
7. Start the server: flask run
   Voila you may now test the endpoints via Postman or any other API Testing Tool of preference.

---

Detailed details

Python 3.11, Flask 3.0.3 are used. (others may found in requirements.txt)

To create tables i used SQLAlchemy, with which I declared tables as classes and then used Flask-Migrate to populate them in the postgres db

To migrate data from excel to db i created a script import_data.py
it uses pandas to read xlsx file, create dataframe and send data to db tables
just execute that python file to migrate data from excel to db tables: python import_data.py

For logs i used logging package. Since it provides simple logging experience and customization.
It will generate logs folder with app.log file within which will keep the logs. Besides if the code will be deployed on lambda and that lambda will have access to CloudWatch the logs will appear there as well.

For Unit Tests i used standard python framework 'unittest'.
I configured it to point to local sqllite db, which is generated, populated with test data and deleted after the test case.
To run unit tests, execute this command: python -m unittest tests/test_app.py

For deployment i used Zappa(best for adjusting lambda settings,imo) and Github Actions(free).
I set up the CI/CD workflow inside .github/workflows/main.yml. For now i put non-existing branch "deploy" so it won't start the workflow
It will establish connection with AWS account, using the aws credentials that will be stored inside repo secrets, and push the code to Lambda using zappa.
The reason for using zappa is to make configurations to Lambda settings simpler and faster. The configs can be found in zappa_settings.json
