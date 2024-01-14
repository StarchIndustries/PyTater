import hashlib
import json.decoder
import logging
import random
import zlib

import requests
import signal
import sys
import threading
import time


class PyTater:

    def __init__(self):
        self.block_found = False
        self.valid_miner = False

        self.block_count = 0
        self.block_height = 0
        self.halving_count = 0
        self.starch_balance = 0
        self.starting_blocks = 0

        self.last_block = None
        self.last_block_hash = None
        self.last_own_block = None
        self.last_own_block_hash = None
        self.miner_id = None
        self.pending_blocks = None

    def get_chain_config(self):
        # logging.info("Getting chain config...")
        try:
            res = requests.get('https://starch.one/api/blockchain_config')
        except TimeoutError:
            logging.error("Timeout fetching chain config!")
            return
        try:
            response = res.json()
        except json.decoder.JSONDecodeError:
            return

        try:
            self.block_height = response['blockchain_size']
            self.last_block = response['last_block']
            self.last_block_hash = self.last_block['hash']
        except KeyError:
            return

        logging.info(
            "Block Height: {} (Hash: {}, Color: {}, Miner: {})".format(self.block_height, self.last_block['hash'],
                                                                       self.last_block['color'],
                                                                       self.last_block['miner_id']))
        return response

    def get_pending(self):
        res = requests.get('https://starch.one/api/pending_blocks')

        try:
            response = res.json()
        except json.decoder.JSONDecodeError:
            return

        try:
            if response['pending_blocks']:
                self.block_found = False
                self.pending_blocks = response['pending_blocks']
                for block in self.pending_blocks:
                    if block['miner_id'] == self.miner_id:
                        self.block_found = True
                        self.last_own_block = block
                        self.last_own_block_hash = block['previous_hash']
        except KeyError:
            return

    def get_status(self):
        if self.miner_id is None:
            return

        res = requests.get('https://starch.one/api/miner/' + self.miner_id)
        try:
            response = res.json()
        except json.decoder.JSONDecodeError:
            logging.error(res)
            return
        try:
            self.starch_balance = response['balance']
            if self.starting_blocks == 0 and response['blocks'] != 0:
                self.starting_blocks = response['blocks']
            if response['blocks'] != self.starting_blocks:
                if response['blocks'] - self.starting_blocks != self.block_count:
                    logging.info("New Block Adopted! Block Count (this run): {}".format(self.block_count))
                self.block_count = response['blocks'] - self.starting_blocks
            self.valid_miner = True
        except KeyError as e:
            self.valid_miner = False
            self.starting_blocks = 0
            self.block_count = 0
            self.starch_balance = 0
            self.miner_id = None
            logging.error("Miner ID not found!")

    def sync(self, should_sync):
        logging.info("Booting up anticipation... Get ready for a simmering sensation.")
        while should_sync.is_set():
            start = time.time()
            self.get_status()
            self.get_pending()
            end = time.time()
            elapsed = end - start
            # logging.info("Time spent syncing: "+elapsed.__str__())
            if elapsed < 12.5:
                time.sleep(12.5 - elapsed)
            # time.sleep(12)

    # {
    #   "blockchain_size": 3714,
    #   "halving_count": 1,
    #   "last_block": {
    #     "color": "#6c72fb",
    #     "datetime": "01-13-2024:17-06-17",
    #     "hash": "f6fdb4beadb905edcc18da884877b85f84596eed850586bb29970f5f6e658878",
    #     "id": 218713,
    #     "miner_id": "1DF92481",
    #     "previous_hash": "9c360fc71d71e81ab61718c170284a2dd2b87e582cb5fbe48c6ba4921ba05208",
    #     "reward": 25000000
    #   },
    #   "rewards": 25000000
    # }
    def mine_block(self):
        logging.info("Unearthing $STRCH treasures with potato prowess... Mining spudtastic crypto gold.");
        self.get_chain_config()
        if self.block_found and self.last_own_block['previous_hash'] == self.last_block['hash']:
            logging.info("My Last Block:     (Hash: {}, Color: {})".format(self.last_own_block['previous_hash'],
                                                                           self.last_own_block['color']))
        else:
            logging.info("We should mine a block!")
            new_block = self.solve(self.last_block['hash'])
            self.submit_block(new_block)

    def submit_block(self, new_block):
        requests.post('https://starch.one/api/submit_block', json=new_block)
        logging.info("New block submitted to the chain!")

    def solve(self, blockhash):
        color = self.randomColor(blockhash)
        logging.debug("Solving New Block:\nHash: {}\nMiner ID: {}\nColor: {}".format(blockhash, self.miner_id, color))
        solution = blockhash + " " + self.miner_id + " " + color
        m = hashlib.sha256()
        m.update(bytes(solution, 'ascii'))
        new_hash = m.hexdigest()
        logging.info("Block hash: {}".format(new_hash))
        return {'hash': new_hash, 'color': color, 'miner_id': self.miner_id}

    def randomColor(self, blockhash: str):
        seed = zlib.crc32(bytes(blockhash + self.miner_id, 'ascii'))
        random.seed(seed)
        random_number = random.randint(0, 16777215)
        hex_number = '{0:06X}'.format(random_number)
        return '#' + hex_number

        # return "#000000"

    def mine(self, should_mine):
        logging.info("Diving deep into the crypto potato mine... Extracting $STRCH gems with starchy precision.")
        while should_mine.is_set():
            start = time.time()
            self.mine_block()
            end = time.time()
            elapsed = end - start
            if elapsed < 24.5:
                time.sleep(24.5 - elapsed)


valid_miner = False
starting_blocks = 0
block_count = 0
starch_balance = 0
miner_id = None
running_sync = None
miner_running = None
do_mine = threading.Event()
run_sync = threading.Event()


def end_script(signal, frame):
    global do_mine, run_sync
    logging.info("Stop signal received!")
    do_mine.clear()
    run_sync.clear()
    sys.exit(0)


def run():
    global do_mine, run_sync, running_sync, miner_running
    # global valid_miner, miner_id
    logging.info("Loading potato goodness... Spudtacular moments are on the way!")

    miner = PyTater()

    run_sync.set()
    running_sync = threading.Thread(target=miner.sync, args=(run_sync,), daemon=True)
    running_sync.start()

    while miner.valid_miner is False:
        miner.miner_id = input("Enter your Miner ID: ")
        miner.get_status()

    do_mine.set()
    miner_running = threading.Thread(target=miner.mine, args=(do_mine,), daemon=True)
    miner_running.start()


if __name__ == '__main__':
    try:
        log_format = "%(asctime)s: %(message)s"
        logging.basicConfig(format=log_format, level=logging.INFO,
                            datefmt="%H:%M:%S")

        run()
        signal.signal(signal.SIGINT, end_script)

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        end_script(None, None)
