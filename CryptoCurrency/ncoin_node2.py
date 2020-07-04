from flask import Flask, jsonify, request
import hashlib 
import datetime
import json 
from uuid import uuid4
import requests 
from urllib.parse import urlparse 

#Create the block chain class and its function 
class Blockchain(object):

	def __init__(self):
		#create the Genesis block first. It will have proof=1 and previous_hash as 0.
		self.chain = [] # our Blockchain
		self.transactions = [] # our list of transaction
		self.create_block(proof=1, previous_hash='0')
		self.nodes = set() #A list of different nodes which are interconnected 

	def create_block(self, proof, previous_hash):
		"""
		Logic to create the block and add it to the block chain.
		This function will be called only when a new block is mined by a miner.
		"""
		block = {
		'index': len(self.chain) + 1,
		'timestamp': str(datetime.datetime.now()),
		'proof': proof,
		'previous_hash': previous_hash,
		'transactions': self.transactions
		}
		self.transactions = [] # clear the transactions list
		#add the block to the chain
		self.chain.append(block)
		return block

	def get_last_block(self):
		"""
		Function to get the last block in the block chain.
		"""
		return self.chain[-1]

	def proof_of_work(self, previous_proof):
		"""
		Method to find out the new proof value by using the previous proof \
		and solving the cryptographic puzzle to get the hash with leading 4 zeroes.
		"""
		new_proof = 1
		check_proof = True #used to indicate if the correct proof was found
		while check_proof:
			#construct the hash by taking difference of the squares of the 2 proofs and converting them to utf encoded strings
			new_hash = hashlib.sha256(str(new_proof ** 2 - previous_proof ** 2).encode()).hexdigest()
			if new_hash.startswith('0000'):
				check_proof = False
			else:
				new_proof = new_proof + 1 #increment the new_proof till proper hash is found
		return new_proof

	def hash_block(self, block):
		"""
		Method to hash a given block.
		"""
		block_string = json.dumps(block, sort_keys=True).encode()
		hashed_block = hashlib.sha256(block_string).hexdigest()
		return hashed_block

	def verify_blockchain(self, chain):
		"""
		Method to verify if all the blocks present in the blockchain are valid.
		"""
		block_index = 1 #block verifiation starts from the block after the genesis block.
		while block_index < len(chain):
			block = chain[block_index]
			previous_block = chain[block_index - 1]
			#verify the previous hash field
			previous_hash = block['previous_hash']
			actual_previous_hash = self.hash_block(previous_block)
			#verify the proof fields
			proof = block['proof']
			previous_proof = previous_block['proof']
			proof_hash = hashlib.sha256(str(proof ** 2 - previous_proof ** 2).encode()).hexdigest()
			if previous_hash != actual_previous_hash:
				return False
			if not proof_hash.startswith('0000'):
				return False
			block_index = block_index + 1
		return True

	def add_transactions(self, sender, receiver, amount):
		"""
		Method to add the transactions to the transactions list
		"""
		self.transactions.append({'sender': sender,
								  'receiver': receiver,
								  'amount': amount
								  })
		previous_block = self.get_last_block()
		#return the index of next block that wil be mined to which we will add the transaction
		return previous_block['index'] + 1 

	def add_nodes(self, address):
		"""
		Method to append the address of other nodes to this blockchain instance
		"""
		parsed_url = urlparse(address)
		self.nodes.add(parsed_url.netloc) # append the hostname to nodes list

	def replace_chain(self):
		"""
		Method to find out the longest chain which will be the valid blockchain that we will use.
		"""
		longest_chain = None
		max_length = len(self.chain)
		for node in self.nodes:
			#get the blockchain belonging to each of the nodes
			response = requests.get('http://%s/get_blockchain' % (node))
			if response.status_code == 201:
				chain = response.json()['blockchain']
				length = response.json()['length']
				#check if the node's blockchain is longer than our blockchain and if it is valid
				if length > max_length and self.verify_blockchain(chain):
					max_length = length
					longest_chain = chain
		if longest_chain:
			self.chain = longest_chain
			return True
		return False 

#Create the logic for mining the block and reating/verifying the Blockchain

#create the Flask app
app = Flask(__name__)
#initialize the blockchain
blockchain = Blockchain()
#initialize the node address of the node which is running this script
node_address = str(uuid4()).replace('-','')

#create the endpoint for mining a new block 
@app.route('/mine_block', methods=['GET'])
def mine_block():
	"""
	Method to mine a block and return the mined block as response
	"""
	last_block = blockchain.get_last_block()
	previous_proof = last_block['proof']
	new_proof = blockchain.proof_of_work(previous_proof) #Get the new proof using the Proof of Work method
	previous_hash = blockchain.hash_block(last_block) #Get the previous hash field
	#add a transaction entry to provide the mining fees to the miner
	blockchain.add_transactions(sender = node_address, receiver = "Manohar", amount=0.2)
	block = blockchain.create_block(proof=new_proof, previous_hash=previous_hash) # create the new block
	message = {
			'message': 'The block was mined successfully',
			'block': block
	}
	return jsonify(message), 201

#create the endpoint to retrieve the entire blockchain
@app.route('/get_blockchain', methods=['GET'])
def get_blockchain():
	chain = blockchain.chain
	message = {'blockchain':chain,
				'length': len(chain)
			    }
	return jsonify(message), 201

#create the endpoint to verify the blockchain
@app.route('/verify_blockchain', methods=['GET'])
def verify_blockchain():
	chain_status = blockchain.verify_blockchain(blockchain.chain)
	if chain_status:
		message = {'Status': "The Blockchain is valid and secure"}
	else:
		message = {'Status': "The Blockchain is invalid and may not be secure"}
	return jsonify(message), 200

#endpoint to add trnsactions
@app.route('/add_transactions', methods=['POST'])
def add_transactions():
	json = request.get_json()
	transaction_keys = ['sender', 'receiver', 'amount']
	if set(json.keys()) == set(transaction_keys):
		index = blockchain.add_transactions(sender=json['sender'], receiver=json['receiver'],amount=json['amount'])
		message = {'message': 'Transaction will be added to block number %s' % (index),
					'transaction_info': {
										'sender': json['sender'],
										'receiver': json['receiver'],
										'amount': json['amount']
					}}
		return jsonify(message), 201
	else:
		return "Incorrect transaction data", 400

#endpoint to connect nodes
@app.route('/add_nodes', methods=['POST'])
def add_nodes():
	json = request.get_json()
	nodes = json.get('nodes')
	if nodes:
		for node in nodes:
			blockchain.add_nodes(node)

		message = {'message': "the following nodes were added %s" % (nodes)}
		return jsonify(message), 201
	else:
		return "Node information wasnt passed", 400

#endpoint to replace chain with longest chain
@app.route('/replace_chain', methods=['GET'])
def replace_chain():
	result = blockchain.replace_chain()
	if result:
		message = {'New longest chain' : blockchain.chain,
					'length': len(blockchain.chain)
					}
		return jsonify(message), 200
	else:
		return "All chains were identical", 200

#endpoint to get all nodes
@app.route('/get_nodes', methods=['GET'])
def get_nodes():
	nodes = blockchain.nodes
	if nodes:
		message = {'Nodes' : list(nodes)
					}
		return jsonify(message), 200
	else:
		return "No nodes seen", 400

if __name__ == "__main__":
	app.run(host='0.0.0.0', debug=True, port=5002)
