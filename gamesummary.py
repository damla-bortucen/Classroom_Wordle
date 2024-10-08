import sqlite3
from sqlite3 import Error
from prettytable import PrettyTable

x = PrettyTable()


def create_db_connection():
    # create the database and return the handle
    conn = None
    try:
        conn = sqlite3.connect(".\\db\\gamedb.db",  check_same_thread=False)
    except Error as e:
        print(e)
    return conn

def create_game_tables(conn):
    # create the table to keep and store players and game scores
    PlayerTableSQL = """ CREATE TABLE players (
                                        id INTEGER PRIMARY KEY,
                                        name TEXT NOT NULL,
                                        ip_address TEXT
                                        ); """
    ScoreTableSQL = """ CREATE TABLE scores (
                                        id INTEGER PRIMARY KEY,
                                        player_id INTEGER NOT NULL,
                                        target_word TEXT,
                                        winloss INTEGER NOT NULL,
                                        score INTEGER,
                                        FOREIGN KEY (player_id)
                                            REFERENCES players(id)
    ); """

    DeletePlayersSQL = 'DROP TABLE IF EXISTS players'
    DeleteScoresSQL = 'DROP TABLE IF EXISTS scores'

    c = conn.cursor()
    c.execute(DeletePlayersSQL)
    c.execute(DeleteScoresSQL)
    c.execute(PlayerTableSQL)
    c.execute(ScoreTableSQL)

    c.close()


def insertplayer(conn, plyr, ipaddr):
    insertplayerSQL = """INSERT INTO players (name, ip_address)
                        VALUES (?, ?);"""
    checkif_in_tableSQL = """SELECT * FROM players 
                            WHERE name = ? AND ip_address = ?"""
        
    c = conn.cursor()

    alreadyin = c.execute(checkif_in_tableSQL, (plyr, ipaddr)).fetchall()

    if not alreadyin:
        c.execute(insertplayerSQL, (plyr,ipaddr))
        conn.commit()
    c.close()



def insertscore(conn, name, ipaddr, kw, game_wl, score):
    insertscoreSQL = """INSERT INTO scores (player_id, target_word, winloss, score)
                        VALUES (?, ?, ?, ?); """
    checkif_in_tableSQL = """SELECT * FROM scores 
                            WHERE player_id = ? AND target_word = ?"""
    
    c = conn.cursor()
    pl_id = c.execute("SELECT id FROM players WHERE name = ? and ip_address = ?;", (name, ipaddr)).fetchone()
    alreadyin = c.execute(checkif_in_tableSQL, (pl_id[0], kw)).fetchall()

    if not alreadyin:
        c.execute(insertscoreSQL, (pl_id[0], kw, game_wl, score))
        conn.commit()
    c.close()

def printresults(conn):
    ...

def showresults(conn):
    global x
    getscoresSQL = """SELECT players.name, COUNT(scores.winloss), SUM(scores.score) FROM players
                        LEFT JOIN scores ON players.id = scores.player_id
                        GROUP BY scores.player_id ;"""
    c = conn.cursor()
    c.execute(getscoresSQL)
    returnlist = c.fetchall()
    x.clear_rows()
    x.field_names = ["Player", "Games", "Score"]
    for i in returnlist:
        x.add_row([i[0], str(i[1]), str(int(i[2] or 0))])
    c.close()
    x.reversesort = True
    #print(x.get_string(sortby='Score'))
    return x.get_string(sortby='Score')

def initializedb():
    conn = create_db_connection()
    create_game_tables(conn)
    return conn
