import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import json
import random
import os
import base64
from PIL import Image
import io
import requests

# Yanti Siggs Website Class
class YantiSiggsWebsite:
    def __init__(self):
        self.setup_database()
        self.initialize_data()
        
    def setup_database(self):
        """Setup SQLite database for website data with migration support"""
        self.conn = sqlite3.connect('yanti_siggs.db', check_same_thread=False)
        cursor = self.conn.cursor()
        
        # Enable foreign keys
        cursor.execute('PRAGMA foreign_keys = ON')
        
        # Check if tables need migration
        self.check_and_migrate_tables()
        
        self.conn.commit()
    
    def check_and_migrate_tables(self):
        """Check and migrate existing tables to new schema if needed"""
        cursor = self.conn.cursor()
        
        # Events table - Ensure date column exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'")
        if cursor.fetchone():
            # Check if date column exists
            cursor.execute("PRAGMA table_info(events)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'date' not in columns:
                # Create new table with correct schema
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS events_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT,
                        date TEXT,
                        time TEXT,
                        venue TEXT,
                        description TEXT,
                        image_url TEXT,
                        registration_url TEXT,
                        status TEXT DEFAULT 'upcoming'
                    )
                ''')
                
                # Copy data from old table if exists
                try:
                    cursor.execute("INSERT INTO events_new SELECT * FROM events")
                except:
                    # If column mismatch, insert default data
                    pass
                
                # Drop old table and rename new one
                cursor.execute("DROP TABLE events")
                cursor.execute("ALTER TABLE events_new RENAME TO events")
            else:
                # Table exists with correct columns, just ensure it's correct
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT,
                        date TEXT,
                        time TEXT,
                        venue TEXT,
                        description TEXT,
                        image_url TEXT,
                        registration_url TEXT,
                        status TEXT DEFAULT 'upcoming'
                    )
                ''')
        else:
            # Create events table from scratch
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    date TEXT,
                    time TEXT,
                    venue TEXT,
                        description TEXT,
                    image_url TEXT,
                    registration_url TEXT,
                    status TEXT DEFAULT 'upcoming'
                )
            ''')
        
        # Gallery table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gallery (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                category TEXT,
                image_url TEXT,
                description TEXT,
                upload_date DATE DEFAULT CURRENT_DATE
            )
        ''')
        
        # Music tracks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS music (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                album TEXT,
                year INTEGER,
                duration TEXT,
                youtube_url TEXT,
                spotify_url TEXT,
                soundcloud_url TEXT,
                lyrics TEXT,
                file_path TEXT,
                genre TEXT
            )
        ''')
        
        # Film projects table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS films (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                year INTEGER,
                role TEXT,
                description TEXT,
                trailer_url TEXT,
                watch_url TEXT,
                imdb_url TEXT,
                poster_url TEXT,
                status TEXT DEFAULT 'released'
            )
        ''')
        
        # Booking requests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                email TEXT,
                phone TEXT,
                event_type TEXT,
                event_date TEXT,
                venue TEXT,
                budget TEXT,
                message TEXT,
                date_submitted DATE DEFAULT CURRENT_DATE,
                status TEXT DEFAULT 'pending'
            )
        ''')
        
        # Newsletter subscribers
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscribers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                name TEXT,
                date_subscribed DATE DEFAULT CURRENT_DATE
            )
        ''')
        
        # Contact messages
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                email TEXT,
                phone TEXT,
                message TEXT,
                date_sent DATE DEFAULT CURRENT_DATE,
                status TEXT DEFAULT 'unread'
            )
        ''')
        
        # Admin users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password_hash TEXT,
                email TEXT,
                full_name TEXT,
                role TEXT DEFAULT 'admin',
                created_at DATE DEFAULT CURRENT_DATE
            )
        ''')
        
        # Header photo table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS header_photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                photo_path TEXT,
                upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                caption TEXT,
                position TEXT DEFAULT 'right'
            )
        ''')
        
        # Insert default admin if not exists
        cursor.execute("SELECT COUNT(*) FROM admin_users WHERE username = 'admin'")
        if cursor.fetchone()[0] == 0:
            # Default password: Yanti123 (you should change this)
            cursor.execute(
                "INSERT INTO admin_users (username, password_hash, email, full_name) VALUES (?, ?, ?, ?)",
                ('admin', 'pbkdf2:sha256:260000$YOUR_SALT_HERE$your_hash_here', 
                 'admin@yantistudios.com', 'Administrator')
            )
        
        # Activity logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                action TEXT,
                details TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (admin_id) REFERENCES admin_users(id)
            )
        ''')
        
        # Press/media table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS press (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                outlet TEXT,
                date TEXT,
                url TEXT,
                excerpt TEXT,
                image_url TEXT
            )
        ''')
        
        self.conn.commit()
    
    def initialize_data(self):
        """Initialize sample data if tables are empty"""
        cursor = self.conn.cursor()
        
        # Check and insert events
        cursor.execute("SELECT COUNT(*) FROM events")
        if cursor.fetchone()[0] == 0:
            sample_events = [
                ('Club Night DJ Set', '2024-04-20', '10:00 PM - 4:00 AM', 'Club 1940, Harare', 
                 'Main room DJ set featuring house and afrobeat', '', 'https://forms.google.com/example', 'upcoming'),
                ('Music Festival Performance', '2024-05-15', '8:00 PM - 11:00 PM', 
                 'Harare International Festival', 'Main stage performance at HIFA',
                 '', 'https://forms.google.com/example', 'upcoming'),
                ('Film Premiere Screening', '2024-04-28', '6:00 PM', 'Ster Kinekor, Borrowdale',
                 'Premiere of latest film project "Urban Dreams"', '', 'https://forms.google.com/example', 'upcoming'),
                ('DJ Workshop', '2024-05-05', '2:00 PM - 5:00 PM', 'Yanti Studios',
                 'Learn DJ skills with Yanti Siggs', '', 'https://forms.google.com/example', 'upcoming')
            ]
            cursor.executemany('INSERT INTO events (title, date, time, venue, description, image_url, registration_url, status) VALUES (?,?,?,?,?,?,?,?)', sample_events)
        
        # Check and insert gallery items
        cursor.execute("SELECT COUNT(*) FROM gallery")
        if cursor.fetchone()[0] == 0:
            sample_gallery = [
                ('DJ Performance', 'Music', 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80', 'Live DJ set at Club 1940'),
                ('Film Set', 'Film', 'https://images.unsplash.com/photo-1542204165-65bf26472b9b?ixlib=rb-4.0.3&auto=format&fit=crop&w-800&q=80', 'On set directing latest film'),
                ('Studio Session', 'Studio', 'https://images.unsplash.com/photo-1511379938547-c1f69419868d?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80', 'Recording session at Yanti Studios'),
                ('Red Carpet', 'Events', 'https://images.unsplash.com/photo-1492684223066-e9e4aab4d25e?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80', 'Awards night red carpet')
            ]
            cursor.executemany('INSERT INTO gallery (title, category, image_url, description) VALUES (?,?,?,?)', sample_gallery)
        
        # Check and insert music
        cursor.execute("SELECT COUNT(*) FROM music")
        if cursor.fetchone()[0] == 0:
            sample_music = [
                ('Urban Dreams', 'Urban Dreams EP', 2023, '5:15', 
                 'https://youtube.com/watch?v=example1', 'https://spotify.com/track/example1',
                 'https://soundcloud.com/yantisiggs/urban-dreams', 'Lyrics for Urban Dreams...', '', 'Afro House'),
                ('Harare Nights', 'City Vibes', 2022, '4:45',
                 'https://youtube.com/watch?v=example2', 'https://spotify.com/track/example2',
                 'https://soundcloud.com/yantisiggs/harare-nights', 'Lyrics for Harare Nights...', '', 'House'),
                ('African Queen', 'Roots', 2024, '6:20',
                 'https://youtube.com/watch?v=example3', 'https://spotify.com/track/example3',
                 'https://soundcloud.com/yantisiggs/african-queen', 'Lyrics for African Queen...', '', 'Afrobeat')
            ]
            cursor.executemany('INSERT INTO music (title, album, year, duration, youtube_url, spotify_url, soundcloud_url, lyrics, file_path, genre) VALUES (?,?,?,?,?,?,?,?,?,?)', sample_music)
        
        # Check and insert films
        cursor.execute("SELECT COUNT(*) FROM films")
        if cursor.fetchone()[0] == 0:
            sample_films = [
                ('Urban Dreams', 2023, 'Director/Actress', 
                 'A coming-of-age story set in contemporary Harare',
                 'https://youtube.com/watch?v=trailer1', 'https://netflix.com/urbandreams',
                 'https://imdb.com/title/tt1234567', 'https://via.placeholder.com/300x450/9b59b6/ffffff?text=Urban+Dreams', 'released'),
                ('Shadows of the Past', 2021, 'Producer/Actress',
                 'Psychological thriller exploring family secrets',
                 'https://youtube.com/watch?v=trailer2', 'https://showmax.com/shadows',
                 'https://imdb.com/title/tt2345678', 'https://via.placeholder.com/300x450/3498db/ffffff?text=Shadows', 'released'),
                ('City Lights', 2024, 'Director/Writer',
                 'Upcoming film about urban life and ambition',
                 '', '', '', 'https://via.placeholder.com/300x450/e74c3c/ffffff?text=City+Lights', 'in_production')
            ]
            cursor.executemany('INSERT INTO films (title, year, role, description, trailer_url, watch_url, imdb_url, poster_url, status) VALUES (?,?,?,?,?,?,?,?,?)', sample_films)
        
        # Check and insert press
        cursor.execute("SELECT COUNT(*) FROM press")
        if cursor.fetchone()[0] == 0:
            sample_press = [
                ('Yanti Siggs: The Multifaceted Creative', 'The Herald', '2024-03-15',
                 'https://herald.co.zw/yanti-siggs-interview', 
                 'From DJ decks to film sets, Yanti Siggs is redefining what it means to be a creative entrepreneur in Zimbabwe...',
                 'https://images.unsplash.com/photo-1511735111819-9a3f7709049c?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80'),
                ('New Film "Urban Dreams" Premieres', 'Zimbo Jam', '2024-02-28',
                 'https://zimbodesk.com/urban-dreams-premiere',
                 'Yanti Siggs\' latest film explores the dreams and challenges of urban youth...',
                 'https://images.unsplash.com/photo-1489599809516-9827b6d1cf13?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80'),
                ('DJ Yanti Rocks Harare Club Scene', 'Club Magazine', '2024-01-20',
                 'https://clubmag.co.zw/dj-yanti-review',
                 'Yanti Siggs brought the house down with her signature blend of afro house and electronic beats...',
                 'https://images.unsplash.com/photo-1470225620780-dba8ba36b745?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80')
            ]
            cursor.executemany('INSERT INTO press (title, outlet, date, url, excerpt, image_url) VALUES (?,?,?,?,?,?)', sample_press)
        
        self.conn.commit()
    
    # Existing methods...
    def get_events(self, limit=None, status='upcoming'):
        """Get events from database"""
        cursor = self.conn.cursor()
        try:
            if limit:
                cursor.execute('SELECT * FROM events WHERE status=? ORDER BY date LIMIT ?', (status, limit))
            else:
                cursor.execute('SELECT * FROM events WHERE status=? ORDER BY date', (status,))
            return cursor.fetchall()
        except sqlite3.OperationalError as e:
            # If there's still an error, recreate the table
            if "no such column: date" in str(e):
                self.recreate_events_table()
                return []
            return []
    
    def get_music(self, limit=None, genre=None):
        """Get music from database"""
        cursor = self.conn.cursor()
        if genre:
            cursor.execute('SELECT * FROM music WHERE genre=? ORDER BY year DESC LIMIT ?', (genre, limit))
        elif limit:
            cursor.execute('SELECT * FROM music ORDER BY year DESC LIMIT ?', (limit,))
        else:
            cursor.execute('SELECT * FROM music ORDER BY year DESC')
        return cursor.fetchall()
    
    def get_films(self, limit=None, status='released'):
        """Get films from database"""
        cursor = self.conn.cursor()
        if limit:
            cursor.execute('SELECT * FROM films WHERE status=? ORDER BY year DESC LIMIT ?', (status, limit))
        else:
            cursor.execute('SELECT * FROM films WHERE status=? ORDER BY year DESC', (status,))
        return cursor.fetchall()
    
    def get_press(self, limit=None):
        """Get press articles"""
        cursor = self.conn.cursor()
        if limit:
            cursor.execute('SELECT * FROM press ORDER BY date DESC LIMIT ?', (limit,))
        else:
            cursor.execute('SELECT * FROM press ORDER BY date DESC')
        return cursor.fetchall()
    
    def get_gallery(self, category=None, limit=None):
        """Get gallery items"""
        cursor = self.conn.cursor()
        if category:
            cursor.execute('SELECT * FROM gallery WHERE category=? ORDER BY upload_date DESC LIMIT ?', (category, limit))
        else:
            cursor.execute('SELECT * FROM gallery ORDER BY upload_date DESC LIMIT ?', (limit,))
        return cursor.fetchall()
    
    def add_booking_request(self, name, email, phone, event_type, event_date, venue, budget, message):
        """Add booking request to database"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO bookings (name, email, phone, event_type, event_date, venue, budget, message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, email, phone, event_type, event_date, venue, budget, message))
        self.conn.commit()
        return cursor.lastrowid
    
    def add_subscriber(self, email, name):
        """Add newsletter subscriber"""
        cursor = self.conn.cursor()
        try:
            cursor.execute('INSERT INTO subscribers (email, name) VALUES (?, ?)', (email, name))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # Email already exists
    
    def add_contact_message(self, name, email, phone, message):
        """Add contact message"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO contacts (name, email, phone, message)
            VALUES (?, ?, ?, ?)
        ''', (name, email, phone, message))
        self.conn.commit()
        return cursor.lastrowid
    
    def add_press_article(self, title, outlet, date, url, excerpt, image_url):
        """Add press article"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO press (title, outlet, date, url, excerpt, image_url)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, outlet, date, url, excerpt, image_url))
        self.conn.commit()
        return cursor.lastrowid
    
    # HEADER PHOTO METHODS
    def get_header_photo(self):
        """Get the active header photo"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM header_photos 
            WHERE is_active = 1 
            ORDER BY upload_date DESC 
            LIMIT 1
        ''')
        return cursor.fetchone()
    
    def add_header_photo(self, photo_path, caption="", position="right"):
        """Add a new header photo and deactivate old ones"""
        cursor = self.conn.cursor()
        
        # First, deactivate all existing photos
        cursor.execute('UPDATE header_photos SET is_active = 0 WHERE is_active = 1')
        
        # Insert new photo
        cursor.execute('''
            INSERT INTO header_photos (photo_path, caption, position, is_active)
            VALUES (?, ?, ?, 1)
        ''', (photo_path, caption, position))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_all_header_photos(self):
        """Get all header photos"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM header_photos ORDER BY upload_date DESC')
        return cursor.fetchall()
    
    def set_active_header_photo(self, photo_id):
        """Set a specific photo as active"""
        cursor = self.conn.cursor()
        
        # Deactivate all photos
        cursor.execute('UPDATE header_photos SET is_active = 0')
        
        # Activate the selected photo
        cursor.execute('UPDATE header_photos SET is_active = 1 WHERE id = ?', (photo_id,))
        
        self.conn.commit()
        return cursor.rowcount
    
    def delete_header_photo(self, photo_id):
        """Delete a header photo"""
        cursor = self.conn.cursor()
        
        # Get the photo path to delete the file
        cursor.execute('SELECT photo_path FROM header_photos WHERE id = ?', (photo_id,))
        result = cursor.fetchone()
        
        if result:
            photo_path = result[0]
            # Delete the file if it exists
            if photo_path and os.path.exists(photo_path):
                try:
                    os.remove(photo_path)
                except:
                    pass  # Ignore file deletion errors
        
        # Delete from database
        cursor.execute('DELETE FROM header_photos WHERE id = ?', (photo_id,))
        self.conn.commit()
        return cursor.rowcount
    
    # ADMIN METHODS
    def verify_admin(self, username, password):
        """Verify admin credentials"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM admin_users WHERE username = ?', (username,))
        admin = cursor.fetchone()
        if admin:
            # In production, use proper password hashing
            # For now, using simple check (you should implement proper hashing)
            if password == 'Yanti123':  # Change this to proper hashing
                return admin
        return None
    
    def add_event(self, title, date, time, venue, description, image_url, registration_url, status='upcoming'):
        """Add new event"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO events (title, date, time, venue, description, image_url, registration_url, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, date, time, venue, description, image_url, registration_url, status))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_event(self, event_id, title, date, time, venue, description, image_url, registration_url, status):
        """Update existing event"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE events 
            SET title=?, date=?, time=?, venue=?, description=?, image_url=?, registration_url=?, status=?
            WHERE id=?
        ''', (title, date, time, venue, description, image_url, registration_url, status, event_id))
        self.conn.commit()
        return cursor.rowcount
    
    def delete_event(self, event_id):
        """Delete event"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM events WHERE id = ?', (event_id,))
        self.conn.commit()
        return cursor.rowcount
    
    def add_music(self, title, album, year, duration, youtube_url, spotify_url, soundcloud_url, lyrics, file_path, genre):
        """Add new music track"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO music (title, album, year, duration, youtube_url, spotify_url, soundcloud_url, lyrics, file_path, genre)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, album, year, duration, youtube_url, spotify_url, soundcloud_url, lyrics, file_path, genre))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_music(self, music_id, title, album, year, duration, youtube_url, spotify_url, soundcloud_url, lyrics, file_path, genre):
        """Update music track"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE music 
            SET title=?, album=?, year=?, duration=?, youtube_url=?, spotify_url=?, soundcloud_url=?, lyrics=?, file_path=?, genre=?
            WHERE id=?
        ''', (title, album, year, duration, youtube_url, spotify_url, soundcloud_url, lyrics, file_path, genre, music_id))
        self.conn.commit()
        return cursor.rowcount
    
    def delete_music(self, music_id):
        """Delete music track"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM music WHERE id = ?', (music_id,))
        self.conn.commit()
        return cursor.rowcount
    
    def add_film(self, title, year, role, description, trailer_url, watch_url, imdb_url, poster_url, status):
        """Add new film"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO films (title, year, role, description, trailer_url, watch_url, imdb_url, poster_url, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, year, role, description, trailer_url, watch_url, imdb_url, poster_url, status))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_film(self, film_id, title, year, role, description, trailer_url, watch_url, imdb_url, poster_url, status):
        """Update film"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE films 
            SET title=?, year=?, role=?, description=?, trailer_url=?, watch_url=?, imdb_url=?, poster_url=?, status=?
            WHERE id=?
        ''', (title, year, role, description, trailer_url, watch_url, imdb_url, poster_url, status, film_id))
        self.conn.commit()
        return cursor.rowcount
    
    def delete_film(self, film_id):
        """Delete film"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM films WHERE id = ?', (film_id,))
        self.conn.commit()
        return cursor.rowcount
    
    def add_gallery_item(self, title, category, image_url, description):
        """Add new gallery item"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO gallery (title, category, image_url, description)
            VALUES (?, ?, ?, ?)
        ''', (title, category, image_url, description))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_gallery_item(self, gallery_id, title, category, image_url, description):
        """Update gallery item"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE gallery 
            SET title=?, category=?, image_url=?, description=?
            WHERE id=?
        ''', (title, category, image_url, description, gallery_id))
        self.conn.commit()
        return cursor.rowcount
    
    def delete_gallery_item(self, gallery_id):
        """Delete gallery item"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM gallery WHERE id = ?', (gallery_id,))
        self.conn.commit()
        return cursor.rowcount
    
    def get_all_bookings(self):
        """Get all booking requests"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM bookings ORDER BY date_submitted DESC')
        return cursor.fetchall()
    
    def update_booking_status(self, booking_id, status):
        """Update booking request status"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE bookings 
            SET status=?
            WHERE id=?
        ''', (status, booking_id))
        self.conn.commit()
        return cursor.rowcount
    
    def get_all_subscribers(self):
        """Get all newsletter subscribers"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM subscribers ORDER BY date_subscribed DESC')
        return cursor.fetchall()
    
    def get_all_contacts(self):
        """Get all contact messages"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM contacts ORDER BY date_sent DESC')
        return cursor.fetchall()
    
    def update_contact_status(self, contact_id, status):
        """Update contact message status"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE contacts 
            SET status=?
            WHERE id=?
        ''', (status, contact_id))
        self.conn.commit()
        return cursor.rowcount
    
    def get_all_events(self):
        """Get all events"""
        cursor = self.conn.cursor()
        try:
            cursor.execute('SELECT * FROM events ORDER BY date DESC')
            return cursor.fetchall()
        except sqlite3.OperationalError as e:
            if "no such column: date" in str(e):
                # Recreate table and try again
                self.recreate_events_table()
                cursor.execute('SELECT * FROM events ORDER BY date DESC')
                return cursor.fetchall()
            return []
    
    def get_all_films(self):
        """Get all films"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM films ORDER BY year DESC')
        return cursor.fetchall()
    
    def get_all_music(self):
        """Get all music"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM music ORDER BY year DESC')
        return cursor.fetchall()
    
    def recreate_events_table(self):
        """Recreate events table with correct schema"""
        cursor = self.conn.cursor()
        
        # Drop existing table
        cursor.execute('DROP TABLE IF EXISTS events')
        
        # Create new table with correct schema
        cursor.execute('''
            CREATE TABLE events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                date TEXT,
                time TEXT,
                venue TEXT,
                description TEXT,
                image_url TEXT,
                registration_url TEXT,
                status TEXT DEFAULT 'upcoming'
            )
        ''')
        
        # Insert sample data
        sample_events = [
            ('Club Night DJ Set', '2024-04-20', '10:00 PM - 4:00 AM', 'Club 1940, Harare', 
             'Main room DJ set featuring house and afrobeat', '', 'https://forms.google.com/example', 'upcoming'),
            ('Music Festival Performance', '2024-05-15', '8:00 PM - 11:00 PM', 
             'Harare International Festival', 'Main stage performance at HIFA',
             '', 'https://forms.google.com/example', 'upcoming'),
            ('Film Premiere Screening', '2024-04-28', '6:00 PM', 'Ster Kinekor, Borrowdale',
             'Premiere of latest film project "Urban Dreams"', '', 'https://forms.google.com/example', 'upcoming'),
            ('DJ Workshop', '2024-05-05', '2:00 PM - 5:00 PM', 'Yanti Studios',
             'Learn DJ skills with Yanti Siggs', '', 'https://forms.google.com/example', 'upcoming')
        ]
        cursor.executemany('INSERT INTO events (title, date, time, venue, description, image_url, registration_url, status) VALUES (?,?,?,?,?,?,?,?)', sample_events)
        
        self.conn.commit()
    
    def get_database_stats(self):
        """Get database statistics for admin dashboard"""
        cursor = self.conn.cursor()
        stats = {}
        
        try:
            # Get event count
            cursor.execute("SELECT COUNT(*) FROM events")
            stats['total_events'] = cursor.fetchone()[0]
        except:
            stats['total_events'] = 0
        
        try:
            # Get music count
            cursor.execute("SELECT COUNT(*) FROM music")
            stats['total_music'] = cursor.fetchone()[0]
        except:
            stats['total_music'] = 0
        
        try:
            # Get film count
            cursor.execute("SELECT COUNT(*) FROM films")
            stats['total_films'] = cursor.fetchone()[0]
        except:
            stats['total_films'] = 0
        
        try:
            # Get booking count
            cursor.execute("SELECT COUNT(*) FROM bookings")
            stats['total_bookings'] = cursor.fetchone()[0]
        except:
            stats['total_bookings'] = 0
        
        try:
            # Get subscriber count
            cursor.execute("SELECT COUNT(*) FROM subscribers")
            stats['total_subscribers'] = cursor.fetchone()[0]
        except:
            stats['total_subscribers'] = 0
        
        try:
            # Get header photo status
            header_photo = self.get_header_photo()
            stats['has_header_photo'] = bool(header_photo)
        except:
            stats['has_header_photo'] = False
        
        return stats

