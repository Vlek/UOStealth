#Autominer by Vlek

import stealth, math, time, re

# This unfortunately does not work as intended due to an error in the Stealth client that causes threading
# issues with Python. After a few runs, it will start doing things in weird orders and eventually fail!

"""Todo list:

- Fix the ore sluffer dropping larger piles when a smaller one of the same ore color would do
    - It's the difference between dropping a small (2 stones, one half ingot) versus a large (12 stones, 2 ingots)

- Figure out pervasive stealth crashing bug. May be due to weird cases with picking up or sluffing ore.

"""

__author__ = 'Vlek'

bookHome = 0x40c3e682
miningBooks = [0x41657AD5, 0x41650D7E, 0x41650D75]


def speechHandler( text, sendername, senderid ):
    if senderid != stealth.Self() and sendername not in ['System','']:
        stealth.AddToSystemJournal( '{}: {}'.format( sendername, re.sub( r'[^\x00-\x7f]', r'?', text ) ) )
        stealth.Beep()

stealth.SetEventProc( 'evUnicodeSpeech', speechHandler )

miningErrorMessages = ['no metal here',
                       'The world will save in 10 seconds.',
                       'Target cannot be seen']

oretypes = ['0x19b9',  # large
            '0x19ba',  # medium
            '0x19b8',  # medium2
            '0x19b7']  # small

orecolors = ['0x0',  # Iron
             '0x973',  # Dull Copper
             '0x966',  # Shadow Iron
             '0x96D',  # Copper
             '0x972',  # Bronze
             '0x8A5',  # Golden
             '0x979',  # Agapite
             '0x89F',  # Verite
             '0x8AB']  # Valorite

recallReagents = ['0xf86',  # Mandrake Root
                  '0xf7b',  # Bloodmoss
                  '0xf7a']  # Blackpearl

pileWeights = {'0x19b9': 12,  # large
               '0x19ba': 7,  # medium
               '0x19b8': 7,  # medium2
               '0x19b7': 2}  # small

runebookslots = [5, 11, 17, 23, 29, 35, 41, 47,
                 53, 59, 65, 71, 77, 83, 89, 95]

scaryNotorieties = [3,  # Attackable (Gray)
                    4,  # Criminal   (Gray)
                    5,  # Enemy      (Orange)
                    6]  # Murderer   (Red)

humanGraphics = [0x0190,  # Male
                 0x0191,  # Female
                 0x00B7]  # Savage Male

def inJournal(text):
    """Returns whether the supplied text is ANYWHERE in the journal"""
    for line in [stealth.Journal(i) for i in range(0, stealth.HighJournal() + 1)]:
        if text.lower() in line.lower():
            return True
    return False


def findTypes(types, colors, containers, subcontainerSearch=False):
    """searches the list of containers for the item types of the specified colors"""
    if type(types) != list:
        types = [types]
    if type(colors) != list:
        colors = [colors]
    if type(containers) != list:
        containers = [containers]
    stealth.FindTypesArrayEx(types, colors, containers, subcontainerSearch)
    return stealth.GetFindedList()


def countTypes(types, colors, containers, subcontainerSearch=False):
    """Returns the total amount of the given items of the specified colors in containers"""
    if type(types) != list:
        types = [types]
    if type(colors) != list:
        colors = [colors]
    if type(containers) != list:
        containers = [containers]
    stealth.FindTypesArrayEx(types, colors, containers, subcontainerSearch)
    return stealth.FindFullQuantity()


def Bank():
    """returns the serial of one's bankbox"""
    return stealth.ObjAtLayer(stealth.BankLayer())


def Mounted(ObjectID=stealth.Self()):
    return stealth.ObjAtLayerEx(stealth.HorseLayer(), ObjectID)


def Print(stuff):
    """Prints stuff to stealth system journal, whatever it is."""
    stealth.AddToSystemJournal(str(stuff))


def waitOnWorldSave():
    if inJournal('The world will save in 10 seconds.') and not inJournal('World save complete.'):
        #Print('Waiting out world save!')

        while inJournal('The world will save in 10 seconds.') and not inJournal('World save complete.'):
            stealth.Wait(1000)
    stealth.Wait(1000)


