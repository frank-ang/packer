import gnupg, logging, os
from subprocess import CalledProcessError, check_output, STDOUT

gpg = gnupg.GPG()

def encrypt(file_path, destination_path, config):
    """
    Encrypts a file and returns its path.
    """
    logging.debug("# encrypt({}, {})".format(file_path, destination_path))
    if config.key_path is None:
        return None

    encrypted_file_path = file_path + config.ENCRYPTED_FILE_SUFFIX
    if destination_path is not None:
        if os.path.isdir(destination_path):
            encrypted_file_path = os.path.join(destination_path, os.path.basename(file_path) + config.ENCRYPTED_FILE_SUFFIX)
        else:
            encrypted_file_path = destination_path

    command = "openssl smime -encrypt -binary -aes-256-cbc -in {} -out {} -outform DER {}".format(file_path, encrypted_file_path, config.key_path)
    logging.debug("## executing command: {}".format(command))
    # E.g. openssl smime -encrypt -binary -aes-256-cbc -in junk.dat -out junk.dat.enc -outform DER certificate.pem
    try:
        cmd_out = check_output(command, stderr=STDOUT, shell=True)
    except CalledProcessError as e:
        raise Exception(e.output) from e
    return encrypted_file_path

def decrypt(file_path, config):
    """
    Decrypts a file, returns the path to the decrypted file.
    """
    logging.debug("# decrypt({})".format(file_path))
    if config.key_path is None:
        return None
    if not file_path.endswith(config.ENCRYPTED_FILE_SUFFIX):
        return None
    decrypted_file_path = file_path.removesuffix(config.ENCRYPTED_FILE_SUFFIX)
    command = "openssl smime -decrypt -binary -stream -in {} -inform DER -out {} -inkey {}".format(file_path, decrypted_file_path, config.key_path)
    logging.debug("## executing command: {}".format(command))
    # E.g. openssl smime -decrypt -binary -in junk.dat.enc -inform DER -out junk.dat.decrypted -inkey private_key.pem
    try:
        cmd_out = check_output(command, stderr=STDOUT, shell=True)
    except CalledProcessError as e:
        raise Exception(e.output) from e
    return decrypted_file_path
