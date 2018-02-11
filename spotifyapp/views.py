from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.core.urlresolvers import reverse

import spotipy.util as util
import spotipy
import math
import operator

import json
import requests


def callback(request):
    code = request.GET.get('code')

    headers = {
        'Authorization': 'Basic MmI1NjBiZWM2YWJhNDNlNmFhOTcwNzIzOTJjNTcwNzc6OGFlMDFiNGE3ZGUyNGY4M2EzMmM4MTE5ZjIzYTcyNTQ=',
    }

    data = [
        ('grant_type', 'authorization_code'),
        ('code', code),
        ('redirect_uri', 'http://localhost:8000/callback'),
    ]

    response = requests.post('https://accounts.spotify.com/api/token', headers=headers, data=data)

    access_token = json.loads(response.text)['access_token']
    refresh_token = json.loads(response.text)['refresh_token']

    request.session['access_token'] = access_token
    request.session['refresh_token'] = refresh_token

    return redirect(reverse('app'))

    return redirect(reverse("app"), {'val_base_song': val_base_song, 'val_de': val_de, 'val_dl': val_dl, 'val_dv': val_dv,
                            'val_el': val_el, 'val_ev': val_ev, 'val_lv': val_lv})


def home(request):
    return render(request, 'index.html')


def app(request):
    val_base_song = request.session['val_base_song'] if 'val_base_song' in request.session else ""
    val_de = request.session['val_de'] if 'val_de' in request.session else 0
    val_dl = request.session['val_dl'] if 'val_dl' in request.session else 0
    val_dv = request.session['val_dv'] if 'val_dv' in request.session else 0
    val_el = request.session['val_el'] if 'val_el' in request.session else 0
    val_ev = request.session['val_ev'] if 'val_ev' in request.session else 0
    val_lv = request.session['val_lv'] if 'val_lv' in request.session else 0

    return render(request, 'app.html', {'val_base_song': val_base_song, 'val_de': val_de, 'val_dl': val_dl,
                                        'val_dv': val_dv, 'val_el': val_el, 'val_ev': val_ev, 'val_lv': val_lv})


def login(request):
    url = 'https://accounts.spotify.com/authorize/?client_id=2b560bec6aba43e6aa97072392c57077&response_type=code&redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fcallback&scope=user-library-read%20playlist-modify-private%20playlist-modify-public'

    return redirect(url)


