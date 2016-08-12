
from azure.storage.blob import BlobService
from mimetypes import guess_type

ACCOUNT = 'msgtest'
CONTAINER = 'telegram'

blob_service = BlobService(account_name=ACCOUNT, account_key='sJQjZXgR/IUH4o4/CmbXue3DGxRgwkzy0SILxJMSgmd26lFCXUdqrtwwjmEPU9CrcIvoJG3yv6L0R55o9BqnXw==')

blob_service.create_container(CONTAINER, x_ms_blob_public_access='container')


def putblob(fileid, filename):
    global ACCOUNT
    blob_service.put_block_blob_from_path(
        CONTAINER,
        fileid,
        filename,
        x_ms_blob_content_type=guess_type(filename)
    )
    return 'https://%s.blob.core.windows.net/%s/%s' %(ACCOUNT, CONTAINER, fileid)

putblob('quotes.pkl', 'quotes.pkl')


blobs = []
marker = None
while True:
    batch = blob_service.list_blobs(CONTAINER, marker=marker)
    blobs.extend(batch)
    if not batch.next_marker:
        break
    marker = batch.next_marker
for blob in blobs:
    print(blob.name)

#blob_service.delete_blob(CONTAINER, 'quotes.pkl')


