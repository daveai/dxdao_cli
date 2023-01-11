import os
from web3 import Web3
import requests
import datetime
from brownie import Wei
import pandas as pd
import json

import warnings
warnings.filterwarnings("ignore")

# Get timestamp from 30 days ago
now = datetime.datetime.now()
thirty_days_ago = now - datetime.timedelta(days=30)
ts_30 = int(thirty_days_ago.timestamp())

mainnet = {
    'net': 'MAINNET',
    'emoji': ':eth:',
    'rpc': 'https://eth-mainnet.alchemyapi.io/v2/0nY-8QtxlISlugKf9W9NVF8V7oyrIgfC',
    'vms': ['0x1C18bAd5a3ee4e96611275B13a8ed062B4a13055', '0x332B8C9734b4097dE50f302F7D9F273FFdB45B84'],
    'avatar': '0x519b70055af55A007110B4Ff99b0eA33071c720a',
    'startingBlock': int(requests.get(f"https://api.etherscan.io/api?module=block&action=getblocknobytime&timestamp={ts_30}&closest=before").json()['result']),
    'abiEndpoint': 'https://api.etherscan.io/api?module=contract&action=getabi&address=',
}

gnosis = {
    'net': 'GNOSIS',
    'emoji': ':gnosis:',
    'rpc': 'https://rpc.gnosischain.com',
    'vms': ['0xDA309aDF1c84242Bb446F7CDBa96B570E901D4CF'],
    'avatar': '0xe716EC63C5673B3a4732D22909b38d779fa47c3F',
    'startingBlock': int(requests.get(f"https://api.gnosisscan.io/api?module=block&action=getblocknobytime&timestamp={ts_30}&closest=before").json()['result']),
    'abiEndpoint': 'https://api.gnosisscan.io/api?module=contract&action=getabi&address=',
}

arbitrum = {
    'net': 'ARBITRUM',
    'emoji': '',
    'rpc': 'https://arb1.arbitrum.io/rpc',
    'vms': ['0x02F93D46C2B56777e9C82CF40917979375C2c711'],
    'avatar': '0x2B240b523f69b9aF3adb1C5924F6dB849683A394',
    'startingBlock': int(requests.get(f"https://api.arbiscan.io/api?module=block&action=getblocknobytime&timestamp={ts_30}&closest=before").json()['result']),
    'abiEndpoint': 'https://api.etherscan.io/api?module=contract&action=getabi&address=',
}

contributorSchemes = [
    '0x08cC7BBa91b849156e9c44DEd51896B38400f55B',
    '0xFAB25c642b3724F3abbef7c61408B37A535F91C8',
    '0x0100F4B3D8A88D5729f0D4D516d436C901C2b4AF',
    '0x016Bf002D361bf5563c76230D19B4DaB4d66Bda4',
]

multicallSchemes = [
    '0x0f4775722a72FA85230c63598e661eC52563Fb4E',
    '0xef9dC3c39CA40A2a3000ACc5ca0467CE1C250808',
    '0x34C42c3ee81A03FD9ea773987b4a6eF62f3fc151',
    '0xaFE59DF878E23623A7a91d16001a66A4DD87e0c0',   
]

ensSchemes = [
    '0xB3ec6089556CcA49549Be01fF446cF40fA81c84D',
]

schemeRegistrar = [
    '0xf050F3C6772Ff35eB174A6900833243fcCD0261F',
    '0x22Ac81BE75cF76281D88A0F3A8Ae59b9abbE9da1',
]

votingMachineAbi = json.load(open('abis/votingMachine.json'))

