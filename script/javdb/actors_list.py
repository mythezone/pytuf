from base import BaseScraper, MongoDB, page_generator
import time
import random


def update_actors(
    category: str, start_page: int, end_page: int, sleep_range: tuple[int, int] = (1, 4)
):
    d = {
        "text": {"name": "strong"},
        "href": {
            "href": "div.actor-box > a",
        },
        "src": {"avatar": "img.avatar"},
        "title": {"title": "div.actor-box > a"},
    }
    scraper = BaseScraper()
    db = MongoDB()
    collection_name = "actors"

    pages = page_generator(
        "https://javdb561.com", f"/actors/{category}", start_page, end_page
    )
    for page in pages:
        scraper.init(page)
        actors_list = scraper.get_list(scraper.soup, "div.actor-box")
        res = []
        for actor in actors_list:
            actor_info = scraper.get_dict(actor, d)
            actor_info["category"] = category
            res.append(actor_info)

        # 以 href 作为唯一键，已存在则更新；不存在则插入
        resp = db.insert_many(
            collection_name, res, key="href", update_on_duplicate=True
        )
        print(f"Inserted {len(resp)} documents from {page}")
        time.sleep(random.randint(*sleep_range))
