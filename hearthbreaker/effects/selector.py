import abc
from hearthbreaker.effects.condition import MinionIsNotTarget

import hearthbreaker.game_objects
from hearthbreaker.effects.base import Selector, Condition


class Player(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_players(self, target):
        pass

    @abc.abstractmethod
    def match(self, source, obj):
        pass

    @staticmethod
    def from_json(name):
        if name == "friendly":
            return FriendlyPlayer()
        elif name == "enemy":
            return EnemyPlayer()
        elif name == "both":
            return BothPlayer


class FriendlyPlayer(Player):
    def match(self, source, obj):
        return source.player is obj.player

    def get_players(self, target):
        return [target]

    def __to_json__(self):
        return "friendly"


class EnemyPlayer(Player):
    def get_players(self, target):
        return [target.opponent]

    def match(self, source, obj):
        return source.player is obj.player.opponent

    def __to_json__(self):
        return "enemy"


class BothPlayer(Player):
    def match(self, source, obj):
        return True

    def get_players(self, target):
        return [target, target.opponent]

    def __to_json__(self):
        return "both"


class CardSelector(Selector, metaclass=abc.ABCMeta):
    def __init__(self, players=FriendlyPlayer()):
        self.players = players

    def get_targets(self, source, player):
        players = player.get_players(player)
        targets = []
        for p in players:
            for card in p.cards:
                if self.selector.match(source, card):
                    targets.append(card)

        return targets

    @abc.abstractmethod
    def match(self, source, obj):
        pass

    def __to_json__(self):
        return {
            'name': 'card',
            'players': self.players
        }

    def __from_json__(self, players='friendly'):
        self.players = Player.from_json(players)
        return self


class SecretSelector(CardSelector):
    def match(self, source, obj):
        return isinstance(obj, hearthbreaker.game_objects.SecretCard)

    def __to_json__(self):
        return {
            'name': 'secret',
            'players': self.players
        }

    def __from_json__(self, players='friendly'):
        self.players = Player.from_json(players)
        return self


class SpellSelector(CardSelector):
    def match(self, source, obj):
        return obj.is_spell()

    def __to_json__(self):
        return {
            'name': 'spell',
            'players': self.players
        }

    def __from_json__(self, players='friendly'):
        self.players = Player.from_json(players)
        return self


class SelfSelector(Selector):
    def get_targets(self, source, player):
        return source

    def match(self, source, obj):
        return source is obj

    def __to_json__(self):
        return {
            'name': 'self'
        }


class PlayerSelector(Selector):
    def __init__(self, players=FriendlyPlayer()):
        self.players = players

    def get_targets(self, source, player):
        return [p.hero for p in self.players.get_players(player)]

    def match(self, source, obj):
        return source.player is obj

    def __to_json__(self):
        return {
            'name': 'player',
            'players': self.players
        }

    def __from_json__(self, players='friendly'):
        self.players = Player.from_json(players)
        return self


class MinionSelector(Selector):
    def __init__(self, condition=MinionIsNotTarget(), players=FriendlyPlayer()):
        self.condition = condition
        self.players = players

    def get_targets(self, source, player):
        players = self.players.get_players(player)
        targets = []
        for p in players:
            for minion in p.minions:
                if self.match(source, minion):
                    targets.append(minion)

        return targets

    def match(self, source, obj):
        if self.condition:
            return isinstance(obj, hearthbreaker.game_objects.Minion) and self.players.match(source, obj)\
                and self.condition.evaluate(source, obj)
        else:
            return isinstance(obj, hearthbreaker.game_objects.Minion) and self.players.match(source, obj)

    def __to_json__(self):
        if self.condition:
            return {
                'name': 'minion',
                'condition': self.condition,
                'players': self.players
            }
        return {
            'name': 'minion',
            'players': self.players
        }

    def __from_json__(self, players, condition=None):
        if condition:
            self.condition = Condition.from_json(**condition)
        self.players = Player.from_json(players)
        return self