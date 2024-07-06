import logging
import os
import re
import datetime
import sys

from functools import partial

class ReplayAnonymizer:
    "Changes the names in a replay file to Player #."

    def __init__(self, filePath=None) -> None:

        self.filePath = filePath

        self.fileVersion = None
        self.chunkyVersion = None
        self.randomStart = None
        self.highResources = None
        self.VPCount = None
        self.matchType = None
        self.localDateString = None
        self.localDate = None
        self.unknownDate = None
        self.replayName = None
        self.gameVersion = None
        self.modName = None
        self.mapName = None
        self.mapNameFull = None
        self.mapDescription = None
        self.mapDescriptionFull = None
        self.mapFileName = None
        self.mapWidth = None
        self.mapHeight = None
        self.playerList = []

        self.player_number = -1
        self.chunkyHeaderLength = -1
        self.__parent_fold_index = None

        self.success = None

        self.data = None
        self.dataIndex = 0

        if filePath:
            self.load(self.filePath)

    def read_4_bytes_as_unsigned_int(self) -> int:
        "Reads 4 bytes as an unsigned int."

        try:
            if self.data:
                fourBytes = bytearray(
                    self.data[self.dataIndex:self.dataIndex+4])
                self.dataIndex += 4
                theInt = int.from_bytes(
                    fourBytes,
                    byteorder='little',
                    signed=False)
                return theInt
        except Exception as e:
            logging.error(str(e))
            logging.error("Failed to read 4 bytes")
            logging.exception("Stack Trace: ")
            self.success = False

    def read_2_bytes_as_unsigned_int(self) -> int:
        "Reads 2 bytes as an unsigned int."

        try:
            if self.data:
                twoBytes = bytearray(
                    self.data[self.dataIndex:self.dataIndex+2])
                self.dataIndex += 2
                theInt = int.from_bytes(
                    twoBytes,
                    byteorder='little',
                    signed=False)
                return theInt
        except Exception as e:
            logging.error(str(e))
            logging.error("Failed to read 4 bytes")
            logging.exception("Stack Trace: ")
            self.success = False

    def read_byte_as_unsigned_int(self) -> int:
        "Reads 1 byte as an unsigned int."

        try:
            if self.data:
                byte = bytearray(
                    self.data[self.dataIndex:self.dataIndex+1])
                self.dataIndex += 1
                theInt = int.from_bytes(
                    byte,
                    byteorder='little',
                    signed=False)
                return theInt
        except Exception as e:
            logging.error(str(e))
            logging.error("Failed to read 4 bytes")
            logging.exception("Stack Trace: ")
            self.success = False            

    def read_bytes(self, numberOfBytes):
        "reads a number of bytes from the data array"

        try:
            if self.data:
                output = bytearray(
                    self.data[self.dataIndex:self.dataIndex+numberOfBytes])
                self.dataIndex += numberOfBytes
                return output
        except Exception as e:
            logging.error(str(e))
            logging.error("Failed to Read bytes")
            logging.exception("Stack Trace: ")
            self.success = False

    def read_length_string(self):
        "Reads an indexed String."

        try:
            if self.data:
                stringLength = self.read_4_bytes_as_unsigned_int()
                theString = self.read_2_byte_string(stringLength=stringLength)
                return theString
        except Exception as e:
            logging.error(str(e))
            logging.error("Failed to read a string of specified length")
            logging.exception("Stack Trace: ")
            self.success = False

    def read_2_byte_string(self, stringLength=0) -> str:
        "Reads a 2byte encoded little-endian string of specified length."

        try:
            if self.data:
                theBytes = bytearray(
                    self.data[self.dataIndex:self.dataIndex+(stringLength*2)])
                self.dataIndex += stringLength*2
                theString = theBytes.decode('utf-16le')
                return theString
        except Exception as e:
            logging.error(str(e))
            logging.error("Failed to read a string of specified length")
            logging.exception("Stack Trace: ")
            self.success = False

    def read_length_ASCII_string(self) -> str:
        "Reads ASCII string, the length defined by the first four bytes."

        try:
            if self.data:
                stringLength = self.read_4_bytes_as_unsigned_int()
                theString = self.read_ASCII_string(stringLength=stringLength)
                return theString
        except Exception as e:
            logging.error(str(e))
            logging.error("Failed to read a string of specified length")
            logging.exception("Stack Trace: ")
            self.success = False

    def read_ASCII_string(self, stringLength=0) -> str:
        "Reads an ASCII string of specfied length."
        try:
            if self.data:
                theBytes = bytearray(
                    self.data[self.dataIndex:self.dataIndex+stringLength])
                theString = theBytes.decode('ascii')
                self.dataIndex += stringLength
                return theString
        except UnicodeDecodeError:
            # if unable to get an ASCII string try for a ucs2 string.
            #theString = self.read_2_byte_string(stringLength=stringLength)
            #return theString
            return None


    def read_null_terminated_2_byte_string(self) -> str:
        "Reads a Utf-16 little endian character string."

        try:
            if self.data:
                characters = ""
                for character in iter(
                        partial(self.read_bytes, 2),
                        bytearray(b"\x00\x00")
                ):
                    characters += bytearray(character).decode('utf-16le')
                return characters
        except Exception as e:
            logging.error(str(e))
            logging.error("Failed to read a string of specified length")
            logging.exception("Stack Trace: ")
            self.success = False

    def read_null_terminated_ASCII_string(self) -> str:
        "Reads a byte array until the first NULL and converts to a string."

        try:
            if self.data:
                characters = ""
                for character in iter(
                    partial(self.read_bytes, 1),
                    bytearray(b"\x00")
                ):
                    characters += bytearray(character).decode('ascii')
                return characters
        except Exception as e:
            logging.error(str(e))
            logging.error("Failed to read a string of specified length")
            logging.exception("Stack Trace: ")
            self.success = False

    def seek(self, numberOfBytes, relative=0):
        "Moves the file index a number of bytes forward or backward"

        #logging.info("number of bytes %s", numberOfBytes)

        try:
            numberOfBytes = int(numberOfBytes)
            relative = int(relative)
            if relative == 0:
                assert (0 <= numberOfBytes <= len(self.data))
                self.dataIndex = numberOfBytes
            if relative == 1:
                assert (
                    0 <= (numberOfBytes+self.dataIndex) <= len(self.data))
                self.dataIndex += numberOfBytes
            if relative == 2:
                assert (
                    0 <= (len(self.data) - numberOfBytes) <= len(self.data))
                self.dataIndex = len(self.data) - numberOfBytes
        except AssertionError as e:
            logging.error(str(e))
            logging.error("number of bytes %s" , numberOfBytes)
            logging.error("len(self.data) %s", len(self.data))
            logging.error("realive %s" , relative)
            logging.error("Failed move file Index")
            logging.exception("Stack Trace: ")

    def load(self, filePath=""):
        with open(filePath, "rb") as fileHandle:
            self.data = fileHandle.read()
        success = self.process_data()
        if not success:
            print("Invalid replay file.\n Please provide a valid replay.")

    def save(self, filePath=""):

        if filePath:
            with open(filePath, "wb") as binary_file:
                # Write bytes to file
                binary_file.write(self.data)
            logging.info("saved as %s", filePath)

    def process_data(self) -> bool:
        "Processes replay byte data."

        # Set return flag
        self.success = True

        # Process the file Header
        self.fileVersion = self.read_4_bytes_as_unsigned_int()  # int (8)

        self.read_ASCII_string(stringLength=8)  # COH__REC

        self.localDateString = self.read_null_terminated_2_byte_string()

        # Parse localDateString as a datetime object
        self.localDate = self.decode_date(self.localDateString)

        self.seek(76, 0)

        firstRelicChunkyAddress = self.dataIndex
        
        self.read_ASCII_string(stringLength=12)  # relicChunky

        self.read_4_bytes_as_unsigned_int()  # unknown

        self.chunkyVersion = self.read_4_bytes_as_unsigned_int()  # 3

        self.read_4_bytes_as_unsigned_int()  # unknown

        self.chunkyHeaderLength = self.read_4_bytes_as_unsigned_int()

        self.seek(-28, 1)  # sets file pointer back to start of relic chunky
        self.seek(self.chunkyHeaderLength, 1)  # seeks to begining of FOLDPOST

        self.seek(firstRelicChunkyAddress, 0)
        self.seek(96, 1)
        # move pointer to the position of the second relic chunky

        secondRelicChunkyAddress = self.dataIndex

        self.read_ASCII_string(stringLength=12)  # relicChunky

        self.read_4_bytes_as_unsigned_int()  # unknown
        self.read_4_bytes_as_unsigned_int()  # chunkyVersion 3
        self.read_4_bytes_as_unsigned_int()  # unknown
        chunkLength = self.read_4_bytes_as_unsigned_int()

        self.seek(secondRelicChunkyAddress, 0)
        self.seek(chunkLength, 1)  # seek to position of first viable chunk

        self.parse_chunk()
        self.parse_chunk()

        return self.success

    def parse_chunk(self):

        chunkType = self.read_ASCII_string(stringLength=8)
        # Reads FOLDFOLD, FOLDDATA, DATASDSC, DATAINFO etc

        logging.info(chunkType)

        chunkVersion = self.read_4_bytes_as_unsigned_int()

        chunkLength = self.read_4_bytes_as_unsigned_int()

        chunkNameLength = self.read_4_bytes_as_unsigned_int()

        self.seek(8, 1)

        if chunkNameLength > 0:
            self.read_ASCII_string(stringLength=chunkNameLength)  # chunkName

        chunkStart = self.dataIndex

        # Here we start a recusive loop
        if chunkType:
            if (chunkType.startswith("FOLD")):

                while (self.dataIndex < (chunkStart + chunkLength)):
                    self.parse_chunk()

        if (chunkType == "DATASDSC") and (int(chunkVersion) == 2004):

            self.read_4_bytes_as_unsigned_int()  # unknown
            self.unknownDate = self.read_length_string()
            self.read_4_bytes_as_unsigned_int()  # unknown
            self.read_4_bytes_as_unsigned_int()  # unknown
            self.read_4_bytes_as_unsigned_int()  # unknown
            self.modName = self.read_length_ASCII_string()
            self.mapFileName = self.read_length_ASCII_string()
            self.read_4_bytes_as_unsigned_int()  # unknown
            self.read_4_bytes_as_unsigned_int()  # unknown
            self.read_4_bytes_as_unsigned_int()  # unknown
            self.read_4_bytes_as_unsigned_int()  # unknown
            self.read_4_bytes_as_unsigned_int()  # unknown
            self.mapName = self.read_length_string()

            value = self.read_4_bytes_as_unsigned_int()
            if value != 0:  # test to see if data is replicated or not
                self.read_2_byte_string(value)  # unknown
            self.mapDescription = self.read_length_string()
            self.read_4_bytes_as_unsigned_int()  # unknown
            self.mapWidth = self.read_4_bytes_as_unsigned_int()
            self.mapHeight = self.read_4_bytes_as_unsigned_int()
            self.read_4_bytes_as_unsigned_int()  # unknown
            self.read_4_bytes_as_unsigned_int()  # unknown
            self.read_4_bytes_as_unsigned_int()  # unknown

        if (chunkType == "DATABASE") and (int(chunkVersion == 11)):

            self.seek(16, 1)

            self.randomStart = True
            self.randomStart = (self.read_4_bytes_as_unsigned_int() == 0)
            #  0 is fixed 1 is random

            self.read_4_bytes_as_unsigned_int()  # COLS

            self.highResources = (self.read_4_bytes_as_unsigned_int() == 1)

            self.read_4_bytes_as_unsigned_int()  # TSSR

            self.VPCount = 250 * (1 << (int)(
                self.read_4_bytes_as_unsigned_int()))

            self.seek(5, 1)

            self.replayName = self.read_length_string()

            self.seek(8, 1)

            self.VPGame = (self.read_4_bytes_as_unsigned_int() == 0x603872a3)

            self.seek(23, 1)

            self.read_length_ASCII_string() # gameminorversion

            self.seek(4, 1)

            self.read_length_ASCII_string() # gamemajorversion

            self.seek(8, 1)
            # matchname
            if (self.read_4_bytes_as_unsigned_int() == 2):
                self.read_length_ASCII_string() # gameversion
                self.gameVersion = self.read_length_ASCII_string()
            self.read_length_ASCII_string()
            # cant find in korean replay
            self.matchType = self.read_length_ASCII_string()
            # korean 2v2 contains a long 'nonsense' string.
            if "\uc0de\u0bad\u0101\u4204\u4cc5\u0103\u1000" in self.matchType:
                self.matchType = "automatch"

        if (chunkType == "DATAINFO") and (chunkVersion == 6):

            userName = self.read_length_string()
            computer = self.read_byte_as_unsigned_int() # 0, 1, 2, 5 - human, AI, remote human, empty slot
            self.read_byte_as_unsigned_int()
            self.read_byte_as_unsigned_int()
            self.read_byte_as_unsigned_int()
            team = self.read_byte_as_unsigned_int() # 0 , 1
            self.read_byte_as_unsigned_int()
            self.read_byte_as_unsigned_int()
            self.read_byte_as_unsigned_int()
            faction = self.read_length_ASCII_string()
            self.read_4_bytes_as_unsigned_int()
            self.read_4_bytes_as_unsigned_int()

            self.playerList.append({'name': userName, 'faction': faction, 'team': team, 'computer' : computer})

        self.seek(chunkStart + chunkLength, 0)


    def replace_username(self):
        "Processes replay byte data."

        self.playerList.clear()
        self.player_number = 1
        self.dataIndex = 0

        # Set return flag
        self.success = False


        while True:
            user_name_header_location = self.data.find('DATAINFO'.encode('ASCII'), self.dataIndex)
            
            if user_name_header_location == -1:
                break

            folder_size_location = user_name_header_location - 16
            self.seek(folder_size_location, 0)
            folder_size = self.read_4_bytes_as_unsigned_int()

            chunk_size_location = user_name_header_location + 12
            self.seek(chunk_size_location, 0)
            chunk_size = self.read_4_bytes_as_unsigned_int()

            user_name_read_location = user_name_header_location + 28
            self.seek(user_name_read_location, 0)
            user_name = self.read_length_string()
            user_name_size = len(user_name)
            user_name_size_bytes = user_name_size * 2

            replacement_user_name = "Player " + str(self.player_number)
            self.player_number += 1
            replacement_user_name_size = len(replacement_user_name)
            replacement_user_name_size_bytes = replacement_user_name_size * 2

            replacement_user_name_size_int4 = replacement_user_name_size.to_bytes(4, 'little')
            replacement_user_name_bytes = bytes(replacement_user_name.strip().encode('utf-16le'))
                
            output = f"'{user_name}' ---> '{replacement_user_name}'"
            print(output)
            logging.info(output)

            bytes_size_difference = (user_name_size_bytes - replacement_user_name_size_bytes)

            start = user_name_read_location
            end = self.dataIndex

            # replace user name
            self.data = self.data[:start] + replacement_user_name_size_int4 + replacement_user_name_bytes + self.data[end:]

            new_chunk_size = chunk_size - bytes_size_difference
            # set the new chunk size
            self.data = self.data[:chunk_size_location] + new_chunk_size.to_bytes(4, 'little') + self.data[chunk_size_location+4:]

            new_folder_size = folder_size - bytes_size_difference
            # set the new folder size
            self.data = self.data[:folder_size_location] + new_folder_size.to_bytes(4, 'little') + self.data[folder_size_location+4:]

            # Resize header
            self.resize_header(size_difference=bytes_size_difference)

            # Replace ALL chat messages
            self.replace_all_chat_messages(user_name=user_name, replacement=replacement_user_name)


    def replace_all_chat_messages(self, user_name : str, replacement : str):
        "user_name must be encoded as utf-16le"
        """
        messages seems to be of the type
        int4 (total_size?) int4 (1) int4 (inner total_size?) NameString int4 (userid) int4 (0) int4 (1) int4 (messagessize) Message
        
        """

        # store the current data index
        temp = self.dataIndex
        while (self.data.find(user_name.encode('utf-16le')) != -1):
            start = self.data.find(user_name.encode('utf-16le')) - 4
            end = start + 4 + (len(user_name) * 2)
            size_of_replacement = len(replacement)
            replacement_size = size_of_replacement.to_bytes(4, 'little')
            replacement_bytes = bytes(replacement.strip().encode('utf-16le'))
            self.data = self.data[:start] + replacement_size + replacement_bytes + self.data[end:]
            # set size of message
            start = start - 4
            end = start + 4
            self.dataIndex = start
            original_size = self.read_4_bytes_as_unsigned_int()
            new_size = original_size - (len(user_name) - len(replacement)) * 2
            self.data = self.data[:start] + new_size.to_bytes(4, 'little') + self.data[end:]
            # set size of entire message
            start = start - 8
            end = start + 4
            self.dataIndex = start
            original_size = self.read_4_bytes_as_unsigned_int()
            new_size = original_size - (len(user_name) - len(replacement)) * 2
            self.data = self.data[:start] + new_size.to_bytes(4, 'little') + self.data[end:]

        # reset the curent dataIndex back to its original value
        self.dataIndex = temp


    def resize_header(self, size_difference):
        "resizes the header"
        # store current dataIndex
        temp = self.dataIndex
        foldinfo_location = self.data.find("FOLDINFO".encode('ASCII'))

        start = foldinfo_location + 12
        end = foldinfo_location + 16

        self.seek(start, 0)
        old_size = self.read_4_bytes_as_unsigned_int()
        new_size = old_size - size_difference

        self.data = self.data[:start] + new_size.to_bytes(4, 'little') + self.data[end:]
        # set dataIndex back to its original value
        self.dataIndex = temp


    def decode_date(self, timeString) -> datetime:
        "Processes the date string."

        # 24hr: DD-MM-YYYY HH:mm
        reEuro = re.compile(r"(\d\d).(\d\d).(\d\d\d\d)\s(\d\d).(\d\d)")
        match = re.match(reEuro, timeString)
        if match:
            #logging.info("Euro String")
            #logging.info(match.groups())
            try:
                day = int(match.group(1))
                month = int(match.group(2))
                year = int(match.group(3))
                hour = int(match.group(4))
                minute = int(match.group(5))
                return datetime.datetime(
                    year=year,
                    month=month,
                    day=day,
                    hour=hour,
                    minute=minute
                )
            except Exception as e:
                logging.error(str(e))
                logging.exception("Exception : ")

        # 12hr: MM/DD/YYYY hh:mm XM *numbers are not 0-padded
        reUS = re.compile(
            r"(\d{1,2}).(\d{1,2}).(\d\d\d\d)\s(\d{1,2}).(\d{1,2}).*?(\w)M"
            )
        match = re.match(reUS, timeString)
        if match:
            #logging.info("US Date String")
            #logging.info(match.groups())
            try:
                day = int(match.group(2))
                month = int(match.group(1))
                year = int(match.group(3))
                hour = int(match.group(4))
                minute = int(match.group(5))
                meridiem = str(match.group(6))
                if "p" in meridiem.lower():
                    hour = hour + 12
                return datetime.datetime(
                    year=year,
                    month=month,
                    day=day,
                    hour=hour,
                    minute=minute
                )
            except Exception as e:
                logging.error(str(e))
                logging.exception("Exception : ")

        # YYYY/MM/DD HH:MM
        reAsian = re.compile(r"(\d\d\d\d).(\d\d).(\d\d)\s([^\u0000-\u007F]+)\s(\d?\d).(\d\d)")
        # korean AM/PM 오후 means PM
        match = re.match(
            reAsian,
            timeString
        )
        if match:
            #logging.info("Asian Date String")
            #logging.info(match.groups())
            try:
                day = int(match.group(3))
                month = int(match.group(2))
                year = int(match.group(1))
                hour = int(match.group(5))
                minute = int(match.group(6))
                meridiem = match.group(4)
                # korean pm
                if meridiem == "오후":
                     hour = hour + 12
                date_time = datetime.datetime(
                    year=year,
                    month=month,
                    day=day,
                    hour=hour,
                    minute=minute
                )
                return date_time
            except Exception as e:
                logging.error(str(e))
                logging.exception("Exception : ")

    def __str__(self) -> str:
        output = "Data:\n"
        output += "fileVersion : {}\n".format(self.fileVersion)
        output += "chunkyVersion : {}\n".format(self.chunkyVersion)
        output += "randomStart : {}\n".format(self.randomStart)
        output += "highResources : {}\n".format(self.highResources)
        output += "VPCount : {}\n".format(self.VPCount)
        output += "matchType : {}\n".format(self.matchType)
        output += "localDateString : {}\n".format(self.localDateString)
        output += "localDate : {}\n".format(self.localDate)
        output += "unknownDate : {}\n".format(self.unknownDate)
        output += "replayName : {}\n".format(self.replayName)
        output += "gameVersion : {}\n".format(self.gameVersion)
        output += "modName : {}\n".format(self.modName)
        output += "mapName : {}\n".format(self.mapName)
        output += "mapNameFull : {}\n".format(self.mapNameFull)
        output += "mapDescription : {}\n".format(self.mapDescription)
        output += "mapDescriptionFull : {}\n".format(self.mapDescriptionFull)
        output += "mapFileName : {}\n".format(self.mapFileName)
        output += "mapWidth : {}\n".format(self.mapWidth)
        output += "mapHeight : {}\n".format(self.mapHeight)
        output += "playerList Size : {}\n".format(len(self.playerList))
        output += "playerList : {}\n".format(self.playerList)
        return output

if __name__ == "__main__":

    # Program Entry Starts here
    # Default error logging log file location:
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(
        format='%(asctime)s (%(threadName)-10s) [%(levelname)s] %(message)s',
        filename='log_file.log',
        filemode="a",
        level=logging.INFO)

    logging.getLogger().setLevel(logging.INFO)

    if len(sys.argv) == 3:

        if os.path.isfile(sys.argv[1]) and sys.argv[2]:
            replay_anon = ReplayAnonymizer(filePath=sys.argv[1])
            replay_anon.replace_username()
            replay_anon.save(filePath= sys.argv[2])
        else:
            print(
                "please enter a valid replay filename as the first argument.\n"
                "and an output filename eg: output.rec as the second argument.")
            
    else:
        print("Usage: replay_anonymizer.py input.rec output.rec")
