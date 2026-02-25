from PIL import Image, ImageDraw, ImageFont
import os

def create_architecture_diagram():
    # 16:9 resolution (1920x1080)
    width, height = 1920, 1080
    bg_color = (252, 252, 252)  # Light mode background
    primary_color = (66, 133, 244)  # Google Blue / Primary
    secondary_color = (52, 168, 83)  # Green / Success
    accent_color = (251, 188, 4)  # Yellow / Warning
    text_color = (33, 33, 33)
    border_color = (224, 224, 224)

    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Load font (falling back to default if necessary)
    try:
        title_font = ImageFont.truetype("arial.ttf", 60)
        subtitle_font = ImageFont.truetype("arial.ttf", 36)
        label_font = ImageFont.truetype("arial.ttf", 28)
        small_font = ImageFont.truetype("arial.ttf", 20)
    except:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        label_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # Draw Title
    draw.text((width // 2, 80), "GenCon SG Application Architecture", fill=text_color, font=title_font, anchor="mm")
    draw.line((width // 4, 130, 3 * width // 4, 130), fill=border_color, width=2)

    def draw_box(x, y, w, h, title, items, color):
        # Shadow/Border
        draw.rectangle([x-2, y-2, x+w+2, y+h+2], outline=border_color, width=1)
        draw.rectangle([x, y, x+w, y+h], fill=(255, 255, 255), outline=color, width=3)
        # Header
        draw.rectangle([x, y, x+w, y+45], fill=color)
        draw.text((x + w // 2, y + 22), title, fill=(255, 255, 255), font=subtitle_font, anchor="mm")
        # Items
        for i, item in enumerate(items):
            draw.text((x + 20, y + 65 + i * 35), f"• {item}", fill=text_color, font=label_font)

    # 1. Frontend Layer (Top)
    draw_box(200, 200, 500, 250, "Client Layer", [
        "Web Browsers (Jinja2 Templates)",
        "Socket.io-client (Real-time)",
        "WebRTC (Video/Audio Signaling)",
        "Local Assets (JS/CSS/Sounds)"
    ], primary_color)

    # 2. Flask Application Layer (Middle)
    draw_box(800, 200, 600, 350, "Backend (Flask Application)", [
        "Blueprints (Auth, Senior, Youth, Admin)",
        "Socket.io Handlers (Games, Chat)",
        "Middleware (Auth, Decorators, CORS)",
        "Template Rendering (Server-side)",
        "RESTful API Endpoints"
    ], primary_color)

    # 3. Service Layer (Bottom Middle)
    draw_box(800, 650, 600, 250, "Service Layer", [
        "ELO Rating Engine (Skill Levels)",
        "Engagement Streaks (Engagement)",
        "APScheduler (Event Reminders)",
        "Chat Safety (AI-driven Moderation)"
    ], secondary_color)

    # 4. Storage Layer (Bottom Right)
    draw_box(1450, 200, 400, 250, "Data Layer", [
        "SQLAlchemy (ORM)",
        "Relational Database (Models)",
        "Static Storage (Uploads)",
        "Local Cache"
    ], accent_color)

    # 5. External Integrations (Bottom Left)
    draw_box(200, 650, 500, 250, "External Integrations", [
        "Google OAuth2 (Social Login)",
        "SMTP Service (Email Delivery)",
        "DeepSeek AI API (Moderation)",
        "External Game Bots"
    ], (234, 67, 53))  # Reddish

    # Draw Connections (Simplified)
    # Client -> Backend
    draw.line((700, 325, 800, 325), fill=border_color, width=5)
    # Backend -> Storage
    draw.line((1400, 325, 1450, 325), fill=border_color, width=5)
    # Backend -> Services
    draw.line((1100, 550, 1100, 650), fill=border_color, width=5)
    # Backend -> External
    draw.line((450, 550, 800, 650), fill=border_color, width=3)

    # Footer
    draw.text((width // 2, 1020), "Developed for WDP-Assignment • Modern Modular Architecture", fill=(150, 150, 150), font=small_font, anchor="mm")

    img.save("architecture_showcase.png")
    print("Architecture diagram saved as architecture_showcase.png")

if __name__ == "__main__":
    create_architecture_diagram()
