def test_home_ok(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"Home" in res.data
