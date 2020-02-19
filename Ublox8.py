#! /usr/bin/env python3
"""
Program to read in data from the BB3 wetlabs sensor.
"""

try:
    import serial
except ImportError as message:
    print("Failed to import serialReaderial, maybe it is not installed correctly? Error was: {}".format(message))

try:
    import datetime 
except ImportError as message:
    print("Failed to import datetime, maybe it is not installed correctly? Error was: {}".format(message))

try:
    import time
except ImportError as message:
    print("Failed to import time, maybe it is not installed correctly? Error was: {}".format(message))

# try:
#     from dummy_sensors import DummyEXAMPLESensor
# except ImportError as message:
#     print("Failed to import DummyBB3Sensor from dummy_sensors, check your files. Error was: {}".format(message))

import struct
from pymemcache.client import base

def generateFletcherChecksum(byteArray):
    """
    Function to calculate the checksum from the received line of data.
    Returns the checksum generated from the line.
    """
    CK_A = 0
    CK_B = 0

    for I in range(len(byteArray)):
        CK_A = CK_A + byteArray[I]
        CK_A &= 0xFF 
        CK_B = CK_B + CK_A    
        CK_B &= 0xFF

    return (CK_A, CK_B)

# def sizeTester():
   
#     structValues = {
#         'c': 1,
#         'x':1,
#         'b': 1,
#         'B': 1,
#         '?': 1,
#         'h': 2,
#         'H': 2,
#         'i': 4,
#         'I': 4,
#         'l': 4,
#         'L': 4,
#         'q': 8,
#         'Q': 8,
#         'e': 2,
#         'f': 4,
#         'd': 8
#     }

#     for item in structValues:
#         print("character {} has byte buffer value {}".format(item,struct.calcsize(item)))

# def UnpackMessage(structFormat, payload):
#     print("here")

#     messageData = struct.unpack(structFormat, bytearray(payload))   
#     yield (messageData)
#     # print("NEW MESSAGE \n\n") 
#     # for dataIndex in range(len(messageData)):
#     #     print("{} is: {}".format(messageFormat[dataIndex], messageData[dataIndex]))

def UnpackMessage(structFormat, payload):
    messageData = struct.unpack(structFormat, bytearray(payload)) 
    return (messageData)

def PayloadIdentifier(payload, ID, Class):

    from ublox8Dictionary import ClassIDs
    Class = str(hex(Class).lstrip("0x")).zfill(2)
    ID = str(hex(ID).lstrip("0x")).zfill(2)
    identifier = str(Class) + str(ID) #+ str(length)

    if identifier in ClassIDs.keys():
        if(identifier == "0107"):
            data = UnpackMessage(ClassIDs[identifier][0], payload)
            return (data)
            # UnpackMessage(ClassIDs[identifier][0], payload)
        else:
            pass #MAKE THE LOGGER to say this message hasn't been implemented yet.  
        
def ValidateLine(currentLine):
    loadsOfHexData = []
    # check if line is valid using checksum
    loadsOfHex = list(bytearray(currentLine).hex())                 
    # Organise the hex data into the correct pairs.
    for index in range(0, len(loadsOfHex), 2):
        val = loadsOfHex[index] + loadsOfHex[index+1]
        if len(val) == 2:
            loadsOfHexData.append(val)
    base16Data = [int(x, 16) for x in loadsOfHexData]
    currentByteLine = bytearray(base16Data)
    checkSumA, checkSumB = generateFletcherChecksum(currentByteLine[2:-2])
    return (currentByteLine, checkSumA, checkSumB)

