import os
from pytube import YouTube
from pydub import AudioSegment
from google.cloud import storage
from google.resumable_media import requests, common
from google.auth.transport.requests import AuthorizedSession
from urllib.parse import urlparse, parse_qs 


bucket_name='visumm-store'
storage_client = storage.Client()
bucket = storage_client.get_bucket(bucket_name)
speech_client = speech_v1.SpeechClient()


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


# Function to upload to GCS
def upload_blob(source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    print('inside upload_blob')
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    print('File {} uploaded to {}.'.format(source_file_name, destination_blob_name))


# Function to download from GCS
def download_blob(source_blob_name, destination_file_name):
    """Downloads a blob from the bucket."""
    print('inside download_blob')
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)
    print('File {} has been downloaded to {}.'.format(source_blob_name, destination_file_name))


# Function to get video id from youtube url
def extract_video_id_from_url(url):
    parsed_url = urlparse(url)
    qs = parse_qs(parsed_url.query)
    if 'v' in qs.keys() and len(qs['v']) >= 1: 
        video_id = qs['v'][0]
    else:
        video_id = None
    return video_id    


# Function to extract youtube_url from request
def get_youtube_url(request):
    if request.args and 'youtube_url' in request.args:
        return request.args.get('youtube_url')     


# Function to download youtube video. Stores video in GCS.
def get_youtube_video(yt_link, output_filename):
    yt_object = YouTube(yt_link)
    yt_stream = yt_object.streams.filter(only_audio=True).first()
    data = yt_stream.stream_to_buffer()
    with GCSObjectStreamUpload(client=storage_client, bucket_name=bucket_name, blob_name=output_filename) as fh:
        fh.write(data.getbuffer())


# Function to transform .mp4 to .flac
def transform_audio_to_flac(input_filename, output_filename):
    print('inside transform_audio_to_flac')
    # constants for local storage
    local_filename='/tmp/temp.mp4'
    local_filename_transformed='/tmp/temp.flac'
    # Get file from S3 bucket
    download_blob(input_filename, local_filename)
    # Convert file from MP4 to flac
    mp4_audio = AudioSegment.from_file(local_filename, format="mp4")
    mp4_audio.export(local_filename_transformed, format="flac")
    # Store file to S3 bucket
    upload_blob(local_filename_transformed, output_filename)


# Function to extract text from audio file. Stores .txt in GCS
def get_text_from_audio(input_filename, output_filename):
    print('inside sample_long_running_recognize')
    storage_uri = 'gs://' + bucket_name + '/' + input_filename

    # S2T config
    sample_rate_hertz = 44100
    language_code = "en-US"
    encoding = enums.RecognitionConfig.AudioEncoding.FLAC
    config = {
        "sample_rate_hertz": sample_rate_hertz,
        "language_code": language_code,
        "audio_channel_count": 2,
        "encoding": encoding,
    }
    audio = {"uri": storage_uri}

    operation = client.long_running_recognize(config, audio)
    response = operation.result()

    full_transcript=''
    for result in response.results:
        # First alternative is the most probable result
        alternative = result.alternatives[0]
        full_transcript = full_transcript + alternative.transcript + '\n'
    print('full_transcript: \n', full_transcript)

    # write to file
    local_fpath = '/tmp/full_transcript.txt'
    with open(local_fpath,  'w') as f:
        f.write(full_transcript)
    
    # upload to bucket
    upload_blob(local_fpath, output_filename)

    return full_transcript

# Function to summarize text
def get_summary(input_filename, output_filename):
    # Get full text
    blob = bucket.get_blob(input_filename)
    text = blob.download_as_string()
    # Call the summarize API
    body = summarize(text, 0.5)
    # Write to GCS     
    blob = bucket.blob(output_filename)
    blob.upload_from_string(body, content_type="text/plain")


def main(request):
    youtube_url = get_youtube_url(request)
    if not youtube_url:
        print('ERROR: no youtube_url was provided. exiting')
        response = { "statusCode": 400, "error": "You must provide a valid youtube_url as a query string parameter"}
        return json.dumps(response, indent=4)
    youtube_id = extract_video_id_from_url(youtube_url)
    # Get youtube video
    outfile_mp4 = youtube_id + '/audio.mp4'
    get_youtube_video(youtube_url, outfile_mp4)
    # Transform .mp4 to .flac
    outfile_flac = youtube_id + '/audio.flac'
    transform_audio_to_flac(outfile_mp4, outfile_flac)
    # Tranform .flac to .txt
    outfile_full_text = youtube_id + '/audio_full_text.txt'
    text_full = get_text_from_audio(outfile_flac, outfile_full_text)
    # Transform full text to summary
    outfile_summary = youtube_id + '/audio_summary.txt'
    text_summary = get_summary(outfile_full_text, outfile_summary)
    # respond
    response = {
        "statusCode": 200, 
        "text": text_full
        "summary": text_summary,
    }
    return json.dumps(response, indent=4)
