import datetime


class Video:
    
    def __init__(self, start_path, end_path):
        self.start_path = start_path
        self.end_path = end_path
        self.date_uploaded = datetime.datetime.now()
    
    def save_to_db(self, con):
        with con:
            cur = con.cursor()
            cur.execute("INSERT INTO video (start_path, end_path, date_uploaded) VALUES (?, ?, ?)",
                       (self.start_path, self.end_path, self.date_uploaded))
            self.id = cur.lastrowid

class Frame:
    def __init__(self, video_id, number_in_video):
        self.video_id = video_id
        self.number_in_video = number_in_video
    
    def save_to_db(self, con):
        with con:
            cur = con.cursor()
            cur.execute("INSERT INTO frame (video_id, number_in_video) VALUES (?, ?)",
                       (self.video_id, self.number_in_video))
            self.id = cur.lastrowid

class Box:
    def __init__(self, frame_id, x1, y1, x2, y2, object_class, confidence):
        self.frame_id = frame_id
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.object_class = object_class
        self.confidence = str(confidence)
    
    def save_to_db(self, con):
        with con:
            cur = con.cursor()
            cur.execute("INSERT INTO box (frame_id, x1, y1, x2, y2, object_class, confidence) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (self.frame_id, self.x1, self.y1, self.x2, self.y2, self.object_class, self.confidence))
            self.id = cur.lastrowid


class Archive:
    
    def __init__(self, path):
        self.path = path

    def save_to_db(self, con):
        with con:
            cur = con.cursor()
            cur.execute("INSERT INTO video (path) VALUES (?)",
                       (self.path))
            self.id = cur.lastrowid

class Image:
    def __init__(self, archive_id, path):
        self.archive_id = archive_id
        self.path = path
    
    def save_to_db(self, con):
        with con:
            cur = con.cursor()
            cur.execute("INSERT INTO frame (archive_id, path) VALUES (?, ?)",
                       (self.archive_id, self.path))
            self.id = cur.lastrowid

class ImageBox:
    def __init__(self, image_id, x, y, w, h, object_class):
        self.image_id = image_id
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.object_class = object_class
    
    def save_to_db(self, con):
        with con:
            cur = con.cursor()
            cur.execute("INSERT INTO box (image_id, x, y, w, h, object_class) VALUES (?, ?, ?, ?, ?, ?)",
                       (self.image_id, self.x, self.y, self.w, self.h, self.object_class))
            self.id = cur.lastrowid