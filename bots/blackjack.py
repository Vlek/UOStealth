#Event-based Blackjack NPC by Vlek, Leader of the Bloodskull Clan

"""Todo list:

-Write a script that causes stealth to fail and check if it still saves stats

-Make the bot able to interpret the things given to him
    -Put a check in for gold and gold checks
    -Make him able to figure out how much gold checks are worth

-Give him the ability to give gold to players
    -Ability to open bank (probably needs to know when it is open)
    -Take inventory of the amount of gold in the bank
    -Be able to make checks
    -Give the checks/gold to the player
        -Give 5k gold or less in gold, else checks?
    -Must be able to handle the case where the player cancels the trade.

-Clean up check whether player has statistics with a function that takes a playerid
    -Should add them if they're not already in instead of replying true or false.

-Add in sidebets?

-Allow users to set the color that the bot uses when it talks to them.

-Add in a pause for when a player says something to the bot.
    - Should it only respond to messages sent every second?

"""

import stealth, random, time, os.path
import cPickle as pickle

__author__ = 'Vlek'
__version__ = '0.1.5'

__decks__ = 2
__payout__ = 1.2 #5:6
__maxbet__ = 50000
__minbet__ = 100
__msgcolor__ = 52
__emoteafterplay__ = 0.75 #0 - 100%, 1.0 - 0%, or never emote after the player plays a game.

#This number should inform the maxbet. Everytime someone wagers money,
#This number will rise and fall which will cause the bot to be able to
#Accept bigger or smaller bets. It should keep enough to cash everyone
#out that has money with the bot, and also enough to do maxbet*1.2*50
#the maxbet should be raised until 1 mil where possible.
#For now, I want to see the amount of gold being raked in. I might be able
#to do some good with it instead of throwing it away (buying up hybrid armor)
#Amount necessary: players kept gold + maxbet * 1.2 * 50
__goldheld__ = 0

class blackjackStatistics:
    """Class used to house a single player's blackjack statistics"""
    def __init__(self, senderid):
        self.player = senderid
        self.wins = 0
        self.losses = 0
        self.ties = 0
        self.blackjacks = 0
        self.earnings = 0
        self.goldlost = 0
        self.goldwon = 0
        #This is the current amount the player wishes to wager.
        #Should send up an error message when the player wishes to
        #Bet with more than they have. Bet 0 is playing without money.
        self.betamount = 0
        self.currentHand = 0


