# Stealth trainer using moongates by Vlek

import stealth, time

"""
This script will train one's stealth using moongates. What it does is teleport to
hide the player, attempts to use stealth, and then goes back to a safe place. It
will continue doing so until GM. It is also able to wait out saves so that they
do not muck up its teleporting.
"""

def wait( miliseconds ):
    """Performs the specified wait in miliseconds"""
    time.sleep( miliseconds * 0.001 )
    

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


def gumpexists( gumpid ):
    """Looks through all gumpindexes for the specified gumpid, returns bool"""
    for index in range( stealth.GetGumpsCount() ):
        if stealth.GetGumpID( index ) == gumpid:
            return True
    return False


def waitforgump( gumpid, milliseconds ):
    while milliseconds:
        if gumpexists( gumpid ):
            return True
        wait( 100 if milliseconds >= 100 else milliseconds )
    return False


def replygump( gumpid, replynum, option=False ):
    """reponds to the first gump with the gumpid it finds with the replynum"""
    for index in range( stealth.GetGumpsCount() ):
        if stealth.GetGumpID( index ) == gumpid:
            if option:
                stealth.NumGumpChestBox( index, 
            stealth.NumGumpButton( index, replynum )
            return True
    return False


def Bank():
    """returns the serial of one's bankbox"""
    return stealth.ObjAtLayer(stealth.BankLayer())


def Print(stuff):
    """Prints stuff to stealth system journal, whatever it is."""
    stealth.AddToSystemJournal(str(stuff))


def waitOnWorldSave():
    while inJournal('The world will save in 10 seconds.') and not inJournal('World save complete.'):
        wait(1000)
    wait(1000)

print('Starting stealth gaining script')

stealth.SetFindDistance(1)

while stealth.GetSkillValue('Stealth') < 100:
    stealth.UseObject(findTypes([0x0F6C],['0xFFFF'],[stealth.Ground()])[0])
    waitforgump(0xe0e675b8,15000)
    replygump(0xe0e675b8,5)
    stealth.UseSkill('Stealth')
    time.sleep(1)
    stealth.UseObject(findTypes([0x0F6C],['0xFFFF'],[stealth.Ground()])[0])
    waitforgump(0xe0e675b8,15000)
    replygump(0xe0e675b8,10)
    time.sleep(12)
    waitOnWorldSave()
