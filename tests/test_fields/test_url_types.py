from dataclasses import dataclass
from urllib.parse import urlsplit

from conformly import HttpUrl, Url, V, case, path


@dataclass
class Links:
    website: HttpUrl
    resource: Url


def test_public_url_markers_generate_supported_schemes() -> None:
    payload = case(Links, seed=0)
    assert urlsplit(payload["website"]).scheme in {"http", "https"}
    assert urlsplit(payload["resource"]).scheme in {
        "http",
        "https",
        "ftp",
        "ftps",
        "ws",
        "wss",
        "file",
    }


def test_public_url_markers_support_explicit_scheme_violation() -> None:
    payload = case(
        Links, valid=False, target=path("website").violate(V.WRONG_URL_SCHEME)
    )
    assert urlsplit(payload["website"]).scheme not in {"http", "https"}
    assert urlsplit(payload["resource"]).scheme
