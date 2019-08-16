 from flask import Flask, request, session, redirect
app = Flask(__name__)
app.config["SECRET_KEY"] = b'\x19VS\x8b5?\x11\xdf\x0e\x9e\xaf\x9c\x86A\t\x01'
    
#Database

import sqlite3
filename = 'data.sqlite'

def initialiseDatabase():
    conn = sqlite3.connect(filename)
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS Credentials (userID TEXT NOT NULL UNIQUE PRIMARY KEY, password TEXT NOT NULL, Name TEXT NOT NULL)')
    cur.execute('CREATE TABLE IF NOT EXISTS MovieInfo (imdbID TEXT NOT NULL UNIQUE PRIMARY KEY, Title TEXT NOT NULL, Year INTEGER, Rated TEXT, Runtime INTEGER, Genre TEXT, Director TEXT, Actors TEXT, Language TEXT, imdbRating REAL, Poster TEXT)')
    cur.execute('CREATE TABLE IF NOT EXISTS Watchlist (userID TEXT NOT NULL, imdbID TEXT NOT NULL, Watched INTEGER NOT NULL, UserRating REAL, UserReview TEXT, FOREIGN KEY(userID) REFERENCES Credentials(userID), FOREIGN KEY(imdbID) REFERENCES MovieInfo(imdbID), PRIMARY KEY (userID, imdbID))')
    conn.commit()
    conn.close()

def getUser(userID):
    conn = sqlite3.connect(filename)
    cur = conn.cursor()
    cur.execute('SELECT * FROM Credentials WHERE userID = ? ', [userID])

    row = cur.fetchone()
    conn.commit()
    conn.close()
    
    return row

def addUser(userID, password, Name):
    conn = sqlite3.connect(filename)
    cur = conn.cursor()
    cur.execute('SELECT userID FROM Credentials WHERE userID = ? ', [userID])
    row = cur.fetchone()
    
    if row is None:
        cur.execute('INSERT INTO Credentials (userID, password, Name) VALUES (?,?,?)', [userID,password,Name])
        result = True
    else:
        result = False
        
    conn.commit()
    conn.close()
    
    return result
    
def addMovieInfo(movie_info):
    headings = ['imdbID','Title','Year','Rated','Runtime','Genre','Director','Actors','Language','imdbRating','Poster']
    conn = sqlite3.connect(filename)
    cur = conn.cursor()
    cur.execute('SELECT imdbID FROM MovieInfo WHERE imdbID = ? ', [movie_info.get('imdbID')])

    row = cur.fetchone()
    if row is None:
        cur.execute('INSERT INTO MovieInfo (imdbID, Title, Year, Rated, Runtime, Genre, Director, Actors, Language, imdbRating, Poster) VALUES (?,?,?,?,?,?,?,?,?,?,?)', [movie_info.get(head) for head in headings])

    conn.commit()
    conn.close()
    
def addWatchlist(userID, imdbID, Watched=0, UserRating=None, UserReview=None):
    conn = sqlite3.connect(filename)
    cur = conn.cursor()
    
    cur.execute('SELECT * FROM Watchlist WHERE userID = ? AND imdbID = ?', [userID,imdbID])
    
    row = cur.fetchone()
    if row is None:
        cur.execute('INSERT INTO Watchlist (userID, imdbID, Watched, UserRating, UserReview) VALUES (?,?,?,?,?)', [userID,imdbID,Watched,UserRating,UserReview])
        result = 'Movie Added!'
    elif row[2] == 1:
        result = "You've already watched this movie."
    else:
        if Watched == 0:
            result = "Movie already in watchlist!"
        else:
            cur.execute('UPDATE Watchlist SET Watched = 1 WHERE userID = ? AND imdbID = ?', [userID,imdbID])
            result = 'Movie Added!'
        
    conn.commit()
    conn.close()
    
    return result
    
def getMovieInfo(imdbID):
    headings = ['imdbID','Title','Year','Rated','Runtime','Genre','Director','Actors','Language','imdbRating','Poster']
    conn = sqlite3.connect(filename)
    cur = conn.cursor()
    
    cur.execute('SELECT * FROM MovieInfo WHERE imdbID = ?',[imdbID])
    row = cur.fetchone()
    
    conn.commit()
    conn.close()
    
    movie_info = dict(zip(headings,row))
    
    return movie_info

def getWatchlist(userID):
    headings = ['userID', 'imdbID', 'Watched', 'UserRating', 'UserReview']
    conn = sqlite3.connect(filename)
    cur = conn.cursor()
    
    cur.execute('SELECT * FROM Watchlist WHERE userID = ?',[userID])
    row = cur.fetchall()
    
    conn.commit()
    conn.close()
    
    user_data = [dict(zip(headings,entry)) for entry in row]
    
    watchlist = [entry['imdbID'] for entry in user_data if entry['Watched'] == 0]
    watchedlist = [(entry['imdbID'],entry['UserRating'],entry['UserReview']) for entry in user_data if entry['Watched'] == 1]
    
    return watchlist,watchedlist

