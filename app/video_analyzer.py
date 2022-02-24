import cv2 as cv
import face_recognition as face_rec
import math
import numpy as np
from tensorflow import keras


def remap(oldMin, oldMax, newMin, newMax, value):
    oldRange = (oldMax - oldMin)  
    newRange = (newMax - newMin)  
    return (((value - oldMin) * newRange) / oldRange) + newMin

def get_enc(img):
    return face_rec.face_encodings(img, [[0, img.shape[0], img.shape[1], 0]], model='large')[0]

def get_dst(p1, p2):
    return math.hypot(p1[0]-p2[0], p1[1]-p2[1])

def resize_to(img, target_h):
    return cv.resize(img, (0, 0), fx=target_h/img.shape[1], fy=target_h/img.shape[1])


def is_equal(known_enc, unknown_enc, tolerance=0.6):
    if [unknown_enc]:
        return face_rec.compare_faces([known_enc], unknown_enc, tolerance)[0]
    return False

def get_last_ind(face_data, face_center, face_h, last_frmae):  # need fix
    for ind in last_frmae:
        dst = get_dst(face_data[ind][3], face_center)
        if dst < 20:
            return ind
    return -1

def get_head_angle(face, model):
    face = cv.cvtColor(face, cv.COLOR_RGB2GRAY)
    face = cv.resize(face, (32, 32))
    face = np.array([face/255], dtype=np.float16)
    pred = model.predict(face)
    return pred[0][0]

def face_filter(face_data: list):
    groups = []
    while face_data:
        face_pattrn = face_data.pop(0)
        group = [face_pattrn]
        for ind in range(len(face_data)-1, -1, -1):
            if is_equal(face_pattrn[1], face_data[ind][1], 0.5):
                group.append(face_data.pop(ind))
        groups.append(group)
    return [sorted(group, key=lambda g: g[3])[0] for group in groups]

def search_in_video(video_path, search_data, setProgressBar):
    print('Launch main analyzer')
    video_h = 800
    face_h = 256
    video = cv.VideoCapture(video_path)
    read, frame = video.read()
    search_encs = [get_enc(img) for img in search_data]
    respose = [[] for _ in range(len(search_data))]  # [img, enc, angle] [parent_ind, img, enc, times]
    frames = []
    frames_locations = []
    print('Start video reading')
    while read:
        if frame.shape[1] > video_h:
            frame = resize_to(frame, video_h)
        frames.append(frame)
        read, frame = video.read()
        read, frame = video.read()
        read, frame = video.read()
        read, frame = video.read()
    setProgressBar(5)
    print('End reading, starting face computing, please whait...')
    for ind, frame in enumerate(frames):
        frames_locations.append(face_rec.face_locations(frame, model="cnn"))
        progress = ind/len(frames)
        setProgressBar(remap(0, 1, 5, 95, progress))

    print('Starting encoding')
    model = keras.models.load_model('head_position_tf.h5')

    for farme_ind, locations in enumerate(frames_locations):

        for location in locations:
            top, right, bottom, left = location
            face = frames[farme_ind][top:bottom, left:right]
            face_enc = get_enc(face)
            face_angle = get_head_angle(face, model)
            if face.shape[1] > face_h:
                face = resize_to(face, face_h)
            
            for i in range(len(search_encs)-1,-1 , -1):
                if is_equal(search_encs[i], face_enc):
                    if respose[i]:
                        if respose[i][2]<face_angle:
                            respose[i] = [face, face_enc, face_angle]
                    else:
                        respose[i] = [face, face_enc, face_angle]

        progress = farme_ind/len(frames)
        setProgressBar(remap(0, 1, 95, 100, progress))

        if cv.waitKey(1) & 0xff == ord('q'):
            break
    del model
    cv.destroyAllWindows()
    respose = [resp[0] for resp in respose if resp]
    return respose

