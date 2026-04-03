import streamlit as st
import pickle
import pandas as pd
import requests
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load data
movies = pickle.load(open('movies.pkl', 'rb'))
similarity = pickle.load(open('similarity.pkl', 'rb'))

# Create session ONCE globally
session = requests.Session()
retry = Retry(total=3, backoff_factor=0.3)
adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
session.mount("https://", adapter)

def fetch_poster(movie_id):
    try:
        if not movie_id or pd.isna(movie_id):
            return "https://placehold.co/500x750?text=No+Poster"
        movie_id = int(movie_id)
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=9f77038376683db4960bf223358fe128"
        response = session.get(url, timeout=5, verify=False)
        response.raise_for_status()
        poster_path = response.json().get('poster_path')
        return "https://image.tmdb.org/t/p/w500/" + poster_path if poster_path else "https://placehold.co/500x750?text=No+Poster"
    except:
        return "https://placehold.co/500x750?text=Error"

def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]

    similar_movies = sorted(
        list(enumerate(distances)),
        reverse=True,
        key=lambda x: x[1]
    )[1:6]

    names = [movies.iloc[i[0]].title for i in similar_movies]
    movie_ids = [movies.iloc[i[0]].movie_id for i in similar_movies]

    # Fetch all 5 posters in parallel instead of one by one
    with ThreadPoolExecutor(max_workers=5) as executor:
        posters = list(executor.map(fetch_poster, movie_ids))

    return names, posters

# UI
st.title('🎬 Movie Recommender App')

selected_movie_name = st.selectbox(
    'Choose a Movie',
    movies['title'].values
)

if st.button('Recommend'):
    with st.spinner('Finding recommendations...'):
        names, posters = recommend(selected_movie_name)

    col1, col2, col3, col4, col5 = st.columns(5)

    for col, name, poster in zip([col1, col2, col3, col4, col5], names, posters):
        with col:
            st.text(name)
            st.image(poster)