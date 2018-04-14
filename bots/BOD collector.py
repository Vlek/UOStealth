# AutoBOD by Vlek

import stealth, time, smtplib, re

"""
This script will load every blacksmith that is set as its own profile and added to the profiles
list, run to the blacksmithy a screen away, get a BOD, and walk back to the inn to log out.
Once it is done handling every profile, it will then email a list of all of the different
BODs that it had collected. If left running, this script will wait four hours and attempt
to gather the BOD's again.

The vendor's serials will also have to be set for this to work!

For the emailing to work, the email from (with password) and to need to be set as well.
I find that mail.com has lax rules regarding third party apps logging into their accounts, so
that's what I had been using to do this.
"""

__author__ = "Vlek"
__version__ = "0.4.0"

# Put your own profiles:
profiles = []

# Add the list of Blacksmith vendor serials that you can get a BOD from here:
vendors = []

# And don't forget these if you want an email about it!
email_from = ''
email_from_password = ''
email_to = ''

# Although these aren't perfect, it's much better than having them off.
stealth.SetMoveOpenDoor(True)
stealth.SetMoveThroughNPC(True)

waypoints = [(564,2179), #Inside the inn
             (566,2179), #One tile inside the inn (near right-side door)
             (568,2179), #One tile outside the inn (near right-side door)
             (575,2179), #Pivot point at lightpost
             (582,2172), #Wall of blacksmiths
             (582,2167)] #Middle of blacksmiths at outter wall

stealth.MoveOpenDoor = True

def ReplyGump( gumpNum, buttonRef ):
    """Replies to a gump by index number to a button by index given"""
    buttons = []
    for line in stealth.GetGumpFullLines( gumpNum ):
        if 'GumpButton' in line:
            buttons.append( line )
    buttons = buttons[1:] #remove buttons header
    stealth.NumGumpButton( gumpNum, int(buttons[buttonRef].split()[-3]) )

class bod:
    smithItems = ['ringmail gloves', 'ringmail leggings', 'ringmail sleeves', 'ringmail tunic',
                  'chainmail coif', 'chainmail leggings', 'chainmail tunic', 'platemail arms',
                  'platemail gloves', 'platemail gorget', 'platemail legs', 'platemail tunic',
                  'plate helm', 'bardiche', 'halberd', 'dagger', 'short spear', 'war fork',
                  'kryss', 'war axe', 'hammer pick', 'mace', 'maul', 'war hammer', 'war mace',
                  'axe', 'battle axe', 'double axe', "executioner's axe", 'large battle axe',
                  'two handed axe', 'war axe', 'broadsword', 'cutlass', 'katana', 'longsword',
                  'scimitar', 'viking sword', 'double axe', 'female plate', 'bascinet',
                  'close helmet', 'helmet', 'norse helm', 'buckler', 'bronze shield',
                  'heater shield', 'metal shield', 'metal kite shield', 'tear kite shield',
                  'spear']

    def __init__(self, gumpinfo):
        bodlisted = []
        midResult = []
        for i in gumpinfo:
            if i != '':
                midResult.append( i )
            else:
                bodlisted.append( midResult )
                midResult = []

        for i in bodlisted:
            if 'Text Lines:' in i:
                self.amount = i[1]

            if 'XmfHTMLGumpColor: X   Y   Width   Height   ClilocID   Background   scrollbar   Hue   ElemNum   ClilocText' in i:
                #Within the section of the bod where it has all of the bod stipluations and also says what to make,
                bodstips = [' '.join(r.split()[11:]) for r in i] #Get just the clilocText info from the elements
                items = []
                for item in bodstips: #This is directly after 'Item(s) requested:'
                    if item in bod.smithItems:
                        items.append( item )
                self.items = items

                colored = False
                for stip in bodstips:
                    if 'All items must be made with' in stip:
                        self.resource =  re.search('^All items must be made with (.*) ingots\.$', stip).group(1)
                        colored = True
                        break

                if not colored:
                    self.resource = 'iron'

                if 'All items must be exceptional.' in bodstips:
                    self.quality = 'exceptional'
                else:
                    self.quality = 'regular'