def post(request):
    access_token = request.session['access_token']
    refresh_token = request.session['refresh_token']

    # Get user inputs
    base_song = request.POST.get('base_song')

    priority_d = float(request.POST.get('priority_d'))
    priority_e = float(request.POST.get('priority_e'))
    priority_l = float(request.POST.get('priority_l'))
    priority_v = float(request.POST.get('priority_v'))

    # Add values to session
    request.session['val_base_song'] = base_song
    request.session['val_de'] = float(request.POST.get('val_de'))
    request.session['val_dl'] = float(request.POST.get('val_dl'))
    request.session['val_dv'] = float(request.POST.get('val_dv'))
    request.session['val_el'] = float(request.POST.get('val_el'))
    request.session['val_ev'] = float(request.POST.get('val_ev'))
    request.session['val_lv'] = float(request.POST.get('val_lv'))

    # Create auth object
    sp = spotipy.Spotify(auth=access_token)

    # takes track id, returns recommended tracks and their features
    def get_recommendation_features(tid):
        # recommendations for base track and their features
        recommendations = sp.recommendations(seed_tracks=[tid], limit=100)

        recommended_ids = []

        for recommendation in recommendations['tracks']:
            recommended_ids.append(recommendation['id'])

        features = sp.audio_features(recommended_ids)

        # initialize tracks dict
        tracks = {}

        # create a key-value dict with track_id and features
        for feature in features:
            tracks[feature['uri']] = feature

        # clean dict, remove unnecessary keys
        for track, value in tracks.items():
            for key in ['key', 'loudness', 'mode', 'speechiness', 'acousticness', 'instrumentalness', 'type', 'id',
                        'uri',
                        'track_href', 'analysis_url', 'duration_ms', 'time_signature']:
                value.pop(key)

        return tracks

    # custom sort key
    def key(x):
        return x[0]["distance"]  # return ISO date string

    # base track
    tid = base_song

    # weights which are taken from priority vector
    w1 = priority_d
    w2 = priority_e
    w3 = priority_l
    w4 = priority_v

    # base track's features
    base_track_features = sp.audio_features(tid)
    base_track_features = base_track_features[0]

    # remove unnecessary keys from base track
    for key in ['key', 'loudness', 'mode', 'speechiness', 'acousticness', 'instrumentalness', 'type', 'id', 'uri',
                'track_href', 'analysis_url', 'duration_ms', 'time_signature']:
        base_track_features.pop(key)

    # get recommended tracks and their features
    tracks = get_recommendation_features(tid)

    # initiate distances dict
    distances = []

    # calculate distances between recommendations and base track
    for id, ftrs in tracks.items():
        temp_dict = {}
        temp_dict['id'] = id
        temp_dict['distance'] = math.sqrt(1 / w1 * ((ftrs['danceability'] - base_track_features['danceability']) ** 2) +
                                          1 / w2 * ((ftrs['energy'] - base_track_features['energy']) ** 2) +
                                          1 / w3 * ((ftrs['liveness'] - base_track_features['liveness']) ** 2) +
                                          1 / w4 * ((ftrs['valence'] - base_track_features['valence']) ** 2))
        temp_dict['tempo'] = ftrs['tempo']

        distances.append(temp_dict)

    # sort by distances descending
    sorted_distances = sorted(distances, key=operator.itemgetter('distance'))

    # print values
    # for key in sorted_distances:
    #    print(key)

    # declare today's top hits playlist spotify id
    todays_top_hits_playlist_id = "37i9dQZF1DXcBWIGoYBM5M"

    todays_tracks = sp.user_playlist_tracks("spotify", todays_top_hits_playlist_id)

    todays_tracks_ids = []

    for todays_track in todays_tracks['items']:
        todays_tracks_ids.append(todays_track['track']['id'])

    todays_tracks_features = sp.audio_features(todays_tracks_ids)
    todays_tracks_tempo = []

    # get today's top hits playlist tracks tempo list
    for todays_tracks_feature in todays_tracks_features:
        if todays_tracks_feature is not None:
            todays_tracks_tempo.append(todays_tracks_feature['tempo'])

    # get first 10 tracks from today's top hits playlist
    todays_tracks_tempo = todays_tracks_tempo[:10]

    # plot today's top hits playlist tempo distribution
    # plt.plot(todays_tracks_tempo)
    # plt.title('Tempo Distribution Of Playlist')
    # plt.ylabel('Tempo (bpm)')
    # plt.show()

    # placement algorithm
    final_playlist = []
    final_playlist_tempo = []

    for hit in todays_tracks_tempo:
        playlist_comparison = []
        for song in sorted_distances:
            temp_vals = {}
            temp_vals['id'] = song['id']
            temp_vals['distempo'] = abs(hit - song['tempo']) * song['distance']
            temp_vals['tempo'] = song['tempo']
            playlist_comparison.append(temp_vals)

        # the song with best distance-tempo numbers
        min_distempo = min(playlist_comparison, key=lambda x: x['distempo'])

        # add that song to final playlist
        final_playlist.append(min_distempo['id'])
        final_playlist_tempo.append(min_distempo['tempo'])

        # and remove it from comparison list
        sorted_distances = [d for d in sorted_distances if d['id'] != min_distempo['id']]

    print(final_playlist)

    headers = {
        'Authorization': 'Bearer ' + access_token,
        'Content-Type': 'application/json',
    }

    data = '{"name":"Dissonance Song Recommendations", "public":false, "description": "A playlist that contains 10 songs based on user preferences."}'

    response = requests.post('https://api.spotify.com/v1/users/coaltunbey/playlists', headers=headers, data=data)

    if 'error' in json.loads(response.text):
        headers = {
            'Authorization': 'Basic MmI1NjBiZWM2YWJhNDNlNmFhOTcwNzIzOTJjNTcwNzc6OGFlMDFiNGE3ZGUyNGY4M2EzMmM4MTE5ZjIzYTcyNTQ=',
        }

        data = [
            ('grant_type', 'refresh_token'),
            ('refresh_token', refresh_token),
        ]

        res = requests.post('https://accounts.spotify.com/api/token', headers=headers, data=data)
        access_token = json.loads(res.text)['access_token']
        sp = spotipy.Spotify(auth=access_token)

        response = requests.post('https://api.spotify.com/v1/users/coaltunbey/playlists', headers=headers, data=data)

    href = json.loads(response.text)['href']
    uri = json.loads(response.text)['uri']

    params = (
        ('uris', ','.join(map(str, final_playlist))),
    )

    requests.post(href + '/tracks', headers=headers, params=params)

    return render(request, 'output.html', {'uri' : uri, 'todays_top_ten_hits_tempo' : todays_tracks_tempo,
                                           'final_playlist_tempo' : final_playlist_tempo,
                                           'priority_d' : priority_d, 'priority_e' : priority_e,
                                           'priority_l' : priority_l, 'priority_v' : priority_v})
