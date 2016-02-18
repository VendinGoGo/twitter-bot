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

    def load_mentions(self, user="VendinGoGo"):
        # Generate query
        query = "@" + user # "@VendinGoGo" by default
        # Load mentions
        mentions = self.api.search(q=query)
        # Iterate through
        for tweet in mentions:
            user = str(tweet.user.screen_name) #.encode('utf8'))
            text = str(tweet.text) #.encode('utf8'))
            print(user + " >> " + text)

if __name__ == "__main__":
    # Create a bot
    bot = Bot()

    # Load mentions
    bot.load_mentions()