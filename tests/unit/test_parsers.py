from app.scraper.parsers import parse_anime_list, parse_detail, parse_episodes


def test_parse_anime_list_on_going():
    html = '<ul><li><a class="hodebgst" href="https://x" title="A">A<color>On-Going</color></a></li></ul>'
    items = parse_anime_list(html)
    assert items[0]["status"] == "on-going"


def test_parse_anime_list_completed():
    html = '<ul><li><a class="hodebgst" href="https://x" title="A">A</a></li></ul>'
    items = parse_anime_list(html)
    assert items[0]["status"] == "completed"


def test_parse_detail_basic():
    html = '''
    <div class="fotoanime" style="overflow:inherit !important;">
      <img src="img.jpg" />
      <div class="infozin"><div class="infozingle">
        <p><span><b>Judul</b>: Title A</span></p>
        <p><span><b>Japanese</b>: JP</span></p>
        <p><span><b>Skor</b>: 8.5</span></p>
        <p><span><b>Produser</b>: Prod</span></p>
        <p><span><b>Tipe</b>: TV</span></p>
        <p><span><b>Status</b>: Completed</span></p>
        <p><span><b>Total Episode</b>: 12</span></p>
        <p><span><b>Durasi</b>: 24</span></p>
        <p><span><b>Tanggal Rilis</b>: 2025</span></p>
        <p><span><b>Studio</b>: Studio A</span></p>
        <p><span><b>Genre</b>: <a>Action</a>, <a>Comedy</a></span></p>
      </div></div>
      <div class="sinopc"><p>S1</p><p>S2</p></div>
    </div>
    '''
    detail, genres, synopsis = parse_detail(html)
    assert detail["title"] == "Title A"
    assert detail["title_japanese"] == "JP"
    assert detail["score"] == "8.5"
    assert detail["producer"] == "Prod"
    assert detail["type"] == "TV"
    assert detail["status_detail"] == "Completed"
    assert detail["total_episode"] == "12"
    assert detail["duration"] == "24"
    assert detail["release_date"] == "2025"
    assert detail["studio"] == "Studio A"
    assert detail["image_url"] == "img.jpg"
    assert genres == ["Action", "Comedy"]
    assert synopsis == "S1\n\nS2"


def test_parse_episodes():
    html = '''
    <div class="episodelist"><ul>
      <li><span><a href="https://x/ep1">Anime Episode 1 Subtitle Indonesia</a></span><span class="zeebr">1 Jan</span></li>
      <li><span><a href="https://x/ep2">Anime Episode 12 (End) Subtitle Indonesia</a></span><span class="zeebr">2 Jan</span></li>
    </ul></div>
    '''
    eps = parse_episodes(html)
    assert eps[0]["episode_url"] == "https://x/ep1"
    assert eps[0]["episode_number"] == 1
    assert eps[1]["episode_number"] == 12
