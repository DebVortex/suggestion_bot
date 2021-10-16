from peewee import Model, CharField,  SmallIntegerField

from database import db

STATE_NEW = 0
STATE_ACCEPTED = 1
STATE_DECLINED = 2

class Suggestion(Model):
    summary = CharField()
    discord_id = CharField()
    state =  SmallIntegerField(default=STATE_NEW)

    class Meta:
        database = db

    def accept(self):
        self.state = STATE_ACCEPTED
        self.save()

    def decline(self):
        self.state = STATE_DECLINED
        self.save()
