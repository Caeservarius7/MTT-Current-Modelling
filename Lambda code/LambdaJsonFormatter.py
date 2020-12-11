# LambdaJsonFormatter.py
# Formats Kinesis Firehose Stream Batch into a json record format
# Python 2.7

from __future__ import print_function

import base64

print('Loading function')


def lambda_handler(event, context):
    output = []

    for record in event['records']:
        print(record['recordId'])
        payload = base64.b64decode(record['data'])

        # Formats the batch into a Json Records format
        # - Adds square brackets at the start and end of the file
        # - separates messages with comma delimiter

        if (record == event['records'][0]):
            # First record
            print('Adding opening "["')
            payload = '[' + payload
        if (record == event['records'][-1]):
            # Last record
            print('Adding closing "]"')
            payload = payload + ']'
        else:
            # Add Comma Separator
            payload = payload + ','

        output_record = {
            'recordId': record['recordId'],
            'result': 'Ok',
            'data': base64.b64encode(payload)
        }
        output.append(output_record)

    print('Successfully processed {} records.'.format(len(event['records'])))

    return {'records': output}
