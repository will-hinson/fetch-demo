import boto3
import hashlib
import json
import logging
import os
import time
from typing import Any, Dict

from sqlalchemy import create_engine, Engine, URL
from sqlalchemy.orm import Session

from .log import log_exception
from .models import UserLogin
from .models._base import _Base
from .sqs import SqsConnectionParams

# build a SQLAlchemy connection URL from environment variables
sql_connection_url: URL = URL.create(
    drivername=os.environ["SQL_DRIVER"],
    username=os.environ["SQL_USER"],
    password=os.environ["SQL_PASSWORD"],
    host=os.environ["SQL_HOST"],
    port=os.environ["SQL_PORT"],
    database=os.environ["SQL_DATABASE"],
)
sqs_connection_params: SqsConnectionParams = SqsConnectionParams(
    queue_url=os.environ["SQS_QUEUE_URL"],
    region=os.environ["SQS_QUEUE_REGION"],
    endpoint=os.environ["SQS_QUEUE_ENDPOINT"],
    aws_key=os.environ["AWS_API_KEY"],
    aws_secret=os.environ["AWS_API_SECRET"],
    # the maximum number of messages to read from the queue at once. default is 1000
    maximum_messages=(
        1_000
        if "SQS_MAX_MESSAGE_COUNT" not in os.environ
        else int(os.environ["SQS_MAX_MESSAGE_COUNT"])
    ),
    # the time in seconds to delay between unsuccessful polls of the queue. default is 5
    poll_delay=(
        5 if "SQS_POLL_DELAY" not in os.environ else int(os.environ["SQS_POLL_DELAY"])
    ),
    # the wait time in seconds for each poll. default is 10
    wait_time=(
        10 if "SQS_WAIT_TIME" not in os.environ else int(os.environ["SQS_WAIT_TIME"])
    ),
)


# set up console logging
logging.basicConfig(
    level=logging.INFO,
    format=f"[%(asctime)s] [{os.getpid()}] [%(levelname)s] %(message)s",
)

logging.info(
    "Connecting to database at %s and SQS queue at %s",
    sql_connection_url.render_as_string(hide_password=True),
    sqs_connection_params.queue_url,
)

# set up the global encryption key for masking
_Base.encryption_key = os.environ["ENCRYPTION_KEY"].encode("utf-8")

# connect to both the database and the SQS queue
sqs_client = boto3.client(
    "sqs",
    region_name=sqs_connection_params.region,
    endpoint_url=sqs_connection_params.endpoint,
    aws_access_key_id=sqs_connection_params.aws_key,
    aws_secret_access_key=sqs_connection_params.aws_secret,
)
engine: Engine = create_engine(sql_connection_url)

with Session(engine) as sql_session:
    # loop forever getting and inserting messages from the queue
    #
    # NOTE: ideally, we'd have some way to pause this as necessary
    while True:
        # try reading a batch of messages from the SQS queue
        # pylint: disable=broad-exception-caught
        response: Dict[str, Any]
        poll_exception: Exception | None = None
        try:
            response = sqs_client.receive_message(
                QueueUrl=sqs_connection_params.queue_url,
                MaxNumberOfMessages=sqs_connection_params.maximum_messages,
                WaitTimeSeconds=sqs_connection_params.wait_time,
            )
        except Exception as exc:
            log_exception(exc, unhandled=True)
            poll_exception = exc

        # if we didn't get any messages, try again
        if "Messages" not in response or poll_exception is not None:
            # delay between each unsuccessful poll
            time.sleep(sqs_connection_params.poll_delay)
            continue

        # convert the messages in the response into a series of SQL records
        logging.info("Retrieved %s messages from queue", len(response["Messages"]))
        created_count: int = 0
        for message_obj in response["Messages"]:
            try:
                message_body: str = message_obj["Body"]
                message_md5: str = message_obj["MD5OfBody"]

                # compare the MD5 hash of the message body and discard this
                # message if they don't match
                if message_md5 != hashlib.md5(message_body.encode("utf-8")).hexdigest():
                    logging.error(
                        "MD5 hash for message body does not match: %s",
                        repr(message_body),
                    )
                    continue

                # convert this record to a UserLogin record and register it with the sql session
                sql_session.add(UserLogin(**json.loads(message_body)))
                created_count += 1
            except Exception as exc:
                log_exception(exc, unhandled=True)

        # commit all of the new user_login records
        sql_session.commit()
        logging.info("Inserted %s user_login records", created_count)

# close out both our sqs client and the SQLAlchemy engine
#
# NOTE: we're currently looping indefinitely so this isn't needed
sqs_client.close()
engine.dispose()
