from dataclasses import dataclass


@dataclass
class SqsConnectionParams:
    endpoint: str
    region: str
    queue_url: str
    aws_key: str
    aws_secret: str
    maximum_messages: int
    poll_delay: int
    wait_time: int