def combineOre(combineAll = True):
    """Combines down either to where the player is under weight or until all are combined as specified by combineAll"""
    # Try to put piles together again
    findDistance = stealth.GetFindDistance()
    stealth.SetFindDistance(2)
    for color in orecolors:

        # if have a small pile of the current color,
        if stealth.FindTypesArrayEx(['0x19b7'], [color], [stealth.Backpack()], False):
            smallPile = stealth.GetFindedList()[0]

            # If you find any larger pile of the ore color,
            if stealth.FindTypesArrayEx(['0x19b9', '0x19ba', '0x19b8'],
                                        [color], [stealth.Backpack()], False):
                largePiles = stealth.GetFindedList()

                # Combine each larger pile with the small pile
                for pile in largePiles:
                    stealth.UseObject(pile)
                    stealth.WaitForTarget(5000)
                    stealth.TargetToObject(smallPile)
                    stealth.Wait(750)

                    # If we can recall after that last combination, break out
                    if not combineAll and stealth.Weight() <= stealth.MaxWeight() + 4:
                        break

        # Else, if you find a small on the ground,
        elif stealth.FindTypesArrayEx(['0x19b7'], [color], [stealth.Ground()], False):
            smallPile = stealth.GetFindedList()[0]

            # If you find any larger pile of the ore color,
            if stealth.FindTypesArrayEx(['0x19b9', '0x19ba', '0x19b8'],
                                        [color], [stealth.Backpack()], False):
                largePiles = stealth.GetFindedList()
                # First, gotta get the small off the ground
                stealth.UseObject(smallPile)
                stealth.WaitForTarget(5000)
                stealth.TargetToObject(largePiles[0])
                stealth.Wait(750)

                # If we can recall after that last combination, break out
                if not combineAll and stealth.Weight() <= stealth.MaxWeight() + 4:
                    break

                # The first large is now small. Target everything on it.
                for pile in largePiles[1:]:
                    stealth.UseObject(pile)
                    stealth.WaitForTarget(5000)
                    stealth.TargetToObject(largePiles[0])
                    stealth.Wait(750)

                    # If we can recall after that last combination, break out
                    if stealth.Weight() <= stealth.MaxWeight() + 4:
                        break
    stealth.SetFindDistance(findDistance)


def sluffOre():
    """Remove the least amount of ore necessary to get out"""
    if stealth.Weight() > stealth.MaxWeight() + 4:
        for color in orecolors:
            for oretype in oretypes:
                if stealth.FindTypesArrayEx([oretype], [color], [stealth.Backpack()], False):

                    # If it's a large pile,
                    if oretype == '0x19b9':
                        weightPerPile = 12

                    # One of the medium piles,
                    elif oretype in ['0x19ba', '0x19b8']:
                        weightPerPile = 7

                    # Else, it's a small
                    else:
                        weightPerPile = 2

                    # Calculate how much you'd have to remove in order to get to a recallable amount
                    sluffAmount = int(
                        math.ceil((stealth.Weight() - (stealth.MaxWeight() + 4)) / float(weightPerPile)))

                    # Remove as much as needed, up to the whole pile, to get under weight
                    for pile in stealth.GetFindedList():

                        pileQuantity = stealth.GetQuantity(pile)

                        # If the current pile isn't enough,
                        if pileQuantity < sluffAmount:
                            stealth.MoveItem(pile, pileQuantity, stealth.Ground(),
                                             stealth.GetX(stealth.Self()),
                                             stealth.GetY(stealth.Self()), stealth.GetZ(stealth.Self()))
                            sluffAmount -= pileQuantity
                            stealth.Wait(750)

                        # Otherwise, you have enough to take care of your plite
                        else:
                            stealth.MoveItem(pile, sluffAmount, stealth.Ground(),
                                             stealth.GetX(stealth.Self()),
                                             stealth.GetY(stealth.Self()), stealth.GetZ(stealth.Self()))
                            stealth.Wait(750)
                            break

                if stealth.Weight() <= stealth.MaxWeight() + 4:
                    break

            if stealth.Weight() <= stealth.MaxWeight() + 4:
                break