def SendMessage():
    print("Executed")
    organisedHexData = []
    serialReader = serial.Serial('/dev/ttyACM0', 460800, timeout = 1)
    # serialReader.write(b'\xff')
    # time.sleep( 0.5 )
    serialReader.write(b'\xb5\x62\x0a\x04\x00\x00\x0e\x34') # b'\xb5\x62\x0a\x04\x00\x00\x0e\x34'
    time.sleep(0.5)
    ProtocolVersion = serialReader.readline()
    protocolVersion2 = serialReader.readline()
    # print(ProtocolVersion)
    # print(protocolVersion2)
    temp = list(ProtocolVersion.hex())
    temp2 = list(protocolVersion2.hex())
    newTemp = []
    for index in range(0, len(temp), 2):
        val = temp[index] + temp[index+1]
        if len(val) == 2:
            newTemp.append(val)

    newTemp2 = []
    for index in range(0, len(temp2), 2):
        val = temp2[index] + temp2[index+1]
        if len(val) == 2:
            newTemp2.append(val)

    newTemp.extend(newTemp2)
    organisedHexData = newTemp[::]
    listOfLines = []
    startIndices = [ i for i in range(len(organisedHexData)-1) if (organisedHexData[i] == 'b5' and organisedHexData[i+1] == '62') ]    

    if(len(startIndices) >= 2):
        for currentStartIndex in range(len(startIndices)-1):
            # For all indexes that are start points, check if each is a full line.
            currentLine = organisedHexData[startIndices[currentStartIndex]:startIndices[currentStartIndex+1]]
            base16Data = [int(x, 16) for x in currentLine]
            currentByteLine = bytearray(base16Data)
            checkSumA, checkSumB = generateFletcherChecksum(currentByteLine[2:-2])
            assert (len(currentByteLine)>1),"{} shorter then 2".format(currentByteLine)
            # If the line is complete and correct then append it to a list of lines.
            if(checkSumA == currentByteLine[-2] and checkSumB == currentByteLine[-1]):
                listOfLines.append(currentLine)
            else:
                # If the line is not complete, check if the "start index" was actually generated in the payload (middle of the message)
                # If it was, check the following start indexes. If none are correct then discard the data.
                for x in range(len(startIndices)-1):
                    currentLine = organisedHexData[startIndices[currentStartIndex]:startIndices[x+1]]
                    base16Data = [int(x, 16) for x in currentLine]
                    currentByteLine = bytearray(base16Data)
                    checkSumA, checkSumB = generateFletcherChecksum(currentByteLine[2:-2])
                    if(checkSumA == currentByteLine[-2] and checkSumB == currentByteLine[-1]):
                        listOfLines.append(currentLine)
                        break
        one = 0
        two = 0
        three = 0
        four=0

        for line in listOfLines:
            if(line[2] == "01" and line[3] == "07"):
                one+=1
            elif(line[2] == "01" and line[3] == "3c"):
                two+=1
            elif(line[2] == "0a" and line[3] == "04"):
                three+=1
            else:
                four+=1
                print("Unkown line")
                print(line)
            
            if(line[2] == "01" and line[3] == "07" or line[2] == "01" and line[3] == "3c"):
                pass
            else:
                print("Full line {}".format(line)) #26
                print("\n payload: {}".format(line[6:-2])) #26
                
                payload = (line[6:-2])
                binaryPayload = []
                for item in payload:
                    data = "{0:08b}".format(int(item, 16))
                    binaryPayload.append(data)
                print(binaryPayload)           
                print("\n")          
            
        print('\n')
        print("one is {}, two is {}, three is {}, four is {}".format(one, two, three, four))
    serialReader.close()
    
def ReadMemcache():
    client = base.Client(('localhost', 11211))

    data = client.get('GPS_UBLOX8')
    return data