while True:
    acceptedBods = []
    rejectedBods = []
    timestamp = time.time()
    nextBODRun = timestamp + 10865 #start time plus three hours and one minute in seconds
    for character in profiles:
        stealth.ChangeProfile( character )
        stealth.Wait( 3000 ) #This is to ensure the last character is able to completely log out.
        stealth.Connect()
        stealth.Wait(250)

        # Walk to the blacksmiths
        for waypoint in waypoints[1:]:
            stealth.NewMoveXY( waypoint[0], waypoint[1], 0, 0, True )

        # Check blacksmiths for one close enough that you can request a BOD from
        for vendor in vendors:
            vendorID = int( vendor, 16 )

            stealth.RequestContextMenu( vendorID )
            stealth.Wait(1500)
            
            menu = stealth.GetContextMenu()

            try:
                if 'Bulk Order Info' in menu[1]:
                    stealth.SetContextMenuHook( vendorID, 0x1 )
                    break
            except:
                stealth.AddToSystemJournal('Something screwy happened with context menu')

        # After requesting a bod, check for BOD gump
        gotBod = False
        totalWait = 5000
        while not gotBod and totalWait >= 0:
            if stealth.GetGumpsCount():
                for gumpNum in range( stealth.GetGumpsCount() ):
                    if stealth.GetGumpID( gumpNum ) in [2611865322, 3188567326L]: #BOD Gump ID's (Small and large)
                        gotBod = True
                        currentBod = bod( stealth.GetGumpFullLines( gumpNum ) )
                        currentBodStr = '{} received BOD: {} {} {} {}'.format(stealth.CharName(), currentBod.items, currentBod.amount, currentBod.quality, currentBod.resource)
                        stealth.AddToSystemJournal( currentBodStr )
                        if currentBod.resource != 'iron':
                            stealth.AddToSystemJournal('Accepting {} BOD!'.format(currentBod.resource))
                            acceptedBods.append( currentBodStr )
                            ReplyGump( gumpNum, 0 )
                        else: #If it's the case that there was a BOD, but it's iron.
                            ReplyGump( gumpNum, 1 )
                            rejectedBods.append( currentBodStr )
                            stealth.AddToSystemJournal('Trash (Iron) BOD!')
            stealth.Wait(250)
            totalWait -= 250
        if not gotBod:
            stealth.AddToSystemJournal("Didn't get served BOD gump. :(")

        # Walk back to the inn
        for waypoint in reversed(waypoints):
            stealth.NewMoveXY( waypoint[0], waypoint[1], 0, 0, True )

        stealth.Disconnect()

    if acceptedBods or rejectedBods: #If it's the case you got a BOD, then send an email about it.
        user = email_from
        toaddrs = [email_to]
        subject = "BOD Run: {} Accepted, {} Rejected".format( len(acceptedBods), len(rejectedBods) )
        text = "Bulk Order Deeds Per Character:\n\n" + 'Accepted Bods:\n' + '\n'.join(acceptedBods) + '\n\nRejected Bods:\n' + '\n'.join(rejectedBods) + '\n\nNext BOD run on {}'.format(time.strftime("%b %d at %H:%M:%S",time.localtime( nextBODRun )))
        message = """From: %s\nTo: %s\nSubject: %s\n\n%s""" % (user, ", ".join(toaddrs), subject, text)
        try:
            server = smtplib.SMTP_SSL('smtp.mail.com',465)
            server.ehlo()
            server.login( user, email_from_password )
            server.sendmail( user, toaddrs, message )
            server.close()
            stealth.AddToSystemJournal('Email sent!')
        except:
            stealth.AddToSystemJournal('Error: unable to send email')

    time.sleep( 10500 ) # Wait 5 minutes shy of 3 hours,

    for i in range( 5 ): # Do da dings!
        stealth.Beep()
        time.sleep( 1 )

    time.sleep( 365 ) # Wait the extra 5 minutes...
