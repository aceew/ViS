import json
from gensim.summarization.summarizer import summarize
from google.cloud import storage

storage_client = storage.Client()

def summarise(data, context):
    print(data)
    bucket_name = data['bucket']
    file_name = data['name']
    if "speech-to-text.txt" not in file_name:
        return

    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.get_blob(file_name)
    text = blob.download_as_string()

    body = summarize(text.decode('utf8'), 0.3)

    filepath_parts = file_name.split('/')
    summary_file = "/"
    summary_file.join(filepath_parts[0])
    summary_file = summary_file + "/summary.txt"
    blob = bucket.blob(summary_file)
    print(summary_file)
    blob.upload_from_string(
        body,
        content_type="text/plain"
    )

    response = {
        "statusCode": 200,
        "body": body
    }

    return json.dumps(response, indent=4)