class GPS_Ublox8:
    """
    The EXAMPLE sensor class to read in data live while in-situ.

    Reads in a line of data, then after checking a certain number of times to see if there is data, adjust a waiting timer.

    The waiting timer is adjusted to avoid unnecessary CPU usage on the Raspberry Pi.
    """

    def __init__(self, port):
        self.port = port

    # def ReadingNOTSTRUCT(self):
    #     """
    #     Generator function to read in data from the sensor.
        
    #     Uses a time taken per line read formula to adjust the time to wait between making checks.

    #     Reads in all the data in the buffer, then splits it up into lines, and processs them individually.
        
    #     """

    #     bitOfData = b''
    #     organisedHexData = []
    #     loadsOfHexData = []

    #     try:

    #         serialReader = serial.Serial('/dev/ttyACM0', 460800, timeout = None)
    #         organisedHexData = []
    #         loadsOfHexData = []
    #         # Continously read in data from the GPS.
    #         while True:           
    #             if serialReader.in_waiting != 0:
    #                 bitOfData = serialReader.read(serialReader.in_waiting)

    #                 loadsOfData = list(bitOfData.hex())                 
    #                 # Organise the hex data into the correct pairs.
    #                 for index in range(0, len(loadsOfData), 2):
    #                     val = loadsOfData[index] + loadsOfData[index+1]
    #                     if len(val) == 2:
    #                         loadsOfHexData.append(val)
                  
    #                 organisedHexData =  organisedHexData + loadsOfHexData
    #                 loadsOfHexData = []
    #                 listOfLines = []
    #                 startIndices = [ i for i in range(len(organisedHexData)-1) if (organisedHexData[i] == 'b5' and organisedHexData[i+1] == '62') ]    

    #                 if(len(startIndices) >= 2):
    #                     for currentStartIndex in range(len(startIndices)-1):
    #                         # For all indexes that are start points, check if each is a full line.
    #                         currentLine = organisedHexData[startIndices[currentStartIndex]:startIndices[currentStartIndex+1]]
    #                         base16Data = [int(x, 16) for x in currentLine]
    #                         currentByteLine = bytearray(base16Data)
    #                         checkSumA, checkSumB = generateFletcherChecksum(currentByteLine[2:-2])
    #                         assert (len(currentByteLine)>1),"{} shorter then 2".format(currentByteLine)
    #                         # If the line is complete and correct then append it to a list of lines.
    #                         if(checkSumA == currentByteLine[-2] and checkSumB == currentByteLine[-1]):
    #                             listOfLines.append(currentLine)
    #                         else:
    #                             # If the line is not complete, check if the "start index" was actually generated in the payload (middle of the message)
    #                             # If it was, check the following start indexes. If none are correct then discard the data.
    #                             for x in range(len(startIndices)-1):
    #                                 currentLine = organisedHexData[startIndices[currentStartIndex]:startIndices[x+1]]
    #                                 base16Data = [int(x, 16) for x in currentLine]
    #                                 currentByteLine = bytearray(base16Data)
    #                                 checkSumA, checkSumB = generateFletcherChecksum(currentByteLine[2:-2])
    #                                 if(checkSumA == currentByteLine[-2] and checkSumB == currentByteLine[-1]):
    #                                     listOfLines.append(currentLine)
    #                                     break
    #                     # For all the lines collected, get the payload out and send it to get sorted... eventually... it's a work in progress..    
    #                     for line in listOfLines:
    #                         # print("Full line {}".format(line)) #26
    #                         # print("\n payload: {} \n".format(line[6:-2])) #26
                            
    #                         payload = (line[6:-2]) 
    #                         print(payload)

    #                         # for item in payload:
    #                         #     float.hex(float(item))

    #                         # print(payload)
    #                         # print(struct.unpack_from("I",bytes(binaryPayload[0])))
    #                         # print("\n")
    #                         # binaryPayload = []
    #                         # for item in payload:
    #                         #     data = "{0:08b}".format(int(item, 16))
    #                         #     binaryPayload.append(data)
    #                         # print(binaryPayload)
    #                         # print(struct.unpack_from("IHBBBBBBIiBbbBiiiiIIiiiiiIIHBBBBBBihH",bytes(binaryPayload)))
                           
    #                         # print(line)
    #                         # # send the payload, ID and class
    #                         # PayloadIdentifier(line[6:-2], line[3], line[2])
    #                         # f = open("/local1/data/scratch/jkb/GPS2.txt", "a")
    #                         # f.write(str(line))
    #                         # f.write('\n')
    #                         # f.close()

    #                     # Any data that was not a complete line, and is in fact a part of the next line to be read in
    #                     # is kept in the organised hex data list so the rest of the line can be appended. 
    #                     organisedHexData = organisedHexData[startIndices[len(startIndices)-1]:]
                    
    #     except ValueError as message:
    #         print("Did not manage to connect to sensor properly, check your settings. Error was: {}".format(message))
    #     except ImportError as message:
    #         print("Importing issue, error was {}".format(message))


    def Reading(self):
            """
            Generator function to read in data from the sensor.
            
            Uses a time taken per line read formula to adjust the time to wait between making checks.

            Reads in all the data in the buffer, then splits it up into lines, and processs them individually.            
            """
            bitOfData = b''

            # Variables to manager a reader timer
            numberOfChecksToMake = 10
            timeToSleep = 1
            targetChecksPerLine = 1.3
            targetLinesPerCheck = 1/targetChecksPerLine


            try:
                myPort = '/dev/'+self.port
                serialReader = serial.Serial(myPort, 460800, timeout = None)
                LotOfData = []
                # Continously read in data from the GPS.
                while True:        

                    # Keep a record of number of lines read this pass, to calculate timer
                    lineCount = 0

                    for i in range(numberOfChecksToMake):
                        # Sleep so the program isn't spamming buffer with read requests
                        time.sleep(timeToSleep)

                        if serialReader.in_waiting != 0:
                            bitOfData = serialReader.read(serialReader.in_waiting)
                            bitOfDataInAList = list(bitOfData)           
                            LotOfData =  LotOfData + bitOfDataInAList
                            
                            bitOfDataInAList = []
                            listOfLines = []
                            bitOfData = b''
                            if len(LotOfData) > 400:
                                raise IOError("Port Failed")
                            
                            startIndices = [ i for i in range(len(LotOfData)-1) if (LotOfData[i] == 181 and LotOfData[i+1] == 98) ]
                            if(len(startIndices) >= 2):
                                for currentStartIndex in range(len(startIndices)-1):
                                    # For all indexes that are start points, check if each is a full line.
                                    currentLine = LotOfData[startIndices[currentStartIndex]:startIndices[currentStartIndex+1]]                               
                                    currentHexLine, checkSumA, checkSumB = ValidateLine(currentLine)

                                    assert (len(currentHexLine)>1),"{} shorter then 2".format(currentHexLine)
                                    # If the line is complete and correct then append it to a list of lines.
                                    if(checkSumA == currentHexLine[-2] and checkSumB == currentHexLine[-1]):
                                        listOfLines.append(currentLine)
                                    else:
                                        # If the line is not complete, check if the "start index" was actually generated in the payload (middle of the message)
                                        # If it was, check the following start indexes. If none are correct then discard the data.
                                        for x in range(len(startIndices)-1):
                                            currentLine = LotOfData[startIndices[currentStartIndex]:startIndices[x+1]]
                                            currentHexLine, checkSumA, checkSumB = ValidateLine(currentLine)
                                            if(checkSumA == currentHexLine[-2] and checkSumB == currentHexLine[-1]):
                                                listOfLines.append(currentLine)
                                                break
                                # For all the lines collected, get the payload out and send it to get sorted... eventually... it's a work in progress..    
                                for line in listOfLines:
                                    lineCount += 1
                                    payload = (line[6:-2]) 
                                    ID = line[3]                         
                                    CLASS = line[2]  
                                    data = PayloadIdentifier(payload, ID, CLASS)
                                    yield data
                                
                                # Any data that was not a complete line, and is in fact a part of the next line to be read in
                                # is kept in the organised hex data list so the rest of the line can be appended. 
                                LotOfData = LotOfData[startIndices[len(startIndices)-1]:]           
                    
                    # Re-calculate the amount of time needed to sleep, with the goal of checking buffer at the speed of 1.3 times that of data being available
                    linesPerCheck = lineCount / numberOfChecksToMake
                    newTimeToSleep = timeToSleep * ( targetLinesPerCheck / linesPerCheck ) 
                    timeToSleep = newTimeToSleep
                    # Slowly increase the number of checks before re-adjusting the timer
                    if(numberOfChecksToMake < 100):
                        numberOfChecksToMake += 10

            except ValueError as message:
                print("Did not manage to connect to sensor properly, check your settings. Error was: {}".format(message))
            except ImportError as message:
                print("Importing issue, error was {}".format(message))            


if __name__ == "__main__":
    ports = ["ttyACM0","ttyACM1","ttyUSB0","ttyUSB1"]

    wantedPort = ""

    for port in ports:
        try:
            print("Trying new port {}".format(port)) 
            testGPS = GPS_Ublox8(port)
            GPSReading = testGPS.Reading()
            line = next(GPSReading)
            print(line)
            wantedPort = port
            break
        except Exception as error:
            print(error)
   
    GPS = GPS_Ublox8(wantedPort)
    while True:
        GPSReading = GPS.Reading()
        line = next(GPSReading)
        # Set up memcache
        client = base.Client(('localhost', 11211))
        # Set key and value for memcache, with the line data as the value, and constantly update to be latest data.
        client.set('GPS_UBLOX8', line)

# SendMessage()