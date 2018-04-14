import stealth, random, cleverbot, re

"""
This is probably one of the things I am most proud of. It's a silly little thing that waits
for someone to say something within three tiles of the bot. It then pipes that text into
cleverbot, and the response is said by the bot.

I found it humorous to put two of these things next to each other and then having one
break the ice by saying "Hi" or something. They will talk for hours, and it's a good time watching
them go. It's fun to watch while working on other scripts.

The delay is calculated based on the size of the response to be 'average'.
The average typing speed is 38-40 wpm (190-200 characters).
So the delay per character ought to be 160-210 characters a minute.
160-210             Characters in response
60000 ms            DELAY
"""

cb1 = cleverbot.Cleverbot()

def speechHandler( text, sendername, senderid ):
    if senderid != stealth.Self() and senderid != 'System' and stealth.GetDistance(senderid) < 4:
        stealth.AddToSystemJournal( '{}: {}'.format( sendername, text ) )
        response = cb1.ask( text )
        #See header comment for wait algorithm details
        stealth.Wait( 60000 * len( response ) / random.randint(300,350) )
        stealth.UOSay( response ) 

stealth.SetEventProc( 'evUnicodeSpeech', speechHandler )

while True:
    stealth.Wait( 100 )

