import sqlite3
import pandas as pd
import plotly.express as px


# таймлайн
def create_timeline(video_id, fps):
    conn = sqlite3.connect('DataBase.db')
    df = pd.read_sql(
    f"""
        SELECT 
          box.object_class, 
          CAST(MIN(frame.number_in_video) / {fps} AS INTEGER) AS first_appearance, 
          CAST(MAX(frame.number_in_video) / {fps} AS INTEGER) AS last_appearance,
          CAST(MAX(frame.number_in_video) / {fps} AS INTEGER) - CAST(MIN(frame.number_in_video) / 30 AS INTEGER) AS diff
        FROM 
          'frame' 
        JOIN 
          box ON frame.id = box.frame_id
        WHERE 
          frame.video_id = {video_id}
        GROUP BY 
          box.object_class
        ORDER BY 
          first_appearance;
    """, conn)
    return df


# распределение уверенности модели по данным
def confidence_distribution(video_id):
    con = sqlite3.connect('DataBase.db')
    query = f"""
        SELECT 
          CAST(confidence * %(round_value)s as INTEGER) AS confidence_level, 
          COUNT(*) AS count
        FROM 
          frame 
          JOIN box ON frame.id = box.frame_id
        WHERE 
          video_id = {video_id}
        GROUP BY 
          CAST(confidence * %(round_value)s as INTEGER)
        ORDER BY 
          confidence_level
        """
    
    df_10 = pd.read_sql(query % {"round_value" : "10"}, con)
    fig_10 = px.bar(df_10, x="confidence_level", y="count", color="count",
                   labels={'count': "Количество распознанных объектов", 
                          'confidence_level': "Округление (10%)"})
    
    df_100 = pd.read_sql(query % {"round_value" : "100"}, con)
    fig_100 = px.bar(df_100, x="confidence_level", y="count", color="count",
                   labels={'count': "Количество распознанных объектов", 
                          'confidence_level': "Округление (1%)"})
    
    return fig_10, fig_100


#Получение количества объектов каждого класса по кадрам:
def count_by_class(video_id):
    con = sqlite3.connect('DataBase.db')

    df = pd.read_sql(
        f"""
            WITH all_classes AS (
              SELECT 'bpla_copter' AS object_class 
              UNION ALL SELECT 'plain'
              UNION ALL SELECT 'helicopter'
              UNION ALL SELECT 'bird'
              UNION ALL SELECT 'bpla_plain' 
            )
            SELECT 'frame'.id as frame_id, ac.object_class, COALESCE(COUNT('box'.confidence), 0) as count_by_class
            FROM 'frame'
            CROSS JOIN all_classes ac
            LEFT JOIN 'box' ON 'frame'.id = 'box'.frame_id AND ac.object_class = 'box'.object_class
            WHERE 'frame'.video_id = {video_id}
            GROUP BY 'frame'.id, ac.object_class
        """, con)

    fig = px.line(df, x='frame_id', y='count_by_class', color='object_class', 
                  labels={'frame_id': "Кадр", 
                          'count_by_class': "Количество объектов",
                          'object_class': "Обозначения:"})
    return fig
