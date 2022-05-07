

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

    def capture_and_search(self, delay=5):
        j = json.loads('{}')
        logging.info(f'[STYLE RECOMMENDATION] Take photo after {delay} seconds...')
        # unit of delay: sec
        # Please make an UI for printing remaining seconds to screen. (ex. 5, 4, 3, 2, 1 and 'processing....')
        # Can I just 'time.sleep(delay * 1000)' for just waiting?
        
        # After 5 seconds,
        ret, frame = cap.read()
        if ret == False:
            logging.error('[STYLE RECOMMENDATION] Frame capture error occured. Exiting feature...')
            msg = {'exception': 'Frame capture error'}
            j.update(msg)
            return j
        
        # save into image file
        tm = datetime.datetime.now()
        stamp = f"{tm:%Y%m%d-%H%M%S}"
        self.user_style_filename = "user-style-" + stamp + ".jpg"
        logging.info(f'[STYLE RECOMMENDATION] Saving captured picture as {self.user_style_filename}')
        cv2.imwrite(os.path.join('caches', self.user_style_filename), frame)
        
        # go through API and get result
        logging.info(f'[STYLE RECOMMENDATION] Searching by image {self.user_style_filename}....')
        self.result = self.reverse_search_inst.search_by_local_image(self.user_style_filename)
        
        removeAllImgCaches()
        
        # check if exception occured
        if 'exception' in self.result:
            logging.error(f'[STYLE RECOMMENDATION] An error occured while transfer and receive data with reverse search api.')
            return None
        return self.result




if __name__ == '__main__':
    os.environ['AWS_SHARED_CREDENTIALS_FILE'] = "/home/jy-ubuntu/Downloads/awsconfig.ini"
    a = StyleRecommend("eb8ebf0acdac23660b37f17ae4d3a823afaa7a732823c82b9d26db741f0e14fb", "jongsul")
    r = a.capture_and_search(delay=0)
    print(r)
    print(type(r))