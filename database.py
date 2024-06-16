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
with con:
 con.execute("""
     CREATE TABLE archive (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       path TEXT
     );
 """)
with con:
    con.execute("""
        CREATE TABLE image (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          archive_id INTEGER,
          path TEXT,
          FOREIGN KEY (archive_id) REFERENCES archive(id)
        );
    """)
with con:
    con.execute("""
        CREATE TABLE image_box (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          image_id INTEGER,
          x REAL,
          y REAL,
          w REAL,
          h REAL,
          object_class TEXT,
          FOREIGN KEY (image_id) REFERENCES image(id)
        );
    """)