# FastChat-221BHackerStreet




Message forwarding between python scripts: protocol

scripts will share messages as json files of dictionaries. Do a json load. The dictionary has a field: 'command' which will be present in all such disctionaries. It contains what to do with the dictionary.


For load_balancer connection by client: {'command':'ping'}
For message sent by load balancer to user: {'command':'authentication token', 'server port':'server socket number', 'token':'token'} 
For message sent by load balancer to suitable server: {'command':'authentication token', 'token':'token'}


Client makes initial connection with server, {'command':'first connection', 'authentication token':'token', 'username':'name'} 


Server checks token and then checks if username present in database. 
If wrong token, reject connection from client. Send back a message {'command':'error','type':'wrong authentication token'}


If username is new, Send back a message: {'command':'new user'}. User should be shown suitable message by client and client will send back created password. The message will be of the form: {'command':'new password', 'password':'password'}. Server stores this username, password in database. Sends back message: {'command':'register for keyServer'} (note: keyserver uses a database to store keys of all registered users). 
User at this point connects to key server at port 5013. Sends message {'command':'STORE', 'username':'username', 'key':'key'}. Keyserver sends back either {'command':'ERROR'} which implies user already exists or it sends back {'command':'INFO'} which means successful keyserver insertion done.
Then user disconnects from keyserver and starts sending regular messages.

If username exists, send back a message: {'command':'existing user'}. User should be shown suitable message by client and client will send back user entered password. Message of form: {'command':'password authenticate', 'password': 'password'}. Server checks password. If wrong, send back message: {'command':'re-enter'}. This causes process to repeat. Else, server sends back message: {'command':'password accepted'}.
If password wrong more than 3 times, server sends message {'command':'error', 'type':'wrong password error'}. Server then disconnects from client.
Once client properly connected and authenticated, read pending messages from the database. If any messages found, send a message to client: {'command':'pending messages', 'messages':[] (this is an array of all messages, each has regular message format)}.

Once a client is online and messaging, they type their messages. A client is expected to enter either 'SEND' or 'READ'. If the client enters READ, they are prompted to enter a username. They may also enter 'all'. If they enter the username, all messages recieved from that username are showed. Otherwise, all messages recieved are displayed along with sender usernames.

If client enters SEND, they are prompted to enter their message as well as the username of the reviever. client makes socket connection with keyserver. Sends message to key server of form {'command':'RETRIEVE', 'username':'userxyz'} to get public key of userxyz. Key server sends back message {'command':'PUBKEY', 'pubkey':'key'}. Keyserver could also return {'command':'error'...} which means user not found etc.


Client uses that key to encrypt the message and then sends message to their server. {'command':'user-user message', 'encrypted message':'message', 'reciever username':'userxyz', 'sender username':'user1'}.

When a server recieves a message from client, it checks command. If command=='user-user message'. Server then checks if given username is connected to that server in its socket list. If yes, directly send back a message to suitable user : {'command':'user-user message', 'encrypted message':'message', 'reciever username':'userxyz', 'sender username':'user1'}.

If given username not connected to that server, open database and find that user. Server then sees which server that user is connected to and send a message to that server over the server-server socket. message:{'command':'user-user message', 'encrypted message':'message', 'reciever username':'userxyz', 'sender username':'user1'}. This message is recieved by other server on server-server socket. It forwards message as:
{'command':'user-user message', 'encrypted message':'message', 'reciever username':'userxyz', 'sender username':'user1'} to suitable user connected to it. If user not found at this stage, i.e user not found connected to the server it was supposed to be connected to, then store the message in the database, with other details. 

When a client recieves a message, if it has command=='user-user message', store the message data in the list mantained by the python script. allow user to read from this list.






How to run:
Run load balancer, followed by servers in order. They take port number as command lie argument so enter them one by one as 5001, 5002 etc.

