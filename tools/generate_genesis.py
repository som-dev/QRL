# coding=utf-8
from __future__ import print_function
import simplejson as json

from pyqrllib.pyqrllib import hstr2bin

from qrl.generated import qrl_pb2
from qrl.core import config
from qrl.core.Transaction import TransferTransaction
from qrl.core.Block import Block
from qrl.crypto.xmss import XMSS


def create_tx(addrs_to, amounts, signing_xmss, nonce):
    tx = TransferTransaction.create(addrs_to=addrs_to,
                                    amounts=amounts,
                                    fee=0,
                                    xmss_pk=signing_xmss.pk)
    tx.sign(signing_xmss)
    tx._data.nonce = nonce
    return tx


def get_migration_transactions(signing_xmss):
    transactions = []

    with open('data/token_migration.json', 'r') as f:
        json_data = json.load(f)

    count = 1
    addrs_to = []
    amounts = []
    # output_limit = config.dev.transaction_multi_output_limit
    output_limit = 4  # Overriding output limit to 4, to get multiple txns and better testing scenario
    for addr in json_data:
        addrs_to.append(bytes(hstr2bin(addr[1:])))
        amounts.append(json_data[addr])

        count += 1
        if count % output_limit == 0:
            transactions.append(create_tx(addrs_to, amounts, signing_xmss, count // output_limit))

            addrs_to = []
            amounts = []

    if addrs_to:
        transactions.append(create_tx(addrs_to, amounts, signing_xmss, count))

    return transactions


seed = bytes(hstr2bin(input('Enter extended hexseed: ')))

dist_xmss = XMSS.from_extended_seed(seed)

transactions = get_migration_transactions(signing_xmss=dist_xmss)

block = Block.create(block_number=0,
                     prevblock_headerhash=config.dev.genesis_prev_headerhash,
                     transactions=transactions,
                     miner_address=dist_xmss.address)

block.set_nonces(0, 0)

block._data.genesis_balance.MergeFrom([qrl_pb2.GenesisBalance(address=config.dev.coinbase_address,
                                                              balance=105000000000000000)])

k = block.blockheader.to_json()

with open('genesis.json', 'w') as f:
    f.write(block.to_json())
