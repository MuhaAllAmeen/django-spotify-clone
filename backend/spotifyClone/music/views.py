import os
from django.shortcuts import render,redirect
from django.contrib import messages
from django.contrib.auth.models import User, auth
from django.contrib.auth.decorators import login_required
from . import spotify_API


@login_required(login_url='login')
def index(request):
    if 'access_token' in request.session:
        artists_data = get_top_artists(request)
        songs_data = get_top_songs(request)
        return render (request,'index.html',{"top_artists":artists_data,"top_tracks":songs_data})    
    else:
        url = spotify_API.login_with_spotify()
        return redirect(url)
    

def callback(request):
    url = spotify_API.callback(request)
    return redirect(url)

def get_top_artists(request):
    artists = ["Drake", "Taylor Swift", "Dua Lipa", "Britney Spears", "Zack Knight", "Tyga"]
    top_artists_details = []
    for artist in artists:
        result = spotify_API.search_for_artists(request,artist)
        top_artists_details.append((result["name"],result["id"],result["images"][0]["url"]))
    return top_artists_details

def get_top_songs(request):
    result = spotify_API.search_for_artists(request,"Drake")
    artist_id = result["id"]
    songs = spotify_API.get_songs_by_artist(request,artist_id)
    top_songs = []
    for song in songs:
        top_songs.append((song["name"],song["id"],song["album"]["images"][0]["url"]))
    return top_songs


def login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user_login = auth.authenticate(username=username, password=password)
        print('login',user_login)

        if user_login is not None:
            auth.login(request,user_login)
            return redirect('/')
        else:
            messages.info(request,'User not found or credentials invalid')
            return redirect('login')
    else:
        return render (request,'login.html')

def signup(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        password2 = request.POST["password2"]
        if password == password2:
            if User.objects.filter(email=email).exists():
                messages.info(request,"email already exists")
                return redirect('signup')
            elif User.objects.filter(username=username).exists():
                messages.info(request,"username already exists")
                return redirect('signup')
            else:
                user = User.objects.create_user(username=username,email=email,password=password)
                user.save()

                return login(request)
                
        else:
            messages.info(request,"Password are not matching")
            return redirect('signup')
    else:
        return render (request,'signup.html')

@login_required(login_url='login')
def logout(request):
    auth.logout(request)
    return redirect('login')

def music(request,id):
    result = spotify_API.get_track_details_by_ID(request,id)

    context ={
        "album_cover":result['album']['images'][0]['url'],
        "track_name":result['name'],
        "track_uri":result['uri'],
        "artist_name":result['artists'][0]['name'],
        "duration_text":result['duration_ms'],
        "token":request.session["access_token"]
    }
    return render(request,'music.html',context)

def profile(request,id):
    result = spotify_API.get_artist_by_ID(request=request,id=id)
    top_tracks = spotify_API.get_songs_by_artist(request,id)
    top_tracks_list = []
    for track in top_tracks:
        track_duration = f"{int((track['duration_ms']/(1000*60))%60)}:{int((track['duration_ms']/1000)%60)}"
        top_tracks_list.append(
            {
                "track_name":track["name"],
                "track_duration":track_duration,
                "track_image":track["album"]["images"][0]["url"],
                "track_id":track["id"],
                "track_popularity":track["popularity"]
            }
        )
    context = {
        "artist_name": result['name'],
        "artist_image" : result['images'][0]['url'],
        "artist_popularity": result['popularity'],
        "top_tracks":top_tracks_list
    }
    return render (request, 'profile.html',context)

def search(request):
    if request.method == "POST":
        query = request.POST['search_query']
        result = spotify_API.search(request=request,query=query)
        artist_results = result['artists']['items']
        track_results = result['tracks']['items']
        tracks_list= []
        artists_list = []
        for artist in artist_results:
            if len(artist['images'])>0:
                artists_list.append({
                    "artist_name":artist["name"],
                    "artist_id":artist["id"],
                    "artist_popularity":artist["popularity"],
                    "artist_image": artist['images'][0]['url']
                })
        for track in track_results:
            track_duration = f"{int((track['duration_ms']/(1000*60))%60)}:{int((track['duration_ms']/1000)%60)}"
            tracks_list.append(
                {
                    "track_name": track['name'],
                    "track_id":track['id'],
                    "track_popularity":track['popularity'],
                    "track_duration":track_duration,
                    "track_image":track['album']['images'][0]['url'],
                    "track_artist": track['artists'][0]['name']
                }
            )
        context = {
            "track_results": tracks_list,
            "artist_results": artists_list
        }
        return render(request,'search.html',context)
    else:
        return render(request,'search.html')