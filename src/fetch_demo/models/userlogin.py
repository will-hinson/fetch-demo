from sqlalchemy import Column, Date, Integer, String

from ._base import _Base
from ..cipher import AesEncryptor


class UserLogin(_Base):
    __tablename__: str = "user_logins"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        # mask our target fields for this instance. this could also be done on insertion
        # to the database using a SQLAlchemy TypeDecorator
        #
        # I have chosen to mask here so that in the event that other code needs to utilize
        # these fields after instantiation, they will already be masked
        encryptor: AesEncryptor = AesEncryptor(key=_Base.encryption_key)
        for mask_field in "ip", "device_id":
            # don't try to hash the current value if it is None
            if (current_value := getattr(self, mask_field)) is None:
                continue

            # otherwise, convert the value to a string and hash it with sha512
            setattr(
                self,
                mask_field,
                encryptor.encrypt(str(current_value)),
            )

        # convert the incoming dot-separated version string to an integer
        #
        # pylint: disable=no-member
        self.app_version = int(self.app_version.replace(".", ""))

    # pylint: disable=line-too-long
    #
    # Define all of the fields that are present in the database table. 'masked_ip' and
    # 'masked_device_id' have the 'masked_' prefix dropped to simplify instantiation using
    # the parsed JSON data
    #
    # NOTE: Since the user_logins table does not have any primary key, SQLAlchemy requires
    # us to select a set of columns for the mapper to use as a compound key. For the purposes
    # of this demo, I have marked all of the columns as part of the compound key
    #
    # See https://docs.sqlalchemy.org/en/20/faq/ormconfiguration.html#how-do-i-map-a-table-that-has-no-primary-key
    # for additional detail
    #
    # pylint: enable=line-too-long

    user_id: Column = Column("user_id", String(128), nullable=True, primary_key=True)
    device_type: Column = Column(
        "device_type", String(32), nullable=True, primary_key=True
    )
    ip: Column = Column("masked_ip", String(256), nullable=True, primary_key=True)
    device_id: Column = Column(
        "masked_device_id", String(256), nullable=True, primary_key=True
    )
    locale: Column = Column("locale", String(32), nullable=True, primary_key=True)
    app_version: Column = Column(
        "app_version", Integer, nullable=True, primary_key=True
    )
    create_date: Column = Column("create_date", Date, nullable=True, primary_key=True)
