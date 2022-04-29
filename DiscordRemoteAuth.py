import base64, json, threading, time, websocket
from Crypto.Cipher    import PKCS1_OAEP
from Crypto.Hash      import SHA256
from Crypto.PublicKey import RSA

class RemoteAuthClient:

    def __init__(self, on_connected=None, on_finish=None, on_scan=None, on_close=None):
        self.ws = websocket.WebSocketApp('wss://remote-auth-gateway.discord.gg/?v=1', 
                                        header={'Origin': 'https://discord.com'},
                                        on_message=(self.on_message),
                                        on_close=(self.on_close))
        
        self.key = RSA.generate(2048)
        self.cipher = PKCS1_OAEP.new((self.key), hashAlgo=SHA256)
        
        self.heartbeat_interval = None
        self.last_heartbeat = None
        
        self.token = None
        
        self.on_connected = on_connected
        self.on_scan = on_scan
        self.on_finish = on_finish
        self.on_close = on_close

    def run(self):

        self.ws.run_forever()

    @property
    def public_key(self):
        pub_key = self.key.publickey().export_key().decode('utf-8')
        pub_key = ''.join(pub_key.split('\n')[1:-1])
        return pub_key

    def heartbeat_sender(self):
        while True:
            time.sleep(0.5)
            current_time = time.time()
            time_passed = current_time - self.last_heartbeat + 1
            if time_passed >= self.heartbeat_interval:
                try:
                    self.send('heartbeat')
                    self.last_heartbeat = current_time
                except Exception:
                    return

    def send(self, op, data=None):
        payload = {'op': op}
        if data is not None:
            (payload.update)(**data)
        self.ws.send(json.dumps(payload))

    def decrypt_payload(self, encrypted_payload):
        payload = base64.b64decode(encrypted_payload)
        decrypted = self.cipher.decrypt(payload)
        return decrypted

    def on_message(self, ws, message):
        data = json.loads(message)
        op = data.get('op')
        
        #INITIALISING CONNECTION 
        if op == 'hello':
            self.heartbeat_interval = data.get('heartbeat_interval') / 1000
            self.last_heartbeat = time.time()
            thread = threading.Thread(target=(self.heartbeat_sender))
            thread.daemon = True
            thread.start()
            self.send('init', {'encoded_public_key': self.public_key})
            
        #VALIDATING REQUEST
        elif op == 'nonce_proof':
            nonce = data.get('encrypted_nonce')
            decrypted_nonce = self.decrypt_payload(nonce)
            proof = SHA256.new(data=decrypted_nonce).digest()
            proof = base64.urlsafe_b64encode(proof)
            proof = proof.decode().rstrip('=')
            self.send('nonce_proof', {'proof': proof})
            
        #CONNECTED TO DISCORD
        elif op == 'pending_remote_init':
            self.fingerprint = data.get('fingerprint')
            self.on_connected()
            
        #USER SCANNED QR CODE
        elif op == 'pending_finish':
            self.on_scan()
            
        #USER SUBMITTED
        elif op == 'finish':
            encrypted_token = data.get('encrypted_token')
            token = self.decrypt_payload(encrypted_token)
            self.token = token.decode()
            self.ws.close()
            self.on_finish()

    def on_close(self):
        self.on_close()

    def on_error(ws, error):
        print(error)


if __name__ == '__main__':
    client = RemoteAuthClient().run()