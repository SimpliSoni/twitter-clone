from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId  # Make sure ObjectId is imported
import os
from datetime import datetime      # Make sure datetime is imported
import hashlib

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate a random secret key for sessions

# MongoDB Connection
# Ensure your MongoDB server is running!
# Use environment variables or config file for production connection strings
client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017/'))
db = client['twitter_clone']
users_collection = db['users']
tweets_collection = db['tweets']

# Helper functions
def get_user_by_username(username):
    return users_collection.find_one({'username': username})

def get_user_by_id(user_id):
    # Ensure user_id is valid before querying
    if not ObjectId.is_valid(user_id):
        return None
    try:
        return users_collection.find_one({'_id': ObjectId(user_id)})
    except Exception: # Catch potential errors during DB query
        return None

def get_tweets(limit=50):
    # Get tweets and sort by creation date (newest first)
    return tweets_collection.find().sort('created_at', -1).limit(limit)

def get_user_tweets(username, limit=50):
    # Get tweets from a specific user
    return tweets_collection.find({'username': username}).sort('created_at', -1).limit(limit)

def hash_password(password):
    # Simple password hashing
    return hashlib.sha256(password.encode()).hexdigest()

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        # Get current user
        current_user = get_user_by_id(session['user_id'])
        if not current_user: # Handle case where user_id in session is invalid
             session.clear()
             flash("Session error, please login again.")
             return redirect(url_for('login'))

        # Get tweets from followed users and current user
        following = current_user.get('following', [])
        following.append(current_user['username'])  # Include user's own tweets

        tweets = list(tweets_collection.find({
            'username': {'$in': following}
        }).sort('created_at', -1).limit(50))

        # Get all users for the follow feature (exclude current user)
        all_users = list(users_collection.find({'_id': {'$ne': ObjectId(session['user_id'])}}, {'username': 1, '_id': 0}))

        return render_template('index.html', tweets=tweets,
                              current_user=current_user,
                              all_users=all_users)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Basic validation
        if not username or not password or not confirm_password:
             flash('All fields are required.')
             return redirect(url_for('register'))

        # Check if username already exists
        if get_user_by_username(username):
            flash('Username already exists.')
            return redirect(url_for('register'))

        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match.')
            return redirect(url_for('register'))

        # Create a new user
        new_user = {
            'username': username,
            'password': hash_password(password),
            'created_at': datetime.now(),
            'following': []  # List of usernames the user follows
        }

        try:
            users_collection.insert_one(new_user)
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'An error occurred during registration: {e}')
            return redirect(url_for('register'))

    # Prevent logged-in users from accessing register page
    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Username and password are required.')
            return redirect(url_for('login'))

        user = get_user_by_username(username)

        if user and user['password'] == hash_password(password):
            # Store user ID in session
            session['user_id'] = str(user['_id'])
            flash('Login successful!')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.')
            return redirect(url_for('login')) # Stay on login page after failed attempt

    # Prevent logged-in users from accessing login page
    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    # Clear session
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/tweet', methods=['POST'])
def tweet():
    if 'user_id' not in session:
        flash('Please login to tweet.')
        return redirect(url_for('login'))

    content = request.form['content']
    if not content or len(content.strip()) == 0:
         flash('Tweet content cannot be empty.')
         return redirect(url_for('index'))
    if len(content) > 280:  # Twitter's character limit
        flash('Tweet cannot exceed 280 characters.')
        return redirect(url_for('index'))

    current_user = get_user_by_id(session['user_id'])
    if not current_user: # Handle case where user_id in session is invalid
         session.clear()
         flash("Session error, please login again.")
         return redirect(url_for('login'))

    # Create a new tweet
    new_tweet = {
        'username': current_user['username'],
        'user_id': session['user_id'], # Store as string for consistency
        'content': content,
        'created_at': datetime.now(),
        'likes': [],  # List of user IDs (strings) who liked this tweet
        'updated_at': None # Initialize updated_at field
    }

    try:
        tweets_collection.insert_one(new_tweet)
        flash('Tweet posted!')
    except Exception as e:
        flash(f'An error occurred while posting the tweet: {e}')

    return redirect(url_for('index'))

@app.route('/delete_tweet/<tweet_id>')
def delete_tweet(tweet_id):
    if 'user_id' not in session:
        flash('Please login to delete tweets.')
        return redirect(url_for('login'))

    if not ObjectId.is_valid(tweet_id):
        flash('Invalid tweet ID.')
        return redirect(url_for('index'))

    try:
        # Check if the tweet belongs to the current user
        tweet = tweets_collection.find_one({'_id': ObjectId(tweet_id)})
        if tweet and tweet['user_id'] == session['user_id']:
            tweets_collection.delete_one({'_id': ObjectId(tweet_id)})
            flash('Tweet deleted.')
        elif tweet:
            flash('You can only delete your own tweets.')
        else:
            flash('Tweet not found.')
    except Exception as e:
        flash(f'An error occurred while deleting the tweet: {e}')

    # Redirect to the page the user came from, or index as fallback
    return redirect(request.referrer or url_for('index'))

