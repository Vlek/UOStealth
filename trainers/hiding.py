import stealth

stealth.AddToSystemJournal('Now Training: Hiding')

while stealth.GetSkillValue('Hiding') < 100.0:
    stealth.UseSkill('Hiding')
    stealth.Wait(10250)
    
stealth.AddToSystemJournal('Finished Training: Hiding')
Disconnect()
