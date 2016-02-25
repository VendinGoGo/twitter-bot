import csv
import os

class Note:
    def __init__(self, databaseName="Note Database", fileName="Note.db", schema=[], startString="$start", endString="$end", nameString="$name", tables=[]):
        self.databaseName = databaseName
        if '.' not in fileName:
            # Assume .db if type not specified
            self.file = fileName + ".db"
        else:
            self.file = fileName
        self.schema = []
        for each in schema:
            self.schema.append(str(each))
        self.tables = tables
        self.startString = startString
        self.endString = endString
        self.nameString = nameString

        # Need schema enforcement
        # Need table name support
        # Need display table function
        # SELECT - extracts data from a database
        # UPDATE - updates data in a database
        # DELETE - deletes data from a database
        # INSERT INTO - inserts new data into a database
        # CREATE DATABASE - creates a new database
        # ALTER DATABASE - modifies a database
        # CREATE TABLE - creates a new table
        # ALTER TABLE - modifies a table
        # DROP TABLE - deletes a table
        # CREATE INDEX - creates an index (search key)
        # DROP INDEX - deletes an index

    def appendEntry(self, tableName, newEntry):
        # Determine which table is specified, and append the entry as follows
        pass
        # note.tables[i].append( newEntry )

    def appendTables(self, newTables):
        # Append multiple tables to our database
        # Simply add each table one-by-one
        for eachTable in newTables:
            self.appendTable(eachTable)

    def appendTable(self, newTable):
        # Add the table to our database
        self.tables.append(newTable)

    def displayDatabase(self):
        ## Prints all tables in the database
        # First print header, databaseName
        print("=" * (len(str(self.databaseName)) + 4))
        print("= " + self.databaseName + " =")
        print("=" * (len(str(self.databaseName)) + 4))
        # Now print each table of the database
        for i in range(0, len(self.tables)):
            print("") # For spacing
            self.displayTable(i)

    def displayTable(self, index=0):
        ## Print the table with clean spacing
        # First form array of rows with schema included
        rows = [self.schema]
        # Add actual table content
        for each in self.tables[index]:
            rows.append(each)

        ## Add underline beneath schema
        # Rotate rows to form columns array
        cols = []
        for index in range(len(self.schema)):
            column = []
            for eachRow in rows:
                column.append(eachRow[index])
            cols.append(column)
        # Calculate max length for each column in table
        max_lens = [len(str(max(i, key=lambda x: len(str(x))))) for i in cols]
        # Now hyphen lines of appropriate lengths
        hyphens = []
        for each in max_lens:
            hyphens.append("-"*each)
        # Now insert hyphens into rows
        rows.insert(1, hyphens)

        # Now format output and display
        for row in rows:
            print('|'.join('{0:{width}}'.format(x, width=y) for x, y in zip(row, max_lens)))

    def openNote(self):
        # First check if file exists
        if os.path.isfile(self.file):
            # File exists, load it in
            noteFile = open(self.file, 'r')
            reader = csv.reader(noteFile)
            lines = []
            for eachLine in reader:
                lines.append(eachLine)
            noteFile.close()

            # Read header
            self.databaseName = lines[0][0]

            # Read Schema
            self.schema = lines[4]

            # Find table start points
            startCount = 0
            starts = []
            endCount = 0
            for counter, eachLine in enumerate(lines):
                if self.startString in str(eachLine):
                    startCount += 1
                    starts.append(counter)
                if self.endString in str(eachLine):
                    endCount += 1
            if startCount != endCount:
                # Throw an error
                return
            # Read tables
            self.tables = []
            counter = 0
            lineCounter = 1
            line = ""
            while counter < startCount:
                for eachStartPoint in starts:
                    self.tables.append([])
                    line = lines[eachStartPoint + 1]
                    while self.endString not in str(line):
                        self.tables[counter].append(line)
                        # Get next line, breaking if it is the endString
                        lineCounter += 1
                        line = lines[eachStartPoint + lineCounter]
                    # increment counter for next table
                    counter += 1
                    # Reset lineCounter
                    lineCounter = 1

        else:
            # Print an error
            pass

    def saveNote(self):
        saveFile = open(self.file, 'w', newline='')
        writer = csv.writer(saveFile)
        ## Prepare array to write
        # Header
        rows = [
            [str(self.databaseName)],
            ["=" * len(str(self.databaseName))],
            ["Entry Schema"],
            ["-" * len(str("Entry Schema"))],
            self.schema,
            ["-" * (len(str(self.schema)) - 2 - (len(self.schema) - 1) - (len(self.schema) * 2))],
            ]
        '''
        Schema underline works by accounting for the removed characters in this order:
        String of schema - brackets around schema - spaces between elements - quotes around schema elements
        Which produces the equation: (len(str(self.schema)) - 2 - (len(self.schema) - 1) - (len(self.schema) * 2))
        '''
        # Iterate through 3 dimensional array
        for eachTable in self.tables:
            rows.append([str(self.startString)])
            for eachEntry in eachTable:
                rows.append(eachEntry)
            rows.append([str(self.endString)])

        # Write to file
        writer.writerows(rows)
        saveFile.close()

