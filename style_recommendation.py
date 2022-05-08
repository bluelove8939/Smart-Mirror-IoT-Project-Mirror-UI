

import os
import sys
import datetime
import logging
import cv2
import imutils
import json

import reverse_image_api_wrapper

cap = cv2.VideoCapture(0)


def removeAllImgCaches():
    for filename in os.listdir(os.path.join(os.curdir, 'caches')):
        if filename.endswith('.jpg'):
            os.remove(os.path.join(os.curdir, 'caches', filename))


class StyleRecommend:
    def __init__(self, reverse_search_apikey, s3_bucket_name):
        self.reverse_search_inst = reverse_image_api_wrapper.ReverseSearchApi(apikey=reverse_search_apikey, bucket_name=s3_bucket_name)
        self.user_style_filename = None

    def capture(self):
        # After 5 seconds,
        ret, frame = cap.read()
        if ret == False:
            logging.error('[STYLE RECOMMENDATION] Frame capture error occured. Exiting feature...')
            return False

        # save into image file
        tm = datetime.datetime.now()
        stamp = f"{tm:%Y%m%d-%H%M%S}"
        self.user_style_filename = "user-style-" + stamp + ".jpg"
        logging.info(f'[STYLE RECOMMENDATION] Saving captured picture as {self.user_style_filename}')
        cv2.imwrite(os.path.join('caches', self.user_style_filename), frame)

        return True

    def search(self):
        if self.user_style_filename is None:
            logging.error(f"[STYLE RECOMMENDATION] Error ocurred on searching: There aren't any image captured" )
            return None

        # go through API and get result
        logging.info(f'[STYLE RECOMMENDATION] Searching by image {self.user_style_filename}....')
        result = self.reverse_search_inst.search_by_local_image(self.user_style_filename)
        
        removeAllImgCaches()
        
        # check if exception occured
        if 'exception' in result:
            logging.error(f'[STYLE RECOMMENDATION] An error occured while transfer and receive data with reverse search api')
            return None
        return result