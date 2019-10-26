import os
from pytube import YouTube
from google.cloud import storage
from google.resumable_media import requests, common
from google.auth.transport.requests import AuthorizedSession
from urllib.parse import urlparse, parse_qs 

bucket_name='visumm-store-test'
client = storage.Client()

# This class allows to stream write to Google Cloud Storage
class GCSObjectStreamUpload(object):
    def __init__(
            self, 
            client: storage.Client,
            bucket_name: str,
            blob_name: str,
            chunk_size: int= 1 * 1024 * 1024
        ):
        self._client = client
        self._bucket = self._client.bucket(bucket_name)
        self._blob = self._bucket.blob(blob_name)

        self._buffer = b''
        self._buffer_size = 0
        self._chunk_size = chunk_size
        self._read = 0

        self._transport = AuthorizedSession(
            credentials=self._client._credentials
        )
        self._request = None  # type: requests.ResumableUpload

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, *_):
        if exc_type is None:
            self.stop()

    def start(self, byte_size=None):
        url = (
            f'https://www.googleapis.com/upload/storage/v1/b/'
            f'{self._bucket.name}/o?uploadType=resumable'
        )
        chunk = byte_size if byte_size else self._chunk_size 
        self._request = requests.ResumableUpload(
            upload_url=url, chunk_size=chunk
        )
        self._request.initiate(
            transport=self._transport,
            content_type='application/octet-stream',
            stream=self,
            stream_final=False,
            metadata={'name': self._blob.name},
        )

    def stop(self):
        self._request.transmit_next_chunk(self._transport)

    def write(self, data: bytes) -> int:
        data_len = len(data)
        self._buffer_size += data_len
        self._buffer += data
        del data
        while self._buffer_size >= self._chunk_size:
            try:
                self._request.transmit_next_chunk(self._transport)
            except common.InvalidResponse:
                self._request.recover(self._transport)
        return data_len

    def read(self, chunk_size: int) -> bytes:
        # I'm not good with efficient no-copy buffering so if this is
        # wrong or there's a better way to do this let me know! :-)
        to_read = min(chunk_size, self._buffer_size)
        memview = memoryview(self._buffer)
        self._buffer = memview[to_read:].tobytes()
        self._read += to_read
        self._buffer_size -= to_read
        return memview[:to_read].tobytes()

    def tell(self) -> int:
        return self._read

def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    print('inside upload_blob')
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    print('File {} uploaded to {}.'.format(source_file_name, destination_blob_name))

def extract_video_id_from_url(url):
    parsed_url = urlparse(url)
    qs = parse_qs(parsed_url.query)
    if 'v' in qs.keys() and len(qs['v']) >= 1: 
        video_id = qs['v'][0]
    else:
        video_id = None
    return video_id
    
def get_yt_video(request):
    if request.args and 'youtube_url' in request.args:
        yt_link = request.args.get('youtube_url')
        print('Got a request with youtube_url=', yt_link)
    else:
        print('ERROR: no URL was provided. exiting.')
        return
    yt_id = extract_video_id_from_url(yt_link)
    yt_object = YouTube(yt_link)
    yt_stream = yt_object.streams.filter(only_audio=True).first()
    data = yt_stream.stream_to_buffer()
    with GCSObjectStreamUpload(client=client, bucket_name='visumm-store', blob_name= yt_id + '/youtube-' + yt_stream.default_filename) as fh:
        fh.write(data.getbuffer())

# The lambda function is created from the code above
# The code below is to test locally.
get_yt_video('request')