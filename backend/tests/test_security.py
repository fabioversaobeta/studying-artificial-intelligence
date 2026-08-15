import uuid

import pytest

from app.core.security import (
    InvalidTokenError,
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_verify_succeeds_for_correct_password(self):
        hashed = hash_password("correct horse battery staple")
        assert verify_password("correct horse battery staple", hashed)

    def test_verify_fails_for_incorrect_password(self):
        hashed = hash_password("correct horse battery staple")
        assert not verify_password("wrong password", hashed)

    def test_hash_is_not_the_plaintext(self):
        hashed = hash_password("supersecret123")
        assert hashed != "supersecret123"


class TestTokens:
    def test_access_token_round_trips_to_the_same_user_id(self):
        user_id = uuid.uuid4()
        token = create_access_token(user_id)
        assert decode_token(token, TokenType.ACCESS) == user_id

    def test_refresh_token_rejected_as_access_token(self):
        user_id = uuid.uuid4()
        token = create_refresh_token(user_id)
        with pytest.raises(InvalidTokenError):
            decode_token(token, TokenType.ACCESS)

    def test_garbage_token_rejected(self):
        with pytest.raises(InvalidTokenError):
            decode_token("not-a-real-token", TokenType.ACCESS)
