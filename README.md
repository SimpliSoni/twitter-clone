# Twitter Clone  

A simple Twitter-like web application built using Flask and MongoDB.  

![Home](https://github.com/user-attachments/assets/5d430d26-4a2b-49f3-b890-4a08f7c997cf)


## Tech Stack  

- **Frontend:** HTML, CSS, JavaScript, Bootstrap  
- **Backend:** Flask  
- **Database:** MongoDB  

## Project Structure  

```
/twitter-clone
├── app.py                
├── README.md            
├── /templates           
│   ├── base.html        
│   ├── index.html       
│   ├── login.html       
│   ├── profile.html     
│   └── register.html    
└── /static              
    ├── /css
    │   └── styles.css   
    └── /js
        └── scripts.js   
```

## Features  

✅ **User Authentication** – Signup & Login using Flask sessions  
✅ **Create Tweets** – Users can post short messages  
✅ **Edit Tweets** – Users can now edit messages  
✅ **View Tweets** – Display all tweets from users  
✅ **Delete Tweets** – Users can remove their own tweets  
✅ **Like Tweets** – Simple like feature using MongoDB  
✅ **Follow Users** – Basic follow/unfollow functionality  

## Installation  

1. **Clone the Repository**  
   ```sh
   git clone https://github.com/yourusername/twitter_clone.git
   cd twitter_clone
   ```

2. **Install Dependencies**  
   ```sh
   pip install flask pymongo
   ```

3. **Run the Application**  
   ```sh
   python app.py
   ```

4. **Open in Browser**  
   Visit `http://127.0.0.1:5000` to access the application.  

## Contributing  

Feel free to submit issues or pull requests to improve this project!  

## License  

This project is open-source and available under the MIT License

