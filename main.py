from fastapi import FastAPI, UploadFile, File, Response, Request, WebSocket
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from time import strftime, gmtime

import os, shutil, math, requests, cv2, numpy as np, dlib, json

app = FastAPI()

templates = Jinja2Templates(directory="templates")

camera = cv2.VideoCapture(0)

takePicRequest = False
recentPicTaken = ""

@app.websocket("/ws")
async def get_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            success, frame = camera.read()
            try:
                gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
                faces = face_cascade.detectMultiScale(gray, 1.3, 7)
                count = 0
                for (x, y, w, h) in faces :
                    cv2.rectangle(frame,(x,y),(x+w,y+h),(255,255,0),2)
                    count += 1
                    cv2.putText(frame, str(count) , (x, y - 10), cv2.FONT_HERSHEY_DUPLEX, 0.9, (0, 0, 255), 2)
            except:
                pass
            if not success:
                break
            else:
                ret, buffer = cv2.imencode('.jpg', frame)
                await websocket.send_text("some text")
                await websocket.send_bytes(buffer.tobytes())
    except WebSocketDisconnect:
        print("Client disconnected") 

@app.websocket("/pic")
async def get_stream(websocket: WebSocket):
    global takePicRequest, recentPicTaken
    await websocket.accept()
    try:
        while True:
            success, frame = camera.read()
            if not success:
                break
            else:
                if takePicRequest:
                    takePicRequest = False
                    timeNow = strftime("%d-%b-%y.%H-%M-%S", gmtime())
                    cv2.imwrite(f"images/{timeNow}.png", frame)
                    recentPicTaken = timeNow+".png"
                ret, buffer = cv2.imencode('.jpg', frame)
                await websocket.send_text("some text")
                await websocket.send_bytes(buffer.tobytes())
    except WebSocketDisconnect:
        print("Client disconnected")    

@app.get('/')
def index(request : Request):
    return templates.TemplateResponse("index.html", context={"request" : request})

@app.get('/live')
def live(request : Request):
    return templates.TemplateResponse('live.html', context={"request" : request})

@app.get('/takepic')
def pic(request : Request):
    return templates.TemplateResponse('takepic.html', context={"request" : request})

@app.post('/takepic')
def savepic():
    global takePicRequest
    takePicRequest = True
    WebSocket.close()
    return RedirectResponse(url="/takepic")

@app.get('/result')
def result():
    global recentPicTaken

    filename = recentPicTaken

    filenamesInImages = os.listdir("./")
    while filename.split("/")[-1] in filenamesInImages:
        filename = f"api-{timeNow}-{count}.png"
        count += 1

    # Save the image that is sent from the request and reject if filename is not valid
    with open(filename, "wb") as f:
        if file.filename.split(".")[-1].lower() not in ["jpg", "png", "jpeg", "heif"]:
            return {"faceDetected": "No Face Detected", "confidence": "0%", "error-status": 0, "error-message": "Filename not supported"}
        shutil.copyfileobj(file.file, f)

    # Read image as cv2
    frame = cv2.imread(f"api-{timeNow}.png")

    try:
        if filename == None:
            return {"faceDetected": "No Face Detected", "confidence": "0%", "match-status": False, "error-status": 0, "error-message": "Not a valid filename"}
    except ValueError:
        pass

    # Read recently grabbed image to cv2
    img = cv2.imread(filename)

     # Convert into grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Load the cascade
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    
    # Detect faces
    faces = face_cascade.detectMultiScale3(gray, 1.1, 5, outputRejectLevels = True)
    try :
        face_detected = list(faces[0].tolist())
        weights = list(faces[2].tolist())
        updated_weights = weights.copy()
    
        # Deleting faces that under 50% confidence
        for i in range(len(weights)) :
            if weights[i] < 5 :
                face_detected.pop(i)
                updated_weights.pop(i)
        weights_json = {}
        count = 1
        for i in updated_weights :
            i = '{:.2f}'.format(i*10)
            weights_json[count] = i+"%"
            count += 1
        os.remove(filename)
        return {"face-count" : len(face_detected), "confidence" : weights_json}
    except :
        os.remove(filename)
        return {"face-count" : 0, "confidence" : "0%", "error-code" : "No face detected"}
    else:
        os.remove(filename)
        return {"face-count" : 0, "confidence" : "0%", "error-code" : "Something happened :("}

# API (Methods = POST)
@app.post('/api')
def api(file : UploadFile = File(...)):

    # Get time now for filename
    timeNow = strftime("%d-%b-%y.%H-%M-%S", gmtime())
    filename = f"api-{timeNow}.png"

    # In case any file currently processed have the same
    # filename, to anticipate error rename the file
    filenamesInImages = os.listdir("./")
    while filename.split("/")[-1] in filenamesInImages:
        filename = f"api-{timeNow}-{count}.png"
        count += 1

    # Save the image that is sent from the request and reject if filename is not valid
    with open(filename, "wb") as f:
        if file.filename.split(".")[-1].lower() not in ["jpg", "png", "jpeg", "heif"]:
            return {"faceDetected": "No Face Detected", "confidence": "0%", "error-status": 0, "error-message": "Filename not supported"}
        shutil.copyfileobj(file.file, f)

    # Read image as cv2
    frame = cv2.imread(f"api-{timeNow}.png")

    try:
        if filename == None:
            return {"faceDetected": "No Face Detected", "confidence": "0%", "match-status": False, "error-status": 0, "error-message": "Not a valid filename"}
    except ValueError:
        pass

    # Read recently grabbed image to cv2
    img = cv2.imread(filename)

     # Convert into grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Load the cascade
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    
    # Detect faces
    faces = face_cascade.detectMultiScale3(gray, 1.1, 5, outputRejectLevels = True)
    try :
        face_detected = list(faces[0].tolist())
        weights = list(faces[2].tolist())
        updated_weights = weights.copy()
    
        # Deleting faces that under 50% confidence
        for i in range(len(weights)) :
            if weights[i] < 5 :
                face_detected.pop(i)
                updated_weights.pop(i)
        weights_json = {}
        count = 1
        for i in updated_weights :
            i = '{:.2f}'.format(i*10)
            weights_json[count] = i+"%"
            count += 1
        os.remove(filename)
        return {"face-count" : len(face_detected), "confidence" : weights_json}
    except :
        os.remove(filename)
        return {"face-count" : 0, "confidence" : "0%", "error-code" : "No face detected"}
    else:
        os.remove(filename)
        return {"face-count" : 0, "confidence" : "0%", "error-code" : "Something happened :("}


