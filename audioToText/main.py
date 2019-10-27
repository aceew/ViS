from google.cloud import speech_v1
from google.cloud.speech_v1 import enums
from google.cloud import storage


def upload_blob(source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    print('inside upload_blob')
    # S3
    bucket_name='visumm-store'
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    print('File {} has been uploaded to {}.'.format(source_file_name, destination_blob_name))


def sample_long_running_recognize(request=''):
    bucket_name='visumm-store'

    # S2T
    client = speech_v1.SpeechClient()

    # read input arguments
    if request.args and 'input_filename' in request.args:
        input_filename = request.args.get('input_filename')
        print('got input_filename: ', input_filename)
    else:
      print('ERROR: no input_filename was provided. existing')
      return

    # input filepath as GCS uri
    storage_uri = 'gs://' + bucket_name + '/' + input_filename

    # S2T config
    sample_rate_hertz = 44100
    language_code = "en-US"

    # Encoding of audio data sent. This sample sets this explicitly.
    # This field is optional for FLAC and WAV audio formats.
    encoding = enums.RecognitionConfig.AudioEncoding.FLAC
    config = {
        "sample_rate_hertz": sample_rate_hertz,
        "language_code": language_code,
        "audio_channel_count": 2,
        "encoding": encoding,
    }
    audio = {"uri": storage_uri}

    operation = client.long_running_recognize(config, audio)

    print(u"Waiting for operation to complete...")
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
    
    # output filename to store
    output_filename = input_filename[0:-5] # remove the .flac extension
    output_filename = output_filename + '.txt' # add .txt extension
    upload_blob(local_fpath, output_filename)

#sample_long_running_recognize()