import gnupg, logging

log = logging.getLogger()
log.setLevel(logging.DEBUG)


gpg = gnupg.GPG()
logging.debug(gpg.list_keys())