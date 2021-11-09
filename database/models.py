from peewee import Model, CharField, IntegerField, SmallIntegerField

from database import db

STATE_NEW = 0
STATE_ACCEPTED = 1
STATE_DECLINED = 2

class Suggestion(Model):
    summary = CharField()
    discord_id = IntegerField()
    channel_id = IntegerField()
    guild_id = IntegerField()
    state =  SmallIntegerField(default=STATE_NEW)
    up_votes = IntegerField(default=0)
    down_votes = IntegerField(default=0)

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

    def set_votes(self, upvote, downvote):
        self.up_votes = upvote
        self.down_votes = downvote
        self.save()
