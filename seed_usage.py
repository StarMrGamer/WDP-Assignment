"""
Seed realistic user usage data for existing users.
Run AFTER seed_db.py: python seed_usage.py

Focus: Makes the demo users 'senior' (Madam Tan) and 'youth' (Ryan Lee)
have rich, persona-driven data so every page showcases the app well.
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


def seed_usage():
    with app.app_context():
        # ============================================================
        # Get core demo users
        # ============================================================
        senior = User.query.filter_by(username='senior').first()
        youth = User.query.filter_by(username='youth').first()
        admin = User.query.filter_by(role='admin').first()

        if not senior or not youth or not admin:
            print("ERROR: Run seed_db.py first to create base users.")
            return

        print(f"Found demo users: {senior.full_name} (senior) and {youth.full_name} (youth)")

        # ============================================================
        # 1. ENRICH DEMO USER PROFILES
        # ============================================================
        print("Enriching demo user profiles...")

        senior.bio = (
            "Retired school canteen auntie from Queenstown Secondary School. "
            "Spent 30 years feeding hungry students! Now I enjoy cooking for family, "
            "tending my balcony garden, and sharing stories about old Singapore. "
            "My chicken curry is famous in the whole block lah!"
        )
        senior.languages_json = '["English", "Mandarin", "Hokkien", "Teochew"]'
        senior.interests_json = '["Cooking", "Gardening", "Stories", "Music"]'
        senior.last_active = datetime.utcnow() - timedelta(hours=2)

        youth.bio = (
            "Polytechnic student studying Information Technology at Nanyang Polytechnic. "
            "Joined GenCon SG to give back and learn from our seniors. "
            "I love hearing stories from the old days and helping seniors with tech. "
            "Also a big chess fan — always looking for a good challenge!"
        )
        youth.languages_json = '["English", "Mandarin"]'
        youth.interests_json = '["Tech", "Games", "Chess", "Cooking"]'
        youth.school = 'Nanyang Polytechnic'
        youth.last_active = datetime.utcnow() - timedelta(minutes=30)

        db.session.flush()

        # ============================================================
        # 2. ADDITIONAL USERS for a fuller community / story feed
        # ============================================================
        print("Creating additional users...")

        extra_seniors_data = [
            ('ah_kow', 'Mr Lim Ah Kow', 75, '["Gardening", "Cooking"]', '["English", "Hokkien"]',
             'Retired hawker stall owner. Love sharing recipes with young people.'),
            ('mary_wong', 'Mary Wong', 68, '["Music", "Stories"]', '["English", "Cantonese"]',
             'Former school teacher. Passionate about preserving our heritage stories.'),
            ('ahmad_bin', 'Ahmad Bin Ismail', 71, '["Gardening", "Walking"]', '["English", "Malay"]',
             'Enjoy morning walks at East Coast Park and tending my balcony garden.'),
            ('sita_devi', 'Sita Devi', 69, '["Cooking", "Music"]', '["English", "Tamil"]',
             'Love teaching traditional Indian cooking to the younger generation.'),
            ('uncle_chen', 'Chen Wei Ming', 77, '["Chess", "Stories"]', '["English", "Teochew"]',
             'Retired engineer. Still sharp at chess! Come challenge me.'),
        ]

        new_seniors = []
        for uname, name, age, interests, langs, bio in extra_seniors_data:
            u = User.query.filter_by(username=uname).first()
            if not u:
                u = User(
                    username=uname, email=f'{uname}@gencon.sg',
                    full_name=name, age=age, role='senior',
                    interests_json=interests, languages_json=langs, bio=bio,
                    is_approved=True,
                    created_at=datetime.utcnow() - timedelta(days=random.randint(30, 90)),
                    last_active=datetime.utcnow() - timedelta(hours=random.randint(1, 48))
                )
                u.set_password('password123')
                db.session.add(u)
            new_seniors.append(u)

        extra_youth_data = [
            ('kai_lim', 'Kai Lim', 21, '["Tech", "Music"]', '["English", "Mandarin"]',
             'Engineering student passionate about using tech for social good.'),
            ('priya_k', 'Priya Kumar', 20, '["Arts", "Cooking"]', '["English", "Tamil"]',
             'Love learning about heritage through food and traditional arts.'),
            ('zhi_wei', 'Tan Zhi Wei', 22, '["Chess", "Stories"]', '["English", "Mandarin", "Hokkien"]',
             'Final year student who loves chess and preserving Singaporean stories.'),
        ]

        new_youth = []
        for uname, name, age, interests, langs, bio in extra_youth_data:
            u = User.query.filter_by(username=uname).first()
            if not u:
                u = User(
                    username=uname, email=f'{uname}@gencon.sg',
                    full_name=name, age=age, role='youth',
                    interests_json=interests, languages_json=langs, bio=bio,
                    is_approved=True,
                    created_at=datetime.utcnow() - timedelta(days=random.randint(20, 60)),
                    last_active=datetime.utcnow() - timedelta(hours=random.randint(1, 24))
                )
                u.set_password('password123')
                db.session.add(u)
            new_youth.append(u)

        db.session.flush()

        seniors = User.query.filter_by(role='senior').all()
        youths = User.query.filter_by(role='youth').all()
        all_users = seniors + youths

        # ============================================================
        # 3. BUDDY PAIRS — ensure extras have pairs
        # ============================================================
        print("Creating additional buddy pairs...")
        existing_pairs = {(p.senior_id, p.youth_id) for p in Pair.query.all()}
        programs = ['Intergenerational Tech Bridge', 'Heritage Stories Project', 'Active Ageing Together']

        extra_pair_combos = list(zip(new_seniors, new_youth))
        for s_user, y_user in extra_pair_combos:
            if s_user and y_user and (s_user.id, y_user.id) not in existing_pairs:
                p = Pair(
                    senior_id=s_user.id, youth_id=y_user.id,
                    program=random.choice(programs),
                    status='active',
                    paired_date=datetime.utcnow() - timedelta(days=random.randint(14, 60)),
                    last_interaction=datetime.utcnow() - timedelta(hours=random.randint(1, 72))
                )
                db.session.add(p)
        db.session.flush()

        # ============================================================
        # 4. STORIES — Madam Tan's rich personal stories + others
        # ============================================================
        print("Creating stories...")

        madam_tan_stories = [
            ("My Famous Chicken Curry", "Family",
             "For 30 years at Queenstown Secondary School canteen, my chicken curry was the students' favourite. "
             "The secret? I use fresh curry leaves and grind my own spices every morning from whole seeds. "
             "My late husband used to say my curry is 'can die for' — that's his way of saying shiok lah! "
             "Even now in my seventies, I still make a big pot every Sunday. "
             "My children and grandchildren all come home just for the curry. Food is how I show love."),
            ("Growing Up in Queenstown", "Childhood",
             "In the 1960s, Queenstown was a brand new HDB estate — one of the first in Singapore. "
             "I remember moving there from our attap house in Buona Vista when I was 10 years old. "
             "Everything felt so modern! But we children still ran barefoot everywhere — the void deck, the playground. "
             "My mother would scold us but we never listened. Those carefree days playing five stones and zero point "
             "with the kampong kids — I miss them very much."),
            ("The Day I Became a Mother", "Family",
             "When my firstborn daughter Linda was put into my arms at KK Hospital in 1975, I cried and cried. "
             "My husband thought something was wrong! But I was crying from happiness. She was so tiny but so perfect. "
             "I was only 21 years old — just a girl myself. Raising three children on a hawker stall income was not easy, "
             "but we managed. Seeing them all graduated and settled, I feel very proud lah. Worth every hard day."),
            ("My Balcony Garden", "Hobbies",
             "When we got our HDB flat, I refused to give up gardening even on the 9th floor! "
             "I started with just chilli padi and curry leaves in old cooking oil tins. "
             "Now my corridor and balcony have more than 60 pots — pandan, laksa leaves, turmeric, galangal, "
             "even a little rambutan tree! My neighbour Mrs Lim always complains I take up too much corridor space, "
             "but she never refuses when I give her lemongrass for her cooking. Ha!"),
            ("30 Years at the Canteen", "Work Life",
             "People think working in a school canteen is simple. Cook rice, sell noodles, that's it right? "
             "But you learn so much about young people. I watched thousands of students grow up — "
             "from shy Primary One children to confident PSLE takers. "
             "Some came back as teachers, lawyers, doctors. A few still recognise me at the market and say "
             "'Eh, canteen auntie!' I always feel so happy. "
             "That job fed my family and gave me a second family too."),
        ]

        tan_story_objects = []
        for title, category, content in madam_tan_stories:
            if not Story.query.filter_by(user_id=senior.id, title=title).first():
                story = Story(
                    user_id=senior.id, title=title, content=content, category=category,
                    created_at=datetime.utcnow() - timedelta(days=random.randint(3, 28))
                )
                db.session.add(story)
                tan_story_objects.append(story)
        db.session.flush()

        # Pull all of Madam Tan's stories (including ones from seed_db.py)
        all_tan_stories = Story.query.filter_by(user_id=senior.id).all()

        # Other seniors' stories
        other_stories = [
            ("Walking to School in the Kampong", "Childhood",
             "In the 1960s, I walked 3 kilometres to school barefoot through the kampong every day. "
             "We would pass rubber plantations and sometimes see monkeys. My friend Ah Huat and I always stopped "
             "at the provision shop to look at sweets we couldn't afford. The shopkeeper uncle sometimes gave us "
             "one sweet each if we helped sweep his floor. Those were simple but happy times.", 'mary_wong'),
            ("National Service in 1970", "Work Life",
             "When I was called up for National Service in 1970, I was both scared and excited. "
             "Basic Military Training at Pulau Tekong was tough — the mosquitoes were terrible! "
             "But I made lifelong friends. My section mate Kumar and I still meet for kopi "
             "every Saturday at our favourite kopitiam in Toa Payoh. 55 years of friendship!", 'uncle_chen'),
            ("My Corridor Garden", "Hobbies",
             "When we moved from kampong to HDB, I thought I could never garden again. "
             "But I started growing chilli padi, kangkong, and pandan in old tins on my corridor. "
             "Now my balcony has over 50 plants! Neighbours always come for curry leaves and pandan. "
             "Gardening keeps me happy and healthy at 71.", 'ahmad_bin'),
            ("Teaching My Granddaughter to Make Kueh", "Family",
             "Last Chinese New Year, I taught my granddaughter Sophie how to make kueh lapis. "
             "She was so impatient waiting for each layer! But when she tasted the finished kueh, "
             "her eyes lit up: 'Ah Ma, this is better than any cake!' "
             "That moment made all the effort worthwhile. I hope she carries on this tradition.", 'ah_kow'),
            ("Learning Teochew Opera", "Family",
             "My grandmother was a Teochew opera performer in her youth. "
             "Every evening she would teach me the basic moves and songs in our small flat in Chinatown. "
             "The neighbours would open their windows to listen. Sometimes they would clap! "
             "I never became a performer, but those evenings taught me the importance of preserving our culture.", 'uncle_chen'),
            ("The Old Satay Club at Elizabeth Walk", "Childhood",
             "Before the Esplanade was built, there was the Satay Club near the waterfront. "
             "Every Friday night my father would take us there. The smell of satay grilling, "
             "the sea breeze, the sound of laughter — it was magical. "
             "10 cents per stick! I can still taste the peanut sauce. Those were the days.", 'sita_devi'),
            ("My Favourite Kopitiam", "Hobbies",
             "For 30 years I have been going to the same kopitiam at Block 85 Bedok North. "
             "The kopi uncle knows my order — kopi gao siu dai. "
             "The corner table near the fan is 'my' table. "
             "I've watched Singapore change through that kopitiam window for three decades. "
             "The kopi uncle is 78 now but still makes the best kopi in the East.", 'mary_wong'),
        ]

        all_created_stories = list(all_tan_stories)
        for title, category, content, username in other_stories:
            author = User.query.filter_by(username=username).first()
            if author and not Story.query.filter_by(user_id=author.id, title=title).first():
                story = Story(
                    user_id=author.id, title=title, content=content, category=category,
                    created_at=datetime.utcnow() - timedelta(days=random.randint(5, 45))
                )
                db.session.add(story)
                all_created_stories.append(story)
        db.session.flush()

        # ============================================================
        # 5. REACTIONS & COMMENTS — Ryan specifically reacts to Tan's
        # ============================================================
        print("Adding reactions and comments...")
        reaction_types = ['heart', 'smile', 'clap', 'hug']

        ryan_comments_for_tan = [
            "Madam Tan, this story made me so hungry! I can't wait to taste your curry one day 😄",
            "This is so vivid! Queenstown sounds so different from today. I love hearing about old Singapore.",
            "This is so touching. You must be the proudest mum! Thank you for sharing such a personal memory.",
            "60 pots on the balcony?! That's amazing. Can I visit your garden sometime?",
            "You changed so many students' lives, Madam Tan. This is truly inspiring to read.",
        ]

        for i, story in enumerate(all_tan_stories):
            if not StoryReaction.query.filter_by(story_id=story.id, user_id=youth.id).first():
                db.session.add(StoryReaction(
                    story_id=story.id, user_id=youth.id,
                    reaction_type=random.choice(reaction_types),
                    created_at=story.created_at + timedelta(hours=random.randint(1, 48))
                ))
            if not StoryComment.query.filter_by(story_id=story.id, user_id=youth.id).first():
                db.session.add(StoryComment(
                    story_id=story.id, user_id=youth.id,
                    content=ryan_comments_for_tan[i % len(ryan_comments_for_tan)],
                    created_at=story.created_at + timedelta(hours=random.randint(2, 72))
                ))

        # Generic reactions and comments from all users on all stories
        generic_comments = [
            "Thank you for sharing! This really touched my heart.",
            "Wah, this brings back so many memories! My grandparent told similar stories.",
            "This is so precious. We need to preserve these stories for future generations.",
            "I love hearing about old Singapore! So different from today.",
            "Your story is so vivid, I can almost taste the food!",
            "Please share more stories like this! So inspiring.",
            "Reading this made my day. Thank you for preserving our heritage.",
            "So inspiring! Singapore has come so far because of your generation.",
        ]

        all_stories_in_db = Story.query.all()
        for story in all_stories_in_db:
            reactors = random.sample(all_users, min(random.randint(3, 7), len(all_users)))
            for user in reactors:
                if user.id == story.user_id:
                    continue
                if not StoryReaction.query.filter_by(story_id=story.id, user_id=user.id).first():
                    db.session.add(StoryReaction(
                        story_id=story.id, user_id=user.id,
                        reaction_type=random.choice(reaction_types),
                        created_at=story.created_at + timedelta(hours=random.randint(1, 72))
                    ))
            commenters = random.sample(all_users, min(random.randint(1, 3), len(all_users)))
            for user in commenters:
                if user.id == story.user_id:
                    continue
                db.session.add(StoryComment(
                    story_id=story.id, user_id=user.id,
                    content=random.choice(generic_comments),
                    created_at=story.created_at + timedelta(hours=random.randint(2, 96))
                ))
        db.session.flush()

        # ============================================================
        # 6. MESSAGES — Rich personal conversation between Madam Tan & Ryan
        # ============================================================
        print("Creating messages...")

        existing_msg_count = Message.query.filter(
            ((Message.sender_id == senior.id) & (Message.recipient_id == youth.id)) |
            ((Message.sender_id == youth.id) & (Message.recipient_id == senior.id))
        ).count()

        if existing_msg_count < 10:
            # Conversation 1: First introduction (30 days ago)
            for i, (sid, rid, text, days_ago, mins) in enumerate([
                (youth.id, senior.id, "Good morning Madam Tan! I'm Ryan, your buddy volunteer. So happy to meet you!", 30, 0),
                (senior.id, youth.id, "Wah Ryan! Nice to meet you lah. My grandson helped me set up this app. He say very useful one!", 30, 8),
                (youth.id, senior.id, "That's so sweet of him! I heard you love cooking? I love eating haha 😄", 30, 14),
                (senior.id, youth.id, "Ha ha! Yes yes, I cook every day. Come come, one day I cook for you. My chicken curry very famous one!", 30, 20),
                (youth.id, senior.id, "Seriously?! I would love that. My grandma also made amazing curry. Brings back so many memories.", 30, 28),
                (senior.id, youth.id, "Your ah ma taught you to cook?", 30, 45),
                (youth.id, senior.id, "A little bit! But I can't compare to the real thing. Maybe you can teach me someday!", 30, 50),
                (senior.id, youth.id, "Aiyah no problem. Come Saturday, I teach you. But must be patient ah, cannot rush good cooking!", 30, 62),
            ]):
                db.session.add(Message(
                    sender_id=sid, recipient_id=rid, content=text,
                    original_language='en',
                    created_at=datetime.utcnow() - timedelta(days=days_ago, minutes=mins)
                ))

            # Conversation 2: Tech help (20 days ago)
            for sid, rid, text, days_ago, mins in [
                (youth.id, senior.id, "Madam Tan, did you manage to try the video call app I mentioned?", 20, 0),
                (senior.id, youth.id, "Wah this one difficult leh Ryan. I press wrong button everything disappear!", 20, 12),
                (youth.id, senior.id, "Haha no worries! Let's do it step by step. First, find the WhatsApp icon on your home screen.", 20, 16),
                (senior.id, youth.id, "WhatsApp... okay found it! Then?", 20, 25),
                (youth.id, senior.id, "Open it, then tap the camera icon at the top right to start a video call with someone.", 20, 28),
                (senior.id, youth.id, "Oh! I can see you! Ryan your hair so messy lah!", 20, 40),
                (youth.id, senior.id, "Hahaha I just woke up! But you look great Madam Tan!", 20, 42),
                (senior.id, youth.id, "Thank you ah boy. You remind me of my youngest son. Very patient and good heart one.", 20, 55),
            ]:
                db.session.add(Message(
                    sender_id=sid, recipient_id=rid, content=text,
                    original_language='en',
                    created_at=datetime.utcnow() - timedelta(days=days_ago, minutes=mins)
                ))

            # Conversation 3: Recipe sharing (10 days ago)
            for sid, rid, text, days_ago, mins in [
                (senior.id, youth.id, "Ryan ah, you remember the kueh lapis I told you about?", 10, 0),
                (youth.id, senior.id, "YES! Did you make it already??", 10, 4),
                (senior.id, youth.id, "Made yesterday! Come this Saturday for tea time. I also make kaya pandan butter cake.", 10, 12),
                (youth.id, senior.id, "WHAT! You're too good to me Madam Tan! What time should I come?", 10, 15),
                (senior.id, youth.id, "Come 3pm. Also bring your appetite, I cooking mee siam also. Big portion!", 10, 22),
                (youth.id, senior.id, "You're going to make me so fat haha!", 10, 25),
                (senior.id, youth.id, "Never mind! Young people must eat more. Still growing!", 10, 35),
                (youth.id, senior.id, "Hahaha I'm 20 lah not 10! But okay okay, I'll eat a lot 😄", 10, 38),
                (senior.id, youth.id, "Good good! See you Saturday. Don't be late ah!", 10, 50),
            ]:
                db.session.add(Message(
                    sender_id=sid, recipient_id=rid, content=text,
                    original_language='en',
                    created_at=datetime.utcnow() - timedelta(days=days_ago, minutes=mins)
                ))

            # Conversation 4: Story interview plan (2 days ago)
            for sid, rid, text, days_ago, mins in [
                (youth.id, senior.id, "Madam Tan! I just read your canteen story on the app. It made me tear up a little!", 2, 0),
                (senior.id, youth.id, "Aiyah so drama lah you! But thank you ah. That job means a lot to me.", 2, 10),
                (youth.id, senior.id, "You really touched so many lives. I'd love to write it up properly — can I interview you?", 2, 15),
                (senior.id, youth.id, "Interview? Like for newspaper ah? Ha! Okay lah, can. But I talk a lot one ah, be careful!", 2, 28),
                (youth.id, senior.id, "That's perfect! The more stories the better. Saturday after tea okay?", 2, 31),
                (senior.id, youth.id, "Okay settled! I prepare photos also. Got many old photos from the canteen days.", 2, 42),
                (youth.id, senior.id, "Amazing! I can't wait 😊", 2, 45),
            ]:
                db.session.add(Message(
                    sender_id=sid, recipient_id=rid, content=text,
                    original_language='en',
                    created_at=datetime.utcnow() - timedelta(days=days_ago, minutes=mins)
                ))

        # Generic messages for other pairs
        generic_convos = [
            [
                (True, "Good morning! Hope you had a good rest today 😊"),
                (False, "Morning! Yes, went for my walk already. Feeling energetic!"),
                (True, "Did you check out the new story on the app?"),
                (False, "Yes! Very touching. Singapore really has changed so much."),
            ],
            [
                (True, "Uncle, I've been practicing chess online to prepare for our rematch!"),
                (False, "Haha good! But online is different from real board. Come challenge me!"),
                (True, "This Saturday free?"),
                (False, "Okay Saturday 10am. Bring your best game!"),
            ],
        ]

        pairs = Pair.query.filter_by(status='active').all()
        for pair in pairs:
            if pair.senior_id == senior.id and pair.youth_id == youth.id:
                continue
            existing = Message.query.filter(
                ((Message.sender_id == pair.senior_id) & (Message.recipient_id == pair.youth_id)) |
                ((Message.sender_id == pair.youth_id) & (Message.recipient_id == pair.senior_id))
            ).count()
            if existing < 4:
                convo = random.choice(generic_convos)
                base_time = datetime.utcnow() - timedelta(days=random.randint(1, 20))
                for i, (youth_sends, text) in enumerate(convo):
                    sid = pair.youth_id if youth_sends else pair.senior_id
                    rid = pair.senior_id if youth_sends else pair.youth_id
                    db.session.add(Message(
                        sender_id=sid, recipient_id=rid, content=text,
                        original_language='en',
                        created_at=base_time + timedelta(minutes=i * random.randint(5, 20))
                    ))
        db.session.flush()

        # ============================================================
        # 7. COMMUNITY MEMBERSHIPS & POSTS
        # ============================================================
        print("Populating communities...")

        # Ensure demo users join the right communities
        senior_communities = ['Heritage Cooking', 'Story Sharing Circle', 'Gardening Enthusiasts', 'Active Seniors']
        youth_communities = ['Tech Helpers', 'Story Collectors', 'Game Facilitators']

        for comm_name in senior_communities:
            comm = Community.query.filter_by(name=comm_name).first()
            if comm and not CommunityMember.query.filter_by(community_id=comm.id, user_id=senior.id).first():
                db.session.add(CommunityMember(
                    community_id=comm.id, user_id=senior.id,
                    joined_at=datetime.utcnow() - timedelta(days=40)
                ))

        for comm_name in youth_communities:
            comm = Community.query.filter_by(name=comm_name).first()
            if comm and not CommunityMember.query.filter_by(community_id=comm.id, user_id=youth.id).first():
                db.session.add(CommunityMember(
                    community_id=comm.id, user_id=youth.id,
                    joined_at=datetime.utcnow() - timedelta(days=35)
                ))
        db.session.flush()

        # Madam Tan's community posts (persona-driven)
        tan_community_posts = {
            'Heritage Cooking': [
                "Just made my mother's recipe for kueh dadar! The pandan aroma filled my whole flat. Anyone else still makes traditional kueh at home?",
                "Secret to good chicken rice chilli: fresh chilli padi, young ginger, and a squeeze of calamansi lime. Never use the bottled one!",
                "My curry leaves plant is growing so well this year! Fresh curry leaves make such a big difference. Cannot use dried one lah!",
            ],
            'Story Sharing Circle': [
                "Just shared my story about working in the school canteen for 30 years. So many memories came flooding back! Thank you all for the kind comments 😊",
                "Does anyone have old photos of Queenstown in the 1960s? I am trying to find pictures of my old school. So different from today!",
            ],
        }

        # Ryan's community posts (persona-driven)
        ryan_community_posts = {
            'Tech Helpers': [
                "Pro tip: start with WhatsApp for video calling since seniors usually already have it. Less new apps to learn!",
                "Today I helped Madam Tan video call her sister in Malaysia for the first time. The look on her face when she saw her sister — priceless 😭",
                "Remember: celebrate every small win! When a senior successfully sends their first voice message, that's a BIG moment for them.",
            ],
            'Story Collectors': [
                "Just recorded an amazing interview with my buddy about her 30 years as a school canteen auntie. Stories about students coming back as doctors — so touching!",
                "Tip: use your phone's voice recorder app during interviews instead of typing. It captures their natural tone and you won't miss anything.",
            ],
        }

        for comm_name, posts in tan_community_posts.items():
            comm = Community.query.filter_by(name=comm_name).first()
            if comm:
                for post_text in posts:
                    if not CommunityPost.query.filter_by(community_id=comm.id, user_id=senior.id, content=post_text).first():
                        db.session.add(CommunityPost(
                            community_id=comm.id, user_id=senior.id, content=post_text,
                            created_at=datetime.utcnow() - timedelta(days=random.randint(2, 25))
                        ))

        for comm_name, posts in ryan_community_posts.items():
            comm = Community.query.filter_by(name=comm_name).first()
            if comm:
                for post_text in posts:
                    if not CommunityPost.query.filter_by(community_id=comm.id, user_id=youth.id, content=post_text).first():
                        db.session.add(CommunityPost(
                            community_id=comm.id, user_id=youth.id, content=post_text,
                            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 20))
                        ))

        # Generic community posts and memberships for other users
        generic_posts_data = {
            'Heritage Cooking': [
                "Had the best laksa at Katong today. Reminded me of my mother's homemade version!",
                "Does anyone know how to make proper nonya kueh dadar? The ones outside are never as good.",
            ],
            'Traditional Arts': [
                "Started a Chinese calligraphy class at the CC. So relaxing! Any seniors want to join?",
                "The heritage art exhibition at the National Museum is wonderful. Highly recommend!",
            ],
            'Story Sharing Circle': [
                "My grandson helped me type out my story about the old Toa Payoh swimming pool. Good memories!",
                "Reading everyone's stories here makes me so happy. We have such rich histories.",
            ],
            'Tech Helpers': [
                "Created a simple guide for video calling. Happy to share with other volunteers!",
                "Helped 3 seniors set up email today. Their excitement was so wholesome!",
            ],
            'Story Collectors': [
                "Starting a photo archive project — scanning old photos from seniors. Anyone want to help?",
                "The stories I've collected this month are incredible. Planning to compile a heritage booklet!",
            ],
            'Game Facilitators': [
                "Organised a chess tournament at the senior centre. The uncles were SO competitive!",
                "Uncle Chen beat all the youth volunteers at Chinese Chess today. Absolute legend.",
            ],
            'Gardening Enthusiasts': [
                "My chilli padi plants are finally flowering! Can't wait to harvest for my sambal.",
                "Anyone know how to deal with mealybugs on curry leaf plants? They keep coming back!",
            ],
            'Active Seniors': [
                "Morning walk group at Bishan Park every Tuesday and Thursday at 6:30am. All welcome!",
                "Just completed my 100th walk of the year! Feeling fitter than ever at 72.",
            ],
            'Wellness Champions': [
                "Organised a gentle yoga session for seniors at the CC. Great turnout!",
                "Reminder: hydration is so important in Singapore's heat, especially for seniors!",
            ],
            'Arts & Crafts Buddies': [
                "Made friendship bracelets with my senior buddy today. She was so patient teaching me!",
                "Looking for ideas for our next craft session. Any suggestions?",
            ],
            'Language Exchange': [
                "Learning a few Hokkien phrases from my buddy. 'Jiak pa buay?' means 'Have you eaten?'",
                "My senior buddy is teaching me Teochew. Such a beautiful dialect!",
            ],
            'Music & Songs': [
                "My buddy sang a beautiful Mandarin folk song today. I recorded it with her permission!",
                "Looking for old Singapore songs to share. Any recommendations?",
            ],
        }

        all_communities = Community.query.all()
        for community in all_communities:
            # Add other users as members
            pool = seniors if community.name in senior_communities else youths
            sample_size = min(random.randint(2, len(pool)), len(pool))
            members_to_add = random.sample(pool, sample_size)

            for user in members_to_add:
                if not CommunityMember.query.filter_by(community_id=community.id, user_id=user.id).first():
                    db.session.add(CommunityMember(
                        community_id=community.id, user_id=user.id,
                        joined_at=datetime.utcnow() - timedelta(days=random.randint(5, 60))
                    ))

            # Add generic posts
            posts = generic_posts_data.get(community.name, [])
            for post_text in posts:
                if not CommunityPost.query.filter_by(community_id=community.id, content=post_text).first():
                    poster = random.choice(members_to_add) if members_to_add else seniors[0]
                    db.session.add(CommunityPost(
                        community_id=community.id, user_id=poster.id, content=post_text,
                        created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
                    ))

        db.session.flush()

        # Update member counts
        for community in all_communities:
            community.member_count = CommunityMember.query.filter_by(community_id=community.id).count()
        db.session.flush()

        # ============================================================
        # 8. EVENT PARTICIPATION
        # ============================================================
        print("Adding event participants...")
        now = datetime.utcnow()
        events = Event.query.all()
        for event in events:
            is_past = event.date < now
            participants = random.sample(all_users, min(random.randint(3, 8), len(all_users)))
            for user in participants:
                if not EventParticipant.query.filter_by(event_id=event.id, user_id=user.id).first():
                    db.session.add(EventParticipant(
                        event_id=event.id, user_id=user.id,
                        registered_at=datetime.utcnow() - timedelta(days=random.randint(1, 14)),
                        reminder_24h_sent=is_past, reminder_1h_sent=is_past
                    ))
        db.session.flush()

        # ============================================================
        # 9. CHECK-INS — Madam Tan's realistic mood diary
        # ============================================================
        print("Creating check-ins...")

        if Checkin.query.filter_by(user_id=senior.id).count() < 5:
            tan_checkins = [
                (1,  'Great', "Ryan came to visit today and we had such a good chat! He tried my chicken curry — cannot stop eating! So happy!"),
                (4,  'Good',  "Went to the market this morning. Met my old neighbour Mrs Chong. Had kopi and caught up for a whole hour."),
                (8,  'Great', "My daughter Linda called from Australia. She's coming back for Chinese New Year! Cannot wait!"),
                (13, 'Okay',  "Stayed home today. A bit tired but finished the Channel 8 drama series I was watching."),
                (17, 'Good',  "Joined the morning exercise group at the void deck. Good to move the body. Met some new friends!"),
                (22, 'Not Good', "My knees are aching again today. Cannot walk much. Missing my late husband a little today."),
                (27, 'Good',  "Feeling better! Made a big batch of pineapple tarts to give the neighbours. Baking always cheers me up."),
                (31, 'Great', "Taught Ryan how to make curry paste from scratch today! His enthusiasm reminded me of teaching my own children. So touching."),
            ]
            for days_ago, mood, note in tan_checkins:
                db.session.add(Checkin(
                    user_id=senior.id, mood=mood, notes=note,
                    created_at=datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(9, 20))
                ))

        # Generic check-ins for other seniors
        moods = ['Great', 'Good', 'Okay', 'Not Good']
        mood_weights = [0.3, 0.4, 0.2, 0.1]
        generic_notes = {
            'Great': ["Had a wonderful day! Feeling great.", "My buddy visited today. So happy!", "Won at chess today — still got it!"],
            'Good':  ["Normal day, watched TV and read newspaper.", "Went to the market, met old friends.", "Nice video call with family in the evening."],
            'Okay':  ["Feeling a bit tired today. Didn't sleep well.", "Quiet day at home. A bit lonely.", "Weather too hot to go out."],
            'Not Good': ["My knees are aching. Hard to walk.", "Feeling quite lonely. Children all busy.", "Miss my late spouse a lot today."],
        }
        for snr in seniors:
            if snr.id == senior.id:
                continue
            if Checkin.query.filter_by(user_id=snr.id).count() < 3:
                for i in range(random.randint(3, 6)):
                    mood = random.choices(moods, weights=mood_weights, k=1)[0]
                    db.session.add(Checkin(
                        user_id=snr.id, mood=mood,
                        notes=random.choice(generic_notes[mood]) if random.random() > 0.3 else None,
                        created_at=datetime.utcnow() - timedelta(days=i * random.randint(2, 6), hours=random.randint(8, 20))
                    ))
        db.session.flush()

        # ============================================================
        # 10. STREAKS & BADGES for demo users
        # ============================================================
        print("Setting up streaks and badges...")

        tan_streak = Streak.query.filter_by(user_id=senior.id).first()
        if tan_streak:
            tan_streak.current_streak = 7
            tan_streak.longest_streak = 21
            tan_streak.points = 520
            tan_streak.games_played = 15
            tan_streak.games_won = 9
        else:
            db.session.add(Streak(
                user_id=senior.id, current_streak=7, longest_streak=21,
                points=520, games_played=15, games_won=9
            ))

        ryan_streak = Streak.query.filter_by(user_id=youth.id).first()
        if ryan_streak:
            ryan_streak.current_streak = 12
            ryan_streak.longest_streak = 28
            ryan_streak.points = 870
            ryan_streak.games_played = 22
            ryan_streak.games_won = 15
        else:
            db.session.add(Streak(
                user_id=youth.id, current_streak=12, longest_streak=28,
                points=870, games_played=22, games_won=15
            ))

        for badge_type in ['First Steps', 'Story Keeper', 'Heritage Champion', 'Social Butterfly', 'Week Warrior']:
            if not Badge.query.filter_by(user_id=senior.id, badge_type=badge_type).first():
                db.session.add(Badge(
                    user_id=senior.id, badge_type=badge_type,
                    earned_at=datetime.utcnow() - timedelta(days=random.randint(5, 40))
                ))

        for badge_type in ['First Steps', 'Tech Wizard', 'Heritage Champion', 'Week Warrior', 'Community Star', 'Helping Hand']:
            if not Badge.query.filter_by(user_id=youth.id, badge_type=badge_type).first():
                db.session.add(Badge(
                    user_id=youth.id, badge_type=badge_type,
                    earned_at=datetime.utcnow() - timedelta(days=random.randint(3, 35))
                ))

        all_badge_types = ['First Steps', 'Story Keeper', 'Social Butterfly', 'Game Enthusiast',
                           'Week Warrior', 'Heritage Champion', 'Helping Hand', 'Community Star']
        for user in new_seniors + new_youth:
            if not Streak.query.filter_by(user_id=user.id).first():
                db.session.add(Streak(
                    user_id=user.id,
                    current_streak=random.randint(1, 10), longest_streak=random.randint(5, 20),
                    points=random.randint(100, 600), games_played=random.randint(3, 20), games_won=random.randint(1, 12)
                ))
            for bt in random.sample(all_badge_types, random.randint(1, 3)):
                if not Badge.query.filter_by(user_id=user.id, badge_type=bt).first():
                    db.session.add(Badge(
                        user_id=user.id, badge_type=bt,
                        earned_at=datetime.utcnow() - timedelta(days=random.randint(1, 45))
                    ))
        db.session.flush()

        # ============================================================
        # 11. GAME HISTORY — Ryan vs Madam Tan + others
        # ============================================================
        print("Creating game history...")
        games = Game.query.all()
        if games:
            chess = next((g for g in games if 'Chess' in g.title and 'Chinese' not in g.title), games[0])
            chinese_chess = next((g for g in games if 'Chinese' in g.title), games[0])

            # Specific game history: Ryan vs Madam Tan (Ryan leads 3-2, Tan winning latest)
            specific_matches = [
                (chess.id,         senior.id, youth.id,  youth.id,  1200, 1215, 1200, 1185, 28),
                (chess.id,         youth.id,  senior.id, youth.id,  1215, 1226, 1185, 1174, 21),
                (chess.id,         senior.id, youth.id,  senior.id, 1226, 1238, 1174, 1162, 14),
                (chinese_chess.id, senior.id, youth.id,  senior.id, 1200, 1218, 1200, 1182, 7),
                (chess.id,         youth.id,  senior.id, youth.id,  1238, 1250, 1162, 1150, 3),
            ]

            for gid, p1, p2, winner, p1b, p1a, p2b, p2a, days_ago in specific_matches:
                db.session.add(GameHistory(
                    game_id=gid, player1_id=p1, player2_id=p2, winner_id=winner,
                    player1_elo_before=p1b, player1_elo_after=p1a,
                    player2_elo_before=p2b, player2_elo_after=p2a,
                    completed_at=datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(0, 8))
                ))

            # Generic game history for other users
            for _ in range(10):
                game = random.choice(games)
                p1, p2 = random.sample(all_users, 2)
                winner = random.choice([p1, p2, None])
                p1_elo = p1.elo or 1200
                p2_elo = p2.elo or 1200
                db.session.add(GameHistory(
                    game_id=game.id, player1_id=p1.id, player2_id=p2.id,
                    winner_id=winner.id if winner else None,
                    player1_elo_before=p1_elo, player1_elo_after=p1_elo + random.randint(-25, 25),
                    player2_elo_before=p2_elo, player2_elo_after=p2_elo + random.randint(-25, 25),
                    completed_at=datetime.utcnow() - timedelta(days=random.randint(1, 30), hours=random.randint(0, 12))
                ))
        db.session.flush()

        # ============================================================
        # 12. NOTIFICATIONS for demo users
        # ============================================================
        print("Creating notifications...")

        tan_notifications = [
            ("New Message from Ryan!", "Ryan sent you a message. Tap to read it!", "message", False),
            ("Event Reminder", "Heritage Cooking Class is in 2 days. Don't forget to join!", "event", False),
            ("Badge Earned!", "Congratulations! You earned the Story Keeper badge!", "game", True),
            ("New Comment on Your Story", "Ryan commented on 'My Famous Chicken Curry'. Check it out!", "message", True),
            ("Weekly Check-in", "How are you feeling this week? Take a moment to check in.", "message", True),
        ]

        ryan_notifications = [
            ("New Message from Madam Tan", "Madam Tan replied to your message!", "message", False),
            ("Game Challenge!", "You have a pending chess game with Madam Tan.", "game", False),
            ("Event Reminder", "Digital Literacy Workshop is tomorrow. Don't be late!", "event", True),
            ("Badge Earned!", "You earned the Heritage Champion badge. Keep it up!", "game", True),
            ("Community Update", "New posts in the Tech Helpers community.", "message", True),
        ]

        for title, message, ntype, is_read in tan_notifications:
            db.session.add(Notification(
                user_id=senior.id, title=title, message=message, type=ntype, is_read=is_read,
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 7), hours=random.randint(0, 20))
            ))

        for title, message, ntype, is_read in ryan_notifications:
            db.session.add(Notification(
                user_id=youth.id, title=title, message=message, type=ntype, is_read=is_read,
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 7), hours=random.randint(0, 20))
            ))

        generic_notif_pool = [
            ('New Message', 'You have a new message from your buddy!', 'message'),
            ('Event Reminder', 'An event you registered for is coming up soon.', 'event'),
            ('Badge Earned', 'Congratulations on your new achievement badge!', 'game'),
            ('Community Activity', 'New posts in your community. Check them out!', 'message'),
        ]
        for user in all_users:
            if user.id in [senior.id, youth.id]:
                continue
            for _ in range(random.randint(1, 3)):
                title, message, ntype = random.choice(generic_notif_pool)
                db.session.add(Notification(
                    user_id=user.id, title=title, message=message, type=ntype,
                    is_read=random.choice([True, False]),
                    created_at=datetime.utcnow() - timedelta(days=random.randint(0, 14), hours=random.randint(0, 23))
                ))
        db.session.flush()

        # ============================================================
        # 13. SUPPORT TICKETS
        # ============================================================
        print("Creating support tickets...")
        tickets_data = [
            ('Bug Report', 'Cannot upload profile picture',
             'When I try to upload a new profile picture, the page just refreshes and nothing changes. Tried JPG and PNG.', 'open'),
            ('Feature Request', 'Add more traditional games',
             'Would be great to have Congkak or Five Stones! The seniors would love it.', 'submitted'),
            ('General Inquiry', 'How to use the translation feature?',
             'My senior buddy speaks mostly Mandarin. I heard there is a translate button — how do I use it?', 'closed'),
        ]
        for ttype, subject, desc, status in tickets_data:
            user = random.choice([senior, youth])
            db.session.add(SupportTicket(
                user_id=user.id, ticket_type=ttype, subject=subject, description=desc, status=status,
                admin_notes='Resolved by admin.' if status == 'closed' else None,
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 20))
            ))

        # ============================================================
        # 14. SAMPLE CHAT REPORT (for admin moderation demo)
        # ============================================================
        print("Creating sample report...")
        if not Message.query.filter_by(is_flagged=True).first():
            some_pair = Pair.query.filter(Pair.senior_id != senior.id).first() or Pair.query.first()
            if some_pair:
                flagged_msg = Message(
                    sender_id=some_pair.youth_id, recipient_id=some_pair.senior_id,
                    content="Aiyah this is so stupid lah, I really don't want to do this anymore",
                    original_language='en', is_flagged=True,
                    created_at=datetime.utcnow() - timedelta(days=5)
                )
                db.session.add(flagged_msg)
                db.session.flush()
                db.session.add(ChatReport(
                    message_id=flagged_msg.id,
                    reported_by=some_pair.senior_id,
                    reported_user_id=some_pair.youth_id,
                    reason='Inappropriate Language',
                    description='The message contains unkind words that made me feel uncomfortable.',
                    status='pending',
                    created_at=datetime.utcnow() - timedelta(days=5)
                ))

        # ============================================================
        # COMMIT ALL
        # ============================================================
        db.session.commit()

        print("\n✅ Usage data seeded successfully!")
        print(f"   Stories:         {Story.query.count()}")
        print(f"   Messages:        {Message.query.count()}")
        print(f"   Community Posts: {CommunityPost.query.count()}")
        print(f"   Check-ins:       {Checkin.query.count()}")
        print(f"   Notifications:   {Notification.query.count()}")
        print(f"   Game History:    {GameHistory.query.count()}")
        print(f"   Support Tickets: {SupportTicket.query.count()}")
        print(f"\n   Login credentials:")
        print(f"   - senior / password123  →  {senior.full_name} (Madam Tan)")
        print(f"   - youth  / password123  →  {youth.full_name} (Ryan Lee)")
        print(f"   - admin  / password123  →  Admin dashboard")


if __name__ == '__main__':
    seed_usage()
