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


# расширенный таймлайн опасных объектов
def create_danger_timeline(video_id, fps, danger_class):
    conn = sqlite3.connect('DataBase.db')
    df = pd.read_sql(
    f"""
       WITH numbered_frames AS (
          SELECT 
            number_in_video,
            LEAD(number_in_video, 1, 0) OVER (ORDER BY number_in_video) - number_in_video AS diff,
            SUM(CASE WHEN diff > {fps} THEN 1 ELSE 0 END) OVER (ORDER BY number_in_video) AS chain_id,
            confidence
          FROM (
            SELECT 
              number_in_video,
              LEAD(number_in_video, 1, 0) OVER (ORDER BY number_in_video) - number_in_video AS diff,
              b.confidence
            FROM frame f
            JOIN box b ON f.id = b.frame_id
            WHERE b.object_class = '{danger_class}' AND f.video_id = {video_id}
          ) subquery
        ),
        grouped_chains AS (
          SELECT 
            chain_id,
            MIN(number_in_video) AS min_number_in_video,
            MAX(number_in_video) AS max_number_in_video,
            MIN(confidence) AS min_confidence,
            MAX(confidence) AS max_confidence,
            AVG(confidence) AS avg_confidence
          FROM numbered_frames                     
          GROUP BY chain_id
          HAVING MIN(number_in_video) IS NOT NULL
        )
        SELECT 
          chain_id,
          CAST(min_number_in_video / {fps} AS INTEGER) as start_sec,
          CAST(max_number_in_video / {fps} AS INTEGER) as end_sec,
          min_confidence,
          max_confidence,
          avg_confidence
        FROM grouped_chains
        ORDER BY chain_id;
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


#Получение количества объектов каждого класса для групп из n кадров
def count_by_class(video_id, n):
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
            SELECT CAST(frame_id / {n} AS INTEGER) AS num_n_frames, object_class, avg(count_by_class) AS count_by_class
            FROM (
              SELECT frame.id as frame_id, ac.object_class, COALESCE(COUNT(box.confidence), 0) AS count_by_class
              FROM frame
              CROSS JOIN all_classes ac
              LEFT JOIN box ON frame.id = box.frame_id AND ac.object_class = box.object_class
              WHERE frame.video_id = {video_id}
              GROUP BY frame.id, ac.object_class) subquery
            GROUP BY CAST(frame_id / {n} AS INTEGER), object_class
        """, con)

    fig = px.line(df, x='num_n_frames', y='count_by_class', color='object_class', 
                  labels={'num_n_frames': f"Номер группы из {n} кадров", 
                          'count_by_class': "Среднее количество объектов в группе кадров",
                          'object_class': "Обозначения:"})
    return fig
