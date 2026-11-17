"""
From Dev to Prod 2 – Events API Testing
2. One Unit Test
"""

from werkzeug.security import check_password_hash


def test_user_password_hashing_behaves_correctly(user_params, user):
    """
    Test a User model behavior (e.g. password hashing/checking)
    """
    assert check_password_hash(user.password_hash, user_params["password"])


def test_user_to_dict_not_shows_password_hash(user):
    """
    Test small pure function/utility you have in your Events API.
    """
    user_dict = user.to_dict()
    assert "password_hash" not in user_dict
