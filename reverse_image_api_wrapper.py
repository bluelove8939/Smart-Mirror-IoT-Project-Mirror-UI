# required packages: google-search-results, boto3
import os
import boto3
import logging
import json
from botocore.exceptions import ClientError
from serpapi import GoogleSearch



def upload_file_to_bucket(file_name, bucket, object_name=None):
    s3_client = boto3.client('s3')
    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)
    
    if not os.path.isfile(file_name):
        return False
    
    # Upload the file
    try:
        response = s3_client.upload_file(file_name, bucket, object_name, ExtraArgs={'ACL': 'public-read'})
    except ClientError as e:
        logging.error(e)
        return False

    if response['ResponseMetadata']['HTTPStatusCode'] < 200 and response['ResponseMetadata']['HTTPStatusCode'] >= 300:
        logging.error(f"[REVERSE IMAGE API] Failed uploading image file {file_name}")
        return False

    return True

def delete_object_from_bucket(bucket, object_name):
    s3_client = boto3.client('s3')
    response = s3_client.delete_object(
            Bucket=bucket,
            Key=object_name
    )
    if response['ResponseMetadata']['HTTPStatusCode'] < 200 and response['ResponseMetadata']['HTTPStatusCode'] >= 300:
        logging.error(f"[REVERSE IMAGE API] Failed deleting image file {object_name}")
        return False
    return True


# to initialize this class below: (var) = ~~_wrapper.ReverseSearchApi(apikey='', image_filename='')
class ReverseSearchApi:
    def __init__(self, apikey, bucket_name):
        self.bucket_name = bucket_name
        self.apikey = apikey
        # self.endpoint_url = "https://" + bucket_name + ".s3.amazonaws.com/" + image_filename
    
    def search_by_local_image(self, image_filename):
        j = json.loads('{}')
        # an image from camera is already exists, so steps: upload -> api -> delete image. 
        # upload image file to AWS S3 bucket and make it public
        if not upload_file_to_bucket(os.path.join('caches', image_filename), self.bucket_name):
            msg = {'exception': 'Failed to upload image to S3 bucket'}
            logging.error('[REVERSE SEARCH API] Failed to upload image to S3 bucket')
            j.update(msg)
            return j
        
        # call reverse search api
        self.endpoint_url = "https://" + self.bucket_name + ".s3.amazonaws.com/" + image_filename
        self.params = {
            "engine": "google_reverse_image", 
            "image_url": self.endpoint_url, 
            "api_key": self.apikey, 
            "hl": "ko", 
            "gl": "kr"
        }
        self.search = GoogleSearch(self.params)
        self.results = self.search.get_dict()
        # print(self.results)
        # print(type(self.results))
        
        # check return response of API
        if 'error' in self.results:
            msg = {'exception': 'Error occured from response of Reverse Search API'}
            logging.error('[REVERSE SEARCH API] Error occured from response of Reverse Search API')
            j.update(msg)
            return j
        
        # copy results to JSON load
        url_chunk = self.results['inline_images']
        for idx, s in enumerate(url_chunk):
            t = {1 + idx: s.get('source')}
            j.update(t)
        
        # remove uploaded image file in S3 bucket (not local image)
        if not delete_object_from_bucket(self.bucket_name, image_filename):
            logging.info(f'[STYLE RECOMMENDATION] Image file \'{image_filename}\' uploaded to S3 bucket is not removed.')
        else:
            logging.info(f'[STYLE RECOMMENDATION] Image file \'{image_filename}\' is successfully removed from S3 bucket.')
        
        return j
        
