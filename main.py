import tweepy
import yaml
import MySQLdb
from geopy.distance import vincenty
import ast
import re

class Bot():
    def __init__(self):
        # Load config
        tokens = self.load_config()

        ## Prepare Twitter
        # Create auth and api
        self.auth = tweepy.OAuthHandler(tokens['consumer_key'], tokens['consumer_secret'])
        self.auth.set_access_token(tokens['access_token'], tokens['access_token_secret'])
        self.api = tweepy.API(self.auth)

        # Configure database
        self.configure_db(tokens['host'], tokens['user'], tokens['password'], tokens['database'])
        # Configure Twitter
        self.configure_twitter()

        # Start Twitter Stream
        self.start_twitter()

    def start_twitter(self):
        self.stream.filter(track=[self.query])

    def configure_twitter(self, query="@VendinGoGo"):
        self.stream_listener = MyStreamListener()
        self.stream_listener.set_parent(self)
        self.stream = tweepy.Stream(auth=self.auth, listener=self.stream_listener)
        self.query = query

    def configure_db(self, host="localhost", user="appuser", password="password", database="vending"):
        # Connect to database
        self.db = MySQLdb.connect(host=host, user=user, passwd=password, db=database)
        # Set cursor
        self.cursor = self.db.cursor()

    def test_db(self):
        ## Debug
        # Execute SQL statement
        self.cursor.execute("SELECT * FROM vendinglocation")

        # Commit changes
        self.db.commit()

        # Get number of rows in resulting set
        number_rows = int(self.cursor.rowcount)

        # Display each row
        for each in range(0, number_rows):
            print(str(self.cursor.fetchone()))


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
                coords = tweet.coordinates
                print(tweet.coordinates)
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
                    print("-- Coordinates:" + str(coords))
                if place:
                    print("-- Place:" + place)

                # Print two new lines for readability
                print("")
                print("")

        # Return
        return mentions

    def load_tweets(self, user="VendinGoGo", display=False):
        # Define variables
        mentions = []
        query = "@" + user # "@VendinGoGo" by default
        # Load mentions
        api_mentions = self.api.search(q=query)
        # Iterate through
        for tweet in api_mentions:
            mentions.append(tweet)
        # Return
        return mentions

#override tweepy.StreamListener to add logic to on_status
class MyStreamListener(tweepy.StreamListener):
    def set_parent(self, parent):
        self.parent = parent

    def on_status(self, status):
        # Print the message
        print(str(status.user.screen_name) + ": " + str(status.text))
        # Debug prints
        # print("Full status information", status)
        # print("Now examining status coordinates more closely \n -----------")
        # print("Status[coords]: " + str(status['coords']))
        # print("Status[coords]['type']: " + str(status['coords']['type']))
        # print("Status[coords]['coordinates']: " + str(status['coords']['coordinates']))
        # print("Status[place]: " + str(status['place']))
        # print("DONE examining status coordinates more closely \n -----------")

        # Filter out tweets not containing location data
        location_info = None
        if status.place:
            print("-place exists")
            try:
                if len(status.place) > 0:
                    location_info = "place"
            except:
                print("--place is empty")
                pass
        if status.coordinates:
            print("-Coordinates exists")
            try:
                if len(status.coordinates) > 0:
                    location_info = "coordinates"
            except:
                print("--coordinates are empty")
                pass
        if not location_info:
            print("-No location information found")
            # print(status)
            return

        # Gather most accurate location of tweet available
        tweet_location = None
        if location_info == "place":
            ## Bounding box, calculate middle of region
            # Convert place from string to list
            status.place = ast.literal_eval(status.place)
            # Calculate average of every index across the list and convert to tuple
            tweet_location = tuple(x for x in [sum(y) / len(y) for y in zip(*status.place[0])])
        else:
            print("-No place found")
        if location_info == "coordinates":
            if len(status.coordinates) > 0:
                # Most precise location
                try:
                    print(status.coordinates)
                except:
                    print(str(status.coordinates))
                tweet_location = (status.coordinates['coordinates'][0], status.coordinates['coordinates'][1])
            else:
                print("-No coordinates found")
        else:
            print("-No coordinates found")

        ## Find nearest location from vending machine
        # Execute SQL statement
        self.parent.cursor.execute("SELECT id, lat, lng FROM vendinglocation")

        # Get number of rows in resulting set
        number_rows = int(self.parent.cursor.rowcount)
        distance = 350 # Will serve as maximum distance for nearby tweets
        closest = None

        # Iterate through all vending machines in database
        for index in range(0, number_rows):
            # Get vending machine location and id
            row = self.parent.cursor.fetchone()
            vending_id = row[0]
            vending_location = (row[2], row[1])

            # Debug print
            # print("-Vending location @ "+ str(vending_location))

            # If closer than current closest
            if (vincenty(tweet_location, vending_location).feet < distance):
                # Update closest machine variables
                distance = vincenty(tweet_location, vending_location).miles
                closest = vending_id
                print("-Found closer vending machine:" + str(closest))

        # If a vending machine was found close enough
        if closest:
            print("-We found a closest machine!")
            print("--Vending machine id: " + str(closest))

            ### Write a status update for it
            ## Get body text
            body = re.sub('@VendinGoGo', '', status.text)
            print("--Tweet content less @VendinGoGo: " + body)
            ## Get user ID of poster
            user = self.parent.api.get_user(screen_name=status.user.screen_name)
            user_id = user.id
            ## Check if they are registered with us
            # Execute SQL statement
            self.parent.cursor.execute("SELECT * FROM users WHERE id=" + str(user_id))
            number_rows = int(self.parent.cursor.rowcount)
            if number_rows == 0:
                # User is not registered; do that now
                print("--Registered user " + str(user.name))
                self.parent.cursor.execute("INSERT INTO users (id, name, oauth) VALUES (" + str(user_id) + ", " + str(user.name) + ", " + str(0) + ")")
                self.parent.db.commit()
            ## Post status
            print("-Updated status")
            self.parent.cursor.execute("INSERT INTO statuses (userId, vendingId, comment) VALUES (" + str(user_id) + ", " + str(closest) + ", \"" + str(body) + "\")")
            self.parent.db.commit()
        else:
            # Was not close enough to a vending location
            print("-Was not near a vending machine")

    def on_error(self, status_code):
        if status_code == 420:
            #returning False in on_data disconnects the stream
            return False

