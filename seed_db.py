from app import app
from models import db, User, Community, Pair, Event, EventParticipant, Badge, Streak, Game, GameSession, RegistrationCode, Story, ChatReport
from werkzeug.security import generate_password_hash

def seed_data():
    with app.app_context():
        # Reset Database
        print("Dropping all tables...")
        db.drop_all()
        print("Creating all tables...")
        db.create_all()

        # Create Users
        print("Creating users...")
        admin = User(
            username='admin',
            email='admin@gencon.sg',
            full_name='System Admin',
            age=30,
            role='admin',
            password_hash=generate_password_hash('password123'),
            is_approved=True
        )

        senior = User(
            username='senior',
            email='senior@gencon.sg',
            full_name='Madam Tan',
            age=72,
            role='senior',
            password_hash=generate_password_hash('password123'),
            interests_json='["Cooking", "Stories"]',
            is_approved=True
        )

        youth = User(
            username='youth',
            email='youth@gencon.sg',
            full_name='Ryan Lee',
            age=19,
            role='youth',
            password_hash=generate_password_hash('password123'),
            interests_json='["Tech", "Games"]',
            is_approved=True
        )
        
        db.session.add(admin)
        db.session.add(senior)
        db.session.add(youth)
        db.session.commit()

        # Create Communities
        print("Creating communities...")
        
        # Senior Communities
        senior_comms = [
            {
                'name': 'Traditional Arts',
                'type': 'Story',
                'icon': 'fas fa-palette',
                'banner_class': 'arts',
                'tags': 'Painting, Calligraphy, Heritage',
                'desc': 'Explore and share traditional Singaporean art forms including calligraphy, batik painting, and Chinese brush painting.'
            },
            {
                'name': 'Heritage Cooking',
                'type': 'Hobby',
                'icon': 'fas fa-utensils',
                'banner_class': 'cooking',
                'tags': 'Recipes, Food Heritage, Cooking Tips',
                'desc': 'Share traditional recipes, cooking techniques, and culinary stories passed down through generations.'
            },
            {
                'name': 'Story Sharing Circle',
                'type': 'Story',
                'icon': 'fas fa-book-open',
                'banner_class': 'culture',
                'tags': 'Life Stories, History, Wisdom',
                'desc': 'A safe space to share life experiences, wisdom, and stories from Singapore\'s rich history.'
            },
            {
                'name': 'Gardening Enthusiasts',
                'type': 'Hobby',
                'icon': 'fas fa-seedling',
                'banner_class': 'gardening',
                'tags': 'Plants, Gardening, Nature',
                'desc': 'Connect with fellow gardening lovers to share tips on growing tropical plants and herbs.'
            },
            {
                'name': 'Music & Songs',
                'type': 'Hobby',
                'icon': 'fas fa-music',
                'banner_class': 'music',
                'tags': 'Music, Songs, Memories',
                'desc': 'Share your love for music, from traditional songs to modern tunes.'
            },
            {
                'name': 'Active Seniors',
                'type': 'Hobby',
                'icon': 'fas fa-walking',
                'banner_class': 'sports',
                'tags': 'Fitness, Wellness, Activities',
                'desc': 'Stay active and healthy together! Share fitness tips and walking routes.'
            }
        ]

        # Youth Communities
        youth_comms = [
            {
                'name': 'Story Collectors',
                'type': 'Story',
                'icon': 'fas fa-book-open',
                'banner_class': 'storytelling',
                'tags': 'Storytelling, Heritage, Documentation',
                'desc': 'Document and preserve seniors\' life stories. Help create a digital archive of history.'
            },
            {
                'name': 'Tech Helpers',
                'type': 'Learning',
                'icon': 'fas fa-laptop',
                'banner_class': 'tech',
                'tags': 'Technology, Teaching, Digital Skills',
                'desc': 'Bridge the digital divide by teaching seniors how to use smartphones and computers.'
            },
            {
                'name': 'Game Facilitators',
                'type': 'Hobby',
                'icon': 'fas fa-gamepad',
                'banner_class': 'games',
                'tags': 'Games, Recreation, Active Aging',
                'desc': 'Organize and facilitate traditional and modern games with seniors.'
            },
            {
                'name': 'Arts & Crafts Buddies',
                'type': 'Hobby',
                'icon': 'fas fa-palette',
                'banner_class': 'arts',
                'tags': 'Arts, Crafts, Creative',
                'desc': 'Explore creativity through arts and crafts with seniors.'
            },
            {
                'name': 'Language Exchange',
                'type': 'Learning',
                'icon': 'fas fa-language',
                'banner_class': 'language',
                'tags': 'Language, Dialects, Culture',
                'desc': 'Practice and preserve mother tongues through conversations with seniors.'
            },
            {
                'name': 'Wellness Champions',
                'type': 'Hobby',
                'icon': 'fas fa-heartbeat',
                'banner_class': 'wellness',
                'tags': 'Wellness, Exercise, Health',
                'desc': 'Promote health and wellness through exercise and mindfulness activities.'
            }
        ]

        # Add Senior Communities
        for c in senior_comms:
            if not Community.query.filter_by(name=c['name']).first():
                comm = Community(
                    name=c['name'],
                    type=c['type'],
                    icon=c['icon'],
                    banner_class=c['banner_class'],
                    tags=c['tags'],
                    description=c['desc'],
                    created_by=admin.id,
                    member_count=0 
                )
                db.session.add(comm)
        
        # Add Youth Communities
        for c in youth_comms:
            if not Community.query.filter_by(name=c['name']).first():
                comm = Community(
                    name=c['name'],
                    type=c['type'],
                    icon=c['icon'],
                    banner_class=c['banner_class'],
                    tags=c['tags'],
                    description=c['desc'],
                    created_by=admin.id,
                    member_count=0 
                )
                db.session.add(comm)

        db.session.commit()
        print("Database seeded with communities.")

        # Create Events
        print("Creating events...")
        from datetime import datetime, timedelta

        event1 = Event(
            title='Traditional Storytelling Session',
            description='Learn the art of storytelling from experienced seniors. Help document their life stories and preserve cultural heritage.',
            event_type='in-person',
            location='Toa Payoh Community Center',
            date=datetime.utcnow() + timedelta(days=10),
            capacity=20,
            created_by=admin.id
        )

        event2 = Event(
            title='Digital Literacy Workshop for Seniors',
            description='A workshop for youth volunteers to learn how to teach seniors basic digital skills like using a smartphone and video calling.',
            event_type='online',
            location='Zoom',
            date=datetime.utcnow() + timedelta(days=15),
            capacity=50,
            created_by=admin.id
        )
        
        event3 = Event(
            title='Heritage Cooking Class',
            description='Learn to cook traditional dishes from senior chefs. Document recipes and cooking techniques passed down through generations.',
            event_type='in-person',
            location='Ang Mo Kio Community Kitchen',
            date=datetime.utcnow() + timedelta(days=25),
            capacity=15,
            created_by=admin.id
        )

        # ~24h from now — triggers the 24h reminder on next scheduler tick
        event4 = Event(
            title='Morning Tai Chi with Seniors',
            description='Join us for a gentle tai chi session at the park, guided by our senior instructors. Great for all fitness levels.',
            event_type='in-person',
            location='Bishan Park Pavilion',
            date=datetime.utcnow() + timedelta(hours=24),
            capacity=30,
            status='approved',
            created_by=admin.id
        )

        # Past event — both reminders already sent
        event5 = Event(
            title='Seniors Photography Walk',
            description='A guided photography walk around the Civic District with seniors sharing stories about how the area has changed.',
            event_type='in-person',
            location='Padang, City Hall',
            date=datetime.utcnow() - timedelta(days=3),
            capacity=20,
            status='approved',
            created_by=admin.id
        )

        db.session.add(event1)
        db.session.add(event2)
        db.session.add(event3)
        db.session.add(event4)
        db.session.add(event5)
        db.session.commit()

        # Register senior + youth for the upcoming 24h event and the past event
        ep_upcoming = EventParticipant(
            event_id=event4.id,
            user_id=senior.id,
            registered_at=datetime.utcnow() - timedelta(days=5),
            reminder_24h_sent=False,
            reminder_1h_sent=False
        )
        ep_upcoming2 = EventParticipant(
            event_id=event4.id,
            user_id=youth.id,
            registered_at=datetime.utcnow() - timedelta(days=5),
            reminder_24h_sent=False,
            reminder_1h_sent=False
        )
        ep_past = EventParticipant(
            event_id=event5.id,
            user_id=senior.id,
            registered_at=datetime.utcnow() - timedelta(days=10),
            reminder_24h_sent=True,
            reminder_1h_sent=True
        )
        ep_past2 = EventParticipant(
            event_id=event5.id,
            user_id=youth.id,
            registered_at=datetime.utcnow() - timedelta(days=10),
            reminder_24h_sent=True,
            reminder_1h_sent=True
        )
        db.session.add_all([ep_upcoming, ep_upcoming2, ep_past, ep_past2])
        db.session.commit()
        print("Database seeded with events.")

        # Create Streaks and Badges for Youth
        print("Seeding youth progress...")
        from models import Badge, Streak
        
        # Streak for Ryan
        ryan_streak = Streak(
            user_id=youth.id,
            current_streak=5,
            longest_streak=12,
            points=450,
            games_played=12,
            games_won=8
        )
        db.session.add(ryan_streak)

        # Streak for Senior
        senior_streak = Streak(
            user_id=senior.id,
            current_streak=3,
            points=350,
            games_played=15,
            games_won=10
        )
        db.session.add(senior_streak)

        # Badges for Ryan
        badges = [
            Badge(user_id=youth.id, badge_type='First Steps'),
            Badge(user_id=youth.id, badge_type='Story Keeper'),
            Badge(user_id=youth.id, badge_type='Tech Wizard'),
            Badge(user_id=youth.id, badge_type='Heritage Champion')
        ]
        for b in badges:
            db.session.add(b)

        # Create other youth for leaderboard
        other_youth_data = [
            ('sarah_chen', 'Sarah Chen', 1250, 18, 127),
            ('david_tan', 'David Tan', 980, 15, 98),
            ('emily_wong', 'Emily Wong', 850, 11, 87),
            ('marcus_lim', 'Marcus Lim', 720, 10, 75)
        ]
        
        for username, name, pts, badge_count, hours in other_youth_data:
            u = User(
                username=username,
                email=f"{username}@gencon.sg",
                full_name=name,
                age=20,
                role='youth',
                password_hash=generate_password_hash('password123'),
                is_approved=True
            )
            db.session.add(u)
            db.session.flush() # Get ID
            
            # Add streak/points
            s = Streak(user_id=u.id, points=pts, current_streak=badge_count) # Using current_streak as proxy for badges for now
            db.session.add(s)
            
            # Add some badges to make them show up in counts
            for i in range(badge_count):
                db.session.add(Badge(user_id=u.id, badge_type=f'Badge {i}'))

        db.session.commit()
        print("Database seeded successfully!")

        # Create Games
        print("Seeding games...")
        games_list = [
            Game(
                title='International Chess',
                description='The classic game of strategy. Command your army, protect your King, and checkmate your opponent!',
                icon='fas fa-chess-king',
                badge_label='Strategy',
                badge_class='modern',
                badge_icon='fas fa-brain',
                players_text='2 Players',
                duration_text='20-40 min',
                type_label='Strategy',
                type_icon='fas fa-brain',
                bg_gradient='background: linear-gradient(135deg, #2C3E50 0%, #4CA1AF 100%);'
            ),
            Game(
                title='Chinese Chess (Xiangqi)',
                description='A traditional strategy board game for two players. Capture the enemy General to win!',
                icon='fas fa-chess-board',
                badge_label='Traditional',
                badge_class='traditional',
                badge_icon='fas fa-landmark',
                players_text='2 Players',
                duration_text='20-40 min',
                type_label='Strategy',
                type_icon='fas fa-brain',
                bg_gradient='background: linear-gradient(135deg, #C0392B 0%, #E74C3C 100%);'
            ),
            Game(
                title='Tic-Tac-Toe',
                description='Simple, fast, and fun! Get three in a row to win. A perfect quick game to play during a chat session.',
                icon='fas fa-th',
                badge_label='Classic',
                badge_class='modern',
                badge_icon='fas fa-laptop',
                players_text='2 Players',
                duration_text='2-5 min',
                type_label='Logic',
                type_icon='fas fa-lightbulb',
                bg_gradient='' # specific class handles it
            )
        ]
        
        for g in games_list:
            db.session.add(g)
        db.session.commit()
        
        # Create active game session
        chess = Game.query.filter_by(title='International Chess').first()
        
        # Create Buddy Pair (ESSENTIAL for buddy features to work)
        if senior and youth:
            pair = Pair(
                senior_id=senior.id,
                youth_id=youth.id,
                program='Intergenerational Tech Bridge',
                status='active'
            )
            db.session.add(pair)
            db.session.commit()
            print("Seeded buddy pair.")

        if chess and senior and youth:
            gs = GameSession(
                game_id=chess.id,
                player1_id=senior.id,
                player2_id=youth.id,
                current_turn_id=senior.id, # Senior's turn
                status='waiting' # Set to waiting to test readiness
            )
            db.session.add(gs)
            db.session.commit()
            print("Seeded waiting game session.")

        # Create Registration Codes
        print("Seeding registration codes...")
        codes = [
            RegistrationCode(code='SENIOR2025', role='senior'),
            RegistrationCode(code='YOUTH2025',  role='youth'),
            RegistrationCode(code='GENCON01',   role='senior'),
            RegistrationCode(code='GENCON02',   role='youth'),
        ]
        for c in codes:
            db.session.add(c)
        db.session.commit()
        print("Seeded registration codes.")

        # Create sample Stories
        print("Seeding stories...")
        story1 = Story(
            user_id=senior.id,
            title='Growing Up in Kampong Days',
            content='When I was young, our whole kampong would gather under the big angsana tree every evening. The children would play gasing while the elders chatted over kopi-o. Those days taught me the true meaning of community — everyone looked out for one another.',
            category='Childhood'
        )
        story2 = Story(
            user_id=senior.id,
            title='My First Day at the Factory',
            content='I started work at the textile factory at age 16. The noise from the machines was deafening but the friendships I made there lasted a lifetime. My supervisor, Auntie Rose, taught me that hard work and integrity are worth more than any salary.',
            category='Work Life'
        )
        db.session.add_all([story1, story2])
        db.session.commit()

        # Create a sample story report (to test moderation UI)
        story_report = ChatReport(
            story_id=story1.id,
            reported_by=youth.id,
            reported_user_id=senior.id,
            reason='Misinformation',
            description='Sample report for testing the story moderation feature.',
            status='pending'
        )
        db.session.add(story_report)
        db.session.commit()
        print("Seeded stories and sample story report.")

if __name__ == '__main__':
    seed_data()
