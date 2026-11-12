"""Microsoft hesabıyla giriş (cihaz kodu akışı) ve hesap saklama.

Akış: Microsoft OAuth -> Xbox Live -> XSTS -> Minecraft servisleri -> profil.
Parola launcher'a hiç girilmez; kullanıcı tarayıcıda Microsoft'un sayfasında onaylar.
"""
import json
import os
import time

from . import http

MS_DEVICE = "https://login.microsoftonline.com/consumers/oauth2/v2.0/devicecode"
MS_TOKEN = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
XBL_AUTH = "https://user.auth.xboxlive.com/user/authenticate"
XSTS_AUTH = "https://xsts.auth.xboxlive.com/xsts/authorize"
MC_LOGIN = "https://api.minecraftservices.com/authentication/login_with_xbox"
MC_PROFILE = "https://api.minecraftservices.com/minecraft/profile"
SCOPE = "XboxLive.signin offline_access"

XSTS_ERRORS = {
    2148916233: "Bu Microsoft hesabının Xbox profili yok. xbox.com üzerinden oluşturun.",
    2148916235: "Xbox Live bu ülkede kullanılamıyor.",
    2148916236: "Hesap için yetişkin doğrulaması gerekiyor.",
    2148916237: "Hesap için yetişkin doğrulaması gerekiyor.",
    2148916238: "Çocuk hesabı: bir yetişkinin hesabı bir aileye eklemesi gerekiyor.",
}


class AuthError(Exception):
    pass


def client_id(paths):
    cid = os.environ.get("PYLAUNCHER_CLIENT_ID")
    if not cid and paths.config.is_file():
        cid = json.loads(paths.config.read_text(encoding="utf-8")).get("client_id")
    if not cid:
        raise AuthError(
            "Microsoft girişi için bir Azure uygulama kimliği (client ID) gerekli.\n"
            "README'deki 'Microsoft girişi' bölümüne bakın, sonra:\n"
            "  python -m pylauncher config client_id <KİMLİK>"
        )
    return cid


# --- hesap deposu -----------------------------------------------------------

def load_accounts(paths):
    if paths.accounts.is_file():
        return json.loads(paths.accounts.read_text(encoding="utf-8"))
    return {"active": None, "accounts": {}}