# Outside class definition

def test(testName, note, idealDatabaseName, idealSchema, idealTables):
    # Variables
    testsFailed = 0
    testsPassed = 0
    # Comparisons
    if str(note.databaseName) != idealDatabaseName:
        print("Test failed @ " + testName + ", databaseName")
        print("Should be: " + idealDatabaseName)
        print("Was: " + str(note.databaseName))
        testsFailed += 1
    else:
        testsPassed += 1

    if str(note.schema) != idealSchema:
        print("Test failed @ " + testName + ", schema")
        print("Should be: " + idealSchema)
        print("Was: " + str(note.schema))
        testsFailed += 1
    else:
        testsPassed += 1

    if str(note.tables) != idealTables:
        print("Test failed @ " + testName + ", tables")
        print("Should be: " + idealTables)
        print("Was: " + str(note.tables))
        testsFailed += 1
    else:
        testsPassed += 1
    # Print results of test
    print("Note." + testName + " test results:")
    print("Passed: " + str(testsPassed))
    print("Failed: " + str(testsFailed))
    # Return the counter for use in parent function
    return testsFailed


if __name__ == "__main__":
    ### Run tests
    ## Test openNote
    # Variables
    totalTestsFailed = 0
    testsFailed = 0
    testsPassed = 0
    # Configure
    note = Note(fileName="test\example_01.db")
    note.openNote()
    # Set expectations
    idealDatabaseName = "Database Name"
    idealSchema = "['Fields', 'Go', 'In', 'Here', 'As', 'Examples']"
    idealTables = "[[['Actual', 'Fields', 'Go', 'Here', 'In', 'Database'], ['Columns', 'These', 'can', 'be', 'anything', 'that'], ['you', 'would', 'want', 'your', 'database', 'to'], ['store', 'Including', 'python', 'objects', 'or', 'etc']], [['These', 'are', 'simply', 'CSV', 'formatted', 'rows']]]"
    # Print the database
    note.displayDatabase()
    # Run test
    totalTestsFailed += test("openNote", note, idealDatabaseName, idealSchema, idealTables)
    print("") # For spacing

    ## Test saveNote
    # Variables
    testsFailed = 0
    testsPassed = 0
    # Configure
    note = Note(databaseName="Example_02", fileName="test\example_02.db",
    schema=["1","2","3","4"])
    newTables = [[["test", 2, '4', "complete"]],[[1,2,3,4]]]
    note.tables = newTables
    note.saveNote()
    note = Note(fileName="test\example_02.db")
    note.openNote()
    # Set expectations
    idealDatabaseName = "Example_02"
    idealSchema = "['1', '2', '3', '4']"
    idealTables = "[[['test', '2', '4', 'complete']], [['1', '2', '3', '4']]]"
    # Print the database
    note.displayDatabase()
    # Run test
    totalTestsFailed += test("saveNote", note, idealDatabaseName, idealSchema, idealTables)
    print("") # For spacing

    ## Test appendTable
    # Variables
    testsPassed = 0
    testsFailed = 0
    # Configure
    note = Note(
        databaseName="Example_03",
        fileName="test\example_03.db",
        schema=[1,2],
        tables = [[[1,2], [3,4]]])
    note.saveNote()
    note.appendTable([[5,6], [7,8]])
    note.saveNote()
    note = Note(fileName="test\example_03.db")
    note.openNote()
    # Set expectations
    idealDatabaseName = "Example_03"
    idealSchema = "['1', '2']"
    idealTables = "[[['1', '2'], ['3', '4']], [['5', '6'], ['7', '8']]]"
    # Print the database
    note.displayDatabase()
    # Run test
    totalTestsFailed += test("appendTable", note, idealDatabaseName, idealSchema, idealTables)
    print("") # For spacing

    if totalTestsFailed == 0:
        print("\nAll tests passed.")
    else:
        print("\nTotal tests failed: " + str(totalTestsFailed))
