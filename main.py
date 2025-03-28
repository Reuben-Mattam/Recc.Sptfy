import re
import pandas as pd
import tkinter as tk
from tkinter import filedialog
from datetime import datetime
from collections import Counter
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
import os

# --- Spotify API setup ---

load_dotenv()

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"), 
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
))

def extract_playlist_id(playlist_url):
    """extract the playlist ID from a spotify playlist URL"""
    match = re.search(r"playlist/([a-zA-Z0-9]+)", playlist_url)
    return match.group(1) if match else None

def get_playlist_tracks(playlist_url):
    """fetch all tracks from spotify playlist and return dfs"""
    playlist_id = extract_playlist_id(playlist_url)
    if not playlist_id:
        raise ValueError("Invalid Spotify playlist URL !")

    # retrive playlist tracks, future note: may need to handle pagination for long playlists !! research later
    results = sp.playlist_tracks(playlist_id)
    tracks_items = results['items']

    tracks_data = []
    albums_data = []
    artists_data = []
    genres_counter = Counter()

    for item in tracks_items:
        track = item['track']
        if not track:
            continue

        # track details
        track_name = track['name']
        track_id = track['id']
        track_url = track['external_urls']['spotify']
        track_image = track['album']['images'][0]['url'] if track['album']['images'] else None

        # album details
        album_name = track['album']['name']
        album_id = track['album']['id']
        album_image = track['album']['images'][0]['url'] if track['album']['images'] else None

        # artist details
        artist = track['artists'][0]
        artist_name = artist['name']
        artist_id = artist['id']

        # fetch artist info for genres and image
        artist_info = sp.artist(artist_id)
        artist_image = artist_info['images'][0]['url'] if artist_info.get('images') else None
        genres = artist_info.get('genres', [])

        for genre in genres:
            genres_counter[genre] += 1

        tracks_data.append([track_name, track_id, track_url, track_image, artist_name])
        albums_data.append([album_name, album_id, album_image, artist_name])
        artists_data.append([artist_name, artist_id, artist_image])

    genres_data = [[genre, count] for genre, count in genres_counter.items()]

    # create df with the desired columns
    comp_tracks_df  = pd.DataFrame(tracks_data,  columns=["Song Name", "Track ID", "Song URL", "Track Image", "Artist"])
    comp_albums_df  = pd.DataFrame(albums_data,  columns=["Album", "Album ID", "Album Image", "Artist"])
    comp_artists_df = pd.DataFrame(artists_data, columns=["Artist", "Artist ID", "Artist Image"])
    comp_genres_df  = pd.DataFrame(genres_data,  columns=["Genre", "Count"])

    return comp_tracks_df, comp_albums_df, comp_artists_df, comp_genres_df

def main():
    # initialize Tkinter
    root = tk.Tk()
    root.withdraw()

    # select excel file
    file_path = filedialog.askopenfilename(
        title="Select an Excel file !",
        filetypes=[("Excel files", "*.xlsx *.xls")]
    )
    
    if not file_path:
        print("No file selected. Exiting !")
        return

    try:
        excel_data = pd.read_excel(file_path, sheet_name=None)
        
        # get individual sheets based on expected names
        df_timestamp = excel_data['timestamp']
        df_tracks    = excel_data['tracks']
        df_albums    = excel_data['albums']
        df_artists   = excel_data['artists']
        df_genres    = excel_data['genres']

        print("Excel file loaded successfully !")
        print(f"Timestamp sheet: {df_timestamp.shape[0]} rows, {df_timestamp.shape[1]} columns")
        print(f"Tracks sheet: {df_tracks.shape[0]} rows, {df_tracks.shape[1]} columns")
        print(f"Albums sheet: {df_albums.shape[0]} rows, {df_albums.shape[1]} columns")
        print(f"Artists sheet: {df_artists.shape[0]} rows, {df_artists.shape[1]} columns")
        print(f"Genres sheet: {df_genres.shape[0]} rows, {df_genres.shape[1]} columns")
        
    except KeyError as e:
        print(f"Error: Missing expected sheet {e} !")
        return
    except Exception as e:
        print(f"An error occurred while reading the Excel file: {e} !")
        return

    # ask user for valid sotify playlist URL
    while True:
        spotify_url = input("Enter a Spotify playlist URL: ").strip()
        try:
            # validate URL and get playlist data
            comp_tracks_df, comp_albums_df, comp_artists_df, comp_genres_df = get_playlist_tracks(spotify_url)
            print("Spotify playlist loaded successfully.")
            print(f"Tracks sheet: {comp_tracks_df.shape[0]} rows, {comp_tracks_df.shape[1]} columns")
            print(f"Albums sheet: {comp_albums_df.shape[0]} rows, {comp_albums_df.shape[1]} columns")
            print(f"Artists sheet: {comp_artists_df.shape[0]} rows, {comp_artists_df.shape[1]} columns")
            print(f"Genres sheet: {comp_genres_df.shape[0]} rows, {comp_genres_df.shape[1]} columns")
            break
        except Exception as e:
            print(f"Error with the playlist URL: {e} !")
            print("Please enter a valid Spotify playlist URL !")

if __name__ == "__main__":
    main()
