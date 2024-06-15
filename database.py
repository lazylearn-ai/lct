import sqlite3


con = sqlite3.connect('DataBase.db')
with con:
    con.execute("""
        CREATE TABLE video (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          start_path TEXT,
          end_path TEXT,
          date_uploaded TIMESTAMP
        );
    """)
with con:
    con.execute("""
        CREATE TABLE frame (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          video_id INTEGER,
          number_in_video INTEGER,
          FOREIGN KEY (video_id) REFERENCES video(id)
        );
    """)
with con:
    con.execute("""
        CREATE TABLE box (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          frame_id INTEGER,
          x1 REAL,
          y1 REAL,
          x2 REAL,
          y2 REAL,
          object_class TEXT,
          confidence REAL,
          FOREIGN KEY (frame_id) REFERENCES frame(id)
        );
    """)