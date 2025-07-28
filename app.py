import streamlit as st
import pickle
import pandas as pd
import requests
import hashlib
import os

# ---------------------- USER AUTHENTICATION SETUP ----------------------

USER_DATA_FILE = "users.csv"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if os.path.exists(USER_DATA_FILE):
        return pd.read_csv(USER_DATA_FILE)
    else:
        return pd.DataFrame(columns=["username", "password"])

def save_user(username, password):
    users = load_users()
    if username in users['username'].values:
        return False
    new_user = pd.DataFrame([[username, hash_password(password)]], columns=["username", "password"])
    users = pd.concat([users, new_user], ignore_index=True)
    users.to_csv(USER_DATA_FILE, index=False)
    return True

def verify_user(username, password):
    users = load_users()
    hashed = hash_password(password)
    return any((users['username'] == username) & (users['password'] == hashed))


# ---------------------- MOVIE RECOMMENDER LOGIC ----------------------

def fetch_poster(title):
    try:
        response = requests.get(
            f'https://api.imdbapi.dev/search/titles?query={title}&limit=1'
        )
        data = response.json()
        return data["titles"][0]["primaryImage"]["url"]
    except:
        return "https://via.placeholder.com/300x450.png?text=No+Poster"

movies_dict = pd.DataFrame(pickle.load(open('movie_dict.pkl', 'rb')))
similarity = pickle.load(open('similarity.pkl', 'rb'))

def recommend(movie_title):
    movie_index = movies_dict[movies_dict['title'] == movie_title].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommended_movies = []
    recommended_movies_posters = []

    for i in movies_list:
        title = movies_dict.iloc[i[0]].title
        recommended_movies.append(title)
        recommended_movies_posters.append(fetch_poster(title))

    return recommended_movies, recommended_movies_posters


# ---------------------- STREAMLIT UI ----------------------

st.set_page_config(page_title="🎬 Movie Recommender", page_icon="🎥", layout="wide")

# Session State
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None

# ---------------------- LOGIN/SIGNUP PAGES ----------------------

def show_login():
    st.markdown("<h2 style='text-align: center;'>🔐 Login to Continue</h2>", unsafe_allow_html=True)
    with st.container():
        username = st.text_input("👤 Username")
        password = st.text_input("🔑 Password", type="password")
        if st.button("🚪 Login", use_container_width=True):
            if verify_user(username, password):
                st.success("Login successful!")
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid credentials!")

def show_signup():
    st.markdown("<h2 style='text-align: center;'>📝 Create an Account</h2>", unsafe_allow_html=True)
    with st.container():
        username = st.text_input("👤 Choose Username")
        password = st.text_input("🔑 Choose Password", type="password")
        if st.button("✅ Sign Up", use_container_width=True):
            if save_user(username, password):
                st.success("Account created! You can now login.")
            else:
                st.warning("⚠️ Username already exists!")


# ---------------------- MAIN RECOMMENDER PAGE ----------------------

def show_recommender():
    st.markdown(f"<h2 style='text-align: center;'>🎬 Welcome, {st.session_state.username}!</h2>", unsafe_allow_html=True)

    selected_movie_name = st.selectbox(
        '🎞️ Select a movie to get recommendations:',
        movies_dict['title'].values
    )

    if st.button('✨ Recommend Movies', use_container_width=True):
        names, posters = recommend(selected_movie_name)

        st.markdown("<h4 style='text-align: center;'>🎥 Top 5 Recommendations</h4>", unsafe_allow_html=True)
        cols = st.columns(5)
        for i in range(5):
            with cols[i]:
                st.image(posters[i], caption=names[i], use_container_width=True)

    st.markdown("---")
    if st.button("🔓 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.rerun()


# ---------------------- SIDEBAR NAVIGATION ----------------------

st.sidebar.title("🎞️ Navigation")

if not st.session_state.logged_in:
    nav_option = st.sidebar.radio("Go to", ["Login", "Sign Up"])
    if nav_option == "Login":
        show_login()
    else:
        show_signup()
else:
    show_recommender()