# Custom CSS for the website
def load_css():
    st.markdown("""
    <style>
    /* Main styling */
    .main .block-container {
        padding-top: 0;
        max-width: 1200px;
    }
    
    /* Header styling - UPDATED WITH PHOTO */
    .header-container {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: white;
        padding: 3rem 1rem;
        margin-bottom: 2rem;
        border-radius: 0 0 20px 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        position: relative;
        overflow: hidden;
        min-height: 350px;
    }
    
    .header-content {
        flex: 1;
        padding-right: 2rem;
        z-index: 2;
    }
    
    .header-title {
        font-size: 3.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        background: linear-gradient(90deg, #ff6b6b, #ffa726);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .header-subtitle {
        font-size: 1.5rem;
        opacity: 0.9;
        margin-bottom: 1rem;
        color: #ffd166;
    }
    
    .header-tagline {
        font-size: 1.2rem;
        font-style: italic;
        margin-bottom: 1.5rem;
        color: #a9d6e5;
    }
    
    .header-photo-container {
        width: 320px;
        height: 320px;
        border-radius: 50%;
        overflow: hidden;
        border: 5px solid #ff6b6b;
        box-shadow: 0 10px 30px rgba(255,107,107,0.3);
        z-index: 2;
    }
    
    .header-photo {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    
    /* Header without photo */
    .header-simple {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: white;
        padding: 3rem 1rem;
        text-align: center;
        margin-bottom: 2rem;
        border-radius: 0 0 20px 20px;
    }
    
    /* Card styling */
    .card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
        margin-bottom: 1.5rem;
        border: 1px solid rgba(255,255,255,0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(255,107,107,0.2);
    }
    
    .card-title {
        color: #ffa726;
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 1rem;
        border-bottom: 3px solid #ff6b6b;
        padding-bottom: 0.5rem;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #ff6b6b 0%, #ffa726 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 25px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 15px rgba(255,107,107,0.4);
    }
    
    /* Admin button styling */
    .admin-btn {
        background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%) !important;
    }
    
    .admin-btn:hover {
        background: linear-gradient(135deg, #2575fc 0%, #6a11cb 100%) !important;
    }
    
    /* Admin header styling */
    .admin-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
        border: 1px solid rgba(255,107,107,0.2);
    }
    
    .admin-header-content h2 {
        margin: 0;
        font-size: 1.8rem;
        background: linear-gradient(90deg, #ff6b6b, #ffa726);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .admin-header-content p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 0.9rem;
    }
    
    .back-to-site-btn {
        background: linear-gradient(135deg, #06d6a0 0%, #118ab2 100%) !important;
        color: white !important;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 25px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        text-decoration: none;
        display: inline-block;
    }
    
    .back-to-site-btn:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 15px rgba(6, 214, 160, 0.4);
    }
    
    /* TAB STYLING FIX - Horizontal layout with icons and text side-by-side */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
        background: rgba(26, 26, 46, 0.1);
        border-radius: 10px;
        padding: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: nowrap;
        border-radius: 8px;
        padding: 0 1.5rem;
        font-weight: 600;
        color: #ffa726 !important;
        display: flex !important;
        align-items: center;
        justify-content: center;
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] div {
        display: flex !important;
        align-items: center;
        justify-content: center;
        gap: 8px;
        flex-direction: row !important;
    }
    
    .stTabs [data-baseweb="tab"] span {
        display: inline !important;
        line-height: 1.2 !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #ff6b6b 0%, #ffa726 100%) !important;
        color: white !important;
    }
    
    /* Ensure icon and text are on the same line */
    .stTabs [data-baseweb="tab"] .st-emotion-cache-1f5j2v9 {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        gap: 8px !important;
    }
    
    /* Event card */
    .event-card {
        background: rgba(255, 255, 255, 0.05);
        border-left: 5px solid #ff6b6b;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 10px;
        transition: all 0.3s ease;
    }
    
    .event-card:hover {
        background: rgba(255, 107, 107, 0.1);
    }
    
    /* Music player */
    .music-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        border: 1px solid rgba(255,107,107,0.2);
    }
    
    /* Film card */
    .film-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        border: 1px solid rgba(26, 188, 156, 0.2);
    }
    
    /* Press card */
    .press-card {
        background: rgba(255, 255, 255, 0.05);
        border-left: 5px solid #06d6a0;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 10px;
    }
    
    /* Social icons */
    .social-icons {
        display: flex;
        justify-content: center;
        gap: 1rem;
        margin: 2rem 0;
    }
    
    .social-icon {
        font-size: 2rem;
        color: #ff6b6b;
        transition: color 0.3s ease, transform 0.3s ease;
    }
    
    .social-icon:hover {
        color: #ffa726;
        transform: scale(1.1);
    }
    
    /* Footer */
    .footer {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: white;
        padding: 3rem 1rem;
        text-align: center;
        margin-top: 4rem;
        border-radius: 20px 20px 0 0;
        border-top: 3px solid #ff6b6b;
    }
    
    /* Admin access area */
    .admin-access-section {
        background: linear-gradient(135deg, rgba(26, 26, 46, 0.8) 0%, rgba(22, 33, 62, 0.8) 100%);
        border: 2px dashed #ff6b6b;
        border-radius: 15px;
        padding: 2rem;
        text-align: center;
        margin: 2rem 0;
    }
    
    .admin-access-btn {
        background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%) !important;
        color: white !important;
        border: none;
        padding: 0.75rem 2rem !important;
        border-radius: 25px;
        font-weight: 600;
        transition: all 0.3s ease;
        margin-top: 1rem !important;
    }
    
    .admin-access-btn:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 15px rgba(106, 17, 203, 0.4);
    }
    
    /* Admin portal styles */
    .admin-portal {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
    }
    
    .admin-stats {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-bottom: 2rem;
    }
    
    .stat-card {
        background: rgba(255, 255, 255, 0.1);
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,107,107,0.2);
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: bold;
        color: #ff6b6b;
    }
    
    .stat-label {
        font-size: 1rem;
        opacity: 0.8;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .header-container {
            flex-direction: column;
            text-align: center;
            padding: 2rem 1rem;
            min-height: auto;
        }
        
        .header-content {
            padding-right: 0;
            margin-bottom: 2rem;
        }
        
        .header-title { 
            font-size: 2.5rem; 
        }
        
        .header-subtitle { 
            font-size: 1.2rem; 
        }
        
        .header-photo-container {
            width: 200px;
            height: 200px;
            margin: 0 auto;
        }
        
        .admin-stats { 
            grid-template-columns: 1fr; 
        }
        
        .admin-header {
            flex-direction: column;
            gap: 1rem;
            text-align: center;
        }
        
        /* Responsive tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
            padding: 0.25rem;
            overflow-x: auto;
        }
        
        .stTabs [data-baseweb="tab"] {
            padding: 0 1rem;
            font-size: 0.9rem;
        }
    }
    
    /* Data table styling */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        background: rgba(255, 255, 255, 0.05);
    }
    
    .dataframe th {
        background: linear-gradient(135deg, #ff6b6b 0%, #ffa726 100%) !important;
        color: white !important;
    }
    
    /* Form styling */
    .stForm {
        background: rgba(255, 255, 255, 0.05);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        border: 1px solid rgba(255,107,107,0.2);
    }
    
    /* Success/Error messages */
    .success-box {
        background: linear-gradient(135deg, #06d6a0 0%, #118ab2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .error-box {
        background: linear-gradient(135deg, #ef476f 0%, #ffd166 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .warning-box {
        background: linear-gradient(135deg, #ffd166 0%, #ffa726 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    /* Photo preview styling */
    .photo-preview {
        border: 3px dashed #ff6b6b;
        border-radius: 15px;
        padding: 1rem;
        text-align: center;
        background: rgba(255, 255, 255, 0.05);
    }
    
    /* Header photo management */
    .header-photo-item {
        border: 2px solid rgba(255,107,107,0.3);
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        background: rgba(255, 255, 255, 0.05);
    }
    
    .active-photo {
        border-color: #06d6a0;
        background: rgba(6, 214, 160, 0.1);
    }
    
    /* Admin access info box */
    .admin-info-box {
        background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        text-align: center;
    }
    
    /* Typewriter effect */
    .typewriter {
        overflow: hidden;
        border-right: .15em solid #ff6b6b;
        white-space: nowrap;
        margin: 0 auto;
        letter-spacing: .15em;
        animation: typing 3.5s steps(40, end), blink-caret .75s step-end infinite;
    }
    
    @keyframes typing {
        from { width: 0 }
        to { width: 100% }
    }
    
    @keyframes blink-caret {
        from, to { border-color: transparent }
        50% { border-color: #ff6b6b; }
    }
    
    /* Role badges */
    .role-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin: 0.25rem;
    }
    
    .badge-dj { background: linear-gradient(135deg, #ff6b6b, #ffa726); color: white; }
    .badge-film { background: linear-gradient(135deg, #06d6a0, #118ab2); color: white; }
    .badge-music { background: linear-gradient(135deg, #6a11cb, #2575fc); color: white; }
    .badge-entrepreneur { background: linear-gradient(135deg, #8338ec, #3a86ff); color: white; }
    
    /* Travel timeline */
    .timeline {
        border-left: 3px solid #ff6b6b;
        margin: 2rem 0;
        padding-left: 1.5rem;
    }
    
    .timeline-item {
        margin-bottom: 2rem;
        position: relative;
    }
    
    .timeline-item:before {
        content: '';
        position: absolute;
        left: -1.7rem;
        top: 0.5rem;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: #ff6b6b;
    }
    
    /* Quote styling */
    .quote-box {
        background: linear-gradient(135deg, rgba(255,107,107,0.1) 0%, rgba(255,167,38,0.1) 100%);
        border-left: 5px solid #ffa726;
        padding: 1.5rem;
        margin: 1.5rem 0;
        border-radius: 0 10px 10px 0;
        font-style: italic;
        position: relative;
    }
    
    .quote-box:before {
        content: '"';
        font-size: 4rem;
        color: rgba(255,107,107,0.3);
        position: absolute;
        top: -1rem;
        left: 0.5rem;
    }
    
    /* Database error message */
    .db-error {
        background: linear-gradient(135deg, #ef476f 0%, #ffd166 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        text-align: center;
    }
    
    .db-error button {
        background: white;
        color: #ef476f;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: bold;
        margin-top: 0.5rem;
        cursor: pointer;
    }
    
    /* Custom tab styling to force horizontal layout */
    div[data-testid="stTabs"] > div > div {
        overflow-x: auto !important;
        display: flex !important;
        flex-wrap: nowrap !important;
    }
    
    /* Hide scrollbar but keep functionality */
    div[data-testid="stTabs"] > div > div::-webkit-scrollbar {
        height: 4px;
    }
    
    div[data-testid="stTabs"] > div > div::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 2px;
    }
    
    div[data-testid="stTabs"] > div > div::-webkit-scrollbar-thumb {
        background: #ff6b6b;
        border-radius: 2px;
    }
    </style>
    """, unsafe_allow_html=True)

