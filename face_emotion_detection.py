import os
import sys
import json
import time
import datetime
import logging
import azure_api_wrapper


#---------------------------------------------------
# this part is for local face detection
# function 'detect_faces' perform DNN with 
import cv2
import imutils
#DNN model source path which will be used in cv2.dnn
face_detection_prototxt = 'model/deploy.prototxt'
face_detection_model = 'model/res10_300x300_ssd_iter_140000.caffemodel'
net = cv2.dnn.readNetFromCaffe(face_detection_prototxt, face_detection_model)

def detect_faces(frame):
    image = imutils.resize(frame, width=400)
    blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
    net.setInput(blob)
    detections = net.forward()
    return detections
#---------------------------------------------------

def removeAllImgCaches():
    for filename in os.listdir(os.path.join(os.curdir, 'caches')):
        if filename.endswith('.jpg'):
            os.remove(os.path.join(os.curdir, 'caches', filename))


# Usage: 
#   (variable) = MirrorFaceDetect() to initialize
class MirrorFaceDetect:
    def __init__(self, face_apikey, face_api_endpoint):
        self.face_api = azure_api_wrapper.AzureFaceApi(apikey=face_apikey, endpoint=face_api_endpoint)

    def detect_motion_webcam(self):
        # initialize variable in Json format, to return exception string
        j = json.loads('{}')
        
        # mark time stamp to save energy and prevent endless loop
        # camera running time should not exceed 60 seconds
        self.stamp = time.time()

        # check if USB webcam is connected
        # USB webcam initialization (may be also applicable for raspberry pi)
        cap = cv2.VideoCapture(0)
        if (cap.isOpened() == False):
            msg = {'exception': 'Webcam is not available'}
            j.update(msg)
            return j
        # check if motion is not detected, through PIR motion sensor
        # sensor is not available, so this feature is diabled.
        # if PIR == 0:
        #     time.sleep(1)
        #     continue
        
        while True:
            # check if time is exceeded, so that camera is not running over 60 seconds
            # if PIR sensor is available, this feature is now useful
            if time.time() - self.stamp > 60:
                msg = {'exception': 'Time exceeded'}
                j.update(msg)
                return j
            # if motion is detected(or be directly executed if PIR sensor is diabled), execute below
            # capture one frame from Webcam
            ret, frame = cap.read()
            if ret == False:
                msg = {'exception': 'Frame capture error'}
                j.update(msg)
                return j
            # Do actions with captured image    
            detections = detect_faces(frame)
            self.appearance = 0
            for i in range(0, detections.shape[2]):
                confidence = detections[0, 0, i, 2]
                if confidence > 0.5:
                    self.appearance += 1
            # check whether face is (faces are) detected or not
            if self.appearance <= 0:
                msg = {'exception': 'Face not detected'}
                logging.info(f"[FACE EMOTION] Error ocurred on detecting face: {msg['exception']}")
                continue

            # if yes, save the image into Jpeg format
            # and save it to capture/ directory
            logging.info('[FACE EMOTION] Face detected')
            tm = datetime.datetime.now()
            stamp = f"{tm:%Y%m%d-%H%M%S}"
            self.face_filename = "face-" + stamp + ".jpg"
            logging.info(f'[FACE EMOTION] Saving captured picture as {self.face_filename}')
            cv2.imwrite(os.path.join('caches', self.face_filename), frame)

            # call face api and get emotion string
            logging.info('[FACE EMOTION] Detecting emotion')
            self.result = self.face_api.detect_face_src(os.path.join('caches', self.face_filename))
            removeAllImgCaches()
            
            if self.result['exception'] != azure_api_wrapper.NO_EXCEPTION_MSG:
                logging.info(f"[FACE EMOTION] Error ocurred on detecting emotion: {self.result['exception']}")
                if self.result['exception'] != azure_api_wrapper.NO_ITERATION_MSG:
                    continue
        
            # return and send the data into Json format
            return self.result

