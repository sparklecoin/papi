import pypeerassets as pa
from sync import Sync, attempt_connection
from models import Deck, Card, Balance, db
from state import DeckState, init_state
from sqlalchemy.exc import IntegrityError
from conf import *
import sys

''' Connection attempts counter'''
node = attempt_connection( Sync() )

def init_p2thkeys():

    if autoload:
        pa.pautils.load_p2th_privkey_into_local_node(node, production)


def add_deck(deck):
    if deck is not None:
        entry = db.session.query(Deck).filter(Deck.id == deck.id).first()
        if '*' in subscribed:
            subscribe = True
        else:
            subscribe = deck.id in subscribed

        if not entry:
            try:
                D = Deck( deck.id, deck.name, deck.issuer, deck.issue_mode, deck.number_of_decimals, subscribe)
                db.session.add(D)
                db.session.commit()
            except Exception as e:
                print(e)
                pass
        else:
            db.session.query(Deck).filter(Deck.id == deck.id).update({"subscribed": subscribe})
            db.session.commit()


def add_cards(cards):
    if cards is not None:
        for cardset in cards:
            for card in cardset:
                entry = db.session.query(Card).filter(Card.txid == card.txid).filter(Card.blockseq == card.blockseq).filter(Card.cardseq == card.cardseq).first()
                if not entry:
                    C = Card( card.txid, card.blockhash, card.cardseq, card.receiver[0], card.sender, card.amount[0], card.type, card.blocknum, card.blockseq, card.deck_id, False )
                    db.session.add(C)
                db.session.commit()


def load_key(deck_id):
    from binascii import unhexlify
    try:
        wif = pa.Kutil(privkey=unhexlify(deck_id), network=node.network).wif
        node.importprivkey( wif, deck_id)
    except Exception as e:
        print(e)


def init_decks():
    accounts = node.listaccounts()
    n = 0

    def message(n):
        sys.stdout.flush()
        sys.stdout.write('\r{} Decks Loaded\r'.format(n))

    if not autoload:
        decks = [pa.find_deck(node,txid,version) for txid in subscribed]

        for deck in decks:
            if deck is not None:
                if deck.id not in accounts:
                    print("deck",deck,"not in account",accounts)
                    load_key(deck.id)
                add_deck(deck)
                try:
                    if not checkpoint(deck.id):
                        add_cards( pa.find_card_transfers(node, deck) )
                        init_state(deck.id)
                except:
                    continue
                n += 1
                message(n)

    else:
        decks = pa.find_all_valid_decks(node, version, production)
        while True:
            try: 
                deck = next( decks )
                if deck.id not in accounts:
                    print("deck",deck,"not in account",accounts)
                    load_key(deck.id)
                add_deck( deck )
                if not checkpoint(deck.id):
                    try:
                        if '*' in subscribed:
                            add_cards( pa.find_card_transfers( node, deck ) )
                        elif deck.id in subscribed:
                            add_cards( pa.find_card_transfers( node, deck ) )
                    except:
                        continue
                    init_state(deck.id)
                    n += 1
                    message(n)
            except StopIteration:
                break


def update_decks(txid):
    deck = pa.find_deck(node, txid, version)
    add_deck(deck)
    return


def which_deck(txid):
    deck = node.gettransaction(txid)
    deck_id = None

    if 'details' in deck.keys():
         owneraccounts = [details['account'] for details in deck['details'] if details['account']]
         if len(owneraccounts):
             deck_id = [details['account'] for details in deck['details'] if details['account']][0]

    if deck_id is not None:
        if deck_id in ('PAPROD','PATEST'):
            update_decks(txid)
        elif deck_id in subscribed or subscribed == ['*']:
            deck = pa.find_deck(node, deck_id, version)
            if not checkpoint(deck_id):
                add_cards( pa.find_card_transfers(node, deck) )
                init_state(deck.id)
                DeckState(deck_id)
        return {'deck_id':deck_id}
    else:
        return


def update_state(deck_id):
    if not checkpoint(deck_id):
        DeckState(deck_id)
        return


def checkpoint(deck_id):
    ''' List all accounts and check if deck_id is loaded into the node'''
    accounts = node.listaccounts()

    if deck_id not in accounts:
        ''' if deck_id is not in accounts, load the key into the local node'''
        load_key(deck_id)

    ''' list all transactions for a particular deck '''
    txs = node.listtransactions(deck_id)

    if isinstance(txs,list):
        ''' Make sure txs is a list rather than a dict with an error. Reverse list order.'''
        checkpoint = txs[::-1]
        ''' Get the most recent card transaction recorded in the database for the given deck '''
        _checkpoint = db.session.query(Card).filter(Card.deck_id == deck_id).order_by(Card.blocknum.desc()).first()

        if _checkpoint is not None:
            ''' If database query doesn't return None type then checkpoint exists'''
            for i, v in enumerate(checkpoint):
                ''' for each transaction in local node listtransactions '''

                if ('blockhash','txid') in v:
                    ''' Check that keys exists within dict ''' 
                    if v['blockhash'] == _checkpoint.blockhash:
                        return True

                    txid = v['txid']
                    rawtx = node.getrawtransaction(txid,1)

                    ''' get deck object of current deck_id '''
                    deck = pa.find_deck(node, deck_id, version)
                    try:
                        ''' check if it's a valid PeerAssets transaction '''
                        pa.validate_card_transfer_p2th(deck, rawtx)
                        ''' return False if checkpoints don't match and True if they do '''
                        return _checkpoint.blockhash == v['blockhash']
                    except Exception:
                        continue

            return False

    return False


def init_pa():
    init_p2thkeys()
    init_decks()

    sys.stdout.write('PeerAssets version {} Initialized'.format(version))
    sys.stdout.flush()