def save_accounts(paths, data):
    paths.root.mkdir(parents=True, exist_ok=True)
    tmp = paths.accounts.with_suffix(".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, paths.accounts)


def active_account(paths):
    data = load_accounts(paths)
    return data["accounts"].get(data.get("active") or "")


def logout(paths, name=None):
    data = load_accounts(paths)
    if name:
        uuid = next((u for u, a in data["accounts"].items() if a["name"] == name), None)
    else:
        uuid = data.get("active")
    if uuid not in data["accounts"]:
        return False
    del data["accounts"][uuid]
    if data.get("active") == uuid:
        data["active"] = next(iter(data["accounts"]), None)
    save_accounts(paths, data)
    return True


# --- giriş zinciri ----------------------------------------------------------

def start_device_login(paths):
    """Kullanıcıya gösterilecek kodu ve adresi döndürür."""
    try:
        return http.fetch_json(
            MS_DEVICE, data={"client_id": client_id(paths), "scope": SCOPE}, form=True
        )
    except http.HttpError as e:
        raise AuthError(f"Microsoft girişi başlatılamadı: {e}") from None


def poll_device_login(paths, device, cancelled=lambda: False):
    """Kullanıcı tarayıcıda onaylayana kadar bekler; Microsoft token'larını döndürür."""
    interval = int(device.get("interval", 5))
    deadline = time.time() + int(device.get("expires_in", 900))
    while time.time() < deadline:
        if cancelled():
            raise AuthError("Giriş iptal edildi.")
        time.sleep(interval)
        try:
            return http.fetch_json(
                MS_TOKEN,
                data={
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "client_id": client_id(paths),
                    "device_code": device["device_code"],
                },
                form=True,
            )
        except http.HttpError as e:
            err = _json(e.body).get("error")
            if err == "authorization_pending":
                continue
            if err == "slow_down":
                interval += 5
                continue
            raise AuthError(f"Microsoft girişi başarısız: {err or e}") from None
    raise AuthError("Giriş kodunun süresi doldu.")


def _json(text):
    try:
        return json.loads(text)
    except ValueError:
        return {}


def _refresh_ms(paths, refresh_token):
    try:
        return http.fetch_json(
            MS_TOKEN,
            data={
                "grant_type": "refresh_token",
                "client_id": client_id(paths),
                "refresh_token": refresh_token,
                "scope": SCOPE,
            },
            form=True,
        )
    except http.HttpError as e:
        raise AuthError(f"Oturum yenilenemedi, yeniden giriş yapın: {e}") from None


def _minecraft_login(ms_access_token):
    """Microsoft token'ından Minecraft token'ı ve profilini üretir."""
    try:
        xbl = http.fetch_json(XBL_AUTH, data={
            "Properties": {
                "AuthMethod": "RPS",
                "SiteName": "user.auth.xboxlive.com",
                "RpsTicket": f"d={ms_access_token}",
            },
            "RelyingParty": "http://auth.xboxlive.com",
            "TokenType": "JWT",
        })
    except http.HttpError as e:
        raise AuthError(f"Xbox Live girişi başarısız: {e}") from None
    uhs = xbl["DisplayClaims"]["xui"][0]["uhs"]
    try:
        xsts = http.fetch_json(XSTS_AUTH, data={
            "Properties": {"SandboxId": "RETAIL", "UserTokens": [xbl["Token"]]},
            "RelyingParty": "rp://api.minecraftservices.com/",
            "TokenType": "JWT",
        })
    except http.HttpError as e:
        code = _json(e.body).get("XErr")
        raise AuthError(XSTS_ERRORS.get(code, f"Xbox yetkilendirmesi başarısız: {e}")) from None
    try:
        mc = http.fetch_json(
            MC_LOGIN, data={"identityToken": f"XBL3.0 x={uhs};{xsts['Token']}"}
        )
    except http.HttpError as e:
        hint = ""
        if e.status == 403:
            hint = (
                " (Azure uygulamanızın Minecraft API izni olmayabilir; "
                "README'deki 'Microsoft girişi' bölümüne bakın.)"
            )
        raise AuthError(f"Minecraft servislerine giriş başarısız: {e}{hint}") from None
    try:
        profile = http.fetch_json(
            MC_PROFILE, headers={"Authorization": f"Bearer {mc['access_token']}"}
        )
    except http.HttpError as e:
        if e.status == 404:
            raise AuthError(
                "Bu hesapta Minecraft: Java Edition yok (ya da profil adı henüz seçilmemiş)."
            ) from None
        raise AuthError(f"Profil alınamadı: {e}") from None
    return mc, profile


def _store(paths, ms, mc, profile):
    data = load_accounts(paths)
    account = {
        "name": profile["name"],
        "uuid": profile["id"],
        "access_token": mc["access_token"],
        "expires_at": int(time.time()) + int(mc.get("expires_in", 86400)),
        "refresh_token": ms["refresh_token"],
    }
    data["accounts"][profile["id"]] = account
    data["active"] = profile["id"]
    save_accounts(paths, data)
    return account


def finish_login(paths, ms):
    mc, profile = _minecraft_login(ms["access_token"])
    return _store(paths, ms, mc, profile)


def session(paths, offline=False):
    """Oyunu başlatmak için oturum bilgisi döndürür; token'ı gerekirse yeniler.

    Çevrimdışı mod yalnızca daha önce giriş yapıp oyuna sahip olduğu doğrulanmış
    bir hesap için kullanılabilir (internet yokken oynamak için).
    """
    account = active_account(paths)
    if not account:
        raise AuthError("Önce giriş yapın: python -m pylauncher login")
    if offline:
        return {"name": account["name"], "uuid": account["uuid"],
                "token": "0", "type": "legacy"}
    if account["expires_at"] - 120 < time.time():
        ms = _refresh_ms(paths, account["refresh_token"])
        account = finish_login(paths, ms)
    return {"name": account["name"], "uuid": account["uuid"],
            "token": account["access_token"], "type": "msa"}
