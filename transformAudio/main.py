from pydub import AudioSegment
from google.cloud import storage

bucket_name='visumm-store'
storage_client = storage.Client()
bucket = storage_client.get_bucket(bucket_name)

def download_blob(source_blob_name, destination_file_name):
    """Downloads a blob from the bucket."""
    print('inside download_blob')
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)
    print('File {} has been downloaded to {}.'.format(source_blob_name, destination_file_name))

def upload_blob(source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    print('inside upload_blob')
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    print('File {} has been uploaded to {}.'.format(source_file_name, destination_blob_name))

def main(request):
    # const declariation
    input_filename='lTxn2BuqyzU/youtube-CGI Animated Short Film Watermelon A Cautionary Tale by Kefei Li & Connie Qin He  CGMeetup.mp4'
    output_filename='temp.mp4'
    output_filename_transformed='temp.flac'
    # Get file from S3 bucket
    download_blob(input_filename, output_filename)
    # Convert file from MP4 to flac
    print('converting files')
    mp4_audio = AudioSegment.from_file(output_filename, format="mp4")
    mp4_audio.export(output_filename_transformed, format="flac")
    # Store file to S3 bucket
    upload_blob(output_filename_transformed, 'lTxn2BuqyzU/audiooo.flac')

main('request')