class pokerGame:

    def __init__(self, senderid):
        self.suits = ['hearts','clubs','diamonds','spades']
        self.suitSymbols = {'hearts':u"\u2661",'clubs':u"\u2663",'diamonds':u"\u2662",'spades':u"\u2660"}
        #Dark versions - 'hearts':u"\u2665", 'diamonds':u"\u2666
        self.cardTypes = [2,3,4,5,6,7,8,9,10,'jack','king','queen','ace']
        self.cards = []

        for suit in self.suits:
            for cardType in self.cardTypes:
                self.cards.append([cardType, suit])

        self.player = senderid
        self.playerName = stealth.GetName(senderid).title()
        self.deck = self.cards*__decks__
        self.playerHand = []
        self.houseHand = []

        #Draw some initial cards
        for i in range(2):
            self.draw()
            self.draw('house')

    def draw(self, person='player'):
        drawnCard = random.choice(self.deck)
        self.deck.pop( self.deck.index( drawnCard ) )
        if person == 'player':
            self.playerHand.append( drawnCard )
        else:
            self.houseHand.append( drawnCard )

    def hit(self):
        self.draw()
        if self.calcHand() < 21:
            self.printHand('- Hit or Stand?')
        else:
            self.stand()


    def stand(self):
        #If player didn't bust or get blackjack, get the dealer some cards
        if not self.calcHand('player') > 21 and not self.isBlackjack():
            while self.calcHand('player') > self.calcHand('house') < 21 or self.calcHand('house') < 17:
                #Must stand on soft 17!
                if not self.calcHand('house') == 17:
                    self.draw('house')
                else:
                    break

        #Check if the player is in the stats dictionary:
        if not self.player in blackjackStats:
            blackjackStats[self.player] = blackjackStatistics(self.player)

        #If house wins,
        if 22 > self.calcHand('house') > self.calcHand('player') or self.calcHand('player') > 21 or not self.isBlackjack() and self.isBlackjack('house'):
            blackjackStats[self.player].losses += 1
            blackjackStats[self.player].earnings -= blackjackStats[self.player].betamount
            blackjackStats[self.player].goldlost += blackjackStats[self.player].betamount
            self.printHand('- {} loses!'.format(self.playerName), False)
            if random.random() > __emoteafterplay__:
                stealth.UOSayColor(random.choice(['[e howl','[e woohoo', '[e clap', '[e yea']),__msgcolor__)
        #If it's a tie
        elif self.calcHand('player') == self.calcHand('house'):
            blackjackStats[self.player].ties += 1
            self.printHand('- {} ties!'.format(self.playerName), False)
            if random.random() > __emoteafterplay__:
                stealth.UOSayColor(random.choice(['[e groan','[e sigh','[e fart','[e sniff']),__msgcolor__)
        #If the player wins
        else:
            blackjackStats[self.player].wins += 1
            blackjackStats[self.player].earnings += blackjackStats[self.player].betamount * __payout__
            blackjackStats[self.player].goldwon += blackjackStats[self.player].betamount
            self.printHand('- {} wins!'.format(self.playerName), False)
            if random.random() > __emoteafterplay__:
                stealth.UOSayColor(random.choice(['[e howl','[e bscough','[e woohoo', '[e clap', '[e yea', '[e no', '[e gasp']),__msgcolor__)

        self.gameEnd()

    def hand(self):
        self.printHand('- Hit or Stand?')

    def printHand(self, message, hidehousehand=True):
        stealth.UOSayColor(u'{}: {} ({}) House: {} {}'.format(self.playerName,
                                                             u' '.join([self.printCard(card) for card in self.playerHand]),
                                                             'Bust' if self.calcHand() > 21 else 'Blackjack' if self.calcHand() == 21 and len(self.playerHand) == 2 else self.calcHand(),
                                                             u' '.join([self.printCard(self.houseHand[0]), '?'] if hidehousehand else [self.printCard(card) for card in self.houseHand]+['({})'.format('Bust' if self.calcHand('house') > 21 else 'Blackjack' if self.calcHand('house') == 21 and len(self.houseHand) == 2 else self.calcHand('house'))]),message),__msgcolor__)

    def calcHand(self, person='player'):
        handTotal = 0
        if person == 'player':
            hand = self.playerHand
        else:
            hand = self.houseHand

        aces = []
        for card in hand:
            #If it's a number card,
            if type(card[0]) == int:
                handTotal += card[0]
            #Gotta deal with aces last
            elif card[0] == 'ace':
                aces.append( card )
            #Else it's a face card
            else:
                handTotal += 10

            if handTotal > 21:
                return 22

        #Here's where we deal with aces
        for card in range(len(aces)):
            handTotal += 1 if handTotal > 10 or aces[card+1:] else 11

        return handTotal

    def isSoft(self, person='player'):
        handTotal = 0
        if person == 'player':
            hand = self.playerHand
        else:
            hand = self.houseHand

        aces = []
        for card in hand:
            #If it's a number card,
            if type(card[0]) == int:
                handTotal += card[0]
            #Gotta deal with aces last
            elif card[0] == 'ace':
                aces.append( card )
            #Else it's a face card
            else:
                handTotal += 10

            if handTotal > 21:
                return False

        #If there's at least one ace and the sum of the number of aces
        #plus the amount of the hand before calculating the aces adds
        #up to less than 12, meaning it can take a face card, then it's soft,
        if aces and handTotal + len(aces) < 12:
            return True


        return False

    def isBlackjack(self, person='player'):
        if person == 'player':
            hand = self.playerHand
        else:
            hand = self.houseHand
        return len(hand) == 2 and self.calcHand(person) == 21

    def printCard(self, card):
        #need to somehow add suitSymbols[card[1]]
        return u'{}{}'.format(card[1][0].upper(),card[0] if type(card[0]) == int else card[0][0].upper())

    def gameEnd(self):
        blackjackStats[self.player].currentHand = 0

    def blackjackCheck(self):
        """This method is called after game creation to check whether to stop.
        It fixes the issue of not being able to properly remove the game from
        the current games list in the case of a blackjack. Also, it's possible
        to get a double payout if they stand afterwards."""

        #If they're lucky enough to draw 21 off the bat,
        if self.calcHand() == 21:
            #End play right away,
            self.stand()
        else:
            #Display hand
            self.hand()

#Statistics loading:
#PlayerID: [gamblingMoney, wins, loses, ties, amountLost, blackjacks?]

if os.path.isfile('stats.pkl'):
    r = open('stats.pkl', 'r')
    blackjackStats = pickle.load(r)
    r.close()
