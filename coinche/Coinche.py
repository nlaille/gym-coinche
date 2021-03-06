from coinche.Deck import Deck
from coinche.Card import Card, Suit, Rank
from coinche.Player import Player, Team
from coinche.Trick import Trick
from coinche.CardsOrder import *
import random
from gym import Env

'''Change auto to False if you would like to play the game manually.'''
'''This allows you to make all passes, and plays for all four players.'''
'''When auto is True, passing is disabled and the computer plays the'''
'''game by "guess and check", randomly trying moves until it finds a'''
'''valid one.'''


class CoincheEnv(Env):

    def __init__(self, playersName, maxScore=100):

        self.maxScore = maxScore

        self.roundNum = 0
        self.deck = Deck()
        self.trickNum = 0  # initialization value such that first round is round 0
        self.dealer = -1  # so that first dealer is 0
        self.passes = [1, -1, 2, 0]  # left, right, across, no pass
        self.currentTrick = Trick()
        self.trickWinner = -1

        # Make four players
        self.players = [Player(playersName[0]),
                        Player(playersName[1]),
                        Player(playersName[2]),
                        Player(playersName[3])]

        # Make two teams
        self.teams = [Team(0, self.players[0], self.players[2]),
                      Team(1, self.players[1], self.players[3])]

        # Linking players to a team
        self.players[0].team = self.teams[0]
        self.players[2].team = self.teams[0]
        self.players[1].team = self.teams[1]
        self.players[3].team = self.teams[1]

        # Linking players to their teammate
        self.players[0].teammate = self.players[2]
        self.players[2].teammate = self.players[0]
        self.players[1].teammate = self.players[3]
        self.players[3].teammate = self.players[1]

        '''
        Player physical locations:
        Game runs clockwise

             p3
        p2        p4
             p1

        '''

        self.event = None
        self.round = 0

        self.renderInfo = {'printFlag': False, 'Msg': ""}

    def _countTrickValue(self):
        """
        This function computes the value of the trick given if the cards are atout cards or not
        ex:
        if atout_suit is heart and the trick is [Ad, Td, 9h, 7d]:
        --> the trickValue is 11(Ad) + 10(Td) + 14(9h) + 0(7d) = 35 for player "Sud"

        There is also the 10 de der that gives ten extra points if you win last trick (7th trick)
        """
        trickValue = 0
        for card in self.currentTrick.trick:

            if card != Card(0, -1):
                if card.suit.iden == self.atout_suit:
                    trickValue += atout_values[card.rank.rank]
                else:

                    trickValue += generic_values[card.rank.rank]
        # 10 de der
        if self.trickNum == 7:
            trickValue += 10
        return trickValue

    @classmethod
    def _handsToStrList(self, hands):
        """
        This function helps to print a hand of a player
        """
        output = []
        for card in hands:
            output += [str(card)]
        return output

    def _dealCards(self, dealer):
        """
        This function deals the deck
        TODO: deal card the coinche way !!!
        """
        i = dealer + 1  # Dealer doesn't deal himself first
        #         while(self.deck.size() > 0):
        #             self.players[i % len(self.players)].addCard(self.deck.deal())
        #             i += 1
        '''3-3-2 Dealing'''
        legalDealingSequences = [[3, 3, 2], [3, 2, 3]]  # Defining academic dealing sequences
        dealingSequence = legalDealingSequences[random.randint(0, 1)]  # Flipping a coin to choose the Dealing Sequence
        for cardsToDeal in dealingSequence:
            print("Taille du paquet: ",self.deck.size())
            deck_size = self.deck.size()  # Size of the deck before i-th round of dealing
            while (self.deck.size() > deck_size - 4 * cardsToDeal):  # Stopping condition on one round
                self.players[i % len(self.players)].addCards(self.deck.deal(cardsToDeal))
                i += 1

    def _evaluateTrick(self):
        self.trickWinner = self.currentTrick.winner
        p = self.players[self.trickWinner]
        p.trickWon(self.currentTrick.trick)

    # print player's hand
    def _printPlayer(self, i):
        p = self.players[i]
        print(p.name + "'s hand: " + str(p.hand))

    # print all players' hands
    def _printPlayers(self):
        for p in self.players:
            print(p.name + ": " + str(p.hand))

    # show cards played in current trick
    def _printCurrentTrick(self):
        trickStr = '\nCurrent table:\n'
        trickStr += "Atout suit of the round: " + Suit(self.atout_suit).__str__() + "\n"
        trickStr += "Trick suit: " + self.currentTrick.suit.__str__() + "\n"
        for i, card in enumerate(self.currentTrick.trick):
            if self.currentTrick.trick[i] is not 0:
                trickStr += self.players[i].name + ": " + str(card) + "\n"
            else:
                trickStr += self.players[i].name + ": None\n"

        return trickStr

    def _getCurrentTrickStrList(self):
        trick_list = []
        for i, card in enumerate(self.currentTrick.trick):
            if self.currentTrick.trick[i] is not 0:
                trick_list += [{'playerName': self.players[i].name, 'card': str(card)}]

        return trick_list

    def _event_GameStart(self):
        self.event_data_for_server = {}
        self.event_data_for_client \
            = {'event_name': self.event
            , 'broadcast': True
            , 'data': {
                "players": [
                    {'playerName': self.players[0].name},
                    {'playerName': self.players[1].name},
                    {'playerName': self.players[2].name},
                    {'playerName': self.players[3].name}
                ]
            }
               }

        for p in self.players:
            p.score = 0
        self.round = 0

        self.renderInfo = {'printFlag': False,
                           'Msg': ""}
        self.renderInfo['printFlag'] = True
        self.renderInfo['Msg'] = '\n*** Hearts Start ***\n'

    def _event_NewRound(self):

        self.round += 1
        if self.roundNum == 0:
            self.deck.shuffle()
        self.roundNum += 1
        self.trickNum = 0
        self.trickWinner = -1
        self.dealer = (self.dealer + 1) % len(self.players)
        for p in self.players:
            p.resetRound()
            p.discardTricks()

        self._dealCards(self.dealer)
        self.currentTrick = Trick()

        self.atout_suit = -1
        self.contrat = 0
        self.leadingTeam = None

        for t in self.teams:
            t.score = 0

        self.event_data_for_client \
            = {'event_name': self.event
            , 'broadcast': True
            , 'data': {
                "Teams": [
                    {'teamName': self.teams[0].name,
                     'score': self.teams[0].score},
                    {'teamName': self.teams[1].name,
                     'score': self.teams[1].score},
                ]
            }
               }

        self.event = 'ShowPlayerHand'
        self.event_data_for_server = {'now_player_index': 0}

        self.renderInfo['printFlag'] = True
        self.renderInfo['Msg'] = '\n*** Start Round {0} ***\n'.format(self.round)
        for p in self.players:
            self.renderInfo['Msg'] += '{0}: {1}\n'.format(p.name, p.score)
            self.renderInfo['Msg'] += 'Leading team: {0}\n'.format(self.leadingTeam)

    def _event_ShowPlayerHand(self):

        if self.event_data_for_server['now_player_index'] < 4:
            now_player_index = self.event_data_for_server['now_player_index']
            self.event_data_for_client \
                = {"event_name": self.event,
                   "broadcast": False,
                   "data": {
                       'playerName': self.players[now_player_index].name,
                       'hand': self._handsToStrList(sum(self.players[now_player_index].hand.hand, []))
                   }
                   }
            self.event_data_for_server['now_player_index'] += 1

        else:
            self.event = 'ChooseContrat'
            self.event_data_for_server = {'shift': 0}
            self.numTurnOfAnnounce = 0

    def _event_ChooseContrat(self):
        shift = self.event_data_for_server['shift']

        if shift == 0 and self.numTurnOfAnnounce == 0:
            self.playerToStartAnnounce = (self.dealer + 1) % 4
            self.current_player = self.players[self.playerToStartAnnounce]
        else:
            self.current_player_i = (self.playerToStartAnnounce + shift) % 4
            self.current_player = self.players[self.current_player_i]

        self.event_data_for_client \
            = {"event_name": self.event,
               "broadcast": False,
               "data": {
                   'playerName': self.current_player.name,
                   'hand': self._handsToStrList(sum(self.current_player.hand.hand, [])),
                   'contrat': self.contrat,
                   'suit': self.atout_suit,
                   'shift': shift}
               }

    def _assert_new_contrat(self, actionData):
        proposed_contrat = actionData["data"]["action"]["value"]
        is_bidding = actionData["data"]["action"]["newContrat"]
        if not is_bidding:
            # The player is not making any announce
            return True
        else:
            if proposed_contrat % 10:
                self.announce_error = "Contrat value must be a multiple of 10"
                return False
            if proposed_contrat < 80:
                self.announce_error = "Contrat value must be greater than 80"
                return False
            if proposed_contrat <= self.contrat:
                self.announce_error = "Contrat must be greater than current contrat"
                return False
            # 180 if there is "Belote&Rebelote"
            if proposed_contrat > 180 and proposed_contrat < 250:
                self.announce_error = "Current contrat value doesn't exist. Announce capo (250) or max 180 !"
                return False
            else:
                return True

    def _event_ChooseContratAction(self, actionData):

        shift = self.event_data_for_server['shift']
        player_must_announce_again = False
        if shift == 0 and self.numTurnOfAnnounce == 0:
            self.playerToStartAnnounce = (self.dealer + 1) % 4
            self.current_player_i = self.playerToStartAnnounce
            self.current_player = self.players[self.playerToStartAnnounce]

        else:
            self.current_player_i = (self.playerToStartAnnounce + shift) % 4
            self.current_player = self.players[self.current_player_i]

        # If new contrat proposed isn't valid
        if not self._assert_new_contrat(actionData):
            print(self.announce_error)
            player_must_announce_again = True
            actionData["data"]["action"]["value"] = None
            actionData["data"]["action"]["suit"] = None
            actionData["newContrat"] = False
            self.event = "ChooseContrat"
            self._event_ChooseContrat()

        else:
            self.contrat = actionData["data"]["action"]["value"]
            self.atout_suit = actionData["data"]["action"]["suit"]
        # If the player as passed or made a valid announce
        if not player_must_announce_again:
            # if the player made a valid announce
            if actionData["data"]["action"]["newContrat"]:
                # if there is a modification of the previous contrat, new turn of announce starting after the current player
                self.playerToStartAnnounce = self.current_player_i
                self.numTurnOfAnnounce = 1
                self.event_data_for_server['shift'] = 0
                self.leadingTeam = self.current_player.team.teamNumber

            if self.event_data_for_server['shift'] < 3:

                self.event_data_for_server['shift'] += 1
                self.event = "ChooseContrat"
                self._event_ChooseContrat()

            else:

                self.event_data_for_server['shift'] += 1
                if self.contrat == 0 and self.atout_suit == -1:
                    self.renderInfo['printFlag'] = True

                    self.renderInfo['Msg'] += "everybody passed - New round is comming"

                    self.event = 'RoundEnd'
                    self._event_ChooseContrat()
                    self.event_data_for_server = {}

                # if everyone had the opportunity to announce, let's play !
                else:
                    self.event = 'PlayTrick'
                    self.renderInfo['Msg'] += 'Leading team: {0}\n'.format(self.leadingTeam)
                    self._event_PlayTrick()

    def _event_PlayTrick(self):

        shift = self.event_data_for_server['shift']
        print("shift", shift, "trickNum", self.trickNum)
        if self.trickNum == 0 and shift == 0:

            current_player = self.players[(self.dealer + 1) % 4]

        else:
            current_player_i = (self.trickWinner + shift) % 4
            current_player = self.players[current_player_i]

        self.event_data_for_client = {
            "event_name": self.event,
            "broadcast": False,
            "data": {
                'playerName': current_player.name,
                'hand': self._handsToStrList(sum(current_player.hand.hand, [])),
                'trickNum': self.trickNum + 1,
                'trickSuit': self.currentTrick.suit.__str__(),
                'currentTrick': self._getCurrentTrickStrList(),
                'contrat': self.contrat,
                'suit': self.atout_suit
            }
        }
    def _assert_valid_play(self, add_card, current_player):

        # If suit is atout, you must go higher if you can
        if (add_card is not None and
                add_card.suit == Suit(self.atout_suit) and
                self.currentTrick.suit == Suit(self.atout_suit)):

            if (current_player.hasHigherAtout(self.atout_suit, self.currentTrick.highest_rank) and
                    atout_rank[add_card.rank.rank] < self.currentTrick.highest_rank):
                print("Must put a higher atout")
                add_card = None

            # player tries to play off suit but has trick suit
        if add_card is not None and add_card.suit != self.currentTrick.suit:
            if current_player.hasSuit(self.currentTrick.suit):
                print("Must play the suit of the current trick.")
                add_card = None
            elif current_player.hasAtout(Suit(self.atout_suit)) and add_card.suit != Suit(self.atout_suit):
                print("Must play Atout.")
                add_card = None
            elif (current_player.hasAtout(Suit(self.atout_suit)) and
                  add_card.suit == Suit(self.atout_suit)):
                # Player can play a higher atout but doesn't do so --> forced to play a higher atout
                if (self.currentTrick.highest_is_atout and
                        current_player.hasHigherAtout(self.atout_suit, self.currentTrick.highest_rank) and
                        atout_rank[add_card.rank.rank] < self.currentTrick.highest_rank):
                    print("Must put a higher atout")
                    add_card = None
        return add_card

    def _event_PlayTrick_Action(self, action_data):

        shift = self.event_data_for_server['shift']
        current_player_i = (self.trickWinner + shift) % 4
        current_player = self.players[current_player_i]
        add_card = current_player.play(action_data['data']['action']['card'])

        if shift == 0:
            self.currentTrick.setTrickSuit(add_card)

        add_card = self._assert_valid_play(add_card=add_card, current_player= current_player)


        if add_card is not None:
            current_player.removeCard(add_card)
            self.currentTrick.addCard(add_card, current_player_i, Suit(self.atout_suit))
            self.event_data_for_server['shift'] += 1
            self.event = 'ShowTrickAction'
            self._event_ShowTrickAction()
        else:
            self.event = 'PlayTrick'
            self._event_PlayTrick()

    def _event_ShowTrickAction(self):

        self.renderInfo['printFlag'] = True
        self.renderInfo['Msg'] = "\n" + self._printCurrentTrick()
        self.renderInfo['Msg'] += 'Leading team: {0}\n'.format(self.leadingTeam)
        self.event_data_for_client \
            = {"event_name": self.event,
               "broadcast": True,
               "data": {
                   'trickNum': self.trickNum + 1,
                   'trickSuit': self.currentTrick.suit.__str__(),
                   'currentTrick': self._getCurrentTrickStrList(),
                   'trickValue': self._countTrickValue(),
                   'contrat': self.contrat,
                   'suit': self.atout_suit
               }
               }

        if self.currentTrick.cardsInTrick < 4:
            self.event = 'PlayTrick'
        else:

            self.event = 'ShowTrickEnd'
            self._evaluateTrick()

            self.players[self.trickWinner].score += self._countTrickValue()
            [t.updateRoundScore() for t in self.teams]

    def _event_ShowTrickEnd(self):

        cards = []
        for card in self.currentTrick.trick:
            cards += [str(card)]

        self.event_data_for_client \
            = {"event_name": self.event,
               "broadcast": True,
               "data": {
                   'trickNum': self.trickNum + 1,
                   'trickWinner': self.players[self.trickWinner].name,
                   'cards': cards,
                   'contrat': self.contrat,
                   'suit': self.atout_suit
               }
               }

        self.renderInfo['printFlag'] = True
        self.renderInfo['Msg'] = '\n*** Trick {0} ***\n'.format(self.trickNum + 1)
        self.renderInfo['Msg'] += 'Winner: {0}\n'.format(self.players[self.trickWinner].name)
        self.renderInfo['Msg'] += 'ValueTrick: {0}\n'.format(self._countTrickValue())

        for i in range(2):
            self.renderInfo['Msg'] += '{}:{}\n'.format(self.teams[i].name, self.teams[i].score)

        self.renderInfo['Msg'] += 'Winning team: {0}\n'.format(self.players[self.trickWinner].team.name)
        self.renderInfo['Msg'] += 'cards: {0}\n'.format(cards)

        self.renderInfo['Msg'] += 'AtoutIs: {0}\n'.format(Suit(self.atout_suit).string)

        self.currentTrick = Trick()

        self.trickNum += 1
        if self.trickNum < 8:
            self.event = 'PlayTrick'
            self.event_data_for_server = {'shift': 0}
        else:
            self.event = 'RoundEnd'
            self.event_data_for_server = {}

    def _event_RoundEnd(self):
        print(self.teams[1].cardsInRound)
        self.event_data_for_client \
            = {"event_name": self.event,
               "broadcast": True,
               "data": {
                   "teams": [
                       {'TeamName': self.teams[0].name,
                        'score': self.teams[0].score},
                       {'TeamName': self.teams[1].name,
                        'score': self.teams[1].score},
                   ],
                   'Round': self.round,
                   'contrat': self.contrat,
                   'suit': self.atout_suit
               }
               }

        self.renderInfo['printFlag'] = True
        self.renderInfo['Msg'] = '\n*** Round {0} End ***\n'.format(self.round)
        for t in self.teams:
            self.renderInfo['Msg'] += 'round Score {0}: {1}\n'.format(t.name, t.score)
            self.renderInfo['Msg'] += 'global score {0}: {1}\n'.format(t.name, t.globalScore)

        roundScore_list_for_teams = [0, 0]
        if self.contrat == 0 and self.atout_suit == -1:
            self.renderInfo['Msg'] += 'Everybody passed'

        elif self.teams[self.leadingTeam].score >= self.contrat:
            self.teams[self.leadingTeam].globalScore += self.contrat
            roundScore_list_for_teams[self.leadingTeam] = self.contrat

        else:
            self.teams[self.leadingTeam - 1].globalScore += self.contrat
            roundScore_list_for_teams[self.leadingTeam - 1] = self.contrat

        roundScore_list_for_players = roundScore_list_for_teams * 2
        max_score_team = max(self.teams, key=lambda x: x.globalScore)
        # new round if no one has lost
        if max_score_team.globalScore < self.maxScore:
            self.event = 'NewRound'
            self.event_data_for_server = {}
        else:
            self.event = 'GameOver'
            self.event_data_for_server = {}

        reward = {}
        for current_player_i in range(len(self.players)):
            reward[self.players[current_player_i].name] = roundScore_list_for_players[current_player_i]

        '''Rebuild Deck from tricks collected by each player'''
        # Gathering Each Team's tricks
        for t in self.teams:
            t.joinCards()
            t.joinHands()

        if (self.teams[0].cardsInRound != []) | (
                self.teams[1].cardsInRound != []):  # If round was played (not everybody passed)
            self.deck.joinTeamsSubDecks(self.teams[0], self.teams[1])


        else:  # Else, Gather back hands
            self.deck.joinTeamsHands(self.teams[0], self.teams[1])
        print("taille du paquet maintenant", self.deck.size())
        self.deck.cut_deck()  # Then cut
        return reward

    def _event_GameOver(self):

        winner = min(self.teams, key=lambda x: x.globalScore)

        self.event_data_for_client \
            = {"event_name": self.event,
               "broadcast": True,
               "data": {
                   "teams": [
                       {'TeamName': self.teams[0].name,
                        'score': self.teams[0].globalScore},
                       {'TeamName': self.teams[1].name,
                        'score': self.teams[1].globalScore},
                   ],
                   'Round': self.round,
                   'Winner': winner.name
               }
               }

        self.renderInfo['printFlag'] = True
        self.renderInfo['Msg'] = '\n*** Game Over ***\n'
        for p in self.teams:
            self.renderInfo['Msg'] += 'round score {0}: {1}\n'.format(p.name, p.score)
            self.renderInfo['Msg'] += '{0}: {1}\n'.format(p.name, p.globalScore)

        self.renderInfo['Msg'] += '\nRound: {0}\n'.format(self.round)
        self.renderInfo['Msg'] += 'Winner: {0}\n'.format(winner.name)

        self.event = None

    def reset(self):

        # Generate a full deck of cards and shuffle it
        self.event = 'GameStart'
        self._event_GameStart()
        observation = self.event_data_for_client
        self.event = 'NewRound'
        self.event_data_for_server = {}

        return observation

    def render(self):

        if self.renderInfo['printFlag']:
            print(self.renderInfo['Msg'])
            self.renderInfo['printFlag'] = False
            self.renderInfo['Msg'] = ""

    def step(self, action_data):
        observation, reward, done, info = None, None, None, None
        print("\n \ntype of event in env.step: ", self.event)
        if self.event == 'NewRound':
            self._event_NewRound()

        elif self.event == 'ShowPlayerHand':
            self._event_ShowPlayerHand()

        elif self.event == 'ChooseContrat' or self.event == 'ChooseContratAction':
            print("clubs = 0")
            print("diamonds = 1")
            print("spades = 2")
            print("hearts = 3")
            if action_data != None:
                self._event_ChooseContratAction(action_data)
            else:
                if self.event == 'ChooseContrat':
                    self._event_ChooseContrat()

        elif self.event == 'PlayTrick' or self.event == 'ShowTrickAction' or self.event == 'ShowTrickEnd':
            print(self.event)
            if action_data != None and action_data['event_name'] == "PlayTrick_Action":

                self._event_PlayTrick_Action(action_data)
            else:
                if self.event == 'PlayTrick':
                    self._event_PlayTrick()
                elif self.event == 'ShowTrickEnd':
                    reward = self._countTrickValue()
                    self._event_ShowTrickEnd()


        elif self.event == 'RoundEnd':
            reward = self._event_RoundEnd()

        elif self.event == 'GameOver':
            self._event_GameOver()

        elif self.event == None:
            self.event_data_for_client = None
            done = True

        print(reward)
        observation = self.event_data_for_client
        return observation, reward, done, info
