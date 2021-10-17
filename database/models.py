from peewee import Model, CharField,  SmallIntegerField

from database import db

STATE_NEW = 0
STATE_ACCEPTED = 1
STATE_DECLINED = 2

class Suggestion(Model):
    summary = CharField()
    discord_id = CharField()
    channel_id = CharField()
    guild_id = CharField()
    state =  SmallIntegerField(default=STATE_NEW)

    class Meta:
        database = db

    def update_state(self, state):
        self.state = state
        self.save()

    def accept(self):
        self.update_state(STATE_ACCEPTED)

    def decline(self):
        self.update_state(STATE_DECLINED)

    def renew(self):
        self.update_state(STATE_NEW)
