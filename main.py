import tweepy
import yaml
# import MySQLdb

class Bot():
    def __init__(self):
        # Load config
        tokens = self.load_config()
        # Create auth and api
        auth = tweepy.OAuthHandler(tokens['consumer_key'], tokens['consumer_secret'])
        auth.set_access_token(tokens['access_token'], tokens['access_token_secret'])
        self.api = tweepy.API(auth)
        # Configure database
        # self.configure_db()

    def configure_db(self, host="localhost", user="appuser", password="password", database="vending"):
        # Connect to database
        self.db = MySQLdb.connect(host=host, user=user, passwd=password, db=database)
        self.cursor = db.cursor()

        ## Debug
        # Execute SQL statement
        cursor.execute("SELECT * FROM LOCATION")

        # Commit changes
        db.commit()

        # Get number of rows in resulting set
        number_rows = int(cursor.rowcount)

        # Display each row
        for each in range(0, number_rows):
            row = cursor.fetchone()
            print(row[0] + " >> " + row[1])


    def load_config(self, file="config.txt"):
        # Load configurations from file
        result = {}
        with open(file, 'r') as stream:
            result = yaml.load(stream)
        return result

    def load_mentions(self, user="VendinGoGo", display=False):
        # Define variables
        mentions = []
        query = "@" + user # "@VendinGoGo" by default
        # Load mentions
        api_mentions = self.api.search(q=query)
        # Iterate through
        for tweet in api_mentions:
            # Define variables
            item = {}
            user = str(tweet.user.screen_name) #.encode('utf8'))
            text = str(tweet.text) #.encode('utf8'))
            # Reset variables
            location = ''
            coords = ''
            place = ''

            # Add each location element found on the tweet object
            if tweet.user.location and tweet.user.location is not "":
                location = str(tweet.user.location)
            if tweet.coordinates:
                coords = str(tweet.coordinates)
            if tweet.place:
                place = str(tweet.place.bounding_box.coordinates)

            # Build item
            item["user"] = user
            item["text"] = text
            item["location"] = location
            item["coords"] = coords
            item["place"] = place
            # Append to mentions
            mentions.append(item)

        # Optionally, print mentions
        if display:
            for each in mentions:
                # Get tweet information
                user = each["user"]
                text = each["text"]
                location = each["location"]
                coords = each["coords"]
                place = each["place"]

                # Print the tweet
                print(user + ": " + text)
                # Print location info found
                if location:
                    print("-- Location:" + location)
                if coords:
                    print("-- Coordinates:" + coords)
                if place:
                    print("-- Place:" + place)

                # Print two new lines for readability
                print("")
                print("")

        # Return
        return mentions

if __name__ == "__main__":
    # Create a bot
    bot = Bot()

    # Load mentions
    dicts = bot.load_mentions(display=False)

    ## Debug Notedb
    mentions = []
    for each in dicts:
        new_item = []
        new_item.append(each["user"])
        new_item.append(each["text"])
        new_item.append(each["coords"])
        new_item.append(each["location"])
        new_item.append(each["place"])
        mentions.append(new_item)

    ## Debug note
    # import Notedb
    from Notedb import Note
    # Create Note
    note = Note(
        databaseName = "Mentions",
        schema       = ["User","Text","Coordinates","Location","Place"])
    # Load existing tweets
    note.openNote()
    # Save new tweets
    # DEBUG
    newtweet = ['1', '2', '3', '4', '5']
    mentions.append(newtweet)
    # Handle null strings
    for eachRow in mentions:
        for eachItem in eachRow:
            if eachItem == None:
                eachItem = ''

    for each in mentions:
        # If tweet is not found
        found = False
        for eachRow in note.tables[0]:
            if set(each) == set(eachRow):
                # If a match is found
                found = True
                break
        if not found:
            # Append it to the table
            note.tables[0].append(each)
    # Save note
    note.saveNote()
