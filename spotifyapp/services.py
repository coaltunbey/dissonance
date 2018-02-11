from __future__ import print_function
import spotipy.util as util
import spotipy
import math
import operator
import requests
import matplotlib.pyplot as plt
import sys
import json
import os


token = "BQBZXrmmrNHo5DEyrxSbSQhouL7lASxJxHDArZlFjS2o4Jj00AL5ToDfCS_koYJv7h10VSNQ0Ppwis9tsTcigKyF5Cj327O35FxhaSNT1mkB3pKsyl2jXWT2b33So5FjtfppRPLiB1ihPmy2Yqi1NF8FR6Nyf-GVboq2foVY1HWMIeZI4YBON2ZUGVVm74RvuHUy29Gn3AjNmnPPy0_e"

sp = spotipy.Spotify(auth=token)




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
        for key in ['key', 'loudness', 'mode', 'speechiness', 'acousticness', 'instrumentalness', 'type', 'id', 'uri',
                    'track_href', 'analysis_url', 'duration_ms', 'time_signature']:
            value.pop(key)

    return tracks


# custom sort key
def key(x):
    return x[0]["distance"]  # return ISO date string

# base track
tid = 'spotify:track:0iuyxMDRdQYqZFfmjelvGH'

# weights
w1 = 4
w2 = 3
w3 = 5
w4 = 2

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
    temp_dict['distance'] = math.sqrt(1/w1*((ftrs['danceability'] - base_track_features['danceability'])**2) +
                              1/w2*((ftrs['energy'] - base_track_features['energy'])**2) +
                              1/w3*((ftrs['liveness'] - base_track_features['liveness'])**2) +
                              1/w4*((ftrs['valence'] - base_track_features['valence'])**2))
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

    # and remove it from comparison list
    sorted_distances = [d for d in sorted_distances if d['id'] != min_distempo['id']]


print(final_playlist)

headers = {
    'Authorization': 'Bearer '+token,
    'Content-Type': 'application/json',
}

data = '{"name":"Dissonance Song Recommendations", "public":false, "description": "A playlist that contains 10 songs based on user preferences."}'

response = requests.post('https://api.spotify.com/v1/users/coaltunbey/playlists', headers=headers, data=data)

if 'error' in json.loads(response.text):
    module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # get current directory
    file_path = os.path.join(module_dir, 'refresh_token.txt')
    handle = open(file_path, 'r+')
    refresh_token = handle.read()
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
else:
    href = json.loads(response.text)['href']
    uri = json.loads(response.text)['uri']
    print(uri)
    params = (
        ('uris', ','.join(map(str, final_playlist))),
    )

    requests.post(href + '/tracks', headers=headers, params=params)






