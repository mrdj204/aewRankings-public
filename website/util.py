"""
Webapp Utilities Module

This module provides utility functions for various webapp tasks.

Module Components:
- get_public_IP: Function to retrieve the public IP address of the machine.
- html_table: Function to generate an HTML table from JSON data.
- pickle_load: Function to load an object from a pickle file.
- pickle_save: Function to save an object to a pickle file.
"""
import logging
import os
import pickle
import socket
from typing import Union, Any

from json2html import json2html


def get_public_IP() -> str:
    """
    Get public IP address without relying on a web service.

    Returns the public IP address of the machine by connecting to a remote server.

    Returns:
    - str: The public IP address as a string if it can be retrieved successfully.
      An empty string is returned if there is an error.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # Use Google's DNS server
            s.connect(('8.8.8.8', 80))
            # Extract the IP address from the connection information.
            ip = s.getsockname()[0]
            return ip
    except Exception as e:
        logging.error("Error: {}".format(e))
        return ""


def html_table(data: Union[list, dict], id: str = "temp_id", classes: str = "") -> str:
    """
    Generate an HTML table from JSON data.

    Parameters:
    - data (Union[list, dict]): The JSON data to convert to an HTML table.
    - id (str, optional): The ID attribute for the HTML table.
    - classes (str, optional): CSS classes for the HTML table.

    Returns:
    - str: The generated HTML table as a string.
    """
    table_attributes = f'class="{classes}"' if classes else f'id="{id}"'
    return json2html.convert(json=data, table_attributes=table_attributes, escape=False)


def pickle_load(file_name: str) -> Any:
    """
    Load an object from a pickle file.

    Parameters:
        file_name (str): The name of the pickle file.

    Returns:
        object: The loaded object, or False if the file does not exist.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not os.path.exists(file_name):
        raise FileNotFoundError
    with open(file_name, "rb") as file:
        return pickle.load(file)


def pickle_save(file_name: str, obj: Any):
    """
    Save an object to a pickle file.

    Parameters:
        file_name (str): The name of the pickle file.
        obj (Any): The object to be saved.
    """
    with open(file_name, "wb") as file:
        pickle.dump(obj, file)


