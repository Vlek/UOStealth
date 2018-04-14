# Tailoring trainer by Vlek

# Unfortunately, this gets a little screwy around edge cases because Stealth is not able to see
# the "real" values of skills and instead opts for giving the player the modified version that
# considers one's stat attributes. This can cause it to hang in the few points between certain
# choices. Watch this script because it could potentially be making things that the player cannot
# actually gain skill making!

import stealth

stealth.SetFindDistance(2)

#cutlist contains a list of items that're made during
#the process of gaining skill. It is used to inform the
#search for items that could be cut up with scissors
#to lessen the character's weight and gain back some resources
cutlist = ['0x152e', #Short Pants
           '0x1516', #Skirt
           '0x1f00', #Fancy Dress
           '0x1515', #Cloak
           '0x1f03', #Robe
           '0x175d', #Oil Cloth (This unfortunately only produces bandages)
           '0x13d6', #Studded Gorget
           '0x1c0c', #Studded Bustier
           '0x1c02', #Studded Armor
           '0x13da', #Studded Legs
           '0x13db'] #Studded Tunics
#0x1452 Bonelegs (You can make them, but you can't cut them!


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


def Print(stuff):
    """Prints stuff to stealth system journal, whatever it is."""
    stealth.AddToSystemJournal(str(stuff))


def waitOnWorldSave():
    if inJournal('The world will save in 10 seconds.') and not inJournal('World save complete.'):
        #Print('Waiting out world save!')

        while inJournal('The world will save in 10 seconds.') and not inJournal('World save complete.'):
            stealth.Wait(1000)
    stealth.Wait(1000)


def gumpexists( gumpid ):
    """Looks through all gumpindexes for the specified gumpid, returns bool"""
    for index in range( stealth.GetGumpsCount() ):
        if stealth.GetGumpID( index ) == gumpid:
            return True
    return False


def replygump( gumpid, button ):
    """replies to a certain gumpid with the desired button. returns True on success"""
    #I could probably do a waitgump here if it's the case it doesn't find it.
    #Would have to see if that'd be annoying or not.
    for index in range( stealth.GetGumpsCount() ):
        if stealth.GetGumpID( index ) == gumpid:
            stealth.NumGumpButton( index, button )
            return True
    return False


def waitOnWorldSave():
    if inJournal('The world will save in 10 seconds.') and not inJournal('World save complete.'):
        Print('Waiting out world save!')

        while inJournal('The world will save in 10 seconds.') and not inJournal('World save complete.'):
            stealth.Wait(1000)
    stealth.Wait(1000)

def cuttingForResources():
    for cuttable in findTypes( cutlist, ['0xFFFF'], stealth.Backpack() ):

        #Use a pair of scissors on anything you've found,
        #I don't know if this also checks the ground...
        scissors = findTypes('0x0F9F','0x0',resourceContainer)
        if scissors:
            stealth.UseObject(scissors[0])
            stealth.WaitForTarget(5000)
            stealth.TargetToObject(cuttable)
            stealth.Wait(750)
        else:
            Print('Someone stole the scissors, mayne. Gotta put some more in the resource container!')
            stealth.exit()


def calcbonus( skill, strength, dexterity, intelligence ):
    """Because stupid stealth can't give you a 'shown skill' score,
    this calculates it down to like .02% accuracy for tailoring"""
    strength = 100.0 if strength > 100 else float(strength)
    dexterity = 100.0 if dexterity > 100 else float(dexterity)
    intelligence = 100.0 if intelligence > 100 else float(intelligence)
    skill = 100.0 if skill > 100 else float(skill)
    shownskill = skill
    #Figure out how much skill is going to affect our bonus:
    skilloffset = 1 - ( float(skill) / 100 )
    #print skilloffset
    #Add strength's part:
    shownskill += skilloffset * ( float( strength ) / 100 ) * 3.7
    #print shownskill
    #Add dexterity's part:
    shownskill += skilloffset * ( float( dexterity ) / 100 ) * 16.28
    #print shownskill
    #Add intelligence's part:
    shownskill += skilloffset * ( float( intelligence ) / 100 ) * 5
    return shownskill

def Mounted(ObjectID=stealth.Self()):
    return stealth.ObjAtLayerEx(stealth.HorseLayer(), ObjectID)


def waitforgump( gumpid, milliseconds ):
    while milliseconds:
        if gumpexists( gumpid ):
            return True
        waitTime = 100 if milliseconds >= 100 else milliseconds
        stealth.Wait( waitTime )
    return False


if stealth.GetSkillValue('Tailoring') < 99.6:
    #Initiating resource as being cloth
    #Might want to add un-cut cloth for some weirdo
    #That's doing this in a tailor shop by buying expensive ass uncut
    resource = '0x1766' #cut cloth
else:
    #We're only checking cut leather. We can check hides, too.
    #Just seems stupid to considering the player can only hold like four anyway.
    resource = '0x1081'

#This variable allows us to keep track of which "page" we're on in
#The crafting menu. That way we know when this needs changing
#Or if we can simply hit the button to craft that item or "make last"
makelast = ''

#We need to make sure we're kept as out of sight as possible. Hide if not hidden!
if not stealth.Hidden():
    stealth.UseSkill("Hiding")
    stealth.Wait(500)

if Mounted():
    stealth.UseObject( stealth.Self() )
    stealth.Wait( 1000 )

stealth.UseObject( stealth.Self() )
stealth.Wait( 1000 )