def fetch_proposals(net):
    w3 = Web3(Web3.HTTPProvider(net['rpc']))
    proposals = []
    for vm in net['vms']:
        vm = w3.eth.contract(address=vm, abi=votingMachineAbi)
        # Get all proposals
        _proposals = vm.events.NewProposal.getLogs(fromBlock=net['startingBlock'])
        # Filter by avatar
        _proposals = [p for p in _proposals if p['args']['_organization'] == net['avatar']]
        # Filter by state
        _proposals = [p for p in _proposals if vm.functions.state('0x' + p['args']['_proposalId'].hex()).call() in [4, 5, 6]]
        # Get scheme for each proposal
        for p in _proposals:
            _proposal_state = vm.functions.proposals('0x' + p['args']['_proposalId'].hex()).call()
            # Create new dict with relevant info
            proposal_data = {
                'proposalId': '0x' + p['args']['_proposalId'].hex(),
                'transactionHash': p['transactionHash'].hex(),
                'scheme': _proposal_state[1],
                'votes': _proposal_state[3],
            }
            # Add proposal to proposals
            proposals.append(proposal_data)
    return proposals
        
def parse_proposals(proposals, net):
    _proposals = []
    w3 = Web3(Web3.HTTPProvider(net['rpc']))
    cs = w3.eth.contract(address='0x8E900Cf9BD655e34bb610f0Ef365D8d476fD7337', abi=json.load(open('abis/contributorScheme.json')))
    mc = w3.eth.contract(address='0x8E900Cf9BD655e34bb610f0Ef365D8d476fD7337', abi=json.load(open('abis/multiCall.json')))
    ens = w3.eth.contract(address='0x8E900Cf9BD655e34bb610f0Ef365D8d476fD7337', abi=json.load(open('abis/ensScheme.json')))
    scheme_register = w3.eth.contract(address='0x8E900Cf9BD655e34bb610f0Ef365D8d476fD7337', abi=json.load(open('abis/schemeRegister.json')))
    print(f"{net['emoji']*4} {net['net']} {net['emoji']*4}:")
    for _p in proposals:
        receipt = w3.eth.getTransactionReceipt(_p['transactionHash'])
        if _p['scheme'] in contributorSchemes:
            logs = cs.events.NewContributionProposal().processReceipt(receipt)
            logs = [l for l in logs if '0x' + l['args']['_proposalId'].hex() == _p['proposalId']]
            p = logs[0]['args']
            print(get_title(p['_descriptionHash']))
            print('0x' + p['_proposalId'].hex())
            if _p['votes'] == 1:
                print(f"Proposal passing: :white_check_mark:")
            else:
                print(f"Proposal passing: :red_circle:")
            if p['_rewards'][1] > 0:
                if net['net'] == 'MAINNET':
                    print('ETH:', round(Wei(p['_rewards'][1]).to('ether'), 2))
                else:
                    print('xDai:', round(Wei(p['_rewards'][1]).to('ether'), 2))
            if p['_rewards'][2] > 0:
                erc20, decimals = check_erc20(p['_externalToken'])
                print(f'{erc20}:', round(p['_rewards'][2] / 10**decimals, 2))
            if p['_reputationChange'] != 0:
                print('REP:', round(Wei(p['_reputationChange']).to('ether'), 2))
            print('')
        if _p['scheme'] in multicallSchemes:
            pass
        
def get_title(proposal_hash):
    ipfs_cache = pd.read_csv('ipfs_cache.csv')
    
    if proposal_hash in ipfs_cache.hash:
        title = ipfs_cache[ipfs_cache['hash'] == proposal_hash].title
        return title
    try: 
        req = requests.get('https://ipfs.io/ipfs/' + proposal_hash)
        title = req.json()['title'].strip()
        text = req.json()['description']
        data = {'hash': proposal_hash,
                'title': title,
                'text': text}
        ipfs_cache = ipfs_cache.append(data, ignore_index=True)
        ipfs_cache.to_csv('ipfs_cache.csv', index=False)
    except ValueError:
        title = "IPFS not returning Title"
    return title

def check_erc20(address):
    df = pd.read_csv('tokens.csv')
    if Web3.toChecksumAddress(address) in df.address.values:
        erc20 = df[df['address'] == Web3.toChecksumAddress(address)]
        return erc20['token'].values[0], erc20['decimals'].values[0]
    else:
        return 'ERC20', 18
    

if __name__ == '__main__':
    proposals = fetch_proposals(mainnet)
    parse_proposals(proposals, mainnet)
    proposals = fetch_proposals(gnosis)
    parse_proposals(proposals, gnosis)
    #proposals = fetch_proposals(arbitrum)
    #parse_proposals(proposals)