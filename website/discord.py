"""
discord.py

This module provides custom classes for Discord OAuth session and client.

Classes:
    - CustomDiscordOAuthSession: Custom session class for Discord OAuth, extending DiscordOAuthSession.
    - CustomDiscordOAuthClient: Custom client class for Discord OAuth, extending DiscordOAuthClient.

Third-party libraries used:
- aiohttp
- dotenv
- starlette_discord
"""

import os
from typing import Union

from aiohttp import ClientResponseError
from dotenv import load_dotenv
from starlette_discord import DiscordOAuthClient, DiscordOAuthSession

from website.models import SessionData

# Load environment variables
load_dotenv()
aewfanhub_id = os.environ.get("AEWFANHUB_ID")
mod_id = os.environ.get("MOD_ROLE_ID")
elite_id = os.environ.get("ELITE_ROLE_ID")
my_user_id = os.environ.get("MY_USER_ID")


class CustomDiscordOAuthSession(DiscordOAuthSession):
    """
    Custom session class for Discord OAuth.

    Adds the `get_fanhub_roles` method to retrieve fanhub discord server roles.
    """

    async def get_fanhub_roles(self) -> Union[SessionData, bool]:
        """
        Get fanhub roles for the user.

        Returns:
            Union[SessionData, bool]: The session data if the user has the required roles, otherwise False.
        """
        try:
            # Attempt to request user roles from the Discord API
            data = await self._discord_request(f"/users/@me/guilds/{aewfanhub_id}/member")
        except ClientResponseError:
            # Handle response error by setting empty roles
            data = {"roles": []}

        user = await self.identify()
        guilds = await self.guilds()

        # elite contributors only, remove to allow more sign ins
        # Check if the user is an elite contributor, if not, return False
        if str(elite_id) not in data['roles']:
            return False

        # Construct and return the session data
        return SessionData(
            username=str(user),
            web_user=str(elite_id) in data['roles'] or str(mod_id) in data['roles'],
            web_admin=str(user.id) == my_user_id,
            fanhub_user=any(str(guild.id) == aewfanhub_id for guild in guilds),
            fanhub_elite=str(elite_id) in data['roles'],
            fanhub_admin=str(mod_id) in data['roles'],
        )


class CustomDiscordOAuthClient(DiscordOAuthClient):
    """
    Custom client class for Discord OAuth.

    Overrides the `session` and `session_from_token` methods to return the CustomDiscordOAuthSession class.
    """
    def session(self, code: str) -> CustomDiscordOAuthSession:
        """
        Create a new DiscordOAuthSession from an authorization code.

        Args:
            code (str): The OAuth2 code provided by the Discord API.

        Returns:
            CustomDiscordOAuthSession: A new OAuth session.
        """
        return CustomDiscordOAuthSession(
            code=code,
            token=None,
            client_id=self.client_id,
            client_secret=self.client_secret,
            scope=self.scope,
            redirect_uri=self.redirect_uri,
        )

    def session_from_token(self, token) -> CustomDiscordOAuthSession:
        """
        Create a new DiscordOAuthSession from an existing token.

        Args:
            token (dict): An existing (valid) access token to use instead of the OAuth code exchange.

        Returns:
            CustomDiscordOAuthSession: A new OAuth session.
        """
        return CustomDiscordOAuthSession(
            code=None,
            token=token,
            client_id=self.client_id,
            client_secret=self.client_secret,
            scope=self.scope,
            redirect_uri=self.redirect_uri,
        )
