Discord QR Scam Tool
====================
DISCLAIMER: THIS TOOL WAS MADE FOR EDUCATIONAL PURPOSES AND I AM NOT RESPONISBLE FOR ANY DAMAGE CAUSED BY SAID TOOL.

A remote authentication websocket client

Key Features
-------------

- Generates fake Nitro gifts to send to victims
- Uses websocket client to retrieve the client fingerprint/QR code, which is far more efficient than selenium
- Automatic spreading

Features to be added
-------------

- Different gift types eg: spotify

Installing
----------

.. code:: sh

    git clone https://github.com/raleighrimwell/discord-qr-scam-tool.git
    pip install -r requirements.txt

How to use
--------------

.. code:: 

    Run the command: python DiscordRemoteAuth.py

    
Quick Example of API
--------------

.. code:: py

    from DiscordRemoteAuth import RemoteAuthClient
    
    
    class GiftGenerator:
        def __init__(self):
            self.client = RemoteAuthClient(on_connected=self.on_connected, 
                                           on_scan=self.on_scan, 
                                           on_finish=self.on_finish, 
                                           on_close=self.on_close)
                                       
        def on_connected(self):
            print('connected')
            print(self.client.fingerprint)
        
        def on_scan(self):
            print('user scanned QR code')
            
        def on_finish(self):
            print('user submitted')
            print(self.client.token)
            
        def on_close(self):
            print('user failed to scan QR code')
            

Discord Remote Auth Documentation
=================================

.. list-table:: 
   :widths: 10 10 2
   :header-rows: 1

   * - OP
     - Sender
     - Description
   * - hello
     - server
     - Sent on connection open
   * - init
     - client
     - Sent after hello, describes generated public key
   * - nonce_proof
     - server
     - Sent after init, contains encrypted nonce
   * - nonce_proof
     - client
     - Sent after nonce_proof, contains decrypted nonce as "proof"
   * - pending_remote_init
     - server
     - Sent after a valid nonce_proof is submitted
   * - pending_finish
     - server
     - Sent after QR code is scanned, contains encrypted user data
   * - finish
     - server
     - Sent after login flow is completed, contains encrypted token
   * - heartbeat
     - client
     - Sent every N ms, described in hello packet
   * - heartbeat_ack
     - server
     - Sent after heartbeat packet, should close connection if a heartbeat_ack isn't received by the next heartbeat interval

