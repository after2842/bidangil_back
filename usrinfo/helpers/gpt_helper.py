from openai import OpenAI
from django.conf import settings
def process_websearch(url):
    print('process websearch!')
    client = OpenAI(api_key= settings.GPT_SECRET)

    completion = client.chat.completions.create(
        model="gpt-4o-search-preview",
        # web_search_options={},
        messages=[{
            "role": "user",
            "content": f"{url}\n Your job is to answer the product name. use the url I gave you to search the product name. RUlE: 1. return ONLY the product name 2. if the prdouct name contains quantity or any of optional information that buyers can choose, exclude it \n examples:'피지오겔 데일리 모이스쳐 테라피 페이셜 크림, 150ml, 2개' should return '피지오겔 데일리 모이스쳐 테라피 페이셜 크림' 3.if the url is unavailable(not reachable, removed product, wrong url...) return 'can't find'",
        }],
    )

    print(completion.choices[0].message.content)
    return str(completion.choices[0].message.content)


    