def analyze_video(video_path, setProgressBar):
    video = cv.VideoCapture(video_path)
    video_h = 320
    f_count = int(video.get(cv.CAP_PROP_FRAME_COUNT))
    frame_split = 4
    frames_data = [] # [[enc, loc], ]

    read, frame = video.read()
    scale_kff = min(video_h/frame.shape[0], 1)
    setProgressBar(3)
    while read:
        frame = cv.resize(frame, (0, 0), fx=scale_kff, fy=scale_kff)
        frame = frame[:,:,::-1] # rgb
        locations = face_rec.face_locations(frame, model="cnn")
        encodings = face_rec.face_encodings(frame, locations)
        frame_data = []
        frame_data = [[encodings[i], locations[i]] for i in range(len(encodings))]
        frames_data.append(frame_data)
        for _ in range(frame_split):
            read, frame = video.read()
        progress = frame_split*len(frames_data)/f_count
        print(len(frames_data), 'of', int(f_count/frame_split))
        setProgressBar(remap(0, 1, 3, 60, progress))
    video.release()

    model = keras.models.load_model('head_position_tf.h5')
    print('model created')
    video = cv.VideoCapture(video_path)

    read, frame = video.read()
    for ind, frame_data in enumerate(frames_data):
        if not(read):
            print('reading error')
            break
        frame = cv.resize(frame, (0, 0), fx=scale_kff, fy=scale_kff)
        for i, [enc, loc] in enumerate(frame_data):
            top, right, bottom, left = loc
            face = frame[top:bottom, left:right]
            angle = get_head_angle(face, model)
            frames_data[ind][i].append(angle)
        for _ in range(frame_split):
            read, frame = video.read()
        progress = ind/f_count
        setProgressBar(remap(0, 1, 60, 80, progress))
    video.release()
    del model


    buffer_faces = []# [frameind, enc, location, angle, buffer_rate]
    result_faces = []

    for frame_ind, frame_data in enumerate(frames_data):
        for enc, loc, ang in frame_data:
            is_new = True
            for buffer_ind, buffer_face in enumerate(buffer_faces):
                if is_equal(buffer_face[1], enc, tolerance=0.65):
                    is_new = False
                    if buffer_face[3] < ang:
                        buffer_faces[buffer_ind] = [frame_ind, enc, loc, ang, 5]
                    else:
                        buffer_faces[buffer_ind][4] = 5
                    break
            if is_new:
                buffer_faces.append([frame_ind, enc, loc, ang, 5])

        del_inds = []
        for buffer_ind, buffer_face in enumerate(buffer_faces):
            buffer_faces[buffer_ind][4] -= 1
            if buffer_faces[buffer_ind][4] == 0:
                del_inds.append(buffer_ind)
        for del_ind in del_inds[::-1]:
            result_faces.append(buffer_faces.pop(del_ind))

        progress = frame_ind/f_count
        setProgressBar(remap(0, 1, 80, 90, progress))

    result_faces += buffer_faces
    print('before filtering', len(result_faces))
    result_faces = sorted(face_filter(result_faces), key=lambda f: f[0])
    print('after filtering', len(result_faces))

    result_imgs = []
    video = cv.VideoCapture(video_path)
    read, frame = video.read()
    for frame_ind, frame_data in enumerate(frames_data):
        if not(read):
            print('reading error')
            break
        while True:
            if not(result_faces):
                break
            if frame_ind == result_faces[0][0]:
                location = result_faces.pop(0)[2]
                top, right, bottom, left = [int(i/scale_kff) for i in location]
                face = frame[top:bottom, left:right]
                result_imgs.append(face)
            else:
                break
        if not(result_faces):
                break
        for _ in range(frame_split):
            read, frame = video.read()
        
        progress = frame_ind/f_count
        setProgressBar(remap(0, 1, 90, 97, progress))
    video.release()
    return result_imgs


def search_in_photos(photos, search_data, setProgressBar):
    result = []
    photos = [[get_enc(p), p] for p in photos]
    search_data = [[get_enc(p), p] for p in search_data]
    setProgressBar(5)
    for i, s in enumerate(search_data):
        for p in photos:
            if is_equal(s[0], p[0], 0.55):
                result.append(p[1])
        progress = i/len(search_data)
        setProgressBar(remap(0, 1, 5, 100, progress))
    return result
