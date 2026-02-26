"""
seed_db.py — Comprehensive demo seed for GenCon SG.

Login credentials (all passwords: password123)
  Admin  : admin
  Seniors: madam_tan | uncle_rajan | auntie_siti | mr_lim | mrs_wong | uncle_ali
  Youth  : ryan_lee  | sarah_chen  | david_tan   | emily_wong | marcus_lim | priya_k
"""

import json
from app import app
from models import (
    db, User, Community, CommunityMember, CommunityPost,
    Pair, Event, EventParticipant,
    Badge, Streak, Game, GameSession, GameHistory, TicTacToeSession,
    RegistrationCode, Story, StoryComment, StoryReaction,
    Message, ChatReport, Checkin, SupportTicket, Notification,
)
from werkzeug.security import generate_password_hash
from datetime import date, datetime, timedelta


def dob_from_age(age):
    return date(datetime.utcnow().year - age, 1, 1)


def seed_data():
    with app.app_context():
        print("Dropping tables…")
        db.drop_all()
        print("Creating tables…")
        db.create_all()

        # ── 1. USERS ──────────────────────────────────────────────────────────
        print("Seeding users…")

        admin = User(
            username='admin', email='admin@gencon.sg',
            full_name='System Admin', dob=dob_from_age(35),
            role='admin', is_approved=True,
            password_hash=generate_password_hash('password123'),
        )

        # Seniors ─────────────────────────────────────────────────────────────
        s1 = User(
            username='senior', email='tan.beehoon@gencon.sg',
            full_name='Madam Tan', dob=dob_from_age(72), phone='+65 9111 2233',
            role='senior', is_approved=True,
            bio='Retired schoolteacher who loves cooking Peranakan dishes and tending to my little garden. Happy to share stories from a simpler Singapore.',
            interests_json=json.dumps(['Cooking', 'Gardening', 'Stories', 'Teaching']),
            languages_json=json.dumps(['EN', 'ZH']),
            accessibility_settings_json=json.dumps({'fontSize': 'large', 'highContrast': False, 'colorBlind': False}),
            elo=1250, password_hash=generate_password_hash('password123'),
        )
        s2 = User(
            username='uncle_rajan', email='rajan.pillai@gencon.sg',
            full_name='Rajan Pillai', dob=dob_from_age(68), phone='+65 9222 3344',
            role='senior', is_approved=True,
            bio='Former music teacher with a love for Carnatic music and cricket. Always happy to share stories from the early days of independent Singapore.',
            interests_json=json.dumps(['Music', 'History', 'Cricket', 'Stories']),
            languages_json=json.dumps(['EN', 'TA']),
            accessibility_settings_json=json.dumps({'fontSize': 'xl', 'highContrast': True, 'colorBlind': False}),
            elo=1150, password_hash=generate_password_hash('password123'),
        )
        s3 = User(
            username='auntie_siti', email='siti.mariam@gencon.sg',
            full_name='Siti Mariam Binte Hassan', dob=dob_from_age(75), phone='+65 9333 4455',
            role='senior', is_approved=True,
            bio='Grandmother of eight! I love cooking Malay dishes and keeping traditional sewing alive. Every stitch tells a story.',
            interests_json=json.dumps(['Cooking', 'Gardening', 'Sewing', 'Family']),
            languages_json=json.dumps(['EN', 'MS']),
            accessibility_settings_json=json.dumps({'fontSize': 'large', 'highContrast': False, 'colorBlind': False}),
            elo=1100, password_hash=generate_password_hash('password123'),
        )
        s4 = User(
            username='mr_lim', email='lim.chenghuat@gencon.sg',
            full_name='Lim Cheng Huat', dob=dob_from_age(70), phone='+65 9444 5566',
            role='senior', is_approved=True,
            bio='Chess enthusiast and amateur photographer. Spent 30 years as an engineer and now enjoy the slower pace of retirement with a camera in hand.',
            interests_json=json.dumps(['Chess', 'Photography', 'Gardening', 'Technology']),
            languages_json=json.dumps(['EN', 'ZH']),
            accessibility_settings_json=json.dumps({'fontSize': 'normal', 'highContrast': False, 'colorBlind': False}),
            elo=1380, password_hash=generate_password_hash('password123'),
        )
        s5 = User(
            username='mrs_wong', email='wong.ahmoi@gencon.sg',
            full_name='Wong Ah Moi', dob=dob_from_age(65), phone='+65 9555 6677',
            role='senior', is_approved=True,
            bio='Retired nurse with a passion for music and handcrafts. I believe in the healing power of connection and laughter.',
            interests_json=json.dumps(['Music', 'Knitting', 'Stories', 'Cooking']),
            languages_json=json.dumps(['EN', 'ZH']),
            accessibility_settings_json=json.dumps({'fontSize': 'large', 'highContrast': False, 'colorBlind': False}),
            elo=1200, password_hash=generate_password_hash('password123'),
        )
        s6 = User(
            username='uncle_ali', email='ali.hassan@gencon.sg',
            full_name='Muhammad Ali Bin Hassan', dob=dob_from_age(78), phone='+65 9666 7788',
            role='senior', is_approved=True,
            bio="Old fisherman who knows every corner of Singapore's waterways. Love sharing stories about life before the HDB flats went up.",
            interests_json=json.dumps(['Fishing', 'History', 'Art', 'Nature']),
            languages_json=json.dumps(['EN', 'MS']),
            accessibility_settings_json=json.dumps({'fontSize': 'xl', 'highContrast': False, 'colorBlind': True}),
            elo=1080, password_hash=generate_password_hash('password123'),
        )

        # Youth ───────────────────────────────────────────────────────────────
        y1 = User(
            username='youth', email='ryan.lee@gencon.sg',
            full_name='Ryan Lee', dob=dob_from_age(19), phone='+65 8111 2233',
            role='youth', is_approved=True,
            bio='Year 1 IT student at NYP. Passionate about using technology to bridge generational gaps.',
            school='Nanyang Polytechnic',
            interests_json=json.dumps(['Tech', 'Gaming', 'Photography', 'Volunteering']),
            languages_json=json.dumps(['EN', 'ZH']),
            elo=1200, password_hash=generate_password_hash('password123'),
        )
        y2 = User(
            username='sarah_chen', email='sarah.chen@gencon.sg',
            full_name='Sarah Chen', dob=dob_from_age(21), phone='+65 8222 3344',
            role='youth', is_approved=True,
            bio='NUS Music student who volunteers to share the joy of music with seniors and learn from their wisdom.',
            school='National University of Singapore',
            interests_json=json.dumps(['Music', 'Photography', 'Art', 'Volunteering']),
            languages_json=json.dumps(['EN', 'ZH', 'TA']),
            elo=1280, password_hash=generate_password_hash('password123'),
        )
        y3 = User(
            username='david_tan', email='david.tan@gencon.sg',
            full_name='David Tan', dob=dob_from_age(20), phone='+65 8333 4455',
            role='youth', is_approved=True,
            bio='NTU Food Science student who loves learning traditional recipes from seniors.',
            school='Nanyang Technological University',
            interests_json=json.dumps(['Cooking', 'Gardening', 'Stories', 'Food']),
            languages_json=json.dumps(['EN', 'ZH']),
            elo=1150, password_hash=generate_password_hash('password123'),
        )
        y4 = User(
            username='emily_wong', email='emily.wong@gencon.sg',
            full_name='Emily Wong', dob=dob_from_age(22), phone='+65 8444 5566',
            role='youth', is_approved=True,
            bio='SMU Arts student passionate about documenting senior life stories and preserving cultural heritage.',
            school='Singapore Management University',
            interests_json=json.dumps(['Art', 'Stories', 'Photography', 'Heritage']),
            languages_json=json.dumps(['EN', 'ZH']),
            elo=1220, password_hash=generate_password_hash('password123'),
        )
        y5 = User(
            username='marcus_lim', email='marcus.lim@gencon.sg',
            full_name='Marcus Lim', dob=dob_from_age(18), phone='+65 8555 6677',
            role='youth', is_approved=True,
            bio='RP student who enjoys chess and photography. Eager to learn from seniors and their life experiences.',
            school='Republic Polytechnic',
            interests_json=json.dumps(['Chess', 'Photography', 'Tech', 'Gaming']),
            languages_json=json.dumps(['EN', 'ZH']),
            elo=1180, password_hash=generate_password_hash('password123'),
        )
        y6 = User(
            username='priya_k', email='priya.krishnamurthy@gencon.sg',
            full_name='Priya Krishnamurthy', dob=dob_from_age(23), phone='+65 8666 7788',
            role='youth', is_approved=True,
            bio='SIT Engineering student who volunteers to share music and cultural exchange with seniors.',
            school='Singapore Institute of Technology',
            interests_json=json.dumps(['Music', 'Tech', 'Dance', 'Culture']),
            languages_json=json.dumps(['EN', 'TA']),
            elo=1100, password_hash=generate_password_hash('password123'),
        )

        db.session.add_all([admin, s1, s2, s3, s4, s5, s6, y1, y2, y3, y4, y5, y6])
        db.session.commit()
        print(f"  {User.query.count()} users created.")

        # ── 2. COMMUNITIES ────────────────────────────────────────────────────
        print("Seeding communities…")

        def make_comm(name, ctype, icon, banner, tags, desc, created_by=None):
            return Community(
                name=name, type=ctype, icon=icon, banner_class=banner,
                tags=tags, description=desc,
                created_by=(created_by or admin.id), member_count=0,
            )

        c_arts    = make_comm('Traditional Arts',      'Story',    'fas fa-palette',    'arts',        'Painting, Calligraphy, Heritage',          'Explore traditional Singaporean art forms including calligraphy, batik painting, and Chinese brush painting.')
        c_cook    = make_comm('Heritage Cooking',       'Hobby',    'fas fa-utensils',   'cooking',     'Recipes, Food Heritage, Cooking Tips',     'Share traditional recipes and cooking techniques passed down through generations.')
        c_circle  = make_comm('Story Sharing Circle',   'Story',    'fas fa-book-open',  'culture',     'Life Stories, History, Wisdom',            "A safe space to share life experiences and wisdom from Singapore's rich history.")
        c_garden  = make_comm('Gardening Enthusiasts',  'Hobby',    'fas fa-seedling',   'gardening',   'Plants, Gardening, Nature',                'Connect with fellow gardening lovers to share tips on growing tropical plants and herbs.')
        c_music   = make_comm('Music & Songs',          'Hobby',    'fas fa-music',      'music',       'Music, Songs, Memories',                   'Share your love for music, from traditional songs to modern tunes.')
        c_active  = make_comm('Active Seniors',         'Hobby',    'fas fa-walking',    'sports',      'Fitness, Wellness, Activities',            'Stay active and healthy together! Share fitness tips and walking routes.')
        c_story   = make_comm('Story Collectors',       'Story',    'fas fa-book-open',  'storytelling','Storytelling, Heritage, Documentation',    "Document and preserve seniors' life stories. Help create a digital archive of history.")
        c_tech    = make_comm('Tech Helpers',           'Learning', 'fas fa-laptop',     'tech',        'Technology, Teaching, Digital Skills',     'Bridge the digital divide by teaching seniors how to use smartphones and computers.')
        c_games   = make_comm('Game Facilitators',      'Hobby',    'fas fa-gamepad',    'games',       'Games, Recreation, Active Aging',          'Organize and facilitate traditional and modern games with seniors.')
        c_crafts  = make_comm('Arts & Crafts Buddies',  'Hobby',    'fas fa-palette',    'arts',        'Arts, Crafts, Creative',                   'Explore creativity through arts and crafts with seniors.')
        c_lang    = make_comm('Language Exchange',      'Learning', 'fas fa-language',   'language',    'Language, Dialects, Culture',              'Practice and preserve mother tongues through conversations with seniors.')
        c_well    = make_comm('Wellness Champions',     'Hobby',    'fas fa-heartbeat',  'wellness',    'Wellness, Exercise, Health',               'Promote health and wellness through exercise and mindfulness activities.')

        # Pending community suggested by a youth user
        c_pending = make_comm('Photography Heritage',  'Story',    'fas fa-camera',     'arts',        'Photography, Heritage, Memory',            'Use photography to document and celebrate seniors and their living history.', created_by=y4.id)
        c_pending.status      = 'pending'
        c_pending.justification = 'Photography is a powerful way to preserve memories. Would love to create this with our seniors!'

        db.session.add_all([c_arts, c_cook, c_circle, c_garden, c_music, c_active,
                            c_story, c_tech, c_games, c_crafts, c_lang, c_well, c_pending])
        db.session.commit()
        print(f"  {Community.query.count()} communities created.")

        # ── 3. GAMES ──────────────────────────────────────────────────────────
        print("Seeding games…")
        g_chess = Game(title='International Chess',     description='The classic game of strategy. Command your army, protect your King, and checkmate your opponent!',                         icon='fas fa-chess-king',  badge_label='Strategy',   badge_class='modern',      badge_icon='fas fa-brain',    players_text='2 Players', duration_text='20-40 min', type_label='Strategy', type_icon='fas fa-brain',     bg_gradient='background: linear-gradient(135deg, #2C3E50 0%, #4CA1AF 100%);')
        g_xq    = Game(title='Chinese Chess (Xiangqi)', description='A traditional strategy board game for two players. Capture the enemy General to win!',                                     icon='fas fa-chess-board', badge_label='Traditional', badge_class='traditional', badge_icon='fas fa-landmark', players_text='2 Players', duration_text='20-40 min', type_label='Strategy', type_icon='fas fa-brain',     bg_gradient='background: linear-gradient(135deg, #C0392B 0%, #E74C3C 100%);')
        g_ttt   = Game(title='Tic-Tac-Toe',             description='Simple, fast, and fun! Get three in a row to win. A perfect quick game to play during a chat session.',                   icon='fas fa-th',          badge_label='Classic',    badge_class='modern',      badge_icon='fas fa-laptop',   players_text='2 Players', duration_text='2-5 min',   type_label='Logic',    type_icon='fas fa-lightbulb', bg_gradient='')
        db.session.add_all([g_chess, g_xq, g_ttt])
        db.session.commit()

        # ── 4. BUDDY PAIRS ────────────────────────────────────────────────────
        print("Seeding pairs…")
        db.session.add_all([
            Pair(senior_id=s1.id, youth_id=y1.id, program='Intergenerational Tech Bridge',   status='active',   last_interaction=datetime.utcnow() - timedelta(hours=2)),
            Pair(senior_id=s2.id, youth_id=y2.id, program='Music & Memories',               status='active',   last_interaction=datetime.utcnow() - timedelta(days=1)),
            Pair(senior_id=s3.id, youth_id=y3.id, program='Heritage Cooking Circle',        status='active',   last_interaction=datetime.utcnow() - timedelta(days=2)),
            Pair(senior_id=s4.id, youth_id=y4.id, program='Story Documentation Project',   status='active',   last_interaction=datetime.utcnow() - timedelta(days=3)),
            Pair(senior_id=s5.id, youth_id=y5.id, program='Games & Wellness',              status='active',   last_interaction=datetime.utcnow() - timedelta(days=5)),
            Pair(senior_id=s6.id, youth_id=y6.id, program='Cultural Language Exchange',    status='inactive', last_interaction=datetime.utcnow() - timedelta(days=30)),
        ])
        db.session.commit()
        print(f"  {Pair.query.count()} pairs created.")

        # ── 5. EVENTS ─────────────────────────────────────────────────────────
        print("Seeding events…")
        now = datetime.utcnow()

        ev = {}
        event_defs = [
            # (key, title, desc, type, location, delta_days, capacity, status, justification, created_by)
            ('story',   'Traditional Storytelling Session',        'Learn the art of storytelling from experienced seniors. Help document their life stories and preserve cultural heritage.',                      'in-person', 'Toa Payoh Community Center',   10,   20, 'approved', None,                                                                              admin.id),
            ('digital', 'Digital Literacy Workshop',               'A hands-on workshop where youth volunteers teach seniors basic digital skills — smartphones, video calls, and online safety.',                  'online',    'Zoom',                         15,   50, 'approved', None,                                                                              admin.id),
            ('cooking', 'Heritage Cooking Class',                  'Learn to cook traditional dishes from senior chefs. Document recipes and cooking techniques passed down through generations.',                  'in-person', 'Ang Mo Kio Community Kitchen', 25,   15, 'approved', None,                                                                              admin.id),
            ('taichi',  'Morning Tai Chi with Seniors',            'A gentle tai chi session at the park, guided by our senior instructors. Great for all fitness levels.',                                        'in-person', 'Bishan Park Pavilion',          0,    30, 'approved', None,                                                                              admin.id),  # ~24 h trigger
            ('photo',   'Seniors Photography Walk',                'A guided photography walk around the Civic District with seniors sharing stories about how the area has changed.',                             'in-person', 'Padang, City Hall',            -3,   20, 'approved', None,                                                                              admin.id),
            ('calli',   'Seniors Calligraphy Exhibition',          'Showcase calligraphy artworks created by seniors at the community centre. A great way to celebrate traditional arts.',                         'in-person', 'Bishan Community Centre',      20,   40, 'pending',  'Would love to let seniors showcase their beautiful work!',                        y4.id),
            ('games',   'Intergenerational Board Games Day',       'A fun afternoon of Scrabble, Chinese Chess, and card games between seniors and youth volunteers. Light refreshments provided.',                 'in-person', 'Toa Payoh Hub',                35,   50, 'pending',  'Fun activity to strengthen buddy bonds through friendly competition.',            admin.id),
            ('dance',   'Cultural Dance Workshop',                  'Learn traditional dances like the Lion Dance and Malay folk dances alongside senior performers.',                                              'in-person', 'Our Tampines Hub',             45,   35, 'approved', None,                                                                              admin.id),
            ('lang',    'Language Exchange Lunch',                 'Share a meal and practice mother tongue languages with seniors. Seniors teach dialects; youth help with apps and menus.',                       'in-person', 'Geylang Serai Market',         -7,   25, 'approved', None,                                                                              admin.id),
            ('tech',    'Tech Help Session for Seniors',           'Youth volunteers guide seniors through common tech challenges — setting up email, video calls, and staying safe online.',                       'online',    'Zoom',                          5,   40, 'approved', None,                                                                              admin.id),
        ]

        for key, title, desc, etype, loc, delta, cap, status, just, creator in event_defs:
            date_val = now + timedelta(days=delta) if key != 'taichi' else now + timedelta(hours=24)
            e = Event(title=title, description=desc, event_type=etype, location=loc,
                      date=date_val, capacity=cap, status=status,
                      justification=just, created_by=creator)
            db.session.add(e)
            ev[key] = e

        db.session.commit()

        # Event registrations
        # Ryan (y1) joins 3 events → First Steps ✓ + Event Organizer ✓
        ep_rows = [
            # (event, user, delta_registered, r24h, r1h)
            (ev['story'],   y1,  -20, False, False),
            (ev['taichi'],  s1,   -5, False, False),
            (ev['taichi'],  y1,   -5, False, False),
            (ev['photo'],   s1,  -10, True,  True),
            (ev['photo'],   y1,  -10, True,  True),
            (ev['photo'],   s4,  -10, True,  True),
            (ev['photo'],   y4,  -10, True,  True),
            (ev['story'],   s1,  -18, False, False),
            (ev['story'],   s2,  -18, False, False),
            (ev['story'],   y2,  -18, False, False),
            (ev['cooking'], s3,   -5, False, False),
            (ev['cooking'], y3,   -5, False, False),
            (ev['cooking'], s1,   -5, False, False),
            (ev['digital'], s4,   -3, False, False),
            (ev['digital'], y3,   -3, False, False),
            (ev['tech'],    s4,   -2, False, False),
            (ev['tech'],    y5,   -2, False, False),
            (ev['dance'],  s3,    -1, False, False),
            (ev['dance'],  s5,    -1, False, False),
            (ev['dance'],  y2,    -1, False, False),
            (ev['dance'],  y6,    -1, False, False),
            (ev['lang'],   s2,   -14, True,  True),
            (ev['lang'],   s6,   -14, True,  True),
            (ev['lang'],   y2,   -14, True,  True),
            (ev['lang'],   y6,   -14, True,  True),
        ]
        seen_ep = set()
        for event_obj, user_obj, reg_delta, r24, r1 in ep_rows:
            key = (event_obj.id, user_obj.id)
            if key in seen_ep:
                continue
            seen_ep.add(key)
            db.session.add(EventParticipant(
                event_id=event_obj.id, user_id=user_obj.id,
                registered_at=now + timedelta(days=reg_delta),
                reminder_24h_sent=r24, reminder_1h_sent=r1,
            ))
        db.session.commit()
        print(f"  Events and registrations seeded.")

        # ── 6. STREAKS ────────────────────────────────────────────────────────
        print("Seeding streaks…")
        db.session.add_all([
            Streak(user_id=y1.id, current_streak=5,  longest_streak=12, points=450,  games_played=12, games_won=8),   # Game Master 12/15
            Streak(user_id=y2.id, current_streak=15, longest_streak=21, points=1250, games_played=22, games_won=14),
            Streak(user_id=y3.id, current_streak=8,  longest_streak=14, points=980,  games_played=18, games_won=10),
            Streak(user_id=y4.id, current_streak=12, longest_streak=18, points=850,  games_played=8,  games_won=5),
            Streak(user_id=y5.id, current_streak=3,  longest_streak=7,  points=720,  games_played=6,  games_won=4),
            Streak(user_id=y6.id, current_streak=1,  longest_streak=3,  points=200,  games_played=3,  games_won=1),
            Streak(user_id=s1.id, current_streak=7,  longest_streak=14, points=350,  games_played=15, games_won=9),
            Streak(user_id=s2.id, current_streak=4,  longest_streak=8,  points=180,  games_played=8,  games_won=3),
            Streak(user_id=s3.id, current_streak=2,  longest_streak=5,  points=120,  games_played=5,  games_won=2),
            Streak(user_id=s4.id, current_streak=10, longest_streak=22, points=520,  games_played=25, games_won=18),
            Streak(user_id=s5.id, current_streak=3,  longest_streak=9,  points=220,  games_played=10, games_won=6),
            Streak(user_id=s6.id, current_streak=1,  longest_streak=4,  points=80,   games_played=4,  games_won=1),
        ])
        db.session.commit()

        # ── 7. STORIES ────────────────────────────────────────────────────────
        print("Seeding stories…")

        stories = {}
        story_defs = [
            # (key, user, title, content, category, days_ago)
            ('s1a', s1, 'Growing Up in Kampong Days',
             'When I was young, our whole kampong would gather under the big angsana tree every evening. The children played gasing while the elders chatted over kopi-o. Everyone looked out for one another — no one locked their doors.',
             'Childhood', 30),
            ('s1b', s1, 'My First Day as a Teacher',
             'I still remember the smell of chalk dust and the rows of eager faces staring back at me. I was only 22 years old, terrified but excited. The children taught me as much as I taught them.',
             'Work Life', 20),
            ('s1c', s1, 'Recipes from My Nyonya Kitchen',
             'My mother would spend the whole morning grinding rempah by hand. The sound of the batu lesung was the music of our kitchen. Today I use a blender, but I always add love the old-fashioned way.',
             'Hobbies', 10),
            ('s2a', s2, 'Music That Shaped My Soul',
             'My father played the veena every evening after dinner. That sound — ancient, warm, endless — shaped everything I became. I went on to teach music for 35 years and I still tear up when I hear a mridangam.',
             'Childhood', 25),
            ('s2b', s2, 'The Day Singapore Became Independent',
             'I was 10 years old and standing beside my father listening to the radio. He cried quietly. I did not understand then, but now — after all these years — I understand completely what that moment meant.',
             'Other', 15),
            ('s3a', s3, 'Sewing Stories Into Every Stitch',
             'My mother taught me to sew when I was seven. Every kebaya I make holds a memory. The blue one is for my wedding. The green one is for the day my first grandchild was born.',
             'Family', 22),
            ('s3b', s3, 'Nasi Lemak at 5am',
             'Every Sunday my mother woke before dawn to cook nasi lemak for the whole neighbourhood. The coconut rice, the sambal, the ikan bilis — I have been trying to recreate that recipe my whole life.',
             'Hobbies', 8),
            ('s4a', s4, 'Building Singapore One Bridge at a Time',
             'As a civil engineer in the 1980s, I worked on some of the expressways you drive on today. We worked six days a week in the heat with very basic equipment. Every overpass I pass now, I remember a colleague.',
             'Work Life', 18),
            ('s4b', s4, 'The Chess That Changed My Life',
             'A stranger challenged me to a chess game at the Toa Payoh library when I was 14. He was an old Indian gentleman who barely spoke. He beat me in 12 moves and left without a word — and I have been studying chess ever since.',
             'Childhood', 5),
            ('s5a', s5, 'Night Shifts and Bedside Stories',
             'As a nurse at SGH for 30 years, I held the hands of patients who had no family to call. I sang old Mandarin songs to calm them. People die the same way they live — the brave ones go quietly.',
             'Work Life', 12),
        ]

        for key, user_obj, title, content, cat, days_ago in story_defs:
            s = Story(user_id=user_obj.id, title=title, content=content, category=cat,
                      created_at=now - timedelta(days=days_ago))
            db.session.add(s)
            stories[key] = s

        db.session.commit()

        # Story reactions (various users reacting to various stories)
        # Ryan (y1) gives 5 reactions → Heritage Champion ✓
        reaction_rows = [
            # (story_key, user, reaction_type)
            ('s1a', y1, 'heart'), ('s1a', y1, 'clap'), ('s1a', y1, 'hug'),
            ('s1b', y1, 'heart'), ('s1b', y1, 'smile'),
            # Other youth react too
            ('s1a', y2, 'heart'), ('s1a', y4, 'hug'),
            ('s2a', y2, 'clap'),  ('s2a', y6, 'heart'),
            ('s3a', y3, 'heart'), ('s3b', y3, 'smile'),
            ('s4a', y4, 'clap'),  ('s4b', y5, 'heart'),
            ('s5a', y2, 'hug'),   ('s5a', y4, 'clap'),
            ('s2b', y2, 'heart'), ('s2b', y6, 'clap'),
            ('s1c', y3, 'smile'), ('s3b', y4, 'heart'),
        ]
        seen_rx = set()
        for sk, user_obj, rtype in reaction_rows:
            key = (stories[sk].id, user_obj.id, rtype)
            if key in seen_rx:
                continue
            seen_rx.add(key)
            db.session.add(StoryReaction(story_id=stories[sk].id, user_id=user_obj.id, reaction_type=rtype))

        # Story comments (Ryan gives 5 → Story Keeper ✓)
        comment_rows = [
            # (story_key, user, content)
            ('s1a', y1, 'This brings back such vivid images of old Singapore! Thank you for sharing, Madam Tan.'),
            ('s1a', y1, 'I never knew about kampong life. It is so different from growing up in an HDB flat.'),
            ('s1a', y1, 'The part about nobody locking their doors — that really struck me.'),
            ('s1b', y1, 'What subject did you teach? You sound like such an inspiring teacher!'),
            ('s1c', y1, 'My grandmother also grinds by hand. She says the blender "kills the flavour" haha!'),
            # Others
            ('s2a', y2, 'Uncle Rajan, this is so moving. Music really does transcend everything.'),
            ('s2b', y2, 'I learned about this in history class but hearing it from someone who was there is completely different.'),
            ('s3a', y3, 'Auntie Siti, can you teach us to sew at the next community event?'),
            ('s3b', y4, 'The 5am nasi lemak image is so beautiful. Food really is memory.'),
            ('s4a', y4, 'The highways you built — we drive on them every day without thinking about the people behind them. Thank you.'),
            ('s4b', y5, 'A stranger teaching chess in a library! This sounds like the plot of a movie, Mr Lim.'),
            ('s5a', y2, 'Mrs Wong, thank you for your service. Singing to calm patients is so touching.'),
            ('s2a', y6, 'The veena is such a beautiful instrument. Did you ever record yourself playing?'),
        ]
        for sk, user_obj, content in comment_rows:
            db.session.add(StoryComment(story_id=stories[sk].id, user_id=user_obj.id, content=content,
                                        created_at=now - timedelta(days=2)))

        db.session.commit()
        print(f"  {Story.query.count()} stories, reactions, and comments seeded.")

        # ── 8. MESSAGES (conversations between pairs) ─────────────────────────
        print("Seeding messages…")

        def msg(sender, recipient, content, lang='en', translated=None, flagged=False, days_ago=0, hours_ago=0):
            db.session.add(Message(
                sender_id=sender.id, recipient_id=recipient.id,
                content=content, original_language=lang,
                translated_content=translated, is_flagged=flagged,
                created_at=now - timedelta(days=days_ago, hours=hours_ago),
            ))

        # ── Ryan (y1) ↔ Madam Tan (s1) — 32 messages, Ryan sends 22 → Conversation Partner ✓
        msg(y1, s1, 'Good morning Madam Tan! How are you doing today?',                                                           days_ago=7)
        msg(s1, y1, 'Good morning Ryan! I am doing well, just finished watering my garden.',                                      days_ago=7)
        msg(y1, s1, 'That sounds lovely! What are you growing these days?',                                                        days_ago=7)
        msg(s1, y1, 'Kangkong, chilli padi, and some pandan. Do you like gardening?',                                             days_ago=7)
        msg(y1, s1, 'I have never tried but it sounds very relaxing. Maybe you can teach me!',                                    days_ago=6)
        msg(s1, y1, 'Of course! Come to the next community event and I will show you.',                                           days_ago=6)
        msg(y1, s1, 'I saw your story about kampong days. It was so touching, Madam Tan.',                                        days_ago=6)
        msg(s1, y1, 'Thank you Ryan. Those memories are very precious to me.',                                                    days_ago=5)
        msg(y1, s1, 'Can I ask — what was your favourite childhood game?',                                                        days_ago=5)
        msg(s1, y1, 'Gasing! Spinning tops. The boys competed for hours. Very noisy but very fun.',                               days_ago=5)
        msg(y1, s1, 'Haha that sounds like competitive gaming but old school! I love chess too — maybe we can play?',            days_ago=4)
        msg(s1, y1, 'Yes! My late husband taught me chess. I am a little rusty but I will try.',                                  days_ago=4)
        msg(y1, s1, 'That is beautiful. I would love to hear more about him sometime if you are comfortable.',                    days_ago=4)
        msg(s1, y1, 'He was a good man. Very patient. Reminds me of you young people who volunteer.',                            days_ago=3)
        msg(y1, s1, 'You are too kind! Are you registered for the Photography Walk this Saturday?',                              days_ago=3)
        msg(s1, y1, 'Yes! I am very excited. I want to see how Civic District has changed.',                                     days_ago=3)
        msg(y1, s1, 'Me too! Should we meet at the entrance together?',                                                          days_ago=2)
        msg(s1, y1, 'Perfect. I will wear my red kebaya so you can spot me easily.',                                             days_ago=2)
        msg(y1, s1, 'I will look out for you! The red kebaya sounds beautiful.',                                                  days_ago=2)
        msg(y1, s1, 'Also, I was reading about your teaching story. What subject did you teach?',                                 days_ago=1)
        msg(s1, y1, 'English and Moral Education for 30 years. I miss my students very much.',                                   days_ago=1)
        msg(y1, s1, 'Wow 30 years! That is such a long and impactful career. The students were lucky.',                          days_ago=1)
        msg(y1, s1, 'By the way, I found a nice recipe for kueh lapis online. Is it similar to yours?',                          hours_ago=6)
        msg(s1, y1, 'Haha! Online recipes always miss something. The secret is patience and love.',                               hours_ago=5)
        msg(y1, s1, 'I will ask you to teach me properly one day then!',                                                          hours_ago=5)
        msg(s1, y1, 'Anytime! Come to my house after the next event.',                                                            hours_ago=4)
        msg(y1, s1, 'That would be amazing, thank you Madam Tan!',                                                                hours_ago=4)
        msg(y1, s1, 'Quick question — can you see the notification bell at the top of the screen okay?',                         hours_ago=3)
        msg(s1, y1, 'Yes I can see it. The font is nice and big now. Much easier for my old eyes!',                               hours_ago=3)
        msg(y1, s1, 'Great! Let me know if you ever need help with any part of the app.',                                         hours_ago=2)
        msg(y1, s1, 'See you at Tai Chi tomorrow morning! I am looking forward to it.',                                           hours_ago=1)
        msg(s1, y1, 'See you there! Sleep early tonight. Hehe.',                                                                  hours_ago=1)

        # ── Sarah (y2) ↔ Uncle Rajan (s2) — mix of EN/TA
        msg(y2, s2, 'Good evening Uncle Rajan! How was your day?',                                                               days_ago=5)
        msg(s2, y2, 'Vanakkam Sarah! Very good. I was listening to old recordings of M.S. Subbulakshmi.',                       days_ago=5, lang='ta', translated='Hello Sarah! Very good. I was listening to old recordings of M.S. Subbulakshmi.')
        msg(y2, s2, 'Oh I love her voice! I am studying Carnatic music a little for one of my modules.',                         days_ago=4)
        msg(s2, y2, 'Really! Then we must practice together. Come, I will teach you some basic swaras.',                         days_ago=4)
        msg(y2, s2, 'That would be incredible! Are you going to the Language Exchange Lunch next week?',                          days_ago=3)
        msg(s2, y2, 'Yes, I signed up! I will teach everyone a few Tamil words. Very fun.',                                       days_ago=3)
        msg(y2, s2, 'I am going too! I also signed up for the Storytelling Session to document your stories.',                    days_ago=2)
        msg(s2, y2, 'Wonderful. I have many stories. We will need more than one session!',                                        days_ago=2)
        msg(y2, s2, 'I cannot wait to hear them. See you there, Uncle Rajan!',                                                   days_ago=1)
        msg(s2, y2, 'Nandri Sarah. Goodnight!', days_ago=1, lang='ta', translated='Thank you Sarah. Goodnight!')

        # ── David (y3) ↔ Auntie Siti (s3) — EN/MS mix, 1 flagged msg for moderation demo
        msg(y3, s3, 'Selamat pagi Auntie Siti! I made nasi goreng for breakfast today and thought of you.',                      days_ago=4, lang='ms', translated='Good morning Auntie Siti! I made fried rice for breakfast today and thought of you.')
        msg(s3, y3, 'Wah so good! Did you use the leftover rice? That is the secret!',                                           days_ago=4)
        msg(y3, s3, 'Yes! And I added sambal belacan. My whole room smelled amazing haha.',                                       days_ago=3)
        msg(s3, y3, 'Next time add a little gula melaka too. Makes the sweetness more complex.',                                  days_ago=3)
        msg(y3, s3, 'Noted! Auntie Siti, can I come learn from you in person one day?',                                          days_ago=2)
        msg(s3, y3, 'Of course, come after the Heritage Cooking Class! We can make kueh too.',                                   days_ago=2)
        # A flagged message for the admin moderation demo
        msg(y3, s3, 'You are such a useless cook!!! Lol jk jk, just testing the safety filter here.',
            flagged=True, days_ago=1)
        msg(s3, y3, 'Aiyah David you scared me! Hahaha. You are a funny one.',                                                   days_ago=1)

        # ── Emily (y4) ↔ Mr Lim (s4) — EN
        msg(y4, s4, 'Hi Mr Lim! I read your story about the library chess stranger. It is incredible.',                           days_ago=6)
        msg(s4, y4, 'Thank you Emily! That one moment changed the course of my entire life.',                                    days_ago=6)
        msg(y4, s4, 'I would love to interview you for my heritage documentation project at SMU.',                               days_ago=5)
        msg(s4, y4, 'Of course. I have many things to share. Shall we meet at the Storytelling Session?',                       days_ago=5)
        msg(y4, s4, 'Perfect! I will bring my recording equipment.',                                                             days_ago=4)
        msg(s4, y4, 'Very good. Do you play chess at all?',                                                                      days_ago=4)

        # ── Marcus (y5) ↔ Mrs Wong (s5)
        msg(y5, s5, 'Hi Mrs Wong! I heard you used to sing to patients. That is so special.',                                   days_ago=5)
        msg(s5, y5, 'Hello Marcus! Yes, sometimes the voice is the best medicine.',                                             days_ago=5)
        msg(y5, s5, 'I love chess but I am not so good at the softer things. Can you teach me?',                                days_ago=3)
        msg(s5, y5, 'Of course! Kindness is like chess — you learn by doing, not just reading.',                                days_ago=3)

        # ── Priya (y6) ↔ Uncle Ali (s6)
        msg(y6, s6, 'Selamat petang Pak Ali! I signed up for the Language Exchange event.',                                      days_ago=10, lang='ms', translated='Good afternoon Uncle Ali! I signed up for the Language Exchange event.')
        msg(s6, y6, 'Bagus! I will teach you some real Malay — not textbook Malay!',                                            days_ago=10)
        msg(y6, s6, 'Haha I love that! I want to learn the fishing words especially.',                                           days_ago=9)
        msg(s6, y6, 'Good choice. The sea has the best vocabulary.',                                                             days_ago=9)

        db.session.commit()
        print(f"  {Message.query.count()} messages seeded.")

        # ── 9. COMMUNITY MEMBERS + POSTS ──────────────────────────────────────
        print("Seeding community members and posts…")

        # Memberships — seniors
        for comm, user_obj in [
            (c_arts, s1), (c_cook, s1), (c_circle, s1),
            (c_music, s2), (c_circle, s2), (c_active, s2),
            (c_cook, s3), (c_garden, s3), (c_circle, s3),
            (c_garden, s4), (c_arts, s4), (c_active, s4),
            (c_music, s5), (c_cook, s5), (c_active, s5),
            (c_garden, s6), (c_music, s6),
        ]:
            db.session.add(CommunityMember(community_id=comm.id, user_id=user_obj.id))

        # Memberships — youth (Ryan joins 3 → Community Builder 3/5)
        for comm, user_obj in [
            (c_story, y1), (c_tech, y1), (c_games, y1),          # Ryan: 3 communities
            (c_story, y2), (c_lang, y2), (c_well, y2), (c_crafts, y2),
            (c_cook, y3), (c_story, y3), (c_garden, y3), (c_lang, y3),
            (c_story, y4), (c_arts, y4), (c_lang, y4), (c_crafts, y4),
            (c_games, y5), (c_tech, y5), (c_story, y5),
            (c_lang, y6), (c_well, y6), (c_story, y6),
        ]:
            db.session.add(CommunityMember(community_id=comm.id, user_id=user_obj.id))

        db.session.commit()

        # Community posts
        post_defs = [
            (c_circle, s1, 'Has anyone else been asked to record their life story? I used the voice recording feature and it brought back so many emotions!', None),
            (c_circle, y4, 'Madam Tan your story about the kampong is so beautifully written! We should document more of these for future generations.', None),
            (c_circle, s2, 'I agree with Emily. Our stories are Singapore\'s living history. We must not let them be forgotten.', None),
            (c_story, y1, 'Hello everyone! I am Ryan, here to help document senior stories. If any senior would like to share a story, please message me!', None),
            (c_story, y4, 'Excited to be part of this community! I am working on a heritage documentation project at SMU and would love collaborators.', None),
            (c_story, y2, 'I just listened to Uncle Rajan\'s story about independence. It made me emotional. History class cannot compare to the real thing.', None),
            (c_tech, y1, 'Tip for seniors: if your screen text is too small, go to Profile → Accessibility Settings and increase the font size!', None),
            (c_tech, y5, 'Does anyone\'s senior buddy need help setting up video calls? I can walk through it step by step in the chat.', None),
            (c_tech, s4, 'I managed to set up the video call by myself today! Thank you to the Tech Helpers here for the guide last week.', None),
            (c_cook, s1, 'I made babi pongteh yesterday using my grandmother\'s recipe. The secret is the tauchu — do not rinse it!', None),
            (c_cook, s3, 'Wah Madam Tan you are making me hungry! I will bring my kueh lapis recipe to the Heritage Cooking Class.', None),
            (c_cook, y3, 'Auntie Siti, I tried your sambal recipe! A bit spicy for me but I loved it. Practice makes perfect!', None),
            (c_music, s2, 'If anyone wants to hear a short recording of Carnatic music, I uploaded one to share during our next session.', None),
            (c_games, y5, 'Anyone up for a chess challenge? Mr Lim has agreed to teach me openings. Others welcome to join!', None),
        ]

        posts = []
        for comm, user_obj, content, photo in post_defs:
            p = CommunityPost(community_id=comm.id, user_id=user_obj.id, content=content,
                              photo_url=photo, created_at=now - timedelta(days=3))
            db.session.add(p)
            posts.append(p)

        db.session.commit()

        # A threaded reply to the first circle post
        db.session.add(CommunityPost(
            community_id=c_circle.id, user_id=s2.id,
            content='I recorded mine too! It was strange hearing my own voice tell stories I had not thought about in years.',
            reply_to_id=posts[0].id, created_at=now - timedelta(days=2),
        ))
        db.session.commit()
        print(f"  Community members and posts seeded.")

        # ── 10. GAME HISTORY + ACTIVE SESSIONS ───────────────────────────────
        print("Seeding game history and sessions…")

        def gh(game, p1, p2, winner, p1_elo_b, p1_elo_a, p2_elo_b, p2_elo_a, days_ago):
            db.session.add(GameHistory(
                game_id=game.id, player1_id=p1.id, player2_id=p2.id,
                winner_id=winner.id if winner else None,
                player1_elo_before=p1_elo_b, player1_elo_after=p1_elo_a,
                player2_elo_before=p2_elo_b, player2_elo_after=p2_elo_a,
                completed_at=now - timedelta(days=days_ago),
            ))

        gh(g_chess, s4, y1,   s4,  1355, 1380, 1225, 1200,  2)
        gh(g_chess, s1, y2,   y2,  1275, 1250, 1255, 1280,  4)
        gh(g_chess, s4, y4,   s4,  1330, 1355, 1245, 1220,  6)
        gh(g_chess, y2, y5,   y2,  1230, 1255, 1205, 1180, 10)
        gh(g_chess, s1, y1,   y1,  1250, 1225, 1175, 1200, 14)
        gh(g_xq,    s2, y2,   y2,  1175, 1150, 1255, 1280,  3)
        gh(g_xq,    s4, s1,   s4,  1330, 1355, 1275, 1250,  8)
        gh(g_xq,    y3, y5,   y3,  1175, 1200, 1205, 1180, 12)
        gh(g_ttt,   y1, s1,   y1,  1200, 1210, 1250, 1240,  1)
        gh(g_ttt,   y5, s5,   s5,  1180, 1170, 1200, 1210,  5)

        db.session.commit()

        # One active waiting chess session (Ryan vs Madam Tan)
        db.session.add(GameSession(
            game_id=g_chess.id, player1_id=s1.id, player2_id=y1.id,
            current_turn_id=s1.id, status='waiting',
            player1_ready=False, player2_ready=False,
        ))
        # One waiting tictactoe session (Marcus vs Mrs Wong)
        db.session.add(TicTacToeSession(
            player1_id=y5.id, player2_id=s5.id,
            current_turn_id=y5.id, status='waiting',
        ))
        db.session.commit()
        print("  Game history and sessions seeded.")

        # ── 11. BADGES ────────────────────────────────────────────────────────
        print("Seeding badges…")

        badge_rows = [
            # Ryan (y1) — 5 badges backed by activity data above
            (y1, 'First Steps'),        # 3 events ✓
            (y1, 'Story Keeper'),       # 5 comments ✓
            (y1, 'Event Organizer'),    # 3 events ✓
            (y1, 'Heritage Champion'),  # 5 reactions ✓
            (y1, 'Conversation Partner'),# 22 messages sent ✓
            # Sarah (y2) — 6 badges
            (y2, 'First Steps'), (y2, 'Story Keeper'), (y2, 'Tech Wizard'),
            (y2, 'Community Builder'), (y2, 'Event Organizer'), (y2, 'Heritage Champion'),
            # David (y3) — 4 badges
            (y3, 'First Steps'), (y3, 'Story Keeper'), (y3, 'Game Master'), (y3, 'Event Organizer'),
            # Emily (y4) — 3 badges
            (y4, 'First Steps'), (y4, 'Heritage Champion'), (y4, 'Community Builder'),
            # Marcus (y5) — 2 badges
            (y5, 'First Steps'), (y5, 'Event Organizer'),
            # Priya (y6) — 1 badge
            (y6, 'First Steps'),
            # Streak badges
            (s1, 'Week Warrior'),
            (y2, 'Week Warrior'), (y2, 'Month Master'),
            (y3, 'Week Warrior'),
            (y4, 'Week Warrior'),
            (s4, 'Week Warrior'), (s4, 'Month Master'),
        ]
        for user_obj, btype in badge_rows:
            db.session.add(Badge(user_id=user_obj.id, badge_type=btype))

        db.session.commit()
        print(f"  {Badge.query.count()} badges seeded.")

        # ── 12. CHECK-INS (seniors) ────────────────────────────────────────────
        print("Seeding check-ins…")

        checkin_data = [
            (s1, [('Great', 'Feeling wonderful today! Ryan helped me set up my profile picture.', 0),
                  ('Good',  'A bit tired but overall happy. Cooking class tomorrow!',              7),
                  ('Great', 'Had a lovely morning at Tai Chi in the park.',                       14),
                  ('Good',  'Garden is blooming nicely. Very peaceful.',                          21),
                  ('Okay',  'Knee is a little achy but spirits are good.',                        28),
                  ('Great', 'First week with my buddy Ryan. So sweet, that boy.',                  35)]),
            (s2, [('Good',  'Practiced some Carnatic scales. Felt the music in my bones.',        2),
                  ('Okay',  'Quiet week. Missing old friends.',                                    9),
                  ('Good',  'Sarah asked about Tamil music today. Made me very happy.',            16),
                  ('Not Good', 'Health not great this week. Doctor visit tomorrow.',               23)]),
            (s3, [('Great', 'Cooked nasi lemak for the grandchildren. House smelled amazing.',    1),
                  ('Great', 'David tried my sambal recipe. So funny to see him sweat!',           8),
                  ('Good',  'Sewing circle was lovely today.',                                    15),
                  ('Good',  'Garden has new seedlings. Happy heart.',                             22),
                  ('Great', 'Community cooking class was wonderful!',                             29)]),
            (s4, [('Good',  'Chess game with Emily today. She is learning fast.',                 3),
                  ('Great', 'Found my old engineering blueprints. Such memories.',                10),
                  ('Good',  'Photography walk was excellent. Got some great shots.',               17)]),
            (s5, [('Okay',  'Miss the hospital sometimes. Old habits.',                           4),
                  ('Good',  'Marcus is learning to be more patient. Good boy.',                   11),
                  ('Good',  'Knitting a new scarf. Very calming.',                                18),
                  ('Great', 'Song session with the community today. Wonderful.',                   25)]),
            (s6, [('Good',  'Went fishing at Bedok Jetty early morning. Very peaceful.',           5),
                  ('Not Good', 'Rain all week. Cannot go outside much.',                          12)]),
        ]

        for user_obj, checkins in checkin_data:
            for mood, notes, days_ago in checkins:
                db.session.add(Checkin(
                    user_id=user_obj.id, mood=mood, notes=notes,
                    created_at=now - timedelta(days=days_ago),
                ))

        db.session.commit()
        print(f"  {Checkin.query.count()} check-ins seeded.")

        # ── 13. CHAT REPORTS ──────────────────────────────────────────────────
        print("Seeding chat reports…")

        # Find the flagged message (David's joke message)
        flagged_msg = Message.query.filter_by(is_flagged=True).first()
        # A community post to report
        tech_post = CommunityPost.query.filter_by(community_id=c_tech.id).first()
        # A story to report
        story_to_report = stories['s2b']

        db.session.add_all([
            # 1. Pending message report
            ChatReport(
                message_id=flagged_msg.id if flagged_msg else None,
                reported_by=s3.id, reported_user_id=y3.id,
                reason='Inappropriate',
                description='This message was very rude even if meant as a joke.',
                status='pending',
            ),
            # 2. Under-review community post report
            ChatReport(
                community_post_id=tech_post.id if tech_post else None,
                reported_by=s4.id, reported_user_id=y1.id,
                reason='Spam',
                description='This post appears to be promotional content unrelated to the community.',
                status='under_review',
                admin_notes='Looking into this report. Initial review shows it may be legitimate.',
                ai_analysis='Severity: Low. Content is community-relevant but could be seen as self-promotional.',
            ),
            # 3. Resolved story report
            ChatReport(
                story_id=story_to_report.id,
                reported_by=y3.id, reported_user_id=s2.id,
                reason='Misinformation',
                description='Some historical dates in the story may be inaccurate.',
                status='resolved',
                admin_notes='Reviewed with the author. Content is a personal recollection, not a factual claim. No action needed.',
                ai_analysis='Severity: Low. Personal narrative, not presented as historical fact.',
            ),
            # 4. Dismissed report
            ChatReport(
                reported_by=y5.id, reported_user_id=s5.id,
                reason='Harassment',
                description='Test report — accidental submission.',
                status='dismissed',
                admin_notes='User confirmed this was submitted in error.',
            ),
        ])
        db.session.commit()
        print(f"  {ChatReport.query.count()} chat reports seeded.")

        # ── 14. SUPPORT TICKETS ────────────────────────────────────────────────
        print("Seeding support tickets…")
        db.session.add_all([
            SupportTicket(
                user_id=y1.id, ticket_type='Bug Report',
                subject='Photo upload fails on mobile occasionally',
                description='When I try to upload a profile photo from my phone browser, it sometimes fails with no error message. Happens about 1 in 3 times on iOS Safari.',
                status='open',
            ),
            SupportTicket(
                user_id=y2.id, ticket_type='Feature Request',
                subject='Add language selection for voice messages',
                description='It would be great if we could select the language of a voice message before sending so the translation is more accurate.',
                status='in_progress',
                admin_notes='Great suggestion! This is on our roadmap for the next release. We will update you when it is ready.',
            ),
            SupportTicket(
                guest_email='john.doe@email.com', ticket_type='Account Issue',
                subject='Cannot log in after registration',
                description='I registered with the code GENCON01 but when I try to log in it says my account is not found. Please help.',
                status='submitted',
            ),
            SupportTicket(
                user_id=s1.id, ticket_type='General Inquiry',
                subject='How do I change my profile picture?',
                description='I cannot find where to upload a new photo for my profile. The current one is very old.',
                status='closed',
                admin_notes='Hi Madam Tan! Go to My Profile (top right menu) and click the camera icon on your photo. You can upload a new picture there. Let us know if you need more help!',
            ),
            SupportTicket(
                user_id=s2.id, ticket_type='Bug Report',
                subject='Notifications bell shows wrong count',
                description='The bell icon shows 3 notifications but when I click it there is only 1 new message.',
                status='open',
            ),
        ])
        db.session.commit()
        print(f"  {SupportTicket.query.count()} support tickets seeded.")

        # ── 15. NOTIFICATIONS ─────────────────────────────────────────────────
        print("Seeding notifications…")
        db.session.add_all([
            Notification(user_id=y1.id, title='Event Reminder',
                         message='Morning Tai Chi with Seniors is tomorrow at Bishan Park Pavilion!',
                         type='event', link='/youth/events', is_read=False,
                         created_at=now - timedelta(hours=2)),
            Notification(user_id=y1.id, title='Game Challenge',
                         message='Madam Tan has challenged you to a game of Chess!',
                         type='game', link='/youth/games', is_read=False,
                         created_at=now - timedelta(hours=5)),
            Notification(user_id=y1.id, title='New Message',
                         message='You have a new message from Madam Tan.',
                         type='message', link='/youth/messages', is_read=True,
                         created_at=now - timedelta(days=1)),
            Notification(user_id=s1.id, title='Event Reminder',
                         message='Morning Tai Chi with Seniors is tomorrow! See you at Bishan Park.',
                         type='event', link='/senior/events', is_read=False,
                         created_at=now - timedelta(hours=2)),
            Notification(user_id=s1.id, title='New Message',
                         message='Ryan Lee sent you a message.',
                         type='message', link='/senior/messages', is_read=True,
                         created_at=now - timedelta(hours=6)),
            Notification(user_id=y2.id, title='Event Reminder',
                         message='Language Exchange Lunch is in 5 days. Are you ready?',
                         type='event', link='/youth/events', is_read=False,
                         created_at=now - timedelta(hours=3)),
            Notification(user_id=s2.id, title='Welcome to GenCon SG!',
                         message='Your profile is set up. Start by exploring the Stories section.',
                         type='info', link='/senior/stories', is_read=True,
                         created_at=now - timedelta(days=30)),
        ])
        db.session.commit()
        print(f"  {Notification.query.count()} notifications seeded.")

        # ── 16. REGISTRATION CODES ────────────────────────────────────────────
        print("Seeding registration codes…")
        code_rows = [
            ('YOUTH2025',  False, None),
            ('YOUTH2024',  True,  y2.id),
            ('SENIOR2025', False, None),
            ('SENIOR2024', True,  s2.id),
            ('GENCON01',   False, None),
            ('GENCON02',   False, None),
            ('GENCON03',   False, None),
            ('ADMIN001',   False, None),
        ]
        for code, used, used_by in code_rows:
            db.session.add(RegistrationCode(code=code, is_used=used, used_by_id=used_by))

        db.session.commit()
        print(f"  {RegistrationCode.query.count()} registration codes seeded.")

        print("\n✓ Database seeded successfully!")
        print("─" * 45)
        print("  Admin   : admin / password123")
        print("  Seniors : madam_tan, uncle_rajan, auntie_siti, mr_lim, mrs_wong, uncle_ali")
        print("  Youth   : ryan_lee, sarah_chen, david_tan, emily_wong, marcus_lim, priya_k")
        print("  (all passwords: password123)")
        print("─" * 45)


if __name__ == '__main__':
    seed_data()