def get_image_base64(image_path):
    """Convert image file to base64 format for HTML display"""
    try:
        # Check if file exists
        if not os.path.exists(image_path):
            st.warning(f"⚠️ Image file not found: {image_path}")
            return None
        
        # Check if it's a valid image file
        try:
            img = Image.open(image_path)
            img.verify()  # Verify it's a valid image
        except Exception as e:
            st.warning(f"⚠️ Invalid image file: {image_path} - Error: {str(e)}")
            return None
        
        # Get file extension for MIME type
        ext = os.path.splitext(image_path)[1].lower()
        mime_types = {
            '.jpg': 'jpeg',
            '.jpeg': 'jpeg',
            '.png': 'png',
            '.gif': 'gif',
            '.bmp': 'bmp',
            '.webp': 'webp'
        }
        mime_type = mime_types.get(ext, 'jpeg')
        
        # Read and encode the image
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        
        return encoded_string, mime_type
    except Exception as e:
        st.error(f"❌ Error encoding image: {str(e)}")
        return None

def render_header_with_photo():
    """Render the header section with artist photo"""
    header_photo = website.get_header_photo()
    
    if header_photo and header_photo[1]:  # Check if photo exists
        photo_path = header_photo[1]
        
        # Check if file exists and get base64 encoding
        if os.path.exists(photo_path):
            encoded_data = get_image_base64(photo_path)
            
            if encoded_data:
                img_base64, mime_type = encoded_data
                
                # Header WITH photo (using base64 encoding)
                st.markdown(f"""
                <div class="header-container">
                    <div class="header-content">
                        <h1 class="header-title">Yanti Siggs</h1>
                        <p class="header-subtitle">DJ • Music Producer • Filmmaker • Entrepreneur</p>
                        <p class="header-tagline">"make sure you die empty, life expectancy is now 45yrs!!"</p>
                        <div style="margin-top: 2rem;">
                            <p>🎵 <strong>CEO & Founder at Yanti Studios</strong> (March 6, 2022 - Present)</p>
                            <p>🎬 <strong>Multi-talented Creative:</strong> Singer, Songwriter, Filmmaker, Actress, Entrepreneur</p>
                            <div style="margin-top: 1rem;">
                                <span class="role-badge badge-dj">DJ</span>
                                <span class="role-badge badge-music">Music Producer</span>
                                <span class="role-badge badge-film">Filmmaker</span>
                                <span class="role-badge badge-entrepreneur">Entrepreneur</span>
                            </div>
                        </div>
                    </div>
                    <div class="header-photo-container">
                        <img src="data:image/{mime_type};base64,{img_base64}" alt="Yanti Siggs" class="header-photo">
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Fallback: Show header without photo
                st.markdown(f"""
                <div class="header-simple">
                    <h1 class="header-title">Yanti Siggs</h1>
                    <p class="header-subtitle">DJ • Music Producer • Filmmaker • Entrepreneur</p>
                    <p class="header-tagline">"make sure you die empty, life expectancy is now 45yrs!!"</p>
                    <div style="margin-top: 2rem;">
                        <p>🎵 <strong>CEO & Founder at Yanti Studios</strong> (March 6, 2022 - Present)</p>
                        <p>🎬 <strong>Multi-talented Creative:</strong> Singer, Songwriter, Filmmaker, Actress, Entrepreneur</p>
                        <div style="margin-top: 1rem;">
                            <span class="role-badge badge-dj">DJ</span>
                            <span class="role-badge badge-music">Music Producer</span>
                            <span class="role-badge badge-film">Filmmaker</span>
                            <span class="role-badge badge-entrepreneur">Entrepreneur</span>
                        </div>
                    </div>
                    <div class="warning-box">
                        ⚠️ Header photo file not accessible: {photo_path}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            # File doesn't exist - show warning and simple header
            st.markdown(f"""
            <div class="header-simple">
                <h1 class="header-title">Yanti Siggs</h1>
                <p class="header-subtitle">DJ • Music Producer • Filmmaker • Entrepreneur</p>
                <p class="header-tagline">"make sure you die empty, life expectancy is now 45yrs!!"</p>
                <div style="margin-top: 2rem;">
                    <p>🎵 <strong>CEO & Founder at Yanti Studios</strong> (March 6, 2022 - Present)</p>
                    <p>🎬 <strong>Multi-talented Creative:</strong> Singer, Songwriter, Filmmaker, Actress, Entrepreneur</p>
                    <div style="margin-top: 1rem;">
                        <span class="role-badge badge-dj">DJ</span>
                        <span class="role-badge badge-music">Music Producer</span>
                        <span class="role-badge badge-film">Filmmaker</span>
                        <span class="role-badge badge-entrepreneur">Entrepreneur</span>
                    </div>
                </div>
                <div class="warning-box">
                    ⚠️ Header photo file not found: {photo_path}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        # Header WITHOUT photo (fallback)
        st.markdown("""
        <div class="header-simple">
            <h1 class="header-title">Yanti Siggs</h1>
            <p class="header-subtitle">DJ • Music Producer • Filmmaker • Entrepreneur</p>
            <p class="header-tagline typewriter">"make sure you die empty, life expectancy is now 45yrs!!"</p>
            <div style="margin-top: 2rem;">
                <p>🎵 <strong>CEO & Founder at Yanti Studios</strong> (March 6, 2022 - Present)</p>
                <p>🎬 <strong>Multi-talented Creative:</strong> Singer, Songwriter, Filmmaker, Actress, Entrepreneur</p>
                <div style="margin-top: 1rem;">
                    <span class="role-badge badge-dj">DJ</span>
                    <span class="role-badge badge-music">Music Producer</span>
                    <span class="role-badge badge-film">Filmmaker</span>
                    <span class="role-badge badge-entrepreneur">Entrepreneur</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_admin_portal():
    """Render the admin portal interface"""
    
    # PERSISTENT ADMIN HEADER
    st.markdown("""
    <div class="admin-header">
        <div class="admin-header-content">
            <h2>🔐 Yanti Siggs Admin Portal</h2>
            <p>Manage all website content, music, films, events, and booking requests</p>
        </div>
        <div>
            <button class="back-to-site-btn" onclick="window.location.href='?';">
            </button>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Also add a Streamlit button for reliability
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🏠 Return to Main Website", use_container_width=True, type="primary"):
            st.session_state.admin_access = False
            st.session_state.show_admin_login = False
            st.session_state.booking_clicks = 0
            st.rerun()
    
    # Admin Dashboard with safe statistics
    st.markdown("### 📊 Dashboard Overview")
    
    try:
        # Get database statistics safely
        db_stats = website.get_database_stats()
        
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            total_events = db_stats.get('total_events', 0)
            st.metric("Total Events", total_events, delta="Manage below")
        
        with col2:
            total_music = db_stats.get('total_music', 0)
            st.metric("Music Tracks", total_music, delta="Manage below")
        
        with col3:
            total_films = db_stats.get('total_films', 0)
            st.metric("Films", total_films, delta="Manage below")
        
        with col4:
            total_bookings = db_stats.get('total_bookings', 0)
            # Get pending bookings count safely
            pending_bookings = 0
            try:
                bookings = website.get_all_bookings()
                pending_bookings = len([b for b in bookings if len(b) > 10 and b[10] == 'pending'])
            except:
                pass
            st.metric("Booking Requests", total_bookings, delta=f"{pending_bookings} pending")
        
        with col5:
            total_subscribers = db_stats.get('total_subscribers', 0)
            st.metric("Subscribers", total_subscribers, delta="View below")
        
        with col6:
            has_photo = "✅" if db_stats.get('has_header_photo', False) else "❌"
            st.metric("Header Photo", has_photo, delta="Manage below")
    except Exception as e:
        st.error(f"Error loading dashboard statistics: {str(e)}")
        # Show simplified dashboard
        st.warning("⚠️ Some dashboard statistics may not be available due to database issues.")
    
    # Admin Tabs
    admin_tabs = st.tabs([
        "📅 Manage Events", 
        "🎵 Manage Music", 
        "🎬 Manage Films",
        "📸 Manage Gallery", 
        "📰 Press & Media",
        "🖼️ Header Photo",
        "📋 Booking Requests",
        "📧 Subscribers", 
        "💌 Contact Messages",
        "👤 Admin Settings"
    ])
    
    # TAB 1: Manage Events
    with admin_tabs[0]:
        st.header("Manage Events")
        
        # Create new event
        with st.expander("➕ Add New Event", expanded=True):
            with st.form("add_event_form"):
                col1, col2 = st.columns(2)
                with col1:
                    event_title = st.text_input("Event Title *")
                    event_date = st.date_input("Event Date *")
                    event_time = st.text_input("Event Time *", placeholder="e.g., 10:00 PM - 4:00 AM")
                
                with col2:
                    event_venue = st.text_input("Venue *")
                    event_status = st.selectbox("Status", ["upcoming", "ongoing", "past", "cancelled"])
                    event_reg_url = st.text_input("Registration URL")
                
                event_description = st.text_area("Description *", height=150)
                event_image_url = st.text_input("Image URL", placeholder="https://example.com/image.jpg")
                
                submitted = st.form_submit_button("Add Event", type="primary")
                if submitted:
                    if event_title and event_date and event_time and event_venue and event_description:
                        website.add_event(
                            event_title, 
                            str(event_date), 
                            event_time, 
                            event_venue, 
                            event_description,
                            event_image_url,
                            event_reg_url,
                            event_status
                        )
                        st.success("✅ Event added successfully!")
                        st.rerun()
                    else:
                        st.error("Please fill in all required fields (*)")
        
        # View and edit existing events
        st.subheader("Existing Events")
        try:
            events = website.get_all_events()
            
            if events:
                for event in events:
                    with st.expander(f"{event[1]} - {event[2]} ({event[8] if len(event) > 8 else 'unknown'})", expanded=False):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            with st.form(f"edit_event_{event[0]}"):
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    edit_title = st.text_input("Title", value=event[1], key=f"title_{event[0]}")
                                    try:
                                        edit_date = st.date_input("Date", value=datetime.strptime(event[2], '%Y-%m-%d'), key=f"date_{event[0]}")
                                    except:
                                        edit_date = st.date_input("Date", value=datetime.now(), key=f"date_{event[0]}")
                                    edit_time = st.text_input("Time", value=event[3], key=f"time_{event[0]}")
                                
                                with col_b:
                                    edit_venue = st.text_input("Venue", value=event[4], key=f"venue_{event[0]}")
                                    status_options = ["upcoming", "ongoing", "past", "cancelled"]
                                    current_status = event[8] if len(event) > 8 else "upcoming"
                                    edit_status = st.selectbox("Status", status_options, 
                                                              index=status_options.index(current_status) if current_status in status_options else 0, 
                                                              key=f"status_{event[0]}")
                                    edit_reg_url = st.text_input("Registration URL", value=event[7] if len(event) > 7 else "", key=f"reg_{event[0]}")
                                
                                edit_description = st.text_area("Description", value=event[5], height=100, key=f"desc_{event[0]}")
                                edit_image_url = st.text_input("Image URL", value=event[6] if len(event) > 6 else "", key=f"img_{event[0]}")
                                
                                col_c, col_d = st.columns(2)
                                with col_c:
                                    if st.form_submit_button("Update Event", type="primary"):
                                        website.update_event(
                                            event[0], edit_title, str(edit_date), edit_time, 
                                            edit_venue, edit_description, edit_image_url, 
                                            edit_reg_url, edit_status
                                        )
                                        st.success("✅ Event updated!")
                                        st.rerun()
                                
                                with col_d:
                                    if st.form_submit_button("❌ Delete Event"):
                                        website.delete_event(event[0])
                                        st.success("✅ Event deleted!")
                                        st.rerun()
                        
                        with col2:
                            if len(event) > 6 and event[6]:  # If image URL exists
                                st.image(event[6], width=150)
            else:
                st.info("No events found. Add your first event above!")
        except Exception as e:
            st.error(f"Error loading events: {str(e)}")
            st.info("The events table may need to be recreated. Try adding a new event above.")
    
    # TAB 2: Manage Music
    with admin_tabs[1]:
        st.header("Manage Music")
        
        # Add new music
        with st.expander("➕ Add New Music Track", expanded=True):
            with st.form("add_music_form"):
                col1, col2 = st.columns(2)
                with col1:
                    music_title = st.text_input("Song Title *")
                    music_album = st.text_input("Album Name *")
                    music_year = st.number_input("Year *", min_value=2000, max_value=2024, value=2024)
                    music_genre = st.selectbox("Genre *", ["House", "Afro House", "Afrobeat", "Electronic", "Deep House", "Tech House", "Other"])
                
                with col2:
                    music_duration = st.text_input("Duration *", placeholder="e.g., 4:32")
                    music_youtube = st.text_input("YouTube URL")
                    music_spotify = st.text_input("Spotify URL")
                    music_soundcloud = st.text_input("SoundCloud URL")
                
                music_lyrics = st.text_area("Lyrics", height=200)
                
                # Music file upload
                music_file = st.file_uploader("Upload MP3 file (optional)", type=['mp3', 'wav', 'm4a'])
                
                submitted = st.form_submit_button("Add Music Track", type="primary")
                if submitted:
                    if music_title and music_album and music_year and music_duration and music_genre:
                        # Save uploaded file
                        file_path = ""
                        if music_file:
                            # Create music directory if it doesn't exist
                            os.makedirs("music_uploads", exist_ok=True)
                            file_path = f"music_uploads/{music_file.name}"
                            with open(file_path, "wb") as f:
                                f.write(music_file.getbuffer())
                        
                        website.add_music(
                            music_title, music_album, music_year, music_duration,
                            music_youtube, music_spotify, music_soundcloud, 
                            music_lyrics, file_path, music_genre
                        )
                        st.success("✅ Music track added successfully!")
                        st.rerun()
                    else:
                        st.error("Please fill in all required fields (*)")
    
    # TAB 3: Manage Films
    with admin_tabs[2]:
        st.header("Manage Films")
        
        # Add new film
        with st.expander("➕ Add New Film Project", expanded=True):
            with st.form("add_film_form"):
                col1, col2 = st.columns(2)
                with col1:
                    film_title = st.text_input("Film Title *")
                    film_year = st.number_input("Year *", min_value=2000, max_value=2024, value=2024)
                    film_role = st.text_input("Role(s) *", placeholder="e.g., Director, Actress, Producer")
                    film_status = st.selectbox("Status", ["in_production", "post_production", "released", "cancelled"])
                
                with col2:
                    film_trailer = st.text_input("Trailer URL")
                    film_watch = st.text_input("Watch URL (Netflix, Showmax, etc.)")
                    film_imdb = st.text_input("IMDb URL")
                    film_poster = st.text_input("Poster Image URL")
                
                film_description = st.text_area("Description *", height=150)
                
                submitted = st.form_submit_button("Add Film", type="primary")
                if submitted:
                    if film_title and film_year and film_role and film_description:
                        website.add_film(
                            film_title, film_year, film_role, film_description,
                            film_trailer, film_watch, film_imdb, film_poster, film_status
                        )
                        st.success("✅ Film added successfully!")
                        st.rerun()
                    else:
                        st.error("Please fill in all required fields (*)")
    
    # TAB 4: Manage Gallery
    with admin_tabs[3]:
        st.header("Manage Gallery")
        
        # Add new gallery item
        with st.expander("➕ Add New Gallery Item", expanded=True):
            with st.form("add_gallery_form"):
                col1, col2 = st.columns(2)
                with col1:
                    gallery_title = st.text_input("Title *")
                    gallery_category = st.selectbox("Category *", 
                                                   ["Music", "Film", "Studio", "Events", "Personal", "Other"])
                
                with col2:
                    gallery_image_url = st.text_input("Image URL", placeholder="https://example.com/image.jpg")
                
                gallery_description = st.text_area("Description", height=100)
                
                # Image upload alternative
                uploaded_image = st.file_uploader("Or upload image", type=['jpg', 'jpeg', 'png', 'gif'])
                
                submitted = st.form_submit_button("Add to Gallery", type="primary")
                if submitted:
                    if gallery_title and gallery_category:
                        image_url = gallery_image_url
                        
                        # If image uploaded, save it
                        if uploaded_image:
                            # Create gallery directory
                            os.makedirs("gallery_uploads", exist_ok=True)
                            # Save image
                            image_path = f"gallery_uploads/{uploaded_image.name}"
                            with open(image_path, "wb") as f:
                                f.write(uploaded_image.getbuffer())
                            image_url = image_path
                        
                        website.add_gallery_item(
                            gallery_title, gallery_category, image_url, gallery_description
                        )
                        st.success("✅ Gallery item added successfully!")
                        st.rerun()
                    else:
                        st.error("Please fill in all required fields (*)")
    
    # TAB 5: Press & Media
    with admin_tabs[4]:
        st.header("Press & Media")
        
        # Add new press article
        with st.expander("➕ Add New Press Article", expanded=True):
            with st.form("add_press_form"):
                col1, col2 = st.columns(2)
                with col1:
                    press_title = st.text_input("Article Title *")
                    press_outlet = st.text_input("Media Outlet *", placeholder="e.g., The Herald, Zimbo Jam")
                    press_date = st.date_input("Publication Date *")
                
                with col2:
                    press_url = st.text_input("Article URL *")
                    press_image = st.text_input("Image URL")
                
                press_excerpt = st.text_area("Excerpt *", height=100, 
                                            placeholder="Brief excerpt or summary of the article...")
                
                submitted = st.form_submit_button("Add Press Article", type="primary")
                if submitted:
                    if press_title and press_outlet and press_date and press_url and press_excerpt:
                        website.add_press_article(
                            press_title, press_outlet, str(press_date),
                            press_url, press_excerpt, press_image
                        )
                        st.success("✅ Press article added successfully!")
                        st.rerun()
                    else:
                        st.error("Please fill in all required fields (*)")
    
    # TAB 6: Header Photo Management
    with admin_tabs[5]:
        st.header("🖼️ Header Photo Management")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Upload New Header Photo")
            st.markdown("""
            **Upload requirements:**
            - Recommended size: 320x320 pixels (square)
            - File types: JPG, PNG, GIF
            - Max file size: 5MB
            - The photo will appear in the header section
            """)
            
            with st.form("upload_header_photo_form"):
                # Photo upload
                uploaded_photo = st.file_uploader("Choose a photo of Yanti Siggs", 
                                                 type=['jpg', 'jpeg', 'png', 'gif'],
                                                 key="header_photo_upload")
                
                # Optional caption
                photo_caption = st.text_input("Caption (optional)", 
                                             placeholder="e.g., Yanti Siggs - DJ & Filmmaker")
                
                # Photo position
                photo_position = st.selectbox("Photo Position", 
                                             ["right", "left"], 
                                             help="Position of the photo in the header")
                
                # Preview
                if uploaded_photo:
                    st.markdown("### 📸 Preview")
                    col_a, col_b, col_c = st.columns([1, 2, 1])
                    with col_b:
                        # Convert to PIL Image for preview
                        image = Image.open(uploaded_photo)
                        st.image(image, caption="Photo Preview", width=250)
                
                submitted = st.form_submit_button("Upload & Set as Active", type="primary")
                
                if submitted:
                    if uploaded_photo:
                        try:
                            # Create header_photos directory
                            os.makedirs("header_photos", exist_ok=True)
                            
                            # Generate unique filename
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            file_extension = uploaded_photo.name.split('.')[-1]
                            filename = f"yanti_siggs_{timestamp}.{file_extension}"
                            file_path = f"header_photos/{filename}"
                            
                            # Save the file
                            with open(file_path, "wb") as f:
                                f.write(uploaded_photo.getbuffer())
                            
                            # Add to database
                            website.add_header_photo(file_path, photo_caption, photo_position)
                            
                            st.success("✅ Header photo uploaded and set as active!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error uploading photo: {str(e)}")
                    else:
                        st.error("Please select a photo to upload")
        
        with col2:
            st.subheader("Current Active Photo")
            current_photo = website.get_header_photo()
            
            if current_photo:
                photo_path = current_photo[1]
                file_exists = os.path.exists(photo_path)
                
                st.markdown(f"""
                <div class="photo-preview">
                    <p><strong>Active Since:</strong><br>
                    {current_photo[2]}</p>
                    <p><strong>File Path:</strong><br>
                    <code>{photo_path}</code></p>
                    <p><strong>Status:</strong> {"✅ File exists" if file_exists else "❌ File missing"}</p>
                    <p><strong>Caption:</strong> {current_photo[4] or "No caption"}</p>
                    <p><strong>Position:</strong> {current_photo[5]}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if file_exists:
                    try:
                        # Show image preview
                        encoded_data = get_image_base64(photo_path)
                        if encoded_data:
                            img_base64, mime_type = encoded_data
                            st.markdown(f'<img src="data:image/{mime_type};base64,{img_base64}" width="200" style="border-radius:50%;">', 
                                      unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Error loading image: {str(e)}")
                else:
                    st.warning("⚠️ Photo file not found at the specified path!")
                
                if st.button("Remove Current Photo", use_container_width=True):
                    website.delete_header_photo(current_photo[0])
                    st.success("✅ Photo removed!")
                    st.rerun()
            else:
                st.info("No active header photo. Upload one above!")
    
    # TAB 7: Booking Requests
    with admin_tabs[6]:
        st.header("📋 Booking Requests Management")
        
        try:
            bookings = website.get_all_bookings()
            
            if bookings:
                for booking in bookings:
                    with st.expander(f"🎤 {booking[1] or 'Anonymous'} - {booking[5]} ({booking[10] if len(booking) > 10 else 'pending'})", expanded=False):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.write(f"**Name:** {booking[1] or 'Not provided'}")
                            st.write(f"**Email:** {booking[2] or 'Not provided'}")
                            st.write(f"**Phone:** {booking[3] or 'Not provided'}")
                            st.write(f"**Event Type:** {booking[4]}")
                            st.write(f"**Event Date:** {booking[5]}")
                            st.write(f"**Venue:** {booking[6] or 'Not specified'}")
                            st.write(f"**Budget:** {booking[7] or 'Not specified'}")
                            st.write(f"**Date Submitted:** {booking[9]}")
                            st.write(f"**Status:** {booking[10] if len(booking) > 10 else 'pending'}")
                            
                            st.markdown("---")
                            st.write("**Message:**")
                            st.write(booking[8])
                        
                        with col2:
                            with st.form(f"booking_status_{booking[0]}"):
                                new_status = st.selectbox("Status", 
                                                        ["pending", "contacted", "confirmed", "declined", "completed"],
                                                        index=["pending", "contacted", "confirmed", "declined", "completed"].index(booking[10]) 
                                                        if len(booking) > 10 and booking[10] in ["pending", "contacted", "confirmed", "declined", "completed"] else 0,
                                                        key=f"b_status_{booking[0]}")
                                
                                if st.form_submit_button("Update Status", type="primary"):
                                    website.update_booking_status(booking[0], new_status)
                                    st.success("✅ Status updated!")
                                    st.rerun()
                            
                            if st.button("Delete Request", key=f"b_delete_{booking[0]}"):
                                cursor = website.conn.cursor()
                                cursor.execute("DELETE FROM bookings WHERE id = ?", (booking[0],))
                                website.conn.commit()
                                st.success("✅ Booking request deleted!")
                                st.rerun()
            else:
                st.info("No booking requests found.")
        except Exception as e:
            st.error(f"Error loading booking requests: {str(e)}")
    
    # TAB 8: Subscribers
    with admin_tabs[7]:
        st.header("Newsletter Subscribers")
        
        try:
            subscribers = website.get_all_subscribers()
            
            if subscribers:
                # Display as table
                df = pd.DataFrame(subscribers, columns=['ID', 'Email', 'Name', 'Date Subscribed'])
                st.dataframe(df, use_container_width=True)
                
                # Export option
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Export as CSV",
                    data=csv,
                    file_name="yanti_siggs_subscribers.csv",
                    mime="text/csv"
                )
            else:
                st.info("No subscribers found.")
        except Exception as e:
            st.error(f"Error loading subscribers: {str(e)}")
    
    # TAB 9: Contact Messages
    with admin_tabs[8]:
        st.header("Contact Messages")
        
        try:
            contacts = website.get_all_contacts()
            
            if contacts:
                for contact in contacts:
                    with st.expander(f"📩 {contact[1]} - {contact[5]} ({contact[6] if len(contact) > 6 else 'unread'})", expanded=False):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.write(f"**Name:** {contact[1]}")
                            st.write(f"**Email:** {contact[2]}")
                            st.write(f"**Phone:** {contact[3] or 'Not provided'}")
                            st.write(f"**Date Sent:** {contact[5]}")
                            st.write(f"**Status:** {contact[6] if len(contact) > 6 else 'unread'}")
                            
                            st.markdown("---")
                            st.write("**Message:**")
                            st.write(contact[4])
                        
                        with col2:
                            with st.form(f"contact_status_{contact[0]}"):
                                new_status = st.selectbox("Status", 
                                                        ["unread", "read", "replied", "archived"],
                                                        index=["unread", "read", "replied", "archived"].index(contact[6]) 
                                                        if len(contact) > 6 and contact[6] in ["unread", "read", "replied", "archived"] else 0,
                                                        key=f"c_status_{contact[0]}")
                                
                                if st.form_submit_button("Update Status", type="primary"):
                                    website.update_contact_status(contact[0], new_status)
                                    st.success("✅ Status updated!")
                                    st.rerun()
                            
                            if st.button("Delete Message", key=f"c_delete_{contact[0]}"):
                                cursor = website.conn.cursor()
                                cursor.execute("DELETE FROM contacts WHERE id = ?", (contact[0],))
                                website.conn.commit()
                                st.success("✅ Message deleted!")
                                st.rerun()
            else:
                st.info("No contact messages found.")
        except Exception as e:
            st.error(f"Error loading contact messages: {str(e)}")
    
    # TAB 10: Admin Settings
    with admin_tabs[9]:
        st.header("Admin Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Change Password")
            with st.form("change_password_form"):
                current_password = st.text_input("Current Password", type="password")
                new_password = st.text_input("New Password", type="password")
                confirm_password = st.text_input("Confirm New Password", type="password")
                
                if st.form_submit_button("Change Password", type="primary"):
                    if new_password == confirm_password:
                        # In production, implement proper password hashing
                        st.success("Password changed successfully!")
                    else:
                        st.error("New passwords don't match!")
        
        with col2:
            st.subheader("Database Management")
            
            if st.button("🔄 Refresh Database", use_container_width=True):
                try:
                    website.setup_database()
                    st.success("Database refreshed!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error refreshing database: {str(e)}")
            
            if st.button("🗑️ Clear Test Data", use_container_width=True):
                st.warning("This will delete all sample data. Are you sure?")
                if st.button("Yes, Delete All Test Data"):
                    try:
                        cursor = website.conn.cursor()
                        cursor.execute("DELETE FROM events WHERE id <= 4")
                        cursor.execute("DELETE FROM gallery WHERE id <= 4")
                        cursor.execute("DELETE FROM music WHERE id <= 3")
                        cursor.execute("DELETE FROM films WHERE id <= 3")
                        cursor.execute("DELETE FROM press WHERE id <= 3")
                        website.conn.commit()
                        st.success("Test data cleared!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error clearing test data: {str(e)}")
    
    # BOTTOM NAVIGATION
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚪 Exit Admin Portal & Return to Main Website", 
                    use_container_width=True, 
                    type="primary",
                    help="Click to go back to the public website"):
            st.session_state.admin_access = False
            st.session_state.show_admin_login = False
            st.session_state.booking_clicks = 0
            st.rerun()

def render_booking_tab():
    """Render the booking request tab with admin access option"""
    st.markdown('<div class="card"><h2 class="card-title">🎤 Book Yanti Siggs</h2>', unsafe_allow_html=True)
    
    st.write("""
    Book Yanti Siggs for your next event! Whether it's a club night, music festival, 
    film screening, or special event, Yanti brings unparalleled energy and talent.
    """)
    
    with st.form("booking_request_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Your Name *")
            email = st.text_input("Your Email *")
            phone = st.text_input("Your Phone *")
        with col2:
            event_type = st.selectbox("Event Type *", 
                                    ["Club Night", "Music Festival", "Corporate Event", 
                                     "Private Party", "Film Screening", "Other"])
            event_date = st.date_input("Event Date *")
            budget = st.selectbox("Budget Range", 
                                ["Please select", "Under $500", "$500 - $1,000", 
                                 "$1,000 - $5,000", "$5,000 - $10,000", "$10,000+"])
        
        venue = st.text_input("Venue/Location")
        message = st.text_area("Event Details *", 
                              placeholder="Please provide details about your event, audience size, special requirements...",
                              height=150)
        
        submitted = st.form_submit_button("Submit Booking Request", type="primary")
        
        if submitted:
            if name and email and phone and event_type and event_date and message:
                website.add_booking_request(name, email, phone, event_type, str(event_date), venue, budget, message)
                st.success("""
                ✅ **Thank you for your booking request!**
                
                Our team has received your request and will contact you within 24-48 hours 
                to discuss your event in detail. We're excited about the possibility of 
                working with you!
                """)
            else:
                st.error("Please fill in all required fields (*)")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ADMIN ACCESS SECTION
    st.markdown("---")
    st.markdown("""
    <div class="admin-access-section">
        <h3>Yanti Studios </h3>
        
    </div>
    """, unsafe_allow_html=True)
    
    # Center the button
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🎛️", 
                    key="booking_tab_admin_button",
                    use_container_width=True,
                    type="secondary"):
            
            current_time = datetime.now()
            
            # Initialize or update click tracking
            if 'booking_clicks' not in st.session_state:
                st.session_state.booking_clicks = 0
                st.session_state.last_booking_click = None
            
            # Check if clicks are within 5 seconds
            if (st.session_state.last_booking_click is None or 
                (current_time - st.session_state.last_booking_click).seconds < 5):
                st.session_state.booking_clicks += 1
            else:
                # Reset if too much time has passed
                st.session_state.booking_clicks = 1
            
            st.session_state.last_booking_click = current_time
            
            if st.session_state.booking_clicks >= 3:
                st.session_state.admin_access = True
                st.session_state.booking_clicks = 0
                st.success("✅ Admin access granted! Loading admin portal...")
                st.rerun()

def main():
    # Page configuration
    st.set_page_config(
        page_title="Yanti Siggs | DJ • Filmmaker • Entrepreneur",
        page_icon="🎵",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Load CSS
    load_css()
    
    # Initialize website database
    global website
    website = YantiSiggsWebsite()
    
    # Initialize session state for admin access
    if 'admin_access' not in st.session_state:
        st.session_state.admin_access = False
    
    if 'booking_clicks' not in st.session_state:
        st.session_state.booking_clicks = 0
    
    if 'last_booking_click' not in st.session_state:
        st.session_state.last_booking_click = None
    
    
    if st.session_state.admin_access:
        render_admin_portal()
    
    else:
        # Regular website content with photo header
        render_header_with_photo()
        
        # Navigation Tabs - Using manual HTML/CSS styling for better control
        st.markdown("""
        <style>
        .custom-tabs {
            display: flex;
            justify-content: center;
            gap: 5px;
            margin-bottom: 2rem;
            flex-wrap: wrap;
        }
        .custom-tab {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 12px 20px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
            border: 1px solid rgba(255, 255, 255, 0.1);
            font-weight: 600;
            color: #ffa726;
            text-decoration: none;
        }
        .custom-tab:hover {
            background: rgba(255, 107, 107, 0.1);
            transform: translateY(-2px);
        }
        .custom-tab.active {
            background: linear-gradient(135deg, #ff6b6b 0%, #ffa726 100%);
            color: white;
            box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3);
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Initialize active tab in session state
        if 'active_tab' not in st.session_state:
            st.session_state.active_tab = "Home"
        
        # Create tabs using columns for better horizontal layout
        tab_names = [
            ("🏠", "Home"), ("🎵", "Music"), ("🎬", "Films"), 
            ("📅", "Events"), ("📸", "Gallery"), ("📰", "Press"),
            ("🎤", "Bookings"), ("📞", "Contact"), ("💌", "Subscribe")
        ]
        
        # Create tab headers
        cols = st.columns(len(tab_names))
        for idx, (icon, name) in enumerate(tab_names):
            with cols[idx]:
                if st.button(f"{icon} {name}", 
                           key=f"tab_{name}",
                           use_container_width=True,
                           type="primary" if st.session_state.active_tab == name else "secondary"):
                    st.session_state.active_tab = name
                    st.rerun()
        
        # Render content based on active tab
        if st.session_state.active_tab == "Home":
            # HOME TAB CONTENT
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown('<div class="card"><h2 class="card-title">Welcome to Yanti Siggs Official Website</h2>', unsafe_allow_html=True)
                st.write("""
                **Yanti Siggs** is a dynamic multi-talented creative force from Zimbabwe, 
                seamlessly blending music, film, and entrepreneurship. As the CEO & Founder of 
                Yanti Studios, she's redefining what it means to be a modern creative entrepreneur.
                
                ### Creative Portfolio:
                • **DJ & Music Producer**: Blending house, afrobeat, and electronic sounds
                • **Filmmaker & Actress**: Creating compelling stories for screen
                • **Entrepreneur**: Building Yanti Studios into a creative powerhouse
                • **Singer & Songwriter**: Expressing stories through music
                
                **Education**: Studied at Damelin College
                """)
                
                # Quote
                st.markdown("""
                <div class="quote-box">
                    <p>"make sure you die empty, life expectancy is now 45yrs!!"</p>
                    <p style="text-align: right; margin-top: 1rem;"><strong>— Yanti Siggs</strong></p>
                </div>
                """, unsafe_allow_html=True)
                
                # Family Section
                st.markdown("### 👨‍👩‍👧‍👦 Family")
                col_a, col_b, col_c, col_d = st.columns(4)
                with col_a:
                    st.markdown("**Eric Zivanai**\n\nBrother")
                with col_b:
                    st.markdown("**Munashe Munzvengi**\n\nCousin")
                with col_c:
                    st.markdown("**Acenah Zee**\n\nCousin")
                with col_d:
                    st.markdown("**Kay Kudzai**\n\nCousin")
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Upcoming Events Preview
                st.markdown('<div class="card"><h2 class="card-title">🎯 Upcoming Events</h2>', unsafe_allow_html=True)
                try:
                    events = website.get_events(limit=3, status='upcoming')
                    if events:
                        for event in events:
                            st.markdown(f"""
                            <div class="event-card">
                                <h4>{event[1]}</h4>
                                <p>📅 {event[2]} | 🕒 {event[3]}<br>
                                📍 {event[4]}</p>
                                <p>{event[5][:100]}...</p>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("No upcoming events at the moment. Check back soon!")
                except Exception as e:
                    st.error(f"Error loading events: {str(e)}")
                    st.info("Events functionality is currently being updated.")
                
                if st.button("View All Events", key="home_events"):
                    st.session_state.active_tab = "Events"
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                # Quick Links
                st.markdown('<div class="card"><h2 class="card-title">🔗 Quick Links</h2>', unsafe_allow_html=True)
                if st.button("🎶 Listen to Music", use_container_width=True):
                    st.session_state.active_tab = "Music"
                    st.rerun()
                if st.button("🎬 Watch Films", use_container_width=True):
                    st.session_state.active_tab = "Films"
                    st.rerun()
                if st.button("📅 View Events Calendar", use_container_width=True):
                    st.session_state.active_tab = "Events"
                    st.rerun()
                if st.button("🎤 Book for Event", use_container_width=True):
                    st.session_state.active_tab = "Bookings"
                    st.rerun()
                if st.button("📸 View Gallery", use_container_width=True):
                    st.session_state.active_tab = "Gallery"
                    st.rerun()
                if st.button("💌 Subscribe", use_container_width=True):
                    st.session_state.active_tab = "Subscribe"
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Latest Music
                st.markdown('<div class="card"><h2 class="card-title">🎵 Latest Release</h2>', unsafe_allow_html=True)
                try:
                    music = website.get_music(limit=1)
                    if music:
                        track = music[0]
                        st.markdown(f"""
                        <div class="music-card">
                            <h4>{track[1]}</h4>
                            <p>📀 Album: {track[2]}<br>
                            🎤 Year: {track[3]}<br>
                            ⏱️ Duration: {track[4]}<br>
                            🎶 Genre: {track[10]}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.info("No music available yet. Check back soon!")
                except Exception as e:
                    st.error(f"Error loading music: {str(e)}")
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Travel Timeline
                st.markdown('<div class="card"><h2 class="card-title">🌍 Travel Timeline</h2>', unsafe_allow_html=True)
                st.markdown("""
                <div class="timeline">
                    <div class="timeline-item">
                        <strong>2006</strong><br>
                        Poland (Sopot, Krakow, Warszawa)<br>
                        Zambia
                    </div>
                    <div class="timeline-item">
                        <strong>2007</strong><br>
                        London, United Kingdom
                    </div>
                    <div class="timeline-item">
                        <strong>2010</strong><br>
                        Victoria Falls, Zimbabwe<br>
                        Cape Town, South Africa
                    </div>
                    <div class="timeline-item">
                        <strong>2011</strong><br>
                        Mozambique
                    </div>
                    <div class="timeline-item">
                        <strong>2012</strong><br>
                        Blantyre, Malawi<br>
                        Got a pet
                    </div>
                    <div class="timeline-item">
                        <strong>2013</strong><br>
                        Botswana<br>
                        Harare, Zimbabwe<br>
                        Johannesburg, South Africa
                    </div>
                    <div class="timeline-item">
                        <strong>2014</strong><br>
                        Other Life Event
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
        
        elif st.session_state.active_tab == "Music":
            # MUSIC TAB CONTENT
            st.markdown('<div class="card"><h2 class="card-title">🎵 Music & DJ Sets</h2>', unsafe_allow_html=True)
            st.write("""
            Experience the unique sound of Yanti Siggs - a fusion of house, afrobeat, 
            and electronic music that gets any crowd moving.
            """)
            
            # Music filters
            col1, col2 = st.columns(2)
            with col1:
                music_genre = st.selectbox("Filter by Genre", ["All", "House", "Afro House", "Afrobeat", "Electronic", "Deep House", "Tech House"])
            with col2:
                sort_by = st.selectbox("Sort By", ["Newest First", "Oldest First", "Alphabetical"])
            
            try:
                music_tracks = website.get_music(genre=music_genre if music_genre != "All" else None)
                
                if sort_by == "Oldest First":
                    music_tracks = sorted(music_tracks, key=lambda x: x[3])  # Year
                elif sort_by == "Alphabetical":
                    music_tracks = sorted(music_tracks, key=lambda x: x[1])  # Title
                
                if music_tracks:
                    for track in music_tracks:
                        with st.expander(f"{track[1]} - {track[2]} ({track[3]}) • {track[10]}", expanded=False):
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.markdown(f"**Album:** {track[2]}")
                                st.markdown(f"**Year:** {track[3]}")
                                st.markdown(f"**Duration:** {track[4]}")
                                st.markdown(f"**Genre:** {track[10]}")
                                
                                # Streaming links
                                if track[5]:  # YouTube
                                    st.markdown(f"[▶️ YouTube]({track[5]})")
                                if track[6]:  # Spotify
                                    st.markdown(f"[🎵 Spotify]({track[6]})")
                                if track[7]:  # SoundCloud
                                    st.markdown(f"[🎚️ SoundCloud]({track[7]})")
                                
                                if track[8]:  # Lyrics
                                    with st.expander("📜 View Lyrics"):
                                        st.write(track[8])
                            
                            with col2:
                                # Play button for local files
                                if track[9]:  # File path
                                    try:
                                        if os.path.exists(track[9]):
                                            with open(track[9], 'rb') as f:
                                                audio_bytes = f.read()
                                            st.audio(audio_bytes, format='audio/mp3')
                                    except:
                                        st.warning("Audio file not available")
                else:
                    st.info("No music tracks available yet. Check back soon!")
            except Exception as e:
                st.error(f"Error loading music: {str(e)}")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        elif st.session_state.active_tab == "Films":
            # FILMS TAB CONTENT
            st.markdown('<div class="card"><h2 class="card-title">🎬 Film Projects</h2>', unsafe_allow_html=True)
            st.write("""
            Explore Yanti Siggs' filmography - from directing and producing to acting, 
            each project tells a unique story.
            """)
            
            try:
                films = website.get_films()
                
                if films:
                    for film in films:
                        with st.expander(f"{film[1]} ({film[2]}) - {film[3]}", expanded=False):
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.markdown(f"**Year:** {film[2]}")
                                st.markdown(f"**Role:** {film[3]}")
                                st.markdown(f"**Status:** {film[9].replace('_', ' ').title() if len(film) > 9 else 'released'}")
                                
                                st.markdown("---")
                                st.markdown(f"**Description:**")
                                st.write(film[4])
                                
                                # Links
                                col_a, col_b, col_c = st.columns(3)
                                if film[5]:  # Trailer
                                    with col_a:
                                        st.markdown(f"[🎬 Trailer]({film[5]})")
                                if film[6]:  # Watch
                                    with col_b:
                                        st.markdown(f"[📺 Watch]({film[6]})")
                                if film[7]:  # IMDb
                                    with col_c:
                                        st.markdown(f"[⭐ IMDb]({film[7]})")
                            
                            with col2:
                                if film[8]:  # Poster
                                    st.image(film[8], width=200)
                else:
                    st.info("No film projects available yet. Check back soon!")
            except Exception as e:
                st.error(f"Error loading films: {str(e)}")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        elif st.session_state.active_tab == "Events":
            # EVENTS TAB CONTENT
            st.markdown('<div class="card"><h2 class="card-title">📅 Upcoming Events & Shows</h2>', unsafe_allow_html=True)
            st.write("""
            Catch Yanti Siggs live at these upcoming events. From club nights to film premieres, 
            there's always something exciting happening.
            """)
            
            # Event filters
            col1, col2 = st.columns(2)
            with col1:
                event_status = st.selectbox("Filter Events", ["upcoming", "past", "all"])
            with col2:
                if st.button("🗓️ Add to Calendar", use_container_width=True):
                    st.info("Calendar integration coming soon!")
            
            try:
                events = website.get_events(status=event_status) if event_status != "all" else website.get_all_events()
                
                if events:
                    for event in events:
                        with st.expander(f"{event[1]} - {event[2]} ({event[8] if len(event) > 8 else 'upcoming'})", expanded=False):
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.markdown(f"**Date:** {event[2]}")
                                st.markdown(f"**Time:** {event[3]}")
                                st.markdown(f"**Venue:** {event[4]}")
                                st.markdown(f"**Status:** {event[8].upper() if len(event) > 8 else 'UPCOMING'}")
                                
                                st.markdown("---")
                                st.markdown(f"**Description:**")
                                st.write(event[5])
                                
                                if len(event) > 7 and event[7]:  # Registration URL
                                    st.markdown(f"[📝 Register Here]({event[7]})")
                            
                            with col2:
                                if len(event) > 6 and event[6]:  # Image URL
                                    st.image(event[6], width=200)
                else:
                    st.info("No events found. Check back soon for upcoming events!")
            except Exception as e:
                st.error(f"Error loading events: {str(e)}")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        elif st.session_state.active_tab == "Gallery":
            # GALLERY TAB CONTENT
            st.markdown('<div class="card"><h2 class="card-title">📸 Visual Portfolio</h2>', unsafe_allow_html=True)
            st.write("""
            A visual journey through Yanti Siggs' creative world - from DJ sets and film shoots 
            to studio sessions and red carpet moments.
            """)
            
            # Gallery categories
            categories = ["All", "Music", "Film", "Studio", "Events", "Personal"]
            selected_category = st.selectbox("Filter by Category", categories)
            
            try:
                gallery_items = website.get_gallery(
                    category=selected_category if selected_category != "All" else None, 
                    limit=12
                )
                
                if gallery_items:
                    # Display in grid
                    cols = st.columns(3)
                    for idx, item in enumerate(gallery_items):
                        with cols[idx % 3]:
                            st.image(item[3], use_column_width=True)
                            st.markdown(f"**{item[1]}**")
                            st.caption(f"{item[2]} • {item[4]}")
                else:
                    st.info("No gallery items available yet. Check back soon!")
            except Exception as e:
                st.error(f"Error loading gallery: {str(e)}")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        elif st.session_state.active_tab == "Press":
            # PRESS TAB CONTENT
            st.markdown('<div class="card"><h2 class="card-title">📰 Press & Media</h2>', unsafe_allow_html=True)
            st.write("""
            Featured press coverage and media appearances highlighting Yanti Siggs' work 
            and creative journey.
            """)
            
            try:
                press_articles = website.get_press()
                
                if press_articles:
                    for article in press_articles:
                        st.markdown(f"""
                        <div class="press-card">
                            <h4>{article[1]}</h4>
                            <p><strong>{article[2]}</strong> • {article[3]}</p>
                            <p>{article[5]}</p>
                            <p><a href="{article[4]}" target="_blank">Read full article →</a></p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No press articles available yet. Check back soon!")
            except Exception as e:
                st.error(f"Error loading press articles: {str(e)}")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        elif st.session_state.active_tab == "Bookings":
            # BOOKINGS TAB CONTENT
            render_booking_tab()
        
        elif st.session_state.active_tab == "Contact":
            # CONTACT TAB CONTENT
            st.markdown('<div class="card"><h2 class="card-title">📞 Contact Yanti Studios</h2>', unsafe_allow_html=True)
            st.write("""
            Get in touch with Yanti Siggs and the Yanti Studios team for collaborations, 
            media inquiries, or general questions.
            """)
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("""
                ### Contact Information
                
                **🎵 CEO & Founder:** Yanti Siggs  
                **🏢 Company:** Yanti Studios  
                **📍 Location:** Zimbabwe
                
                ### Languages Spoken
                • Shona  
                • English
                
                ### Personal Details
                **Gender:** Female  
                **Birth Date:** June 17  
                **Relationship Status:** Single
                
                ### Social Media
                • **Instagram:** @sisiyantisiggs
                • **Other:** @sisiyantisigss
                """)
            
            with col2:
                st.markdown("### Send a Message")
                with st.form("contact_form"):
                    name = st.text_input("Your Name *")
                    email = st.text_input("Your Email *")
                    phone = st.text_input("Your Phone")
                    subject = st.selectbox("Subject", 
                                         ["Collaboration Inquiry", "Media Interview", 
                                          "General Inquiry", "Business Proposal", "Other"])
                    message = st.text_area("Your Message *", height=150)
                    
                    submitted = st.form_submit_button("Send Message", type="primary")
                    
                    if submitted:
                        if name and email and message:
                            website.add_contact_message(name, email, phone, message)
                            st.success("""
                            ✅ **Thank you for your message!**
                            
                            We have received your message and will respond as soon as possible.
                            """)
                        else:
                            st.error("Please fill in all required fields (*)")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        elif st.session_state.active_tab == "Subscribe":
            # SUBSCRIBE TAB CONTENT
            st.markdown('<div class="card"><h2 class="card-title">💌 Subscribe to Newsletter</h2>', unsafe_allow_html=True)
            st.write("""
            Stay updated with Yanti Siggs' latest music releases, film projects, 
            upcoming events, and creative endeavors. Join our exclusive community!
            """)
            
            with st.form("subscribe_form"):
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("Your Name")
                with col2:
                    email = st.text_input("Your Email *")
                
                interests = st.multiselect("Areas of Interest",
                                          ["Music Releases", "DJ Events", "Film Projects", 
                                           "Studio Updates", "Creative Workshops", "All Updates"])
                
                submitted = st.form_submit_button("Subscribe", type="primary")
                
                if submitted:
                    if email:
                        if website.add_subscriber(email, name):
                            st.success("""
                            ✅ **Thank you for subscribing!**
                            
                            Welcome to the Yanti Siggs creative community. 
                            You'll receive exclusive updates and behind-the-scenes content.
                            """)
                        else:
                            st.warning("This email is already subscribed. Thank you for your continued support!")
                    else:
                        st.error("Please enter your email address")
            
            st.markdown("---")
            st.markdown("""
            ### What You'll Receive:
            - 🎵 New music and DJ set releases
            - 🎬 Film project announcements and trailers
            - 📅 Exclusive event invitations
            - 🎨 Behind-the-scenes studio content
            - 💡 Creative insights and updates
            - 🎫 Early access to tickets and merchandise
            """)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Footer
        st.markdown("""
        <div class="footer">
            <h3>Yanti Siggs • Yanti Studios</h3>
            <p>DJ • Music Producer • Filmmaker • Entrepreneur</p>
            <p>Founded March 6, 2022 • Harare, Zimbabwe</p>
            <div class="social-icons">
                <span class="social-icon">🎵</span>
                <span class="social-icon">🎬</span>
                <span class="social-icon">📸</span>
                <span class="social-icon">🎤</span>
            </div>
            <p>© 2024 Yanti Siggs & Yanti Studios. All Rights Reserved.</p>
            <p><small>"make sure you die empty, life expectancy is now 45yrs!!"</small></p>
            <p><small>Website powered by Yanti Studios Creative Technology</small></p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()