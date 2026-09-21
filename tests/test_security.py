from app.utils.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hash_roundtrip():
    hashed = hash_password("Sup3rSecret!")
    assert hashed != "Sup3rSecret!"
    assert verify_password("Sup3rSecret!", hashed)
    assert not verify_password("wrong-password", hashed)


def test_jwt_roundtrip():
    token = create_access_token("alice", extra_claims={"role": "ADMIN"})
    payload = decode_access_token(token)
    assert payload["sub"] == "alice"
    assert payload["role"] == "ADMIN"


def test_jwt_rejects_tampered_token():
    token = create_access_token("alice")
    header, payload, signature = token.split(".")
    flipped = "A" if payload[-1] != "A" else "B"
    tampered = f"{header}.{payload[:-1]}{flipped}.{signature}"
    try:
        decode_access_token(tampered)
        assert False, "expected decode to fail"
    except ValueError:
        pass
