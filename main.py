import tweepy
import yaml
import MySQLdb
from geopy.distance import vincenty
import logging
from logging.handlers import TimedRotatingFileHandler
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

        ## Configure bot
        # Configure database
        self.configure_db(tokens['host'], tokens['user'], tokens['password'], tokens['database'])
        # Configure Twitter
        self.configure_twitter()

    def start_twitter(self):
        # Begin twitter stream by passing self.query to stream.filter
        self.stream.filter(track=[self.query])

    def configure_twitter(self, query="@VendinGoGo"):
        # Configure twtter stream on a given search query
        self.stream_listener = MyStreamListener()
        self.stream_listener.set_parent(self)
        self.stream = tweepy.Stream(auth=self.auth, listener=self.stream_listener)
        self.query = query

    def configure_db(self, host="localhost", user="appuser", password="password", database="vending"):
        # Connect to database
        self.db = MySQLdb.connect(host=host, user=user, passwd=password, db=database)
        # Set cursor
        self.cursor = self.db.cursor()

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
        logger.info(str(status.user.screen_name) + ": " + str(status.text))

        # Filter out tweets not containing location data
        location_info = None
        if status.place:
            logger.info("-place exists")
            try:
                if len(status.place) > 0:
                    location_info = "place"
            except:
                logger.info("--place is empty")
        if status.coordinates:
            logger.info("-Coordinates exists")
            try:
                if len(status.coordinates) > 0:
                    location_info = "coordinates"
            except:
                logger.info("--coordinates are empty")
        if not location_info:
            logger.warn("-No location information found")

        # Gather most accurate location of tweet available
        tweet_location = None
        if location_info == "place":
            ## Bounding box, calculate middle of region
            # Convert place from string to list
            status.place = ast.literal_eval(status.place)
            # Calculate average of every index across the list and convert to tuple
            tweet_location = tuple(x for x in [sum(y) / len(y) for y in zip(*status.place[0])])
        else:
            logger.info("-No place found")
        if location_info == "coordinates":
            if len(status.coordinates) > 0:
                # Most precise location
                tweet_location = (status.coordinates['coordinates'][0], status.coordinates['coordinates'][1])
            else:
                logger.info("-No coordinates found")
        else:
            logger.warn("-No coordinates found")

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
                logger.info("-Found closer vending machine:" + str(closest))

        # If a vending machine was found close enough
        if closest:
            # Log to console
            logger.info("-We found a closest machine!")
            logger.info("--Vending machine id: " + str(closest))

            ### Write a status update for it
            ## Get body text and remove unwanted characters
            body = re.sub('@VendinGoGo', '', status.text)
            for x in ['\'', '\"']: # Protect from SQL injection
                body = re.sub(x, '', body)
            logger.info("--Status content: " + body)

            ## Get user ID of poster
            user = self.parent.api.get_user(screen_name=status.user.screen_name)
            user_id = user.id

            ## Check if they are registered with us
            # Execute SQL statement
            self.parent.cursor.execute("SELECT * FROM users WHERE id=" + str(user_id))
            number_rows = int(self.parent.cursor.rowcount)
            if number_rows == 0:
                # User is not registered; do that now
                logger.info("--Registered user " + str(user.name))
                self.parent.cursor.execute("INSERT INTO users (id, name, oauth) VALUES (" + str(user_id) + ", " + str(user.name) + ", " + str(0) + ")")
                self.parent.db.commit()

            ## Post status
            logger.info("-Updated status")
            self.parent.cursor.execute("INSERT INTO statuses (userId, vendingId, comment) VALUES (" + str(user_id) + ", " + str(closest) + ", \"" + str(body) + "\")")
            self.parent.db.commit()
        else:
            # Was not close enough to a vending location
            logger.warn("-Was not near a vending machine")

    def on_error(self, status_code):
        if status_code == 420:
            #returning False in on_data disconnects the stream
            return False

def create_timed_rotating_log(path):
    # Create logger
    logger = logging.getLogger("Rotating Log")
    logger.setLevel(logging.INFO)

    # Create formatter
    logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s] %(message)s")

    # Rotating file handler
    fileHandler = TimedRotatingFileHandler(path, when="midnight", interval=1, backupCount=5)
    fileHandler.setFormatter(logFormatter)
    logger.addHandler(fileHandler)

    # Console output handler
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    logger.addHandler(consoleHandler)

    return logger

if __name__ == "__main__":
    # Create a log file
    log_file = "logs/twitterbot.log"
    logger = create_timed_rotating_log(log_file)

    # Create a bot
    bot = Bot()

    # Start Twitter Stream
    bot.start_twitter()
