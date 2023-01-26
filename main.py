from fastapi import FastAPI, UploadFile, File
from time import strftime, gmtime

import os, shutil, math, requests, cv2, numpy as np, dlib, json

app = FastAPI()

@app.post('/')
def api(file: UploadFile = File(...)):

    # Get time now for filename
    timeNow = strftime("%d-%b-%y.%H-%M-%S", gmtime())
    filename = f"api-{timeNow}.png"

    # In case any file currently processed have the same
    # filename, to anticipate error rename the file
    filenamesInImages = os.listdir("./")
    count = 0
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


