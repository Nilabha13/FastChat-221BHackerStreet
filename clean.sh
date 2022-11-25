#!/bin/bash

if [ -e keys ]
then
	rm -r keys
fi

if [ -e logs ]
then
	rm -r logs
fi

if [ -e images ]
then
	rm -r images
fi

mkdir keys
mkdir keys/server_keys
cp SERVERS_PUBKEY.pem SERVERS_PRIVKEY.pem KEYSERVER_PUBKEY.pem KEYSERVER_PRIVKEY.pem keys/server_keys/
