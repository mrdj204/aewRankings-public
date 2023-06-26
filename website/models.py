"""
models.py

This module defines the data models used in the website.

Classes:
    - SessionData: Data model for session information, defined using Pydantic's BaseModel.

Third-party libraries used:
- pydantic
"""

from pydantic import BaseModel


class SessionData(BaseModel):
    """
    Data model for session information using Pydantic.

    The model is intended to be used for representing session information,
    such as their role and their username.

    Attributes:
        username (str): The username associated with the session.
        web_user (bool): Flag indicating if the session is for a web user.
        web_admin (bool): Flag indicating if the session is for a web admin.
        fanhub_user (bool): Flag indicating if the session is for a fanhub user.
        fanhub_elite (bool): Flag indicating if the session is for a fanhub elite user.
        fanhub_admin (bool): Flag indicating if the session is for a fanhub admin.

    Pydantic's BaseModel automatically validates the types of the input data and allows for easy serialization
    and deserialization of the model.
    """

    username: str
    web_user: bool
    web_admin: bool
    fanhub_user: bool
    fanhub_elite: bool
    fanhub_admin: bool


# session.username
# session.web_user
# session.web_admin
# session.fanhub_user
# session.fanhub_elite
# session.fanhub_admin
