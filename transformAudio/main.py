from pydub import AudioSegment
from google.cloud import storage



def download_blob(source_blob_name, destination_file_name):
    """Downloads a blob from the bucket."""
    print('inside download_blob')
    
    bucket_name='visumm-store'
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)

    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)
    print('File {} has been downloaded to {}.'.format(source_blob_name, destination_file_name))

def upload_blob(source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    print('inside upload_blob')
    bucket_name='visumm-store'
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)

    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    print('File {} has been uploaded to {}.'.format(source_file_name, destination_blob_name))

def transform_audio(request):
    
    # read input arguments
    if request.args and 'input_filename' in request.args:
        input_filename = request.args.get('input_filename')
        print('got input_filename: ', input_filename)
    else:
      print('ERROR: no input_filename was provided. existing')
      return
    # constants for local storage
    local_filename='/tmp/temp.mp4'
    local_filename_transformed='/tmp/temp.flac'
    # Get file from S3 bucket
    download_blob(input_filename, local_filename)
    # Convert file from MP4 to flac
    print('converting files')
    mp4_audio = AudioSegment.from_file(local_filename, format="mp4")
    mp4_audio.export(local_filename_transformed, format="flac")
    # Store file to S3 bucket
    input_filename = input_filename[0:-4] # crop the last 4 chars, '.mp4'
    output_filename = input_filename + '.flac' # this contains bucketname + filename + extension
    upload_blob(local_filename_transformed, output_filename)

#main('request')