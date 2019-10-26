import json
from gensim.summarization.summarizer import summarize

def summarise(request):
    print(request)
    body = summarize(
        "Video sponsor: Formidable (https://formidable.com/)\n\nFriction is a common, and necessary, part of team growth\u2014but when left unchecked, team friction is unhealthy for you, your coworkers, your company, and ultimately your end users.\n\nIn this presentation, I draw on my experiences at organizations large and small to illuminate the sources of team tension, how you can better understand and manage unexpected teammate reactions, and the best ways to give actionable feedback without escalating drama. Your coworkers, your organization, your users, and you will reap the benefits.\n\nAbout Lara Hogan\nLara Hogan is the co-founder of Wherewithall and the author of Designing for Performance and Building a Device Lab. Previously she was VP Engineering at Kickstarter and Engineering Director at Etsy. She champions performance as a part of the overall user experience, helps people get comfortable giving presentations, and believes it\u2019s important to celebrate career achievements with donuts."
    , 0.5)

    response = {
        "statusCode": 200,
        "body": body
    }

    return json.dumps(response, indent=4)