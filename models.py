import peewee

db = peewee.PostgresqlDatabase('ivle_bot_test', user='postgres')

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

        