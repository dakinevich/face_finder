import eel
import os
from tkinter import filedialog, Tk
import cv2 as cv
import base64
import face_recognition as face_rec
import cv2 as cv
from video_analyzer import analyze_video, search_in_video, resize_to, search_in_photos

eel.init('web')

def getHtmlSrc(img):
    retval, buffer = cv.imencode('.jpg', img)
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/jpeg;base64, {img_base64}"

def getMinInd(data):
    keys = list(data.keys())
    ind = 0
    while 1:
        if ind not in keys:
            return ind
        ind+=1

def setProgressBar(persent):
     eel.setProgress(persent)

@eel.expose
def saveFaces():
    if last_faces:
        root = Tk()
        root.withdraw()
        root.wm_attributes('-topmost', 1) # without that it wil go behind all others apps
        path = filedialog.askdirectory(parent=root, 
            initialdir=os.getcwd(),
            title="Pick folder")
        if path:
            for last_face in last_faces:
                i = 1
                while os.path.exists(f'{path}/face-{i}.jpeg'):
                    i+=1
                cv.imwrite(f'{path}/face-{i}.jpeg', last_face)
    else:
        eel.alertMsg('No faces to save')

@eel.expose
def getFirstFrame():
    global video_path
    global mode
    root = Tk()
    root.withdraw()
    root.wm_attributes('-topmost', 1) # without that it wil go behind all others apps
    path = filedialog.askopenfilename(parent=root,
        initialdir=os.getcwd(),
        title = "Pick the video",
        filetypes = (("Video files", ".mp4"),
        ("Video files", ".flv"),
        ("Video files", ".avi"),
        ("Video files", ".mkv")))
    if path:
        mode = "video"
        video_path = path
        cap = cv.VideoCapture(path)
        read, frame = cap.read()
        cap.release()
        return getHtmlSrc(frame)
    return ''

@eel.expose
def getFaces():
    global faces
    face_h = 256
    root = Tk()
    root.withdraw()
    root.wm_attributes('-topmost', 1) # without that it wil go behind all others apps
    paths = filedialog.askopenfilename(parent=root,
        initialdir=os.getcwd(),
        title = "Pick the faces",
        filetypes = (("image files",".jpg"),
        ("image files", ".png"),
        ("image files", ".jpeg")),
        multiple = True)
    if paths:
        inds = []
        bases64 = []
        alerted = False
        for path in paths:
            img = cv.imread(path)
            if img.shape[1] > face_h:
                img = resize_to(img, face_h)
            locations = face_rec.face_locations(img)
            if locations:
                for location in locations:
                    top, right, bottom, left = location
                    face = img[top:bottom, left:right]
                    ind = getMinInd(faces)
                    faces[ind] = face
                    inds.append(ind)
                    bases64.append(getHtmlSrc(face))
            elif not(alerted):
                eel.alertMsg('Need at least one face on photo')
                alerted = True
        return inds, bases64
    return -1, ''

@eel.expose
def getPatterns():
    global patterns
    global mode
    face_h = 256
    root = Tk()
    root.withdraw()
    root.wm_attributes('-topmost', 1) # without that it wil go behind all others apps
    paths = filedialog.askopenfilename(parent=root,
        initialdir=os.getcwd(),
        title = "Pick the pattern face",
        filetypes = (("image files",".jpg"),
        ("image files", ".png"),
        ("image files", ".jpeg")),
        multiple = True)
    if paths:
        inds = []
        bases64 = []
        alerted = False
        mode = 'photo'
        for path in paths:
            img = cv.imread(path)
            if img.shape[1] > face_h:
                img = resize_to(img, face_h)
            locations = face_rec.face_locations(img)
            if locations:
                for location in locations:
                    top, right, bottom, left = location
                    pattern = img[top:bottom, left:right]
                    ind = getMinInd(patterns)
                    patterns[ind] = pattern
                    inds.append(ind)
                    bases64.append(getHtmlSrc(pattern))
            elif not(alerted):
                eel.alertMsg('Need at least one face on photo')
                alerted = True
        return inds, bases64
    return -1, ''

@eel.expose
def removeById(id):
    global faces
    global patterns
    pref, id = id.split('-')
    ind = int(id)
    if pref == 'face':
        if ind in list(faces.keys()):
            faces.pop(ind)
    elif pref == 'pattern':
        if ind in list(patterns.keys()):
            patterns.pop(ind)

@eel.expose
def DOM_update():
    global faces
    global video_path
    global last_faces
    global mode
    global patterns
    inds = []
    pattern_inds = []
    bases64 = []
    pattern64 = []
    results = [getHtmlSrc(i) for i in last_faces]
    base64frame_src = ''
    for key, value in faces.items():
        img = value
        ind =key
        faces[ind] = img
        inds.append(ind)
        bases64.append(getHtmlSrc(img))
    if mode == 'video':
        if video_path:
            cap = cv.VideoCapture(video_path)
            read, frame = cap.read()
            cap.release()
            base64frame_src = getHtmlSrc(frame)
        return inds, bases64, base64frame_src, results
    else:
        for key, value in patterns.items():
            img = value
            ind =key
            patterns[ind] = img
            pattern_inds.append(ind)
            pattern64.append(getHtmlSrc(img))
        return inds, bases64, [pattern_inds, pattern64], results
    
    

@eel.expose
def analyze():
    global faces, video_path, last_faces, mode
    if mode == "video":
        if video_path:
            print("running recognition")
            setProgressBar(0)
            if faces.items():
                fd = search_in_video(video_path, faces.values(), setProgressBar)
            else:
                fd = analyze_video(video_path, setProgressBar)
            last_faces = fd
            imgs = fd
            setProgressBar(100)
            [eel.setNewResult(getHtmlSrc(img)) for img in imgs]
        else:
            eel.alertMsg('No video input')
    elif mode == "photo":
        if faces.items() and patterns.items():
            setProgressBar(0)
            fd = search_in_photos(patterns.values(), faces.values(), setProgressBar)
            last_faces = fd
            imgs = last_faces
            setProgressBar(100)
            print("photo mode processed")
            [eel.setNewResult(getHtmlSrc(img)) for img in imgs]
        else:
            eel.alertMsg('Need face photos to analyze')
    eel.makeEnable()

mode = 'video'
last_faces = []
patterns = dict()
faces = dict() #{id: face}
video_path = ""
eel.start('index.html') #, size=(1000, 500))
