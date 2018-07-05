#!/usr/bin/env python3
print( "Content-type: text/html\n")
import cgitb
import cgi 
import details 

#globals
# for roomKeywords, the keys are words that might be found in emails, and the actual values are the room names that will
# be inserted to the DB
roomKeywords = {'kresge':'kresge',
                'W20': 'W20',
                'verdes': 'W20',
                'stud': 'W20',
                'student center': 'W20',
                'student centre': 'W20',
                'stata': 'stata',
}


cgitb.enable()
#command below takes the arguements from the get request and puts them in some sort of a dictionary
inDataDict = cgi.FieldStorage()

import imaplib, email, os, datetime, sqlite3
# email things
user = details.email
password = details.password 
imap_url = 'imap.gmail.com'
def auth(user,password,imap_url):
    con = imaplib.IMAP4_SSL(imap_url)
    con.login(user,password)
    return con

def getBody(msg):
    if msg.is_multipart():
        return getBody(msg.get_payload(0))
    else:
        return msg.get_payload(None,True)
    
def getSubject(msg):
    decode = email.header.decode_header(msg['Subject'])[0]
    subject = (decode[0])
    return subject


def getSender(msg):
    sender = msg['From']
    # since it has the structure of 'name <email@adress.com> , remove email adress and space that follows it
    sender = sender[:sender.find('<') -1]
    return sender
    
    

def getLatestEmailIndex(con): 
    #how many emails are in the inbox
    lastEmailIndex = str(con.select('INBOX')[1][0]).split("'")[1]
    #print('Index of newest email='+lastEmailIndex)
    return lastEmailIndex

#function to return a string with the Title and body (together) of the most recent email
def getLatestEmail(con):
    #how many emails are in the inbox
    lastEmailIndex = getLatestEmailIndex(con)
    result, data = con.fetch(str(lastEmailIndex),'(RFC822)')
    raw = email.message_from_bytes(data[0][1])
    senderName = getSender(raw)
    subject = getSubject(raw)
    body = getBody(raw)
    if str(subject).find('Re:') != -1:
        return("Reply not shown")
    return (str(subject) +" " + str(body))

#returns the sender name
def getLatestSender(con):
    #how many emails are in the inbox
    lastEmailIndex = getLatestEmailIndex(con)
    result, data = con.fetch(str(lastEmailIndex),'(RFC822)')
    raw = email.message_from_bytes(data[0][1])
    senderName = getSender(raw)
    return senderName

#function that expects a string and spits back a string with the room number
# will return the room number if exists in email, or "No room in email" if not found
def getRoomNumberFromEmail(message, senderName):
    # check if the message is a reply or not
    if message == "Reply not shown":
        return "No room in email"
    numbers = "1234567890"
    lowerCaseLetters = "qwertyuiopasdfghjklzxcvbnm"
    if isinstance(message, str) == True:
        if message.find("-") != -1 :
            found = False
            dashIndex =  message.find('-')
            # look for a signature in the email
            signatureStart = len(message)
            print('<br><br><br>('+ senderName.lower() +') <br><br><br>')
            print('<br><br><br>'+ str(senderName.lower().find('ai shaoul')) +' <br><br><br>')
            
            print('<br><br><br> lower the message=', message.lower())
            print('<br><br><br> the index of the message=', signatureStart)
            
            print('<br><br><br> the sender of the message=i=' + senderName + '<br><br><br>')
            if str(message.lower()).find(senderName.lower()) != -1:
                signatureStart = str(message.lower()).find(senderName.lower())
            print ('  sig start=' + str(signatureStart))
            while found == False:
                # go to a heifen 
                middleIndex =  dashIndex
                # make sure that the dash is before the beginning of the signature
                if middleIndex > signatureStart:
                    break
                beginIndex = middleIndex
                while (message[beginIndex] != " ") and (message[beginIndex] not in lowerCaseLetters):
                    beginIndex -= 1
                #now we have the index of the first space
                endIndex = middleIndex + 4
                #endIndex = message.find(" ", beginIndex)
                roomNumber = message[beginIndex+1:endIndex]
                if len(roomNumber) > 4:
                    if roomNumber[-1] in numbers and roomNumber[-2] in numbers and roomNumber[-3] in numbers:
                        #if all three characters after the dash are numbers, we have the room number
                        return roomNumber
                dashIndex = message.find('-',dashIndex+1)
                if dashIndex == -1:                        
                    break
       
        # now we have not found any room numer, look for keywords
        for word in roomKeywords.keys():
            if message.lower().find(word) != -1:
                return roomKeywords[word]
        return "No room in email"

# get the message:
con = auth(user,password,imap_url)
con.select('INBOX')
message = getLatestEmail(con)
sender = getLatestSender(con)
print("Entire email:<br>" + message+'<br>')
room = getRoomNumberFromEmail(message, sender)
print("Room from email:"+str(room)+'<br>')
# after getting the info, if the room number != "No room in email" then insert
# the data to foodEmails.db, with foodTable inside (room text, time, timestamp)
print (datetime.datetime.now())
# check that the data is not already in the database
#read last entry:
example_db = "foodEmails.db"
conn = sqlite3.connect(example_db)
c = conn.cursor()
things = c.execute('''SELECT * FROM foodTable ORDER BY time DESC;''').fetchone()
lastRoom = things[0]
conn.commit()
conn.close()
#now if the last room is not like the new room, add the new one to db
if lastRoom != room:
    #check if room is actual number of a room
    if room != "No room in email":
        print( "Putting into database")
        example_db = "foodEmails.db"
        conn = sqlite3.connect(example_db)
        c = conn.cursor()
        c.execute('''INSERT into foodTable VALUES (?,?);''',(room,datetime.datetime.now()+datetime.timedelta(hours=7)))
        conn.commit()
        conn.close()
    else:
        print("No room number found in email, none inserted")
else:
    print("This room is already in the db, not inserted")

# present the data nicely:

example_db = "foodEmails.db"
conn = sqlite3.connect(example_db)
c = conn.cursor()
things = c.execute('''SELECT * FROM foodTable ORDER BY time DESC;''').fetchall()

# show as json
outDict = {'data':[]}
for line in range(3):
    outDict['data'].append({'room': str(things[line][0]), 'time':str(things[line][1])[:19]})
    #print ("<br><br>There's food at room "+ str(things[line][0]) + ". True to " + str(things[line][1])[:19]+"<br><br>")
conn.commit()
conn.close()


print('<br><br>')
print(outDict)
