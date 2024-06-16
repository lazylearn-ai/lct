import streamlit as st
from PIL import Image
from nn import predict_photos, predict_video
from uuid import uuid4
from models import Video
import os
from tempstorage import write_temp
import sqlite3
from analytics import confidence_distribution, count_by_class, create_timeline, create_danger_timeline, count_by_image, count_object, percent_area
import cv2


# приложение
pages = ["Загрузка фотографий", "Загрузка видео", "О приложении"]
page = st.sidebar.selectbox("Выберите страницу", pages)


if page == "Загрузка фотографий":
    st.title("Загрузка фотографий")
    uploaded_files = st.file_uploader("Выберите фотографию", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    if uploaded_files is not None and len(uploaded_files) > 0:
        proj_folder = f"runs/photos/{uuid4()}/source/"
        os.makedirs(proj_folder)
        for file in uploaded_files:
            img = Image.open(file)
            img.save(proj_folder + file.name)
        st.info("Начинаю обработку..")
        predictions_zipfile_path, archive_id = predict_photos(proj_folder) 
        with open(predictions_zipfile_path, "rb") as fp:
            btn = st.download_button(
                label="Скачать ZIP",
                data=fp,
                file_name="predictions.zip",
                mime="application/zip"
            )

        # построение графиков
        st.subheader("Количество изображений")
        st.write("Показывает количество снимков (в процентах), сгруппированных по количеству объектов на них.")
        g_class = count_by_image(archive_id) 
        st.plotly_chart(g_class, theme="streamlit", use_container_width=True)

        st.subheader("Количество изображений по классам")
        st.write("Показывает количество изображений по классам в числовом и процентном представлении.") 
        df_counts = count_object(archive_id)
        for row in df_counts.values:
            obj_class = row[0] 
            obj_count = row[1]
            obj_perc = row[2]

            col1, col2, col3 = st.columns(3)
            col1.metric("Класс", obj_class)
            col2.metric("Количество в численном виде", str(obj_count))
            col3.metric("Количество в процентном виде", str(obj_perc) + "%")

        st.subheader("Площадь объектов")
        st.write("График показывает минимальную, среднюю и максимальную площадь найденных объектов по классам.")
        g_perc = percent_area(archive_id) 
        st.plotly_chart(g_perc, theme="streamlit", use_container_width=True)
            

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
            st.video(video_bytes)


            # построение таймлайна
            st.subheader("Таймлайн (базовый)")
            st.write("Показывает основные моменты видео.") 
            timeline = create_timeline(videoEntity.id, fps)
            for row in timeline.values:
                obj_class = row[0] 
                first_appearance = row[1]
                last_appearance = row[2]
                diff = row[3]

                col1, col2, col3 = st.columns(3)
                col1.metric("Класс", obj_class, str(diff) + "c")
                col2.metric("Первое появление", str(first_appearance) + "с")
                col3.metric("Последнее появление", str(last_appearance) + "с")


            # построение таймлайна опасных объектов
            st.subheader("Таймлайн (опасные объекты)")
            st.write("Показывает ключевые моменты, на которых замечены объекты, представляющие угрозу.") 
            st.markdown("""
                        Атрибуты:
                        * chain_id - идентификатор строки
                        * start_sec - начало появления опасного объекта
                        * end_sec - конец появления опасного объекта
                        * min_confidence - минимальный confidence на временном отрезке
                        * max_confidence - максимальный confidence на временном отрезке
                        * avg_confidence - средний confidence на временном отрезке
                        """)
            timeline_copter = create_danger_timeline(videoEntity.id, fps, 'bpla_copter')
            timeline_plain = create_danger_timeline(videoEntity.id, fps, 'bpla_plain')
            st.markdown("**БПЛА коптерного типа**")
            st.table(timeline_copter)
            st.markdown("**БПЛА самолетного типа**")
            st.table(timeline_plain)

            # построение графиков
            g10, g100 = confidence_distribution(videoEntity.id)
            st.subheader("Распределение вероятности")
            st.write("График показывает количество распознанных объектов, сгруппированных по вероятности (confidence score).")
            tab10, tab100 = st.tabs(["Обычный", "Детальный"])
            with tab10:
                st.plotly_chart(g10, theme="streamlit", use_container_width=True)
            with tab100:
                st.plotly_chart(g100, theme="streamlit", use_container_width=True)

            st.subheader("Количество объектов")
            st.write("Показывает количество объектов каждого класса для каждой секунды видео.")
            g_class = count_by_class(videoEntity.id, fps) 
            st.plotly_chart(g_class, theme="streamlit", use_container_width=True)

elif page == "О приложении":
    st.title("О приложении")
    st.write("""
             Это приложение, которое позволяет выполнять детекцию беспилотных летательных аппаратов и других объектов 
             с помощью нейросети YOLO. Приложение сохраняет информацию о загружаемых фото и видео, проводит детекцию и аналитику.
             """)
    with open("Техническая документация.docx", "rb") as tfp:
        tbtn = st.download_button(
            label="Скачать техническую документацию",
            data=tfp,
            file_name="Техническая документация.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    with open("Руководство пользователя.docx", "rb") as ufp:
        ubtn = st.download_button(
            label="Скачать пользовательскую документацию",
            data=ufp,
            file_name="Руководство пользователя.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    st.divider()
    st.image("logo1.png")
    st.divider()

