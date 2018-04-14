import stealth, re

# TODO: Create a dictionary of mobile id's to save player information to
#   Only send an API request to the node webserver if it has been a
#   considerable (more than five minutes) since that person was last seen

# TODO: Figure out some way of capturing guild information. If it's not
#   given with CharName (probs not)
#   I mean, it's really not normal for someone to type with brackets
#   and also have a comma inbetween. In fact, I highly doubt anyone
#   will ever do it.


# TODO: Figure out the issue with the script randomly not working after a while

def speechHandler( text, sendername, senderid ):
    # TODO: Fix this so that it's able to handle unicode
    #   Before, it couldn't handle spaces and stuff. Not good.
    if senderid != stealth.Self() and sendername not in ['System','']:
        stealth.AddToSystemJournal( u'{}: {}'.format( sendername, text ) )

        
stealth.SetEventProc( 'evSpeech', speechHandler )

print('Listening to ingame speech')
while True:
    stealth.Wait( 100 )
