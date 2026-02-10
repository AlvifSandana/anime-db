from typing import List, Tuple, Optional
from selectolax.parser import HTMLParser
import base64
import json



def parse_anime_list(html: str) -> List[dict]:
    tree = HTMLParser(html)
    results: List[dict] = []
    for node in tree.css("li a.hodebgst"):
        title = (node.text() or "").strip()
        href_attr = node.attributes.get("href")
        href = href_attr.strip() if href_attr else ""
        status = "completed"
        color_el = node.css_first("color")
        if color_el and "on-going" in color_el.text().lower():
            status = "on-going"
        results.append({"title": title, "href": href, "status": status})
    return results


def parse_detail(html: str) -> Tuple[dict, List[str], str]:
    tree = HTMLParser(html)
    detail: dict = {
        "image_url": None,
        "title": None,
        "title_japanese": None,
        "score": None,
        "producer": None,
        "type": None,
        "status_detail": None,
        "total_episode": None,
        "duration": None,
        "release_date": None,
        "studio": None,
    }
    genres: List[str] = []
    synopsis: str = ""

    foto = tree.css_first("div.fotoanime")
    if foto:
        img = foto.css_first("img")
        if img:
            detail["image_url"] = img.attributes.get("src")

        info_block = foto.css_first("div.infozin div.infozingle")
        if info_block:
            for p in info_block.css("p"):
                text = p.text().strip()
                if ":" not in text:
                    continue
                label, _, value = text.partition(":")
                key = label.strip().lower()
                val = value.strip()
                if key == "judul":
                    detail["title"] = val
                elif key == "japanese":
                    detail["title_japanese"] = val
                elif key == "skor":
                    detail["score"] = val
                elif key == "produser":
                    detail["producer"] = val
                elif key == "tipe":
                    detail["type"] = val
                elif key == "status":
                    detail["status_detail"] = val
                elif key == "total episode":
                    detail["total_episode"] = val
                elif key == "durasi":
                    detail["duration"] = val
                elif key == "tanggal rilis":
                    detail["release_date"] = val
                elif key == "studio":
                    detail["studio"] = val
                elif key == "genre":
                    anchors = p.css("a")
                    for a in anchors:
                        name = a.text().strip()
                        if name:
                            genres.append(name)

    sinopc = tree.css_first("div.sinopc")
    if sinopc:
        paras = [p.text().strip() for p in sinopc.css("p") if p.text()]
        synopsis = "\n\n".join(paras)

    return detail, genres, synopsis


def parse_episodes(html: str) -> List[dict]:
    tree = HTMLParser(html)
    episodes: List[dict] = []
    for li in tree.css("div.episodelist ul li"):
        a = li.css_first("a")
        if not a:
            continue
        url = a.attributes.get("href", "").strip()
        title = (a.text() or "").strip()
        date_text = None
        date_span = li.css_first("span.zeebr")
        if date_span:
            date_text = date_span.text().strip()

        episode_number: Optional[int] = None
        lower_title = title.lower()
        if "episode" in lower_title:
            parts = lower_title.split("episode")
            if len(parts) > 1:
                tail = parts[1].strip()
                num_str = "".join(ch for ch in tail if ch.isdigit())
                if num_str:
                    episode_number = int(num_str)

        episodes.append(
            {
                "episode_url": url,
                "episode_title": title,
                "episode_date_text": date_text,
                "episode_number": episode_number,
            }
        )
    return episodes


def parse_mirrors(html: str) -> List[dict]:
    tree = HTMLParser(html)
    mirrors: List[dict] = []
    for ul in tree.css("div.mirrorstream ul"):
        cls = ul.attributes.get("class") or ""
        quality = cls[1:] if cls.startswith("m") else cls
        for a in ul.css("li a"):
            dc = a.attributes.get("data-content")
            if not dc:
                continue
            try:
                payload = json.loads(base64.b64decode(dc + "===").decode("utf-8"))
            except Exception:
                continue
            if not {"id", "i", "q"}.issubset(payload.keys()):
                continue
            provider_raw = a.text()
            provider_text = provider_raw.strip() if isinstance(provider_raw, str) else ""
            mirrors.append(
                {
                    "quality": quality,
                    "provider_name": provider_text,
                    "raw_data_content": dc,
                    "mirror_id": payload.get("id"),
                    "mirror_i": payload.get("i"),
                    "mirror_q": payload.get("q"),
                }
            )
    return mirrors


def decode_embed_base64_to_iframe_src(b64_html: str) -> Optional[str]:
    try:
        html = base64.b64decode(b64_html + "===").decode("utf-8", errors="ignore")
    except Exception:
        return None
    doc = HTMLParser(html)
    iframe = doc.css_first("iframe")
    if iframe:
        return iframe.attributes.get("src")
    return None
