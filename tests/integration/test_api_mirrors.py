from app.db import models


def test_get_episode_mirrors_empty(client, db_session):
    anime = models.Anime(source_url="u", title="t", status_list_page="completed")
    db_session.add(anime)
    db_session.flush()
    ep = models.Episode(anime_id=anime.id, episode_url="eu", episode_title="et")
    db_session.add(ep)
    db_session.flush()
    mirror = models.EpisodeMirror(
        episode_id=ep.id,
        quality="480p",
        provider_name="p",
        iframe_src="https://example.com/embed",
        mirror_id=1,
        mirror_i=0,
        mirror_q="480p",
        raw_data_content="",
        fetch_status="success",
    )
    db_session.add(mirror)
    db_session.commit()

    resp = client.get(f"/anime/episodes/{ep.id}/mirrors")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["iframe_src"] == "https://example.com/embed"
