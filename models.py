import os
import peewee

class IBModel(peewee.Model):
    class Meta:
        database = db

class User(IBModel):
    user_id = peewee.CharField(max_length=128, primary_key=True)
    auth_token = peewee.TextField()

class Module(IBModel):
    module_id = peewee.TextField()
    module_code = peewee.CharField(max_length=16)
    acad_year = peewee.CharField(max_length=16)
    semester = peewee.IntegerField()
    class Meta:
        primary_key = peewee.CompositeKey('module_code', 'acad_year', 'semester')

def setup_database():
    db.connect()
    try:
        db.create_tables([User, Module])
    except peewee.OperationalError as e:
        print(e)

if __name__ == '__main__':
    if 'HEROKU' in os.environ:
        import urlparse
        urlparse.uses_netloc.append('postgres')
        url = urlparse.urlparse(os.environ["DATABASE_URL"])
        db = PostgresqlDatabase(database=url.path[1:], user=url.username, password=url.password, host=url.hostname, port=url.port)
    else:
        db = peewee.PostgresqlDatabase('ivle_bot_test', user='postgres')
    setup_database()
        