initialiseDatabase()

#Scraping/Preprocessing

import requests
import json

def getAPIKey(path='OMDBapi.json'):
    with open(path,'r') as file:
        key = json.load(file)
        omdbapi = key['OMDBapi']
    return omdbapi

def search_movie(title, year=None):
    url = 'http://www.omdbapi.com'
    params = {'t':title, 'type':'movie', 'y':year, 'apikey':omdbapi}
    result = requests.get(url, params=params)
    movie = json.loads(result.text)
    
    if movie['Response'] == 'False':
        return
    
    headings = ['imdbID','Title','Year','Rated','Runtime','Genre','Director','Actors','Language','imdbRating','Poster']
    movie_info = {head:movie[head] for head in headings if movie.get(head,'N/A')!='N/A'}
    
    if 'Year' in movie_info:
        movie_info['Year'] = int(movie_info['Year'])
        
    if 'Runtime' in movie_info:
        movie_info['Runtime'] = int(movie_info['Runtime'].split()[0])
    
    if 'imdbRating' in movie_info:
        movie_info['imdbRating'] = float(movie_info['imdbRating'])
    
    return movie_info

omdbapi = getAPIKey()

#Results

def createHeads(headings,caption=''):
    tableData = '\n<caption>'+ caption +'</caption>\n<tr>'
    for head in headings:
        tableData += '\n<th>' + head + '</th>'
    tableData += '\n</tr>'
    return tableData

def createRows(movie_info, headings):
    tableData = '\n<tr>'
    
    for head in movie_info:
        if movie_info[head] is None:
            movie_info[head] = ''
            
    for head in headings:
        tableData += '\n<td>' + str(movie_info.get(head,'')) + '</td>'
    tableData += '\n</tr>'
    return tableData

def showMovieInfo(movie_info):
    headings = ['imdbID','Title','Year','Rated','Runtime','Genre','Director','Actors','Language','imdbRating','Poster']
    tableData = createHeads(headings,caption='Movie Information')
    tableData += createRows(movie_info,headings)
    return tableData
        
def showWatchlist(watchlist):
    headings = ['imdbID','Title','Year','Rated','Runtime','Genre','Director','Actors','Language','imdbRating','Poster']
    tableData = createHeads(headings,caption='Watchlist')
    for imdbID in watchlist:
        movie_info = getMovieInfo(imdbID)
        tableData += createRows(movie_info,headings)
    return tableData
        
def showWatchedlist(watchedlist):
    headings = ['imdbID','Title','Year','Rated','Runtime','Genre','Director','Actors','Language','imdbRating','Poster','YourRating','YourReview']
    tableData = createHeads(headings,caption='Watchedlist')
    for imdbID, UserRating, UserReview in watchedlist:
        movie_info = getMovieInfo(imdbID)
        movie_info['YourRating'] = UserRating
        movie_info['YourReview'] = UserReview
        tableData += createRows(movie_info,headings)
    return tableData

def makeHTTP(inputs=[],outputs=[],buttons=[],links=[],tableData='',action='.',method='post'):
    menu = '<html>\n<style> table, th, td {border: 1px solid black;} </style>\n<body>\n<p>'+session.get('output','')+'</p>\n<table>'+ tableData +'\n</table>\n<form method="'+ method +'" action="'+ action +'">'
    for inp,intro in inputs:
        menu += '\n<p>'+ intro +' <input autocomplete="off" name="'+ inp +'"/></p>'
    for button in buttons:
        menu += '\n<p><input type="submit" name="action" value="'+ button +'"/></p>'
    for button,link in links:
        menu += '\n<p><a href='+ link +'><input type="button" name="action" value="'+ button +'"/></a></p>'
    menu += '\n</form>'
    for output in outputs:
        menu += '\n<p>'+output+'</p>'
    menu += '\n</body>\n</html>'
    session.pop('output',None)
    return menu

#UserHandle

