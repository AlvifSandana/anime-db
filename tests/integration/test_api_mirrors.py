import base64

from fastapi.testclient import TestClient

from app.main import create_app
from app.db.session import SessionLocal, Base, engine
from app.db import models


def setup_function():
    Base.metadata.create_all(bind=engine)


def teardown_function():
    Base.metadata.drop_all(bind=engine)


def test_get_episode_mirrors_empty():
    app = create_app()
    client = TestClient(app)

    # Insert dummy anime, episode, mirror
    session = SessionLocal()
    anime = models.Anime(source_url="u", title="t", status_list_page="completed")
    session.add(anime)
    session.flush()
    ep = models.Episode(anime_id=anime.id, episode_url="eu", episode_title="et")
    session.add(ep)
    session.flush()
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
    session.add(mirror)
    session.commit()
    ep_id = ep.id
    session.close()

    resp = client.get(f"/anime/episodes/{ep_id}/mirrors")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["iframe_src"] == "https://example.com/embed"
