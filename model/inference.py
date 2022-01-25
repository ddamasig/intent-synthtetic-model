#!/usr/bin python3

# import warnings
import logging
import flask
import json
import numpy as np
import pandas as pd
import io
import justext
import string

import requests
s = requests.Session()
s.max_redirects = 20


# dimension tables
# words
words = json.load(open('_words.json'))

# publisher names and output categories
names = pd.read_csv('_names.csv', index_col=0)['Customer Name']
out_cats = [
    "Business",
    "Business News",
    "Science Tech News",
    "News",
    "Lifestyle",
    "Politics",
    "Entertainment"
]
# ICR info
icr_df = pd.read_csv('_icr_df.csv', index_col='PAGE_URL')

# GTC topics
topics = pd.read_csv('_topics.csv', encoding='latin-1')['Gen_TopicName']


# NOTE: Possible cause of the C2 Server Communication issue flagged by AWS.
def get_content(url,
                max_len='auto', timeout=30):
    if max_len == 'auto':
        max_len = np.random.randint(100, 200)

    try:
        # NOTE: One of the URLs in the dataset might be a C2 Server IP Address.
        response = s.get(url, timeout=timeout)
        paragraphs = []

        for paragraph in justext.justext(response.content, justext.get_stoplist("English")):
            if len(paragraphs) <= max_len:
                if not paragraph.is_boilerplate:
                    paragraphs += paragraph.text.split(" ")
        return((" ").join(paragraphs))
    except:
        return("[NAFT]"+(" ").join(np.random.choice(words, size=max_len)))


def get_response(in_df, n_topics=10):

    url_df = pd.DataFrame(in_df.PAGE_URL.unique(), columns=['PAGE_URL'])

    # getting initial table
    url_info = url_df.merge(icr_df, on='PAGE_URL', how='left')
    n_url = len(url_df.index)

    # 1. ICR -- [PAGE_TITLE,PROTOCOL_ICR,SUB_DOMAIN_ICR,PAGE_DOMAIN_ICR,TOP_DOMAIN_ICR,
    #             PATH_ICR,ENDPOINT_ICR,PUBLISHER_ICR]
    # 2. TPC -- [PAGE_CATEGORY_TPC,PAGE_CATEGORY_CONF_TPC]
    # 3. TOC -- [FULL_TEXT_TOC,AUTHOR_TOC,PUB_DATE_TOC]
    # 4. CC -- [PAGE_CATEGORY_TPC,PAGE_CATEGORY_CONF_TPC]
    # 5. (separate dataframe; for each url, get 10 topics) GTC -- [TOPIC_ID_GTC,TOPIC_CONF_GTC]

#     print('start ICR,TOC')
    info_dict = {}
    for url in url_df['PAGE_URL']:
        tmp_dict = {}
        tmp_dict['PATH_ICR'] = ''.join(np.random.choice(list(string.ascii_letters+string.digits),
                                                        replace=True,
                                                        size=np.random.randint(
                                                            3, 16)
                                                        ))
        tmp_dict['ENDPOINT_ICR'] = ''.join(np.random.choice(list(string.ascii_letters+string.digits+string.punctuation),
                                                            replace=True,
                                                            size=np.random.randint(3, 16)))
        # TOC
        tmp_dict["PUB_DATE_TOC"] = str(np.random.choice(
            pd.date_range('2010-01-01', '2020-01-01')))[:10]
        tmp_dict["AUTHOR_TOC"] = '|'.join(
            np.random.choice(names, size=np.random.randint(4)))
        tmp_dict['FULL_TEXT_TOC'] = get_content(url)
        info_dict[url] = tmp_dict

    for k in ['TPC', 'CC']:
        name = f"PAGE_CATEGORY_{k}"
        url_info[name] = np.random.choice(out_cats, size=n_url, replace=True)
        url_info[f"PAGE_CATEGORY_CONF_{k}"] = np.random.uniform(
            0, 1, size=n_url)

        # 5. GTC
        # [TOPIC_ID_GTC,TOPIC_CONF_GTC]
    url_topics = []
    for url in url_df['PAGE_URL']:
        tmp = pd.DataFrame([url]*n_topics, columns=['PAGE_URL'])
        tmp["TOPIC_ID_GTC"] = list(np.random.choice(
            topics, replace=False, size=n_topics))
        tmp["TOPIC_CONF_GTC"] = list(
            np.sort(np.random.uniform(0, 1, size=n_topics))[::-1])
        url_topics.append(tmp)

    url_info = url_info.merge(pd.concat(url_topics), on='PAGE_URL', how='left')
    url_info = url_info.merge(pd.DataFrame.from_dict(info_dict, orient='index'),
                              left_on='PAGE_URL', right_index=True,
                              how='left'
                              )
    final_df = url_df.merge(url_info, on='PAGE_URL', how='left')

    return(final_df)


# Initialize the Flask app
app = flask.Flask(__name__)


@app.route('/ping', methods=['GET'])
def ping():
    try:
        status = 200
        logging.info("Status : 200")
    except:
        status = 400
    return flask.Response(response=json.dumps(' '), status=status, mimetype='application/json')


# NOTE: Looks like sagemaker runtime expects this route
@app.route('/invocations', methods=['POST'])
def invoke():
    # Only accept CSV request body
    if flask.request.content_type == 'text/csv':
        data = flask.request.data.decode('utf-8')
        s = io.StringIO(data)
        # NOTE: Any compression flags should be set in the Batch transform job creation
        df = pd.read_csv(s)
    else:
        return flask.Response(
            response='This predictor only supports CSV data',
            status=415,
            mimetype='text/plain'
        )

    # Run the model logic using the input data
    print('Running the Synthetic Model logic.')
    raw_output_df = get_response(df)

    # Merge the raw output with the input data
    print('Merging the raw output with the input data.')
    out_df = raw_output_df.merge(right=df, how='inner', on=['PAGE_URL'])

    # Encode the final output into CSV
    print('Encoding data into CSV.')
    out = io.StringIO()
    out_df.to_csv(out, index=False)
    result = out.getvalue()

    # Returrn an HTTP response with a CSV response body
    return flask.Response(
        response=result,
        status=200,
        mimetype='text/csv'
    )


if __name__ == '__main__':
    max_len = 10
    print("[NAFT] "+(" ").join(np.random.choice(words, size=max_len)))