@app.route("/Menu/Movies", methods=["GET", "POST"])
def browseMovies():
    userID = session.get('username')
    if userID is None:
        session['output'] = 'Login First!'
        return redirect('/')
    
    movie_info = session.get('movie',{})
    if request.method == "POST":
        
        links = [('Browse Other Movies','/Menu/Movies'), ('Main Menu','/Menu')]
        
        if request.form["action"] == "Submit":
            
            title = request.form["Title"]
            if title is not None:
                movie_info = search_movie(title)
                if 'movie' not in session:
                    session['movie'] = movie_info
                else:
                    session['movie'] = movie_info
                    session.modified = True
                    
                if movie_info is not None:
                    buttons = ['Add to Watchlist', 'Add to Watchedlist']
                    tableData = showMovieInfo(movie_info)
                    return makeHTTP(buttons=buttons,links=links,tableData=tableData,action='/Menu/Movies')
                
            return makeHTTP(inputs=[('Title','Enter Movie Title')],outputs=['Movie Not Found!!','Try Again!!'],buttons=['Submit'],links=[('Main Menu','/Menu')],action='/Menu/Movies')
            
        elif request.form["action"] == "Add to Watchlist":
            imdbID = movie_info.get('imdbID')
            addMovieInfo(movie_info)
            result = addWatchlist(userID, imdbID)
            tableData = showMovieInfo(movie_info)
            return makeHTTP(outputs=[result],links=links,tableData=tableData)
            
        elif request.form["action"] == "Add to Watchedlist":
            addMovieInfo(movie_info)
            tableData = showMovieInfo(movie_info)
            return makeHTTP(inputs=[('YourRating','Enter Your Rating'),('YourReview','Enter Your Review')],buttons=['Add'],tableData=tableData,action='/Menu/Movies')
        
        elif request.form["action"] == "Add":
            UserRating = request.form["YourRating"]
            UserReview = request.form["YourReview"]
            imdbID = movie_info.get('imdbID')
            result = addWatchlist(userID, imdbID, 1, UserRating, UserReview)
            tableData = showMovieInfo(movie_info)
            return makeHTTP(outputs=[result],links=links,tableData=tableData)
            
    return makeHTTP(inputs=[('Title','Enter Movie Title')],buttons=['Submit'],action='/Menu/Movies')

@app.route("/Menu", methods=["GET", "POST"])  
def showMenu():
    userID = session.get('username')
    if userID is None:
        session['output'] = 'Login First!'
        return redirect('/')
    
    buttons = ['Your Watchlist', 'Your Watchedlist']
    links = [('Browse Movies','/Menu/Movies'), ('Logout','/Logout')]
    session.pop('movie', None)
    
    if request.method == "POST":
        
        if request.form["action"] == "Your Watchlist":
            tableData = showWatchlist(getWatchlist(userID)[0])
            return makeHTTP(buttons=buttons[1:],links=links,tableData=tableData,action='/Menu')
            
        elif request.form["action"] == "Your Watchedlist":
            tableData = showWatchedlist(getWatchlist(userID)[1])
            return makeHTTP(buttons=buttons[:1],links=links,tableData=tableData,action='/Menu')
            
    return makeHTTP(buttons=buttons,links=links,action='/Menu')

@app.route("/Signup", methods=["GET", "POST"])
def Signup():
    userID = session.get('username')
    if userID is not None:
        session['output'] = 'Logout First!'
        return redirect('/Menu')
    
    inputs=[('Name','Name'),('userID','ID'),('password','Password')]
    
    if request.method == "POST":
        Name = request.form["Name"]
        userID = request.form["userID"]
        password = request.form["password"]
        
        if Name is not None and len(Name)>2:
            if password is not None and len(password)>4:
                if userID is not None and len(userID)>0 and getUser(userID) is None and addUser(userID,password,Name):
                    session['output'] = 'SignedUp Successfully!'
                    return redirect('/')
                    
                else:
                    output = 'Invalid ID!'
            else:
                output = 'Invalid Password!(At least 5 characters)'
        else:
            output = 'Invalid Name!'
        session['output'] = output
        return makeHTTP(inputs=inputs,buttons=['SignUp'],links=[('Home','/')],action='/Signup')
    
    return makeHTTP(inputs=inputs,buttons=['SignUp'],action='/Signup')

@app.route("/Login", methods=["GET", "POST"])
def Login():
    userID = session.get('username')
    if userID is not None:
        session['output'] = 'Logout First!'
        return redirect('/Menu')
    
    inputs=[('userID','ID'),('password','Password')]
    
    if request.method == "POST":
        userID = request.form["userID"]
        password = request.form["password"]
        if userID is not None:
            result = getUser(userID)
            if result is not None:
                if password is not None and password==result[1]:
                    session['username'] = userID
                    session['output'] = 'Welcome '+str(result[2])
                    return redirect('/Menu')
                
                else:
                    output = 'Incorrect Password!'
            else:
                output = 'Invalid ID!'
        else:
            output = 'Invalid ID!'
        session['output'] = output
        return makeHTTP(inputs=inputs,buttons=['Login'],links=[('Home','/')],action='/Login')
            
    return makeHTTP(inputs=inputs,buttons=['Login'],action='/Login')

@app.route("/Logout", methods=["GET", "POST"])
def Logout():
    userID = session.get('username')
    if userID is None:
        session['output'] = 'Login First!'
    else:
        session['output'] = 'Logged Out Successfully!'
    session.pop('username', None)
    return redirect('/')

@app.route("/", methods=["GET", "POST"])
def HomePage():
    userID = session.get('username')
    if userID is not None:
        session['output'] = 'Logout First!'
        return redirect('/Menu')
    links = [('Login','/Login'), ('Signup','/Signup')]
    return makeHTTP(links=links,method='get')

if __name__ == "__main__":
    app.run(host= '0.0.0.0', debug = False, port=80)