#This allows those characters that've never really been logged in before
#In stealth to get their backpacks open so it can "see" what goodies we have.
stealth.UseObject( stealth.Backpack() )
stealth.Wait(1000)

#While it's the case we're not GM tailoring,
Print('Starting Tailoring Gainer on {}!'.format(stealth.CharName()))
while stealth.GetSkillValue('Tailoring') < 100 and not stealth.Dead():

    waitOnWorldSave()
    
    #If the tailoring gump is open,
    if gumpexists(0x38920abd):

        currentSkill = calcbonus( stealth.GetSkillValue('Tailoring'), stealth.Str(), stealth.Dex(), stealth.Int() )
        
        #If we either don't have resources or are overweight,
        if countTypes(resource,['0x0'],[stealth.Backpack()]) < 20:
            if resource == '0x1766':
                Print('Out of cloth! :(')
            else:
                Print('Out of leather! :(')
            stealth.exit()
                
        #Short pants
        elif currentSkill < 49.7:
            if makelast != 'short pants':
                replygump(0x38920abd, 15)
                waitforgump(0x38920abd, 5000)
                replygump(0x38920abd, 2)
                makelast = 'short pants'
            else:
                replygump(0x38920abd, 21)

        #Skirt
        elif currentSkill < 54:
            if makelast != 'skirt':
                replygump(0x38920abd, 15)
                waitforgump(0x38920abd, 5000)
                replygump(0x38920abd, 23)
                makelast = 'skirt'
            else:
                replygump(0x38920abd, 21)

        #Fancy Dress
        elif currentSkill < 58:
            if makelast != 'fancy dress':
                replygump(0x38920abd, 8)
                waitforgump(0x38920abd, 5000)
                replygump(0x38920abd, 44)
                makelast = 'fancy dress'
            else:
                replygump(0x38920abd, 21)

        #Cloak
        elif currentSkill < 66.3:
            if makelast != 'cloak':
                replygump(0x38920abd, 8)
                waitforgump(0x38920abd, 5000)
                replygump(0x38920abd, 51)
                makelast = 'cloak'
            else:
                replygump(0x38920abd, 21)

        #Robe
        elif currentSkill < 74.6:
            if makelast != 'robe':
                replygump(0x38920abd, 8)
                waitforgump(0x38920abd, 5000)
                replygump(0x38920abd, 58)
                makelast = 'robe'
            else:
                replygump(0x38920abd, 21)

        #Oil Cloth
        elif currentSkill < 99.5:
            if makelast != 'oil cloth':
                replygump(0x38920abd, 22)
                waitforgump(0x38920abd, 5000)
                replygump(0x38920abd, 23)
                makelast = 'oil cloth'
            else:
                replygump(0x38920abd, 21)

        #Studded Gorget
        elif currentSkill < 103.7:
            if makelast != 'studded gorget':
                resource = '0x1081'
                replygump(0x38920abd, 43)
                waitforgump(0x38920abd, 5000)
                replygump(0x38920abd, 2)
                makelast = 'studded gorget'
            else:
                replygump(0x38920abd, 21)

        #Studded Bustier
        elif currentSkill < 107.8:
            if makelast != 'studded bustier':
                replygump(0x38920abd, 50)
                waitforgump(0x38920abd, 5000)
                replygump(0x38920abd, 23)
                makelast = 'studded bustier'
            else:
                replygump(0x38920abd, 21)

        #Studded Armor
        elif currentSkill < 112:
            if makelast != 'studded armor':
                replygump(0x38920abd, 50)
                waitforgump(0x38920abd, 5000)
                replygump(0x38920abd, 37)
                makelast = 'studded armor'
            else:
                replygump(0x38920abd, 21)

        #Studded Leggings
        elif currentSkill < 116.2:
            if makelast != 'studded leggings':
                replygump(0x38920abd, 43)
                waitforgump(0x38920abd, 5000)
                replygump(0x38920abd, 23)
                makelast = 'studded leggings'
            else:
                replygump(0x38920abd, 21)

        #Studded Tunic (You can do bone legs, but bones suck)
        else:
            if makelast != 'studded tunic':
                replygump(0x38920abd, 43)
                waitforgump(0x38920abd, 5000)
                replygump(0x38920abd, 30)
                makelast = 'studded tunic'
            else:
                replygump(0x38920abd, 21)

    #if we don't see the gump, we need to click a tailoring kit or make one
    else:
        sewingkits = findTypes('0xf9d','0x0',[stealth.Backpack()])

        if sewingkits:
            stealth.UseObject( sewingkits[0] )
        else:
            tinkerkits = findTypes(['0x1EB8'],['0x0'],[stealth.Backpack()])

            #If we don't have enough ingots,
            while countTypes('0x1BF2','0x0',[stealth.Backpack()]) < 2:
                Print('Out of Ingots! :(')
                stealth.exit()
            
            #If we have at least one tinkerkit:
            if tinkerkits:
                #Use that tinker kit to get the gump goin'
                stealth.UseObject(tinkerkits[0])
                stealth.WaitGump('8')
                #I don't know if this is technically needed, but I'm erring on the side of caution
                stealth.Wait(250)
                #If we have at least two,
                if len( tinkerkits ) >= 2:
                    #Make a sewing kit
                    stealth.WaitGump('44')
                #If we only have one,
                else:
                    #Make another tinker kit
                    stealth.WaitGump('23')
                stealth.WaitGump('0')
            else:
                Print("Didn't have enough tinkering tools")
                stealth.exit()
        stealth.Wait(1000)
    stealth.Wait(750)