else:
    blackjackStats = {}

def saveStats():
    w = open('stats.pkl', 'w')
    pickle.dump( blackjackStats, w )
    w.close()


def speechHandler( text, sendername, senderid ):
    #if it wasn't a system message or something you said, and they're in range,
    if sendername not in ['System',''] and senderid != stealth.Self() and stealth.GetDistance(senderid) < 4:

        #Lets let it take at least half a second to respond!
        stealth.Wait( 500 )

        #We're going to update our timestamp so that it uses this as the last time the
        #bot has "responded" or been used.
        lastafkmessagetimestamp = time.time()

        #If it's one of our poker options:
        if text.lower() == 'hit':

            #Add them to the stats collection if they're not already there,
            if not senderid in blackjackStats:
                blackjackStats[senderid] = blackjackStatistics(senderid)

            #Start a new game if necessary,
            #(After checking if they have enough gold)
            if not blackjackStats[senderid].currentHand:

                #Check if they have enough money to play their wager amount,
                if blackjackStats[senderid].betamount > blackjackStats[senderid].earnings:
                    stealth.UOSayColor("You do not have enough gold to wager {:,}gp! Change your wager amount or add funds".format(blackjackStats[senderid].betamount),__msgcolor__)
                    return

                blackjackStats[senderid].currentHand = pokerGame(senderid)
                blackjackStats[senderid].currentHand.blackjackCheck()
            else:
                blackjackStats[senderid].currentHand.hit()

        elif text.lower() == 'stand':

            #Add them to the stats collection if they're not already there,
            if not senderid in blackjackStats:
                blackjackStats[senderid] = blackjackStatistics(senderid)

            if blackjackStats[senderid].currentHand:
                blackjackStats[senderid].currentHand.stand()

            #Tell them they need to say hit to start a new game
            else:
                stealth.UOSayColor("You must start a game first by saying 'hit' before standing!",__msgcolor__)

        elif text.lower() == 'hand':

            #Add them to the stats collection if they're not already there,
            if not senderid in blackjackStats:
                blackjackStats[senderid] = blackjackStatistics(senderid)
            if blackjackStats[senderid].currentHand:
                blackjackStats[senderid].currentHand.hand()
            else:
                stealth.UOSay("You need to play to have a hand!")

        elif text.lower() == 'help':
            stealth.UOSayColor("Available commands: hit, stand, hand, bet, rules, earnings, scores, about, and help",__msgcolor__)

        elif text.lower() == 'rules':
            stealth.UOSayColor("The payout is 5:6, dealer stands on soft 17, and there are {} decks!".format(__decks__),__msgcolor__)

        elif text.lower() == 'about':
            stealth.UOSayColor("I am Blackjack v{} by Vlek! I am a player-made goldsink written in UOSteam!".format(__version__),__msgcolor__)

        elif text.lower() == 'scores':
            if senderid in blackjackStats:
                #Wins: 38 (45.2%); Losses: 46 (54.8%); Blackjacks: 3; Total: 84 (+10 ties)
                totalPlays = float(blackjackStats[senderid].wins+blackjackStats[senderid].losses+blackjackStats[senderid].ties)
                stealth.UOSayColor("{} - Wins: {} ({:.1f}%), Losses: {} ({:.1f}%), Ties: {} ({:.1f}%)".format(stealth.GetName(senderid).title(),
                                                                                                      blackjackStats[senderid].wins,
                                                                                                      blackjackStats[senderid].wins/totalPlays*100,
                                                                                                      blackjackStats[senderid].losses,
                                                                                                      blackjackStats[senderid].losses/totalPlays*100,
                                                                                                      blackjackStats[senderid].ties,
                                                                                                      blackjackStats[senderid].ties/totalPlays*100),__msgcolor__)
            else:
                stealth.UOSayColor("You must play first to have scores!",__msgcolor__)

        elif text.lower() == 'bet':
            if not senderid in blackjackStats:
                blackjackStats[senderid] = blackjackStatistics(senderid)
            stealth.UOSayColor("Your current wager amount is {:,}gp per hand.".format(blackjackStats[senderid].betamount),__msgcolor__)

        #If it looks like it could be a wage change
        elif 'bet' in text.lower() and text.lower().index('bet') == 0:
            possibleBet = text.lower().split(' ')
            if len(possibleBet) == 2 and possibleBet[1].isalnum():

                if not senderid in blackjackStats:
                    blackjackStats[senderid] = blackjackStatistics(senderid)

                #Disallow changing bet when the player has a hand,
                if blackjackStats[senderid].currentHand:
                    stealth.UOSayColor("Sorry, no changing bets during a hand",__msgcolor__)
                    return

                if int(possibleBet[1]) > __maxbet__:
                    stealth.UOSayColor("I'm sorry, I do not allow betting over {}gp per hand!".format(__maxbet__),__msgcolor__)
                    return

                #The player can return their betting to zero for free gameplay,
                #but that doesn't mean there's not a minimum amount of gold per hand.
                if int(possibleBet[1]) != 0 and int(possibleBet[1]) < __minbet__:
                    stealth.UOSayColor("I'm sorry, I do not allow betting under {}gp per hand!".format(__minbet__),__msgcolor__)
                    return

                blackjackStats[senderid].betamount = int(possibleBet[1])
                stealth.UOSayColor("You've changed your wager amount to {:,}gp per hand".format(blackjackStats[senderid].betamount),__msgcolor__)
            else:
                stealth.UOSayColor('''To change your amount wagered, say "bet (amount)"''',__msgcolor__)

        elif text.lower() == 'earnings':
            if not senderid in blackjackStats:
                blackjackStats[senderid] = blackjackStatistics(senderid)
            stealth.UOSayColor('Your current balance is {:,}gp!'.format(int(blackjackStats[senderid].earnings)),__msgcolor__)

        elif text.lower() == '*aaahh!*':
            stealth.UOSayColor('[e scream',__msgcolor__)

        elif text.lower() == '*farts*':
            stealth.UOSayColor(random.choice(['[e giggle','[e sniff','[e puke','[e fart','[e groan']), __msgcolor__)

        #Owner commands
        elif senderid in [0xebe9e]: #Orlok

            if 'earnings' in text.lower() and text.lower().index('earnings') == 0:
                if not senderid in blackjackStats:
                    blackjackStats[senderid] = blackjackStatistics(senderid)

                possibleEarnings = text.lower().split(' ')

                if len(possibleEarnings) == 2 and possibleEarnings[1].isalnum():
                    blackjackStats[senderid].earnings = int(possibleEarnings[1])
                    stealth.UOSayColor('Your total earnings amount is now {:,}gp.'.format(int(possibleEarnings[1])),__msgcolor__)

