"""İndirme yardımcıları: yeniden deneme, SHA-1 doğrulama, paralel indirme."""
import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from . import NAME, __version__

USER_AGENT = f"{NAME}/{__version__}"
RETRIES = 4


class HttpError(Exception):
    def __init__(self, url, status, body=""):
        super().__init__(f"{url} -> HTTP {status} {body[:300]}")
        self.url, self.status, self.body = url, status, body


def request(url, data=None, headers=None, form=False, timeout=60):
    """GET (data yoksa) ya da POST yapar, gövdeyi bytes olarak döndürür."""
    hdrs = {"User-Agent": USER_AGENT, "Accept": "application/json, */*"}
    body = None
    if data is not None:
        if form:
            body = urllib.parse.urlencode(data).encode()
            hdrs["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            body = json.dumps(data).encode()
            hdrs["Content-Type"] = "application/json"
    hdrs.update(headers or {})
    last = None
    for attempt in range(RETRIES):
        try:
            req = urllib.request.Request(url, data=body, headers=hdrs)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            text = e.read().decode("utf-8", "replace")
            if e.code < 500 and e.code != 429:
                raise HttpError(url, e.code, text) from None
            last = HttpError(url, e.code, text)
        except (urllib.error.URLError, OSError) as e:
            last = e
        time.sleep(1.5 * (attempt + 1))
    raise last


def fetch_json(url, **kw):
    return json.loads(request(url, **kw))


def sha1_of(path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def is_valid(path, sha1=None, size=None) -> bool:
    p = Path(path)
    if not p.is_file():
        return False
    if sha1:
        return sha1_of(p) == sha1
    if size is not None:
        return p.stat().st_size == size
    return p.stat().st_size > 0


def download(url, path, sha1=None, size=None):
    """Dosya zaten geçerliyse dokunmaz; değilse indirip doğrular."""
    path = Path(path)
    if is_valid(path, sha1, size):
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".part{os.getpid()}")
    last = None
    for _ in range(2):
        tmp.write_bytes(request(url, timeout=120))
        if not sha1 or sha1_of(tmp) == sha1:
            os.replace(tmp, path)
            return True
        last = f"SHA-1 uyuşmuyor: {url}"
    tmp.unlink(missing_ok=True)
    raise IOError(last)


class Job:
    __slots__ = ("url", "path", "sha1", "size")

    def __init__(self, url, path, sha1=None, size=None):
        self.url, self.path, self.sha1, self.size = url, Path(path), sha1, size


def download_many(jobs, progress=None, label="", workers=16):
    """jobs listesini paralel indirir. progress(label, biten, toplam) çağrılır."""
    seen, unique = set(), []
    for j in jobs:
        if j.path not in seen:
            seen.add(j.path)
            unique.append(j)
    total, done = len(unique), 0
    if progress:
        progress(label, 0, total)
    if not unique:
        return
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(download, j.url, j.path, j.sha1, j.size) for j in unique]
        try:
            for f in as_completed(futures):
                f.result()
                done += 1
                if progress:
                    progress(label, done, total)
        except BaseException:
            for f in futures:
                f.cancel()
            raise
