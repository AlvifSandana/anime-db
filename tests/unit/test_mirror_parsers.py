from app.scraper.parsers import parse_mirrors, decode_embed_base64_to_iframe_src
import base64


def test_parse_mirrors_basic():
    html = '''
    <div class="mirrorstream">
      <ul class="m480p">
        <li><a data-content="eyJpZCI6MSwiaSI6MCwicSI6IjQ4MHAifQ==">prov1</a></li>
        <li><a data-content="eyJpZCI6MSwiaSI6MSwicSI6IjQ4MHAifQ==">prov2</a></li>
      </ul>
      <ul class="m720p">
        <li><a data-content="eyJpZCI6MiwiaSI6MCwicSI6IjcyMHAifQ==">prov3</a></li>
      </ul>
    </div>
    '''
    mirrors = parse_mirrors(html)
    assert len(mirrors) == 3
    assert mirrors[0]["quality"] == "480p"
    assert mirrors[0]["provider_name"] == "prov1"
    assert mirrors[0]["mirror_id"] == 1
    assert mirrors[0]["mirror_i"] == 0
    assert mirrors[0]["mirror_q"] == "480p"
    assert mirrors[2]["quality"] == "720p"


def test_decode_embed_base64_to_iframe_src():
    html = '<div><iframe src="https://example.com/embed"></iframe></div>'
    b64 = base64.b64encode(html.encode()).decode()
    src = decode_embed_base64_to_iframe_src(b64)
    assert src == "https://example.com/embed"
