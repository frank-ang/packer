import gnupg, logging

log = logging.getLogger()
log.setLevel(logging.DEBUG)

gpg = gnupg.GPG()
logging.debug(gpg.list_keys())

def encrypt(path, config):
    logging.debug("# encrypt({})".format(path))

def decrypt(path, config):
    logging.debug("# decrypt({})".format(path))