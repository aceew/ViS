import json
from gensim.summarization.summarizer import summarize
from google.cloud import storage

def summarise(data, context):
    print(context)
    print(data.textPayload)
    event = json.loads(data.textPayload)
    bucket_name = event.bucket
    file_name = event.name
    if "speech-to-text.txt" not in file_name:
        return

    storage_client = storage.Client()

    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.get_blob(file_name)
    text = blob.download_as_string()

    body = summarize(text, 0.5)

    filepath_parts = file_name.split('/')
    summary_file = "/"
    summary_file.join(filepath_parts[0:len(filepath_parts - 2)])
    blob = bucket.blob(summary_file)
    blob.upload_from_string(
        body,
        content_type="text/plain"
    )

    response = {
        "statusCode": 200,
        "body": body
    }

    return json.dumps(response, indent=4)