def pickupOre():
    """Picks up as much ore off the ground within a reachable distance as possible"""
    findDistance = stealth.GetFindDistance()
    stealth.SetFindDistance(2)
    if stealth.Weight() < stealth.MaxWeight() + 4:
        #Gotta pick up the good stuff first!
        for color in reversed(orecolors):
            if stealth.FindTypesArrayEx(['0x19b7', '0x19b9', '0x19ba', '0x19b8'], [color], [stealth.Ground()], False):
                groundPiles = stealth.GetFindedList()

                #It might make sense to first sort them by their types in order to best respond to them.

                for pile in groundPiles:
                    freeSpace = (stealth.MaxWeight() + 4) - stealth.Weight()

                    pileType = hex(stealth.GetType(pile))

                    # If it's not a small ore pile and you have a small pile of that color in your backpack,
                    if pileType != '0x19b7' and stealth.FindTypesArrayEx(['0x19b7'], [stealth.GetColor(pile)],
                                                                         [stealth.Backpack()], False):

                        smallPile = stealth.GetFindedList()[0]

                        pileQuantity = stealth.GetQuantity(pile)

                        # If it's the case that it's a large,
                        if pileType == '0x19b9':
                            # Get the new weight considering you get four small at two stones each
                            newWeight = pileQuantity * 4 * 2

                        # If it's one of the mediums,
                        else:
                            # Get the new weight for conversion to two small at two stones each
                            newWeight = pileQuantity * 2 * 2

                        if newWeight <= freeSpace:
                            stealth.UseObject(pile)
                            stealth.WaitForTarget(5000)
                            stealth.TargetToObject(smallPile)
                            stealth.Wait(750)

                    else:
                        # Lets check how much we can grab off the pile.
                        amountGrabbable = freeSpace / pileWeights[pileType]

                        # If we can pick up any,
                        if amountGrabbable > 0:

                            pileQuantity = stealth.GetQuantity(pile)

                            # If we can grab the entire thing,
                            if amountGrabbable >= pileQuantity:
                                stealth.MoveItem(pile, pileQuantity, stealth.Backpack(), 0, 0, 0)
                            else:
                                stealth.MoveItem(pile, amountGrabbable, stealth.Backpack(), 0, 0, 0)

                            stealth.Wait(750)
    stealth.SetFindDistance(findDistance)


