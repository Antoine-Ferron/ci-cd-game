import requests

url = "http://localhost:8081"

def test_user_creation():
    response = requests.get(url + "/player/new/test_user_1")
    assert response.status_code == 200

    user = response.json()
    print(user)
    assert user["playerId"]
    assert user['key']

    # info = requests.get(url + f"/player/{user['playerId']}?key={user['key']}")
    info = requests.get(
        f"{url}/player/{user['playerId']}",
        params={"key": user['key']}  # encodage automatique
    )
    # print('url info:', info)/
    data = info.json()
    assert "money" in data
    assert "stations" in data
    assert "ships" in data

