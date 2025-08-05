from flask import Flask, render_template, request
import requests
import base64

app = Flask(__name__)

# Last.fm API key and Spotify credentials
LASTFM_API_KEY = "yxy"
CLIENT_ID = "zyz"
CLIENT_SECRET = "xyz"

def get_spotify_token():
    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    b64 = base64.b64encode(auth_str.encode()).decode()
    r = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={"Authorization": f"Basic {b64}"},
        data={"grant_type": "client_credentials"}
    )
    return r.json().get("access_token")

def spotify_search_track(track_name):
    token = get_spotify_token()
    r = requests.get(
        "https://api.spotify.com/v1/search",
        headers={"Authorization": f"Bearer {token}"},
        params={"q": track_name, "type": "track", "limit": 1}
    )
    items = r.json().get("tracks", {}).get("items", [])
    if not items:
        return None, None
    t = items[0]
    return t["name"], t["artists"][0]["name"]

def lastfm_similar_tracks(track_name, artist_name, limit=5):
    params = {
        "method": "track.getSimilar",
        "track": track_name,
        "artist": artist_name,
        "limit": limit,
        "api_key": LASTFM_API_KEY,
        "format": "json",
        "autocorrect": 1
    }
    r = requests.get("http://ws.audioscrobbler.com/2.0/", params=params)
    return r.json().get("similartracks", {}).get("track", [])

def spotify_album_data(track_name, artist_name):
    token = get_spotify_token()
    r = requests.get(
        "https://api.spotify.com/v1/search",
        headers={"Authorization": f"Bearer {token}"},
        params={"q": f"track:{track_name} artist:{artist_name}", "type": "track", "limit": 1}
    )
    items = r.json().get("tracks", {}).get("items", [])
    if not items:
        return None
    t = items[0]
    return {
        "name": t["name"],
        "artist": t["artists"][0]["name"],
        "image": t["album"]["images"][0]["url"] if t["album"]["images"] else "",
        "preview": t.get("preview_url")
    }

@app.route("/", methods=["GET", "POST"])
def index():
    recommendations = []
    error = None
    original = None
    if request.method == "POST":
        query = request.form.get("song", "").strip()
        original, artist = spotify_search_track(query)
        if not original:
            error = "Song not found on Spotify. Try again."
        else:
            similar = lastfm_similar_tracks(original, artist, limit=8)
            for s in similar[:5]:
                rec = spotify_album_data(s["name"], s["artist"]["name"])
                if rec:
                    recommendations.append(rec)
            if not recommendations:
                error = "No similar songs found."

    return render_template("index.html",
                           recommendations=recommendations,
                           error=error,
                           original=original)

if __name__ == "__main__":
    app.run(debug=True)
