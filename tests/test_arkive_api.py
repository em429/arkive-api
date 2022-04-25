from starlette.testclient import TestClient

from arkive_api import __version__

from arkive_api.api import app

client = TestClient(app)


def test_version():
    assert __version__ == '0.0.1'


# def test_new_url():
#     """
#     Test new URL that is NOT yet in the database
#     """
#     response = client.get("/index.hu")
#     assert response.status_code == 200
#     response_json = response.json()
#     assert response_json["status"] == "success"


def test_existing_url():
    """
    Test URL that is in the database already
    """
    response1 = client.get("/story.hu")
    assert response1.status_code == 200

    response2 = client.get("/story.hu")
    assert response2.status_code == 200
    response_json = response2.json()
    assert response_json["status"] == "duplicate"