try:
    stealth.AddToSystemJournal('Starting AutoMiner Script!')

    # If you're mounted, unmount
    if Mounted():
        stealth.UseObject(stealth.Self())
        stealth.Wait(750)

    # Main Loop
    while not stealth.Dead():

        #Used for sysjournal output
        currentbook = 0

        #Used for statistics keeping:
        runtimestamp = time.time()

        for runebook in miningBooks:

            #Used for sysjournal output
            currentbook += 1

            #Stats keeping:
            booktimestamp = time.time()

            for slot in runebookslots:

                try:
                    waitOnWorldSave()

                    stealth.UOSayColor('Bank', 54)
                    stealth.Wait(750)

                    # For each ore pile in your backpack,
                    for ore in findTypes(oretypes, orecolors, [stealth.Backpack()]):
                        # Move them to the bank
                        ### There should probably be a check or a while loop here to make sure it makes it into the bank
                        stealth.MoveItem(ore, stealth.GetQuantity(ore), stealth.ObjAtLayer(stealth.BankLayer()), 0, 0, 0)
                        stealth.Wait(750)

                    # While we don't have enough mana to go there and back, wait
                    while stealth.Mana() < 22:
                        stealth.Wait(250)
                        if not inJournal('enter a meditative trance'):
                            stealth.UseSkill('Meditation')
                            #Might want to check lag here to inform the pauses. (No lag: 750, lag: 750 + lagoffset)
                        stealth.Wait(1000)

                    # Pull reagents out of the bank as necessary
                    for reagent in recallReagents:
                        # If you have less than two of the current reagent,
                        while countTypes([reagent], ['0x0'], [stealth.Backpack()]) < 2:
                            # If you have at least two in your bank,
                            if countTypes([reagent], ['0x0'], [Bank()]) >= 2:
                                for reagentPile in findTypes([reagent], ['0x0'], [Bank()]):
                                    # if it's the case that the pile we're looking at has enough to cover our need,
                                    currentReagentPile = stealth.GetQuantity(reagentPile)
                                    if currentReagentPile >= 2:
                                        stealth.MoveItem(reagentPile, 2 - countTypes([reagent], ['0x0'], [stealth.Backpack()]), stealth.Backpack(), 0, 0, 0)
                                        break
                                    else:
                                        stealth.MoveItem(reagentPile, 1, stealth.Backpack(), 0, 0, 0)
                                    stealth.Wait(750)
                            # If we don't have enough reagents to continue,
                            else:
                                Print("Didn't have enough reagents to continue. Stopping.")
                                stealth.exit()

                            stealth.Wait(750)

                    # Pull iron ingots out of the bank where necessary
                    while countTypes(['0x1bf2'], ['0x0'], [stealth.Backpack()]) < 6:
                        ingotAmount = countTypes(['0x1bf2'], ['0x0'], [stealth.Backpack()])
                        # If you have at least two in your bank,
                        if countTypes(['0x1bf2'], ['0x0'], [Bank()]) >= 6:
                            for ingotPile in findTypes(['0x1bf2'], ['0x0'], [Bank()]):
                                # if it's the case that the pile we're looking at has enough to cover our need,
                                currentPileAmount = stealth.GetQuantity(ingotPile)
                                if currentPileAmount >= 6:
                                    stealth.MoveItem(ingotPile, 6 - countTypes(['0x1bf2'], ['0x0'], [stealth.Backpack()]), stealth.Backpack(), 0, 0, 0)
                                    break
                                else:
                                    stealth.MoveItem(ingotPile, currentPileAmount, stealth.Backpack(), 0, 0, 0)
                                    ingotAmount += currentPileAmount
                                stealth.Wait(750)

                        # If we don't have enough ingots to continue,
                        else:
                            Print("Didn't have enough ingots to continue. Stopping.")
                            stealth.exit()

                    waitOnWorldSave()

                except:
                    stealth.AddToSystemJournal('An issue occured while at the bank.')
                    stealth.Beep()

                try:

                    # This needs to check whether it's the case that the location is blocked!
                    stealth.Wait(1000)
                    stealth.UseObject(runebook)
                    stealth.WaitGump(str(slot))

                    stealth.Wait(2000)

                except:
                    stealth.AddToSystemJournal('An issue occured while recalling to mining location.')
                    stealth.Beep()

                try:
                    # Have to set the find distance to "Anything on screen" to detect reds quick enough
                    stealth.SetFindDistance(16)

                    # Check the tile directly north of the character (y - 1)
                    tile = stealth.ReadStaticsXY(stealth.GetX(stealth.Self()), stealth.GetY(stealth.Self()) - 1,
                                                 stealth.WorldNum())

                    if tile:
                        tile = int(tile[0].Tile)
                    else:
                        tile = 0

                    # Mine the ore!
                    stealth.ClearJournal()
                    while True:

                        # First, check whether there are any scary peeps around,
                        if True in [stealth.GetNotoriety(peep) in scaryNotorieties for peep in
                                    findTypes(humanGraphics, 0xFFFF, stealth.Ground())] or stealth.WarTargetID() != 0:
                            Print('Recalling out because of dangerous activity! Book: {}, rune: {}'.format(runebook,slot))
                            #maybe it's like toggling out of warmode in game where you have to go in and out?
                            stealth.SetWarMode(True)
                            stealth.Wait(50)
                            stealth.SetWarMode(False)
                            break

                        # If you find at least one pickaxe or shovel of regular color in your main backpack (no sub containers)
                        if stealth.FindTypesArrayEx(['0xe86', '0xf39'], [0], [stealth.Backpack()], False):
                            stealth.UseObject(stealth.GetFindedList()[0])
                            stealth.WaitForTarget(5000)

                            # Turns out, when you can't find the tile, it's tile of type 0. No Z issues yet.
                            stealth.TargetToTile(tile, stealth.GetX(stealth.Self()),
                                                 stealth.GetY(stealth.Self()) - 1,
                                                 stealth.GetZ(stealth.Self()))

                        # If you find at least one tinker toolkit of regular color in your backpack (no sub containers)
                        elif stealth.FindTypesArrayEx(['0x1eb8'], [0], [stealth.Backpack()], False):
                            toolkits = stealth.GetFindedList()

                            #There should be a check here for whether or not we have the ingots to make the stuff

                            stealth.UseObject(toolkits[0])
                            # This seems to be necessary, otherwise stealth jumps the gun.
                            stealth.Wait(250)

                            # If we have at least two tools,
                            if len(toolkits) > 1:
                                # Make a pickaxe
                                stealth.WaitGump('114')
                                stealth.Wait(250)
                                stealth.WaitGump('0')
                            else:
                                # Make a tinker's toolkit
                                stealth.WaitGump('23')

                            # We need to wait until it appears in our backpack before moving on.
                            stealth.Wait(1000)

                        # When it's the case that we don't have tools or tool kits to make them, stop mining
                        else:
                            stealth.AddToSystemJournal("Ran outta tools! :(")
                            break

                        # This wait helps ensure that the injournal messages will be visible to stealth.
                        stealth.Wait(750)

                        # Check whether any condition to stop has been met
                        if True in [inJournal(message) for message in miningErrorMessages]:
                            break

                        if inJournal("You can't mine "):
                            stealth.AddToSystemJournal('Unable to mine spot {} in book {}'.format(slot, runebook))
                            stealth.Beep()
                            break

                        if inJournal('Your backpack is full'):

                            # We have to reclear the journal so that it doesn't keep triggering this
                            # It has to be done ASAP to reduce chance of missing world save messages
                            stealth.ClearJournal()
                            combineOre()

                            # If it's the case that you're not able to even hold one more big ore
                            if stealth.Weight() > stealth.MaxWeight() - 12:
                                break

                except:
                    stealth.AddToSystemJournal('An issue occured while mining.')
                    stealth.Beep()


                try:
                    # We're no longer trying to find reds, we might look for ore within useable distance
                    stealth.SetFindDistance(2)

                    # If overweight, try combining again
                    # You can still recall with four more stones than one's max weight
                    if stealth.Weight() > stealth.MaxWeight() + 4:

                        # We're going to combine down just enough to get outta here
                        combineOre(False)

                except:
                    stealth.AddToSystemJournal('An issue occured while combining ore.')
                    stealth.Beep()

                try:
                    # After the initial combination, we should check whether we
                    # can get anything off the ground

                    # If we can carry more ore,
                    # Attempt to pickup ore from the ground
                    pickupOre()

                except:
                    stealth.AddToSystemJournal('An issue occured while picking up ore.')
                    stealth.Beep()

                try:
                    # If still overweight, go ahead and sluff some ore
                    # You can still recall with four more stones than one's max weight
                    sluffOre()
                except:
                    stealth.AddToSystemJournal('An issue occured while dropping ore.')
                    stealth.Beep()

                try:
                    # Useobject wait
                    stealth.Wait(1000)
                    beforeRecallX, beforeRecallY = stealth.GetX(stealth.Self()), stealth.GetY(stealth.Self())
                    stealth.CastToObj('Recall', bookHome)
                    lastRecallTimestamp = time.time()

                    #This ensures that the recalling gets done by nesting it until it gets done.
                    while stealth.GetX(stealth.Self()) == beforeRecallX and stealth.GetY(stealth.Self()) == beforeRecallY and not stealth.Dead():
                        if time.time() - lastRecallTimestamp > 3:
                            Print('Recall failed, trying again!')
                            stealth.CastToObj('Recall', bookHome)
                            lastRecallTimestamp = time.time()
                        stealth.Wait(250)

                    #I might need this. I'm checking whether the XYZ checker is good enough.
                    #Considering waitonworldsave does a one second wait already.
                    #stealth.Wait(2000)

                except:
                    stealth.AddToSystemJournal('An issue occured while going home.')
                    stealth.Beep()


            Print('Finished book #{} in {}!'.format(currentbook, time.strftime('%H:%M:%S', time.gmtime(time.time()-booktimestamp))))

        Print('Finished run in {}!'.format(time.strftime('%H:%M:%S', time.gmtime(time.time()-runtimestamp))))
except:
    stealth.AddToSystemJournal('There was an error at some point in the script!')
