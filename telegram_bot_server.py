from aiogram import Bot, Dispatcher, executor, types
from matplotlib import pyplot as plt
from multiprocessing import Event, Process
from PIL import Image
import face_recognition as face_rec
import numpy as np
import cv2 as cv
import datetime
import logging
import asyncio
import json
import io
import os


def bot_executor(update_event):
    API_TOKEN = '5211105284:AAFmQQB1w-lpW79hX6UrGtyN82Kkm5rF04U'
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=API_TOKEN)
    dp = Dispatcher(bot)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    @dp.message_handler(commands=['start', 'help'])
    async def send_welcome(message):
        await message.reply("Hi!\nSend me person photo and will tried to find it!")

    @dp.message_handler(content_types=['photo'])
    async def handle_docs_photo(message):
        print('new_photo')
        h = 500

        file_id = message.photo[-1].file_id
        user_id = message.from_user.id

        file_flow = await bot.download_file_by_id(file_id)
        file_io = io.BytesIO()
        file_io.write(file_flow.getvalue())
        file_img = Image.open(io.BytesIO(file_io.getvalue()),)
        np_img = np.array(file_img)[:, :, ::-1]  # bgr rgb
        np_img = cv.resize(
            np_img, (0, 0), fx=h/np_img.shape[1], fy=h/np_img.shape[1], interpolation=cv.INTER_LINEAR)

        with open('sessions.json', 'r') as f:
            js_file = json.load(f)

        for i in range(len(js_file)-1, -1, -1):
            if js_file[i]['id'] == user_id:
                os.remove(js_file[i]['path'])
                js_file.pop(i)

        encodings = face_rec.face_encodings(np_img)

        if encodings:
            count = len(encodings)

            msg = 'Face' if count == 1 else f'{count} faces'
            await message.reply(msg + ' detected')

            i = 1
            file_path = f'faceEncodings/faceEnc_{i}.npy'
            while os.path.exists(file_path):
                i += 1
                file_path = f'faceEncodings/faceEnc_{i}.npy'
            np.save(file_path, encodings[0])

            js_file.append({'id': user_id, 'path': file_path})
            with open('sessions.json', 'w') as f:
                json.dump(js_file, f)
        else:
            with open('sessions.json', 'w') as f:
                json.dump(js_file, f)

            await message.reply('No face detected')

        update_event.set()

    executor.start_polling(dp, skip_updates=True)


def face_finder(update_event):
    def get_face_dst(known_face_enc, unknown_face, face_location):
        unknown_face_enc = face_rec.face_encodings(unknown_face, face_location)
        if unknown_face_enc:
            return face_rec.face_distance([known_face_enc], unknown_face_enc[0])
        return [1]

    def update_sessions_data():
        with open('sessions.json', 'r') as f:
            sessions_data = json.load(f)
        for ind, session in enumerate(sessions_data):
            face_enc_path = session['path']
            np_enc = np.load(face_enc_path)
            sessions_data[ind]['enc'] = np_enc
        return sessions_data

    async def send_photo_msg(camera_name, location, to_id, img, accuracy):
        _, im_buf = cv.imencode(".jpg", img)
        byte_im = im_buf.tobytes()

        hms_time = str(datetime.datetime.now().time())[:-7]
        messange_text = f'Camera: {camera_name}\nTime: {hms_time}\nAccuracy: {accuracy}%'
        await bot.send_photo(to_id, byte_im, messange_text)
        await bot.send_location(to_id, *location)


    API_TOKEN = '5211105284:AAFmQQB1w-lpW79hX6UrGtyN82Kkm5rF04U'
    bot = Bot(token=API_TOKEN)
    h = 500

    cap = cv.VideoCapture(0)  # 'https://192.168.1.6:8080/video'
    cap_info = ['webCum-1',[55.800516, 37.402845]]
    captures = [[cap, cap_info]]
    print('cap done')
    sessions_data = update_sessions_data()

    while 1:
        if update_event.is_set():
            print('start updating')
            sessions_data = update_sessions_data()
            update_event.clear()

        for cap_data in captures:
            read, img = cap_data[0].read()
            if read:
                faces = face_rec.face_locations(img)
                for face in faces:
                    top, right, bottom, left = face
                    color = (128, 128, 128)
                    rectangle_width = 1
                    for ind, session in enumerate(sessions_data):
                        face_dst = get_face_dst(session['enc'], img, [face])[0]
                        accuracy = int((1-face_dst)*100)
                        print(face_dst)
                        if face_dst < 0.5:
                            color = (0, 0, 255)
                            rectangle_width = 2
                            face_img = img[top:bottom, left:right]
                            asyncio.run(send_photo_msg(
                                cap_data[1][0], cap_data[1][1], session['id'], face_img, accuracy))
                            with open('sessions.json', 'r') as f:
                                check_sessions_data = json.load(f)
                            
                            for ckeck_ind, sess in enumerate(check_sessions_data):
                                compare_ids = sess['id'] == session['id']
                                compare_paths = sess['path'] == session['path']
                                if all([compare_ids, compare_paths, os.path.exists(sess['path'])]):
                                    os.remove(session['path'])
                                    sessions_data.pop(ind)
                                    check_sessions_data.pop(ckeck_ind)
                            with open('sessions.json', 'w') as f:
                                json.dump(check_sessions_data, f)

                    cv.rectangle(img, (left, top), (right, bottom),
                                color, rectangle_width)
                cv.imshow('frame', img)

        if cv.waitKey(1) & 0xff == ord('q'):
            break
    cv.destroyAllWindows()


if __name__ == '__main__':

    update_event = Event()

    p1 = Process(target=face_finder, name='faces', args=[update_event])
    p2 = Process(target=bot_executor, name='bot', args=[update_event])

    p1.start()
    p2.start()

    p1.join()
    p2.kill()
    p2.join()