@app.route('/like_tweet/<tweet_id>')
def like_tweet(tweet_id):
    if 'user_id' not in session:
        flash('Please login to like tweets.')
        return redirect(url_for('login')) # Or perhaps redirect back?

    if not ObjectId.is_valid(tweet_id):
        flash('Invalid tweet ID.')
        return redirect(url_for('index'))

    try:
        tweet = tweets_collection.find_one({'_id': ObjectId(tweet_id)})
        if tweet:
            current_user_id = session['user_id']
            # Check if user already liked this tweet
            if current_user_id in tweet.get('likes', []):
                # Unlike
                tweets_collection.update_one(
                    {'_id': ObjectId(tweet_id)},
                    {'$pull': {'likes': current_user_id}}
                )
            else:
                # Like
                tweets_collection.update_one(
                    {'_id': ObjectId(tweet_id)},
                    {'$push': {'likes': current_user_id}}
                )
        else:
            flash('Tweet not found.')
    except Exception as e:
        flash(f'An error occurred while liking the tweet: {e}')

    # Redirect to the page the user came from, or index as fallback
    return redirect(request.referrer or url_for('index'))

@app.route('/follow/<username>')
def follow(username):
    if 'user_id' not in session:
        flash('Please login to follow users.')
        return redirect(url_for('login'))

    current_user_id = session['user_id']
    current_user = get_user_by_id(current_user_id)
    user_to_follow = get_user_by_username(username)

    if not current_user: # Should not happen if logged in, but good check
        session.clear()
        flash("Session error, please login again.")
        return redirect(url_for('login'))

    if not user_to_follow:
        flash(f'User @{username} not found.')
        return redirect(request.referrer or url_for('index'))

    if current_user['username'] == username:
        flash('You cannot follow yourself.')
        return redirect(request.referrer or url_for('index'))

    try:
        # Check if already following
        if username in current_user.get('following', []):
            # Unfollow
            users_collection.update_one(
                {'_id': ObjectId(current_user_id)},
                {'$pull': {'following': username}}
            )
            flash(f'You unfollowed @{username}.')
        else:
            # Follow
            users_collection.update_one(
                {'_id': ObjectId(current_user_id)},
                {'$push': {'following': username}}
            )
            flash(f'You are now following @{username}.')
    except Exception as e:
         flash(f'An error occurred: {e}')

    # Redirect to the page the user came from, or index as fallback
    return redirect(request.referrer or url_for('index'))


@app.route('/profile/<username>')
def profile(username):
    if 'user_id' not in session:
        flash('Please login to view profiles.')
        return redirect(url_for('login'))

    profile_user = get_user_by_username(username)
    if not profile_user:
        flash(f'User @{username} not found.')
        return redirect(url_for('index'))

    current_user = get_user_by_id(session['user_id'])
    if not current_user: # Handle case where user_id in session is invalid
         session.clear()
         flash("Session error, please login again.")
         return redirect(url_for('login'))

    tweets = list(get_user_tweets(username))

    return render_template('profile.html',
                          profile_user=profile_user,
                          tweets=tweets,
                          current_user=current_user)

# --- NEW ROUTE FOR EDITING TWEETS ---
@app.route('/edit_tweet/<tweet_id>', methods=['GET', 'POST'])
def edit_tweet(tweet_id):
    # 1. Check if user is logged in
    if 'user_id' not in session:
        flash('Please login to edit tweets.')
        return redirect(url_for('login'))

    # 2. Fetch the tweet from DB
    if not ObjectId.is_valid(tweet_id):
        flash('Invalid tweet ID.')
        return redirect(url_for('index'))

    try:
        tweet = tweets_collection.find_one({'_id': ObjectId(tweet_id)})
    except Exception as e: # Handle potential invalid ObjectId or DB error
        flash(f'Error fetching tweet: {e}')
        return redirect(url_for('index'))

    if not tweet:
        flash('Tweet not found.')
        return redirect(url_for('index'))

    # 3. Check if the logged-in user is the author
    if tweet['user_id'] != session['user_id']:
        flash('You can only edit your own tweets.')
        return redirect(url_for('index'))

    # 4. Handle POST request (form submission)
    if request.method == 'POST':
        updated_content = request.form['content']
        if not updated_content or len(updated_content.strip()) == 0:
            flash('Tweet content cannot be empty.')
            # Need current_user to re-render template with error
            current_user = get_user_by_id(session['user_id'])
            return render_template('edit_tweet.html', tweet=tweet, current_user=current_user) # Re-render edit page
        if len(updated_content) > 280:
            flash('Tweet cannot exceed 280 characters')
            # Need current_user to re-render template with error
            current_user = get_user_by_id(session['user_id'])
            return render_template('edit_tweet.html', tweet=tweet, current_user=current_user) # Re-render edit page

        # Update the tweet in the database
        try:
            tweets_collection.update_one(
                {'_id': ObjectId(tweet_id)},
                {'$set': {
                    'content': updated_content,
                    'updated_at': datetime.now() # Track edits
                    }
                }
            )
            flash('Tweet updated successfully!')
            return redirect(url_for('index')) # Or redirect to profile
        except Exception as e:
            flash(f'An error occurred while updating the tweet: {e}')
            # Need current_user to re-render template with error
            current_user = get_user_by_id(session['user_id'])
            return render_template('edit_tweet.html', tweet=tweet, current_user=current_user) # Re-render edit page

    # 5. Handle GET request (show edit form)
    # Fetch current user to pass to base template
    current_user = get_user_by_id(session['user_id'])
    if not current_user: # Should not happen if logged in, but good check
        session.clear()
        flash("Session error, please login again.")
        return redirect(url_for('login'))

    # Pass BOTH tweet AND current_user to the template:
    return render_template('edit_tweet.html', tweet=tweet, current_user=current_user)
# --- END NEW ROUTE ---


if __name__ == '__main__':
    # Use environment variable for port, default to 5000
    port = int(os.environ.get('PORT', 5000))
    # Set debug=False for production
    app.run(debug=True, host='0.0.0.0', port=port)