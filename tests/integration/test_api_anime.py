from app.db import models


def test_list_anime_empty(client):
    resp = client.get("/anime/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_get_anime_detail_not_found(client):
    resp = client.get("/anime/999")
    assert resp.status_code == 404


def test_get_anime_detail_success(client, db_session):
    anime = models.Anime(source_url="u", title="t", status_list_page="completed")
    db_session.add(anime)
    db_session.commit()

    resp = client.get(f"/anime/{anime.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == anime.id
    assert data["title"] == "t"


def test_get_anime_episodes_not_found(client):
    resp = client.get("/anime/999/episodes")
    assert resp.status_code == 404


def test_get_anime_episodes_success(client, db_session):
    anime = models.Anime(source_url="u", title="t", status_list_page="completed")
    db_session.add(anime)
    db_session.flush()
    ep = models.Episode(anime_id=anime.id, episode_url="eu", episode_title="Episode 1", episode_number=1)
    db_session.add(ep)
    db_session.commit()

    resp = client.get(f"/anime/{anime.id}/episodes?order=desc&limit=50&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == ep.id
