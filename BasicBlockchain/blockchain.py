from flask import Flask, jsonify
import hashlib 
import datetime
import json 

#Create the block chain class and its function 
class Blockchain(object):

	def __init__(self):
		#create the Genesis block first. It will have proof=1 and previous_hash as 0.
		self.chain = [] # our Blockchain
		self.create_block(proof=1, previous_hash='0')

	def create_block(self, proof, previous_hash):
		"""
		Logic to create the block and add it to the block chain.
		This function will be called only when a new block is mined by a miner.
		"""
		block = {
		'index': len(self.chain) + 1,
		'timestamp': str(datetime.datetime.now()),
		'proof': proof,
		'previous_hash': previous_hash
		}
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

	def verify_blockchain(self):
		"""
		Method to verify if all the blocks present in the blockchain are valid.
		"""
		block_index = 1 #block verifiation starts from the block after the genesis block.
		while block_index < len(self.chain):
			block = self.chain[block_index]
			previous_block = self.chain[block_index - 1]
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


#Create the logic for mining the block and reating/verifying the Blockchain

#create the Flask app
app = Flask(__name__)
blockchain = Blockchain()

#create the endpoint for mining a new block 
@app.route('/mine-block', methods=['GET'])
def mine_block():
	"""
	Method to mine a block and return the mined block as response
	"""
	last_block = blockchain.get_last_block()
	previous_proof = last_block['proof']
	new_proof = blockchain.proof_of_work(previous_proof) #Get the new proof using the Proof of Work method
	previous_hash = blockchain.hash_block(last_block) #Get the previous hash field
	block = blockchain.create_block(proof=new_proof, previous_hash=previous_hash) # create the new block
	message = {
			'message': 'The block was mined successfully',
			'block': block
	}
	return jsonify(message), 201

#create the endpoint to retrieve the entire blockchain
@app.route('/get-blockchain', methods=['GET'])
def get_blockchain():
	chain = blockchain.chain
	message = {'blockchain':chain}
	return jsonify(message), 201

#create the endpoint to verify the blockchain
@app.route('/verify-blockchain', methods=['GET'])
def verify_blockchain():
	chain_status = blockchain.verify_blockchain()
	if chain_status:
		message = {'Status': "The Blockchain is valid and secure"}
	else:
		message = {'Status': "The Blockchain is invalid and may not be secure"}
	return jsonify(message), 200

if __name__ == "__main__":
	app.run(host='0.0.0.0', debug=True, port=5000)
