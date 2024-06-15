import os
from django.shortcuts import render,redirect
from django.contrib import messages
from django.contrib.auth.models import User, auth
from django.contrib.auth.decorators import login_required
# from spotify_API import get_spotify_token,get_songs_by_artist,search_for_artists
from . import spotify_API


@login_required(login_url='login')
def index(request):
    if 'access_token' in request.session:
        devices = spotify_API.get_devices(request)
        print('devices',devices)
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
    artists = ["Drake", "Taylor Swift", "Dua Lipa", "Britney Spears", "Zack Knight"]
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

    # print(result)
    device_id = request.META.get('HTTP_X_DEVICE', '')
    print(device_id)
    track_duration = f"{int((result['duration_ms']/(1000*60))%60)}:{int((result['duration_ms']/1000)%60)}"
    context ={
        "album_cover":result['album']['images'][0]['url'],
        "track_name":result['name'],
        "track_uri":result['uri'],
        "artist_name":result['artists'][0]['name'],
        "duration_text":track_duration,
        "token":request.session["access_token"]
    }
    # print(context)
    # spotify_API.play_track(request,result['uri'])
    return render(request,'music.html',context)