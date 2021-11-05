UPVOTE = '👍'
DOWNVOTE = '👎'

def get_votes(reactions, vote_emoji):
    return sum([x.count for x in reactions if x.emoji == vote_emoji])