import streamlit as st
from PIL import Image
from nn import predict_photos, predict_video
from uuid import uuid4
from models import Video
import os
from tempstorage import write_temp
import sqlite3
from analytics import confidence_distribution, count_by_class, create_timeline
import cv2


# приложение
pages = ["Загрузка фотографии", "Загрузка видео", "О приложении"]
page = st.sidebar.selectbox("Выберите страницу", pages)


if page == "Загрузка фотографии":
    st.title("Загрузка фотографии")
    uploaded_files = st.file_uploader("Выберите фотографию", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    if uploaded_files is not None and len(uploaded_files) > 0:
        proj_folder = f"runs/photos/{uuid4()}/source/"
        os.makedirs(proj_folder)
        for file in uploaded_files:
            img = Image.open(file)
            img.save(proj_folder + file.name)
        st.info("Начинаю обработку..")
        predictions_zipfile_path = predict_photos(proj_folder)
        with open(predictions_zipfile_path, "rb") as fp:
            btn = st.download_button(
                label="Download ZIP",
                data=fp,
                file_name="predictions.zip",
                mime="application/zip"
            )

elif page == "Загрузка видео":
    st.title("Загрузка видео")
    uploaded_file = st.file_uploader("Выберите видео", type=["mp4", "avi", "mov"])
    if st.button("Начать детекцию", type="primary"):
        if uploaded_file is None:
            st.info("Выберите файл!")
        else:
            st.info("Начинаю обработку..")
            proj_folder = f"runs/videos/{uuid4()}/"
            os.makedirs(proj_folder)
            file_bytes = uploaded_file.getvalue()


            # инициализация путей
            source_video_path = proj_folder + "source.mp4"
            predicted_video = proj_folder + "predicted.mp4"

            # сохранение исходного видео
            with open(source_video_path, "wb") as f:
                f.write(file_bytes)

            # получение количества кадров в секунду
            cap = cv2.VideoCapture(source_video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            videoEntity = Video(
                start_path=source_video_path,
                end_path=predicted_video
            )
            con = sqlite3.connect('DataBase.db')
            videoEntity.save_to_db(con)
            write_temp(str(videoEntity.id))

            # детекция видео 
            predicted_video_cvformat = predict_video(source_video_path)

            # перекодировка
            os.system(f"ffmpeg -i {predicted_video_cvformat} -vcodec libx264 {predicted_video}")

            # отрисовка
            video_file = open(predicted_video, 'rb')
            video_bytes = video_file.read()
            st.video(video_bytes, use_container_width=True)

            # построение таймлайна
            st.subheader("Таймлайн")
            st.write()
            timeline = create_timeline(videoEntity.id, fps)
            for row in timeline.values:
                obj_class = row[0]
                first_appearance = row[1]
                last_appearance = row[2]
                diff = row[3]

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Класс", obj_class)
                col2.metric("Первое появление", str(first_appearance) + "с")
                col3.metric("Последнее появление", str(last_appearance) + "с")
                col4.metric("Длина участка видеоряда", str(diff) + "c")

            # построение графиков
            g10, g100 = confidence_distribution(videoEntity.id)
            st.subheader("Распределение вероятности")
            st.write("График показывает количество распознанных объектов, сгруппированных по вероятности (confidence score).")
            tab10, tab100 = st.tabs(["Обычный", "Детальный"])
            with tab10:
                st.plotly_chart(g10, theme="streamlit", use_container_width=True)
            with tab100:
                st.plotly_chart(g100, theme="streamlit", use_container_width=True)

            g_class = count_by_class(videoEntity.id)
            st.subheader("Название")
            st.write("О чем")
            st.plotly_chart(g_class, theme="streamlit", use_container_width=True)

elif page == "О приложении":
    st.title("О приложении")
    st.write("""
             Это приложение, которое позволяет выполнять детекцию беспилотных летательных аппаратов и других объектов 
             с помощью нейросети YOLO. Приложение сохраняет информацию о загружаемых видео, проводит детекцию и аналитику.
             """)
