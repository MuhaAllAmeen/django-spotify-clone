from datetime import datetime
import os
from dotenv import load_dotenv
import base64
from requests import post,get
import json
import urllib.parse
from django.http import JsonResponse
from django.shortcuts import render,redirect

load_dotenv()

REDIRECT_URI = "http://localhost:8000/callback"
AUTH_URL = "https://accounts.spotify.com/authorize"
API_BASE_URL = "https://api.spotify.com/v1/"

def login_with_spotify():
    scope = 'user-read-private user-read-email user-read-playback-state user-modify-playback-state streaming'
    params = {
        'client_id':os.getenv("SPOTIFY_CLIENT_ID"),
        'response_type':'code',
        'scope':scope,
        'redirect_uri':REDIRECT_URI,
        'show_dialog':True
    }
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    return auth_url

def callback(request):
    print(request.GET['code'])
    if 'error' in request.GET:
        return JsonResponse({"error":request.GET['error']})
    if 'code' in request.GET:
        req_body = {
            'code': request.GET.get('code', None),
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
            'client_id': os.getenv("SPOTIFY_CLIENT_ID"),
            'client_secret': os.getenv("SPOTIFY_CLIENT_SECRET")
        }
        response = post("https://accounts.spotify.com/api/token", data=req_body)
        token_info = response.json()
        request.session['access_token'] = token_info['access_token']
        request.session['refresh_token'] = token_info['refresh_token']
        request.session['expires_at'] = datetime.now().timestamp()+ token_info['expires_in']

        return '/'
    
def checkAccessTokenExpiry(request):
    if 'access_token' not in request.session:
        return redirect('/')
    if datetime.now().timestamp() > request.session['expires_at']:
        print('expired')
        refresh_token(request)

def get_devices(request):
    checkAccessTokenExpiry(request)
    headers = {
        'Authorization': f"Bearer {request.session["access_token"]}"

    }
    response = get('https://api.spotify.com/v1/me/player/devices',headers=headers)
    devices = response.json()
    return JsonResponse(devices).content

def refresh_token(request):
    if 'refresh_token' not in request.session:
        return '/'
    if datetime.now().timestamp() > request.session['expires_at']:
        req_body = {
            'grant_type': 'refresh_token',
            'refresh_token':request.session['refresh_token'],
            "client_id" : os.getenv("SPOTIFY_CLIENT_ID"),
            "client_secret" : os.getenv("SPOTIFY_CLIENT_SECRET")
        }
        response = post("https://accounts.spotify.com/api/token",data=req_body)
        new_token_info = response.json()
        request.session['access_token'] = new_token_info['access_token']
        request.session['expires_at'] = datetime.now().timestamp()+ new_token_info['expires_in']
         


def get_spotify_token():
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes
    ),"utf-8")
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic "+auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"

    }
    data = {"grant_type":"client_credentials"}
    result = post(url, headers=headers, data=data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token

    
def get_auth_header(token):
    return {"Authorization": "Bearer "+token}

def search_for_artists(request,artist_name):
    checkAccessTokenExpiry(request)
    token = request.session["access_token"]
    url = "https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    query = f"?q={artist_name}&type=artist&limit=1"
    query_url = url + query
    result = get(url=query_url,headers=headers)
    json_result = json.loads(result.content)["artists"]["items"]
    if len(json_result)==0:
        print("no artist found")
        return None
    else:
        return json_result[0]
    
def get_songs_by_artist(request, artist_id):
    checkAccessTokenExpiry(request)
    token = request.session["access_token"]
    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?country=AE"
    headers = get_auth_header(token)
    result = get(url,headers=headers)
    json_result = json.loads(result.content)["tracks"]
    return json_result

def get_track_details_by_ID(request,id):
    checkAccessTokenExpiry(request)
    token = request.session["access_token"]
    url = f"https://api.spotify.com/v1/tracks/{id}?market=AE"
    headers = get_auth_header(token)
    result = get(url,headers=headers)
    json_result = json.loads(result.content)
    return json_result

def play_track(request,context_uri):
    token = request.session['access_token']
    print(get_devices(request))
    url = "https://api.spotify.com/v1/me/player/play?device_id=4f6fa5c4fa1e32e710e9e11cd16e7a8c34b71e51"
    headers = {"Authorization": "Bearer "+token,
               "Content-Type": "application/json"
               }
    data = {
        "context_uri": context_uri,
        "offset": {
        "position": 5
        },
        "position_ms": 0
    }

    response = post(url,headers=headers,data=data)
    json_result = response.content
    print(json_result)