if __name__ == "__main__":
    # Create a bot
    create_bot()

    #
    # Debug
    #

    #
    # Debug
    #

    # Load mentions
    # tweets = bot.load_mentions(display=True)
    # for status in tweets:
    #     # Print the message
    #     print(str(status['user']) + ": " + str(status['text']))
    #     # Debug prints
    #     # print("Full status information", status)
    #     # print("Now examining status coordinates more closely \n -----------")
    #     # print("Status[coords]: " + str(status['coords']))
    #     # print("Status[coords]['type']: " + str(status['coords']['type']))
    #     # print("Status[coords]['coordinates']: " + str(status['coords']['coordinates']))
    #     # print("Status[place]: " + str(status['place']))
    #     # print("DONE examining status coordinates more closely \n -----------")
    #
    #     # Filter out tweets not containing location data
    #     if len(status['coords']) < 1 and len(status['place']) < 1:
    #         continue
    #
    #     # Gather most accurate location of tweet available
    #     tweet_location = None
    #     if status['place']:
    #         ## Bounding box, calculate middle of region
    #         # Convert place from string to list
    #         status['place'] = ast.literal_eval(status['place'])
    #         # Calculate average of every index across the list and convert to tuple
    #         tweet_location = tuple(x for x in [sum(y) / len(y) for y in zip(*status['place'][0])])
    #     else:
    #         print("-No place found")
    #     if len(status['coords']) > 0:
    #         # Most precise location
    #         tweet_location = (status['coords']['coordinates'][0], status['coords']['coordinates'][1])
    #     else:
    #         print("-No coordinates found")
    #
    #     ## Find nearest location from vending machine
    #     # Execute SQL statement
    #     bot.cursor.execute("SELECT id, lat, lng FROM vendinglocation")
    #
    #     # Get number of rows in resulting set
    #     number_rows = int(bot.cursor.rowcount)
    #     distance = 200 # Will serve as maximum distance for nearby tweets
    #     closest = None
    #
    #     # Iterate through all vending machines in database
    #     for index in range(0, number_rows):
    #         # Get vending machine location and id
    #         row = bot.cursor.fetchone()
    #         vending_id = row[0]
    #         vending_location = (row[2], row[1])
    #
    #         # Debug print
    #         # print("-Vending location @ "+ str(vending_location))
    #
    #         # If closer than current closest
    #         if (vincenty(tweet_location, vending_location).feet < distance):
    #             # Update closest machine variables
    #             distance = vincenty(tweet_location, vending_location).miles
    #             closest = vending_id
    #             print("-Found closer vending machine:" + str(closest))
    #
    #     # If a vending machine was found close enough
    #     if closest:
    #         print("-We found a closest machine!")
    #         print("--Vending machine id: " + str(closest))
    #
    #         ### Write a status update for it
    #         ## Get body text
    #         body = re.sub('@VendinGoGo', '', status['text'])
    #         print("--Tweet content less @VendinGoGo: " + body)
    #         ## Get user ID of poster
    #         user = bot.api.get_user(screen_name=status['user'])
    #         user_id = user.id
    #         ## Check if they are registered with us
    #         # Execute SQL statement
    #         bot.cursor.execute("SELECT * FROM users WHERE id=" + str(user_id))
    #         number_rows = int(bot.cursor.rowcount)
    #         if number_rows == 0:
    #             # User is not registered; do that now
    #             print("--Registered user " + str(user.name))
    #             bot.cursor.execute("INSERT INTO users (id, name, oauth) VALUES (" + str(user_id) + ", " + str(user.name) + ", " + str(0) + ")")
    #             bot.db.commit()
    #         ## Post status
    #         print("-Updated status")
    #         bot.cursor.execute("INSERT INTO statuses (userId, vendingId, comment) VALUES (" + str(user_id) + ", " + str(closest) + ", \"" + str(body) + "\")")
    #         bot.db.commit()
