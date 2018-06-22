from os import environ

# db connection URI to be passed to sqlalchemy, as in http://docs.sqlalchemy.org/en/latest/core/engines.html
db_engine = environ.get('DB', 'sqlite:///papi.db')
# check if app is running in docker
app_env = environ.get('APP_ENV', None)
# run on testnet or not
testnet = environ.get('PA_TESTNET', True)
# follow production P2TH or not
production = environ.get('PA_PRODUCTION', True)
# autoload the decks
autoload = environ.get('AUTOLOAD', True)
# max attempts to connect to the local node
max_attempts = environ.get('MAX_ATTEMPTS', 10)
# deck version to use
version = environ.get('PA_VERSION', 1)
# ip address of the peercoin node
rpc_host = environ.get('RPC_HOST', 'localhost')
# port of the peercoin node
rpc_port = environ.get('RCP_PORT', '16021')
# username for rpc connection
rpc_username = environ.get('RPC_USERNAME', 'randomuser')
# password for the rpc_connection
rpc_password = environ.get('RPC_PASSWORD', '098ooius00asiIIS00JAJ')
# subscribed deck list
# Use '*' inside the list to subscribe to all decks or use deck id's to subscribe to specified decks only
subscribed = ['*']#17d24b9bca5a090a24af138c2e085f80621396e8c7b6f820dee7140aee15cac1']
