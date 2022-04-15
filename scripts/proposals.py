import os
from web3 import Web3
import requests
import datetime
from brownie import Wei
import pandas as pd
from .abis import *


VOTING_MACHINE_0 = '0x1C18bAd5a3ee4e96611275B13a8ed062B4a13055'
VOTING_MACHINE_1 = '0x332B8C9734b4097dE50f302F7D9F273FFdB45B84'

def fetch_mainnet():
    net = 'MAINNET'
    avatar = '0x519b70055af55A007110B4Ff99b0eA33071c720a'
    w3 = Web3(Web3.HTTPProvider('https://eth-mainnet.alchemyapi.io/v2/0nY-8QtxlISlugKf9W9NVF8V7oyrIgfC'))
    
    # Contribution Proposals
    cp_scheme = '0x08cC7BBa91b849156e9c44DEd51896B38400f55B'
    abi = cp_abi
    scheme = w3.eth.contract(address=cp_scheme, abi=abi)
    proposals = scheme.events.NewContributionProposal.createFilter(fromBlock=get_block(net), argument_filters={'_avatar': avatar})
    proposal_events = proposals.get_all_entries()

    for p in proposal_events:
        p = p['args']
        execution_ts = scheme.functions.getProposalExecutionTime('0x' + p['_proposalId'].hex(), avatar).call()
        if execution_ts == 0:
            print(get_title(p['_descriptionHash']))
            print('0x' + p['_proposalId'].hex())
            if p['_rewards'][1] > 0:
                print('ETH:',  Wei(p['_rewards'][1]).to('ether'))
            if p['_rewards'][2] > 0:
                erc20, decimals = check_erc20(p['_externalToken'])
                print(f'{erc20}:', p['_rewards'][2] / 10**decimals)
            if p['_reputationChange'] != 0:
                print('REP:', Wei(p['_reputationChange']).to('ether'))
            print('')

"""     # Generic Multi Scheme
    gms = '0x0f4775722a72FA85230c63598e661eC52563Fb4E'
    abi = get_abi(gms, net)
    scheme = w3.eth.contract(address=gms, abi=abi)
    proposals = scheme.events.NewMultiCallProposal.createFilter(fromBlock=get_block(net), argument_filters={'_avatar': avatar})
    proposal_events = proposals.get_all_entries()

    for p in proposal_events:
        p = p['args']
        state = scheme.functions.proposals('0x' + p['_proposalId'].hex()).call()
        if state[0] == True and state[1] == False:
            print(get_title(p['_descriptionHash']))
            print('0x' + p['_proposalId'].hex())
            print(f"Calling contract: {p['_contractsToCall']}")
            print('\n')
 """
def fetch_xdai():
    net = 'XDAI'
    avatar = '0xe716EC63C5673B3a4732D22909b38d779fa47c3F'
    w3 = Web3(Web3.HTTPProvider("https://xdai-archive.blockscout.com/"))

    # Genesis protocol
    gp = w3.eth.contract(address='0xDA309aDF1c84242Bb446F7CDBa96B570E901D4CF', abi=gp_abi)

    # Contribution proposals
    cp_scheme = '0x016Bf002D361bf5563c76230D19B4DaB4d66Bda4'
    abi = cp_abi
    scheme = w3.eth.contract(address=cp_scheme, abi=abi)
    # Get all proposals under the scheme
    proposals = scheme.events.NewContributionProposal.getLogs(fromBlock=19002138)
    # Filter for DXdao proposals
    proposal_events = [i for i in proposals if i['args']['_avatar'] == avatar]
    proposal_events = [i for i in proposals if gp.functions.isVotable('0x' + i['args']['_proposalId'].hex()).call()]

    for p in proposal_events:
        p = p['args']
        # Check if proposal is live
        boost = gp.functions.state('0x' + p['_proposalId'].hex()).call()
        if boost in [4,5]:
            print(get_title(p['_descriptionHash']))
            print('0x' + p['_proposalId'].hex())
            if p['_rewards'][1] > 0:
                print('xDai:', Wei(p['_rewards'][1]).to('ether'))
            if p['_rewards'][2] > 0:
                erc20, decimals = check_erc20(p['_externalToken'])
                print(f'{erc20}:', p['_rewards'][2] / 10**decimals)
            if p['_reputationChange'] != 0:
                print('REP:', Wei(p['_reputationChange']).to('ether'))
            print('')

def fetch_all():
    nets = ['MAINNET', 'XDAI', 'ARBITRUM']

    pass

def check_erc20(address):
    df = pd.read_csv('scripts/tokens.csv')
    if Web3.toChecksumAddress(address) in df.address.values:
        erc20 = df[df['address'] == Web3.toChecksumAddress(address)]
        return erc20['token'].values[0], erc20['decimals'].values[0]
    else:
        return 'ERC20', 18



def get_abi(address, network):
    if network == 'MAINNET':
        req = requests.get(f"https://api.etherscan.io/api?module=contract&action=getabi&address={address}&apikey={os.getenv('ETHERSCAN_KEY')}")
        abi = req.json()['result']
    elif network == 'XDAI':
        req = requests.get(f"https://blockscout.com/xdai/mainnet/api?module=contract&action=getabi&address={address}")
        abi = req.json()['result']
    return abi

def get_title(proposal_hash):
    ipfs_cache = pd.read_csv('scripts/ipfs_cache.csv')
    
    if proposal_hash in ipfs_cache.hash:
        title = ipfs_cache[ipfs_cache['hash'] == proposal_hash].title
        return title
    try: 
        req = requests.get('https://ipfs.io/ipfs/' + proposal_hash)
        title = req.json()['title']
        text = req.json()['description']
        data = {'hash': proposal_hash,
                'title': title,
                'text': text}
        ipfs_cache = ipfs_cache.append(data, ignore_index=True)
        ipfs_cache.to_csv('scripts/ipfs_cache.csv', index=False)
    except ValueError:
        title = "IPFS not returning Title"
    return title

def get_block(network):
    now = datetime.datetime.now()
    then = now - datetime.timedelta(days=60)
    ts = int(then.timestamp())
    if network == 'MAINNET':
        req = requests.get(f"https://api.etherscan.io/api?module=block&action=getblocknobytime&timestamp={ts}&closest=before&apikey=KMP3MHD2Q7CZ1UN7753WXNAKQ15GZN3V3C")
        block = int(req.json()['result'])
    elif network == 'XDAI':
        req = requests.get(f"https://blockscout.com/xdai/mainnet/api?module=block&action=getblocknobytime&timestamp={ts}&closest=before")
        block = int(req.json()['result']['blockNumber'])
    elif network == 'ARBITRUM':
        raise NotImplementedError
    else:
        raise NotImplementedError
    return block

if __name__ == '__main__':
    print("Mainnet Contributor Proposals:")
    fetch_mainnet()

    print("GC Contributor Proposals:")
    fetch_xdai()