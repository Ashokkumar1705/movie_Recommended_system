import streamlit as st
import pickle
import pandas as pd
import requests
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import gzip

PLACEHOLDER = "https://via.placeholder.com/500x750?text=No+Image"

# Reusable session with retries (stabilizes flaky network)
session = requests.Session()
retries = Retry(
    total=3,              # try up to 3 times
    backoff_factor=0.6,   # 0.6s, 1.2s, 1.8s...
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)
session.mount("https://", HTTPAdapter(max_retries=retries))

def fetch_poster(movie_id):
    # small delay so 5 rapid calls don't trigger rate-limit
    time.sleep(0.4)
    try:
        url = f'https://api.themoviedb.org/3/movie/{int(movie_id)}?api_key=32537a001b28d15374f9e5da72be0b16&language=en-US'
        response = session.get(url, timeout=8)
        response.raise_for_status()
        data = response.json()
        path = data.get('poster_path') or data.get('backdrop_path')
        return ("https://image.tmdb.org/t/p/w500" + path) if path else PLACEHOLDER
    except Exception:
        return PLACEHOLDER

def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommended_movies = []
    recommended_movies_poster = []
    for i in movies_list:
        # use real TMDB id saved in DataFrame (change 'movie_id' to your column name if different)
        tmdb_id = movies.iloc[i[0]].movie_id
        recommended_movies.append(movies.iloc[i[0]].title)
        recommended_movies_poster.append(fetch_poster(tmdb_id))

    # guarantee 5 entries even if some posters fail
    while len(recommended_movies) < 5:
        recommended_movies.append("N/A")
        recommended_movies_poster.append(PLACEHOLDER)

    return recommended_movies, recommended_movies_poster



movies = pickle.load(open('movies.pkl', 'rb'))
movies_list = movies['title'].values

with gzip.open('similarity.pkl.gz', 'rb') as f:
    similarity = pickle.load(f)


st.title('Movie Recommender System')

selected_movie_name = st.selectbox('How would you like to be  recommended?', movies_list)

if st.button('Recommend'):
    names, posters = recommend(selected_movie_name)

    # beta_columns -> columns
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.text(names[0]); st.image(posters[0], use_container_width=True)
    with col2:
        st.text(names[1]); st.image(posters[1], use_container_width=True)
    with col3:
        st.text(names[2]); st.image(posters[2], use_container_width=True)
    with col4:
        st.text(names[3]); st.image(posters[3], use_container_width=True)
    with col5:
        st.text(names[4]); st.image(posters[4], use_container_width=True)
