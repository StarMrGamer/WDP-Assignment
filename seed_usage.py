"""
Seed realistic user usage data for existing users.
Run AFTER seed_db.py: python seed_usage.py
"""
from app import app
from models import (
    db, User, Story, StoryReaction, StoryComment, Message,
    Pair, Event, EventParticipant, Community, CommunityMember,
    CommunityPost, Checkin, Badge, Streak, SupportTicket,
    Notification, ChatReport, GameHistory, Game
)
from datetime import datetime, timedelta
import random
import json

def seed_usage():
    with app.app_context():
        # Get existing users
        seniors = User.query.filter_by(role='senior').all()
        youths = User.query.filter_by(role='youth').all()
        admin = User.query.filter_by(role='admin').first()

        if not seniors or not youths or not admin:
            print("ERROR: Run seed_db.py first to create base users.")
            return

        print(f"Found {len(seniors)} seniors, {len(youths)} youth, 1 admin")

        # ============================================================
        # 1. CREATE ADDITIONAL SENIORS for more realistic data
        # ============================================================
        print("Creating additional seniors...")
        extra_seniors_data = [
            ('ah_kow', 'Mr Lim Ah Kow', 75, '["Gardening", "Cooking"]', '["English", "Chinese", "Hokkien"]',
             'Retired hawker stall owner. Love sharing recipes with young people.'),
            ('mary_wong', 'Mary Wong', 68, '["Music", "Stories"]', '["English", "Cantonese"]',
             'Former school teacher. Passionate about preserving our heritage stories.'),
            ('ahmad_bin', 'Ahmad Bin Ismail', 71, '["Gardening", "Walking"]', '["English", "Malay"]',
             'Enjoy morning walks at East Coast Park and tending my balcony garden.'),
            ('sita_devi', 'Sita Devi', 69, '["Cooking", "Music"]', '["English", "Tamil"]',
             'Love teaching traditional Indian cooking to the younger generation.'),
            ('uncle_chen', 'Chen Wei Ming', 77, '["Chess", "Stories"]', '["English", "Chinese", "Teochew"]',
             'Retired engineer. Still sharp at chess! Come challenge me.'),
        ]

        new_seniors = []
        for uname, name, age, interests, langs, bio in extra_seniors_data:
            if not User.query.filter_by(username=uname).first():
                u = User(
                    username=uname, email=f'{uname}@gencon.sg',
                    full_name=name, age=age, role='senior',
                    interests_json=interests, languages_json=langs, bio=bio,
                    created_at=datetime.utcnow() - timedelta(days=random.randint(30, 90)),
                    last_active=datetime.utcnow() - timedelta(hours=random.randint(1, 48))
                )
                u.set_password('password123')
                db.session.add(u)
                new_seniors.append(u)
        db.session.flush()

        # Refresh lists
        seniors = User.query.filter_by(role='senior').all()
        youths = User.query.filter_by(role='youth').all()

        # ============================================================
        # 2. CREATE BUDDY PAIRS
        # ============================================================
        print("Creating buddy pairs...")
        existing_pairs = {(p.senior_id, p.youth_id) for p in Pair.query.all()}
        pair_combos = [
            (seniors[i % len(seniors)].id, youths[i % len(youths)].id)
            for i in range(min(len(seniors), len(youths)))
        ]
        for sid, yid in pair_combos:
            if (sid, yid) not in existing_pairs:
                p = Pair(
                    senior_id=sid, youth_id=yid,
                    program=random.choice([
                        'Intergenerational Tech Bridge',
                        'Heritage Stories Project',
                        'Active Ageing Together'
                    ]),
                    status='active',
                    paired_date=datetime.utcnow() - timedelta(days=random.randint(14, 60)),
                    last_interaction=datetime.utcnow() - timedelta(hours=random.randint(1, 72))
                )
                db.session.add(p)
        db.session.flush()

        # ============================================================
        # 3. STORIES (seniors share life stories)
        # ============================================================
        print("Creating stories...")
        stories_data = [
            ("My First Day as a Hawker", "Childhood",
             "I still remember that morning in 1975 when I opened my first nasi lemak stall at Old Airport Road. My hands were shaking as I fried the ikan bilis. The sambal recipe was my mother's - she taught me when I was just 12 years old. That first day, I sold out by 10am! The auntie next door selling kopi told me 'Wah boy, your nasi lemak very power leh!' That gave me the confidence to keep going for 40 years."),
            ("Walking to School in the Kampong", "Childhood",
             "In the 1960s, I used to walk 3 kilometers to school barefoot through the kampong. We would pass by rubber plantations and sometimes see monkeys. My friend Ah Huat and I would always stop at the provision shop to look at the sweets we couldn't afford. The shopkeeper uncle sometimes gave us one sweet each if we helped sweep his shop floor. Those were simple but happy times."),
            ("Learning Teochew Opera from My Grandmother", "Family",
             "My grandmother was a Teochew opera performer in her youth. Every evening after dinner, she would teach me the basic moves and songs in our small flat in Chinatown. The neighbours would open their windows to listen. Sometimes they would clap! I never became a performer, but those evenings with my grandmother taught me about our culture and the importance of preserving traditions."),
            ("National Service in 1970", "Work Life",
             "When I was called up for National Service in 1970, I was both scared and excited. Basic Military Training at Pulau Tekong was tough - the mosquitoes were terrible! But I made lifelong friends. My section mate Kumar and I still meet for kopi every Saturday morning at our favourite kopitiam in Toa Payoh. 55 years of friendship!"),
            ("My Garden on the 12th Floor", "Hobbies",
             "When we moved from our kampong to an HDB flat in Ang Mo Kio in 1978, I thought I could never garden again. But I started growing chilli padi, kangkong, and pandan in pots on my corridor. Now my balcony garden has over 50 plants! My neighbours always come to take my curry leaves and pandan. Gardening keeps me happy and healthy at 71."),
            ("The Day Singapore Became Independent", "Other",
             "I was 8 years old on 9 August 1965. I didn't really understand what was happening, but I remember my father listening to the radio very seriously. My mother was worried. Later that day, the whole kampong gathered and there was a mix of worry and hope. Looking back, I'm so proud of how far our little island has come."),
            ("Teaching My Granddaughter to Make Kueh", "Family",
             "Last Chinese New Year, I taught my granddaughter Sophie how to make kueh lapis. She was so impatient waiting for each layer to cook! But when she finally tasted the finished product, her eyes lit up and she said 'Ah Ma, this is better than any cake!' That moment made all the effort worthwhile. I hope she carries on this tradition."),
            ("My Favourite Kopitiam", "Hobbies",
             "For 30 years, I have been going to the same kopitiam at Block 85 Bedok North. The kopi uncle knows my order - kopi gao siu dai. The table in the corner near the fan is 'my' table. I've read thousands of newspapers there, watched Singapore change through the kopitiam window. The kopi uncle is 78 now but still makes the best kopi in the East."),
            ("Learning to Use a Smartphone", "Other",
             "My grandson Ryan showed me how to use WhatsApp last year. At first I was very confused and accidentally sent a voice message to the wrong person! But now I video call my sister in Malaysia every week. Technology is amazing - I can see her face even though she is so far away. I still prefer talking face to face, but video call is the next best thing."),
            ("The Old Satay Club at Elizabeth Walk", "Childhood",
             "Before the Esplanade was built, there was the Satay Club near the waterfront. Every Friday night, my father would take us there. The smell of satay being grilled, the sea breeze, the sound of laughter - it was magical. I can still taste those chicken satay sticks with the peanut sauce. 10 cents per stick! Those were the days."),
        ]

        created_stories = []
        for title, category, content in stories_data:
            senior = random.choice(seniors)
            days_ago = random.randint(1, 45)
            story = Story(
                user_id=senior.id,
                title=title,
                content=content,
                category=category,
                created_at=datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(0, 12))
            )
            db.session.add(story)
            created_stories.append(story)
        db.session.flush()

        # ============================================================
        # 4. STORY REACTIONS & COMMENTS
        # ============================================================
        print("Adding reactions and comments...")
        reaction_types = ['heart', 'smile', 'clap', 'hug']
        comment_texts = [
            "Thank you for sharing this beautiful story! It really touched my heart.",
            "Wah, this brings back so many memories! My grandfather told similar stories.",
            "This is so precious. We need to preserve these stories for future generations.",
            "I love hearing about old Singapore! So different from today.",
            "Your story is so vivid, I can almost taste the food!",
            "This is amazing, uncle/auntie! Please share more stories like this.",
            "I wish I could have experienced kampong life. Sounds wonderful!",
            "Reading this made my day. Thank you for preserving our heritage.",
            "My grandmother used to say similar things. This makes me miss her.",
            "So inspiring! Singapore has come so far because of your generation.",
            "I learned something new about Singapore today. Thank you!",
            "This should be in a book! What a wonderful life you've lived.",
        ]

        all_users = seniors + youths
        for story in created_stories:
            # 3-8 reactions per story
            reactors = random.sample(all_users, min(random.randint(3, 8), len(all_users)))
            for user in reactors:
                if user.id == story.user_id:
                    continue
                reaction = StoryReaction(
                    story_id=story.id,
                    user_id=user.id,
                    reaction_type=random.choice(reaction_types),
                    created_at=story.created_at + timedelta(hours=random.randint(1, 72))
                )
                db.session.add(reaction)

            # 1-4 comments per story
            commenters = random.sample(all_users, min(random.randint(1, 4), len(all_users)))
            for user in commenters:
                if user.id == story.user_id:
                    continue
                comment = StoryComment(
                    story_id=story.id,
                    user_id=user.id,
                    content=random.choice(comment_texts),
                    created_at=story.created_at + timedelta(hours=random.randint(2, 96))
                )
                db.session.add(comment)
        db.session.flush()

        # ============================================================
        # 5. MESSAGES between buddy pairs
        # ============================================================
        print("Creating messages...")
        pairs = Pair.query.filter_by(status='active').all()

        conversation_templates = [
            # Casual check-ins
            [
                ("Good morning! How are you today?", "en"),
                ("Good morning! I'm doing well, thank you. Had my morning walk already!", "en"),
                ("That's great! Where do you usually walk?", "en"),
                ("Around Bishan Park. The weather was nice this morning. You should join me sometime!", "en"),
                ("I would love that! Maybe this weekend?", "en"),
                ("Sure! Saturday 7am? We can have breakfast after at the hawker centre nearby.", "en"),
            ],
            # Tech help
            [
                ("Auntie, did you manage to download the app I showed you?", "en"),
                ("Yes! But I cannot find it on my phone now. Where did it go?", "en"),
                ("Try swiping left on your home screen. It might be on the next page.", "en"),
                ("Oh! Found it! Thank you ah. You young people so clever with phones.", "en"),
                ("Haha no lah auntie, you're learning fast! Next time I'll show you how to video call.", "en"),
                ("Okay okay, looking forward to it!", "en"),
            ],
            # Recipe sharing
            [
                ("Uncle, can you teach me how to make your famous curry?", "en"),
                ("Haha! Of course. First you need to get fresh spices from Tekka Market.", "en"),
                ("What spices do I need?", "en"),
                ("Cumin, coriander, turmeric, chilli powder, and most importantly - fresh curry leaves!", "en"),
                ("Got it! I'll go to Tekka this weekend.", "en"),
                ("Good! Tell the Indian auntie at stall 23 I sent you. She gives the best quality.", "en"),
                ("Thank you uncle! I'll report back after I try cooking it.", "en"),
                ("Remember - low heat and patience. Don't rush the curry!", "en"),
            ],
            # Story discussion
            [
                ("I read your story about the kampong days. It was so interesting!", "en"),
                ("Thank you for reading it! Those were really different times.", "en"),
                ("Did you really walk barefoot to school?", "en"),
                ("Yes lah! No choice, shoes were expensive. But our feet were tough from running around the kampong all day!", "en"),
                ("Wow, kids today would never believe it. Can I record you telling more stories?", "en"),
                ("Sure, I have many more stories to share. Come visit me this Saturday.", "en"),
            ],
            # Game chat
            [
                ("Uncle, rematch? I want to beat you at chess this time!", "en"),
                ("Haha! You think you can beat this old man? Come lah!", "en"),
                ("I've been practicing online. Prepared my strategy already.", "en"),
                ("Good good. A chess player must always learn. But experience counts for a lot too!", "en"),
                ("Let's play tonight after dinner?", "en"),
                ("Okay. 8pm. Prepare to lose!", "en"),
            ],
            # Multilingual conversation
            [
                ("Ah Ma, 你好吗？", "zh"),
                ("我很好！今天去了公园散步。", "zh"),
                ("That's good! You're staying active.", "en"),
                ("是啊，每天都要运动。你呢？学校忙吗？", "zh"),
                ("A bit busy with exams, but I'll come visit you after!", "en"),
                ("好的好的，我做你最爱吃的鸡饭等你！", "zh"),
            ],
        ]

        for pair in pairs:
            # Each pair gets 1-3 conversations
            num_convos = random.randint(1, 3)
            chosen_convos = random.sample(
                conversation_templates,
                min(num_convos, len(conversation_templates))
            )
            for convo in chosen_convos:
                base_time = datetime.utcnow() - timedelta(days=random.randint(1, 30))
                for i, (text, lang) in enumerate(convo):
                    # Alternate sender
                    if i % 2 == 0:
                        sender_id, recipient_id = pair.youth_id, pair.senior_id
                    else:
                        sender_id, recipient_id = pair.senior_id, pair.youth_id

                    msg = Message(
                        sender_id=sender_id,
                        recipient_id=recipient_id,
                        content=text,
                        original_language=lang,
                        created_at=base_time + timedelta(minutes=i * random.randint(2, 15))
                    )
                    db.session.add(msg)
        db.session.flush()

        # ============================================================
        # 6. COMMUNITY MEMBERSHIPS & POSTS
        # ============================================================
        print("Populating communities...")
        communities = Community.query.all()

        community_posts_data = {
            'Heritage Cooking': [
                "Just made my grandmother's recipe for ondeh ondeh! The pandan was so fragrant. Anyone else make traditional kueh?",
                "Sharing my secret chicken rice chilli sauce recipe - the key is to use fresh chilli padi and a tiny bit of lime juice!",
                "Had the best laksa at Katong today. Reminded me of my late mother's cooking. Nothing beats homemade!",
                "Does anyone know how to make proper nonya kueh dadar? The ones I buy outside are never as good as homemade.",
                "Teaching my neighbour how to make proper sambal. She was amazed at the difference fresh ingredients make!",
            ],
            'Traditional Arts': [
                "Started a Chinese calligraphy class at the CC. It's so relaxing! Any seniors interested in joining?",
                "Look at this beautiful batik piece I completed today! Took me 3 weeks but so worth it.",
                "The heritage art exhibition at the National Museum is wonderful. Highly recommend visiting!",
            ],
            'Story Sharing Circle': [
                "Today I shared my story about growing up in a kampong in Potong Pasir. The young volunteers were so interested!",
                "Just recorded my first voice story on the app. A bit shy but my buddy encouraged me. It's about my first job as a postman.",
                "Reading everyone's stories here makes me so happy. We have such rich histories to share!",
                "My grandson helped me type out my story about the old Toa Payoh swimming pool. Good memories!",
            ],
            'Tech Helpers': [
                "Pro tip: When teaching seniors to use phones, be patient and repeat instructions. They really appreciate it!",
                "Created a simple guide for video calling. Happy to share with other volunteers!",
                "Today I helped 3 seniors set up their email. Their excitement was so wholesome!",
                "Does anyone have tips for teaching seniors about online safety? Want to make sure they don't fall for scams.",
            ],
            'Story Collectors': [
                "Recorded an amazing story from Ah Ma Tan about Singapore in the 1950s. History comes alive!",
                "Starting a photo archive project - scanning old photos from seniors. Anyone want to help?",
                "The stories I've collected this month are incredible. Planning to compile them into a heritage book!",
            ],
            'Game Facilitators': [
                "Organised a chess tournament at the senior centre today. The uncles were SO competitive haha!",
                "Looking for more youth to help facilitate game sessions on weekends. Very rewarding experience!",
                "Uncle Chen beat all the youth volunteers at Chinese Chess today. Legend!",
            ],
            'Gardening Enthusiasts': [
                "My chilli padi plants are flowering! Can't wait to harvest them for my sambal.",
                "Anyone know how to deal with mealybugs on my curry leaf plant? They keep coming back!",
                "Started growing kangkong in a pot on my corridor. Surprisingly easy!",
            ],
            'Active Seniors': [
                "Morning walk group starting at Bishan Park every Tuesday and Thursday, 6:30am. All welcome!",
                "Just completed my 100th walk this year! Feeling fitter than ever at 72.",
                "Tai chi session at the void deck was wonderful today. Good exercise for the joints.",
            ],
        }

        for community in communities:
            # Add members
            eligible = seniors if community.name in [c['name'] for c in [
                {'name': 'Traditional Arts'}, {'name': 'Heritage Cooking'},
                {'name': 'Story Sharing Circle'}, {'name': 'Gardening Enthusiasts'},
                {'name': 'Music & Songs'}, {'name': 'Active Seniors'}
            ]] else youths

            members_to_add = random.sample(eligible, min(random.randint(2, len(eligible)), len(eligible)))
            for user in members_to_add:
                existing = CommunityMember.query.filter_by(
                    community_id=community.id, user_id=user.id
                ).first()
                if not existing:
                    cm = CommunityMember(
                        community_id=community.id,
                        user_id=user.id,
                        joined_at=datetime.utcnow() - timedelta(days=random.randint(5, 60))
                    )
                    db.session.add(cm)

            # Add posts
            posts = community_posts_data.get(community.name, [])
            for post_text in posts:
                poster = random.choice(members_to_add)
                cp = CommunityPost(
                    community_id=community.id,
                    user_id=poster.id,
                    content=post_text,
                    created_at=datetime.utcnow() - timedelta(
                        days=random.randint(1, 30),
                        hours=random.randint(0, 12)
                    )
                )
                db.session.add(cp)

            # Update member count
            community.member_count = len(members_to_add)

        db.session.flush()

        # ============================================================
        # 7. EVENT PARTICIPATION
        # ============================================================
        print("Adding event participants...")
        events = Event.query.all()
        for event in events:
            participants = random.sample(all_users, min(random.randint(3, 10), len(all_users)))
            for user in participants:
                existing = EventParticipant.query.filter_by(
                    event_id=event.id, user_id=user.id
                ).first()
                if not existing:
                    ep = EventParticipant(
                        event_id=event.id,
                        user_id=user.id,
                        registered_at=datetime.utcnow() - timedelta(days=random.randint(1, 14))
                    )
                    db.session.add(ep)
        db.session.flush()

        # ============================================================
        # 8. CHECK-INS (senior mood tracking)
        # ============================================================
        print("Creating check-ins...")
        moods = ['Great', 'Good', 'Okay', 'Not Good']
        mood_weights = [0.3, 0.4, 0.2, 0.1]
        checkin_notes = {
            'Great': [
                "Had a wonderful walk at the park this morning!",
                "My buddy came to visit today. So happy!",
                "Cooked a big meal for my family. Feeling blessed.",
                "Won 3 games of chess today!",
                "",
            ],
            'Good': [
                "Normal day. Watched some TV and read the newspaper.",
                "Went to the market and met some old friends.",
                "Had a nice video call with my daughter in Australia.",
                "Attended the community centre exercise class.",
                "",
            ],
            'Okay': [
                "Feeling a bit tired today. Didn't sleep well.",
                "Quiet day. A bit lonely.",
                "Weather too hot to go out. Stayed home.",
                "",
            ],
            'Not Good': [
                "My knees are aching. Hard to walk today.",
                "Miss my late husband a lot today.",
                "Feeling quite lonely. Children are all busy.",
            ],
        }

        for senior in seniors:
            # 4-8 check-ins over the past weeks
            for i in range(random.randint(4, 8)):
                mood = random.choices(moods, weights=mood_weights, k=1)[0]
                note = random.choice(checkin_notes[mood])
                ci = Checkin(
                    user_id=senior.id,
                    mood=mood,
                    notes=note if note else None,
                    created_at=datetime.utcnow() - timedelta(
                        days=i * random.randint(2, 5),
                        hours=random.randint(8, 20)
                    )
                )
                db.session.add(ci)
        db.session.flush()

        # ============================================================
        # 9. STREAKS for new seniors
        # ============================================================
        print("Creating streaks for new users...")
        for user in new_seniors:
            existing = Streak.query.filter_by(user_id=user.id).first()
            if not existing:
                s = Streak(
                    user_id=user.id,
                    current_streak=random.randint(1, 10),
                    longest_streak=random.randint(5, 20),
                    points=random.randint(100, 600),
                    games_played=random.randint(3, 20),
                    games_won=random.randint(1, 12)
                )
                db.session.add(s)
        db.session.flush()

        # ============================================================
        # 10. ADDITIONAL BADGES
        # ============================================================
        print("Awarding badges...")
        badge_types = [
            'First Steps', 'Story Keeper', 'Social Butterfly',
            'Game Enthusiast', 'Week Warrior', 'Heritage Champion',
            'Helping Hand', 'Community Star'
        ]
        for user in all_users:
            num_badges = random.randint(1, 4)
            chosen = random.sample(badge_types, num_badges)
            for bt in chosen:
                existing = Badge.query.filter_by(user_id=user.id, badge_type=bt).first()
                if not existing:
                    b = Badge(
                        user_id=user.id,
                        badge_type=bt,
                        earned_at=datetime.utcnow() - timedelta(days=random.randint(1, 45))
                    )
                    db.session.add(b)
        db.session.flush()

        # ============================================================
        # 11. SUPPORT TICKETS
        # ============================================================
        print("Creating support tickets...")
        tickets_data = [
            ('Bug Report', 'Cannot upload profile picture',
             'When I try to upload a new profile picture, the page just refreshes and nothing changes. I tried with both JPG and PNG files.', 'open'),
            ('General Inquiry', 'How to change language?',
             'I want to change the app language to Chinese for my grandmother. Where is the setting?', 'closed'),
            ('Feature Request', 'Add more games',
             'It would be great to have more traditional games like Congkak or Five Stones! The seniors would love it.', 'submitted'),
            ('Account Issue', 'Forgot my password',
             'My grandmother forgot her password and cannot log in. Can you help reset it?', 'closed'),
        ]

        for ttype, subject, desc, status in tickets_data:
            user = random.choice(all_users)
            t = SupportTicket(
                user_id=user.id,
                ticket_type=ttype,
                subject=subject,
                description=desc,
                status=status,
                admin_notes='Resolved by admin.' if status == 'closed' else None,
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 20))
            )
            db.session.add(t)
        db.session.flush()

        # ============================================================
        # 12. NOTIFICATIONS
        # ============================================================
        print("Creating notifications...")
        notif_templates = [
            ('New Message', 'You have a new message from your buddy!', 'message'),
            ('Event Reminder', 'Traditional Storytelling Session is in 3 days. Don\'t forget!', 'event'),
            ('Badge Earned', 'Congratulations! You earned the Social Butterfly badge!', 'game'),
            ('New Story', 'Your buddy shared a new story. Check it out!', 'message'),
            ('Check-in Reminder', 'How are you feeling today? Take a moment to check in.', 'message'),
        ]

        for user in all_users:
            num_notifs = random.randint(2, 5)
            for _ in range(num_notifs):
                title, message, ntype = random.choice(notif_templates)
                n = Notification(
                    user_id=user.id,
                    title=title,
                    message=message,
                    type=ntype,
                    is_read=random.choice([True, True, False]),
                    created_at=datetime.utcnow() - timedelta(
                        days=random.randint(0, 14),
                        hours=random.randint(0, 23)
                    )
                )
                db.session.add(n)
        db.session.flush()

        # ============================================================
        # 13. GAME HISTORY
        # ============================================================
        print("Creating game history...")
        games = Game.query.all()
        if games:
            for _ in range(15):
                game = random.choice(games)
                players = random.sample(all_users, 2)
                p1, p2 = players[0], players[1]
                winner = random.choice([p1, p2, None])  # None = draw

                p1_elo = p1.elo or 1200
                p2_elo = p2.elo or 1200

                gh = GameHistory(
                    game_id=game.id,
                    player1_id=p1.id,
                    player2_id=p2.id,
                    winner_id=winner.id if winner else None,
                    player1_elo_before=p1_elo,
                    player1_elo_after=p1_elo + random.randint(-30, 30),
                    player2_elo_before=p2_elo,
                    player2_elo_after=p2_elo + random.randint(-30, 30),
                    completed_at=datetime.utcnow() - timedelta(
                        days=random.randint(1, 30),
                        hours=random.randint(0, 12)
                    )
                )
                db.session.add(gh)

        # ============================================================
        # 14. CHAT REPORT (one example of flagged content)
        # ============================================================
        print("Creating sample report...")
        flagged_msg = Message(
            sender_id=youths[0].id,
            recipient_id=seniors[0].id,
            content="This is stupid, I don't want to play anymore",
            original_language='en',
            is_flagged=True,
            created_at=datetime.utcnow() - timedelta(days=5)
        )
        db.session.add(flagged_msg)
        db.session.flush()

        report = ChatReport(
            message_id=flagged_msg.id,
            reported_by=seniors[0].id,
            reported_user_id=youths[0].id,
            reason='Inappropriate Language',
            description='The message contains unkind words.',
            status='pending',
            created_at=datetime.utcnow() - timedelta(days=5)
        )
        db.session.add(report)

        # ============================================================
        # COMMIT ALL
        # ============================================================
        db.session.commit()
        print("\n✅ Usage data seeded successfully!")
        print(f"   Stories: {len(created_stories)}")
        print(f"   Messages: {Message.query.count()}")
        print(f"   Community Posts: {CommunityPost.query.count()}")
        print(f"   Check-ins: {Checkin.query.count()}")
        print(f"   Notifications: {Notification.query.count()}")
        print(f"   Game History: {GameHistory.query.count()}")
        print(f"   Support Tickets: {SupportTicket.query.count()}")


if __name__ == '__main__':
    seed_usage()
