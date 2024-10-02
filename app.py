import streamlit as st
from googleapiclient.discovery import build
from datetime import datetime
import os
import openai

# Get API keys from environment variables
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not YOUTUBE_API_KEY:
    st.error("YouTube API key not found. Please set the YOUTUBE_API_KEY environment variable.")
    st.stop()

if not OPENAI_API_KEY:
    st.error("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
    st.stop()

youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
openai.api_key = OPENAI_API_KEY

def get_all_comments(video_id: str):
    try:
        comments = []
        nextPageToken = None
        while True:
            response = youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=100,
                pageToken=nextPageToken,
                order='time'
            ).execute()

            for item in response['items']:
                comment = item['snippet']['topLevelComment']['snippet']
                comments.append({
                    'author': comment['authorDisplayName'],
                    'text': comment['textDisplay'],
                    'likes': comment['likeCount'],
                    'published_at': comment['publishedAt']
                })

            nextPageToken = response.get('nextPageToken')
            if not nextPageToken:
                break

        return comments
    except Exception as e:
        return f"An error occurred while fetching comments: {str(e)}"

def extract_questions(comments):
    all_comments_text = " ".join([comment['text'] for comment in comments])
    
    prompt = f"""Analyze the following YouTube comments and extract all direct and indirect questions about the video. Categorize them as either 'Direct' or 'Indirect'.

Comments:
{all_comments_text}

Format your response as follows:
Direct Questions:
1. [Question 1]
2. [Question 2]
...

Indirect Questions:
1. [Question 1]
2. [Question 2]
...

If there are no questions in a category, write 'None found.' under that category.
"""

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that analyzes YouTube comments to extract questions."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000
    )

    return response.choices[0].message.content

st.set_page_config(layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    
    body {
        color: #333;
        font-family: 'Roboto', sans-serif;
        line-height: 1.6;
        background-color: #f0f2f5;
    }
    .main {
        max-width: 800px;
        margin: 0 auto;
        background-color: white;
        padding: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-radius: 8px;
    }
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 12px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 18px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 5px;
        transition: background-color 0.3s;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .comments-container, .questions-container {
        max-width: 800px;
        margin: 2rem auto;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 20px;
        background-color: #f9f9f9;
        max-height: 500px;
        overflow-y: auto;
    }
    .comment {
        background-color: #ffffff;
        border-left: 4px solid #3498db;
        padding: 15px;
        margin-bottom: 15px;
        border-radius: 4px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    .comment-author {
        font-weight: bold;
        color: #2c3e50;
    }
    .comment-date {
        font-size: 0.8em;
        color: #7f8c8d;
    }
    .comment-text {
        margin-top: 5px;
    }
    .comment-likes {
        font-size: 0.9em;
        color: #3498db;
        margin-top: 5px;
    }
</style>
""", unsafe_allow_html=True)

st.title("YouTube Comments Analyzer")

video_id = st.text_input("Enter YouTube Video ID")

if st.button("Analyze Comments"):
    if video_id:
        with st.spinner("Fetching and analyzing comments..."):
            comments = get_all_comments(video_id)
            if isinstance(comments, list):
                st.markdown("<div class='comments-container'>", unsafe_allow_html=True)
                st.markdown("<h2>Comments</h2>", unsafe_allow_html=True)
                for comment in comments:
                    st.markdown(f"""
<div class="comment">
    <div class="comment-author">{comment['author']}</div>
    <div class="comment-date">{comment['published_at']}</div>
    <div class="comment-text">{comment['text']}</div>
    <div class="comment-likes">👍 {comment['likes']}</div>
</div>
""", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

                questions = extract_questions(comments)
                st.markdown("<div class='questions-container'>", unsafe_allow_html=True)
                st.markdown("<h2>Extracted Questions</h2>", unsafe_allow_html=True)
                st.markdown(questions)
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.error(comments)
    else:
        st.error("Please enter a YouTube Video ID.")
