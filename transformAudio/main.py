from pydub import AudioSegment
from google.cloud import storage

bucket_name='visumm-store'

def download_blob(source_blob_name, destination_file_name):
    """Downloads a blob from the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)

    print('Blob {} downloaded to {}.'.format(source_blob_name, destination_file_name))

def main(request):
    # Get file from S3 bucket
    filename='3ueqncw103A/test.flac'
    download_blob(filename, 'tempfile.flac')

    # Convert file from MP4 to flac

    # Store file to S3 bucket

main('request')