def combatHandler( enemyid, attack_ok ):
    if attack_ok:
        #print("We're being attacked by {}!".format( stealth.GetName(enemyid) ))
        stealth.UOSayColor('Guards! Guards!',__msgcolor__)
        stealth.Beep()


stealth.SetEventProc( 'evUnicodeSpeech', speechHandler )
stealth.SetEventProc( 'evAllow_RefuseAttack', combatHandler )

acceptedTrade = False
lastafkmessagetimestamp = time.time()

#If we have any problems, we need to pickle our scores out!
try:
    #This is going to be as event-based as possible.
    #Which means very little if anything happens in the loop.
    #Main Loop
    while True:

        #Since there is no event for trade windows,
        #We're going to have to deal with them within the loop
        try:
            while stealth.IsTrade():
                if not acceptedTrade:
                    stealth.UOSayColor('All gold given to me goes toward your betting pile!',__msgcolor__)
                    acceptedTrade = True
                    tradeTimestamp = time.time()

                #If they've accepted the trade and we haven't,
                if stealth.TradeCheck(0,2) and not stealth.TradeCheck(0,1):
                    stealth.ConfirmTrade(0)

                stealth.Wait(500)

                #if it's been longer than 15 seconds,
                if time.time() - tradeTimestamp > 15:
                    stealth.UseSkill('hiding')
                    stealth.Wait(750)
                    stealth.UOSayColor('Sorry, you took too long to accept the trade!',__msgcolor__)
                    acceptedTrade = False
        finally:
            acceptedTrade = False

        stealth.Wait(500)

        #We don't want to always respond exact after a minute. Should be some randomness in there.
        if time.time() - lastafkmessagetimestamp > 60 and random.random() > 0.50:
            stealth.UOSayColor(random.choice(['[e sigh','[e yawn','[e groan','*Shuffles Cards*',
                                              '[e meow','[e howl','Wun plei blackjack?','*Grins',
                                              '[e fart','[e giggle']),__msgcolor__)
            lastafkmessagetimestamp = time.time()

except:
    pass
#Saving statistics whether we close cleanly or not!
finally:
    stealth.AddToSystemJournal('Saving Blackjack statistics and earnings')
    saveStats()
