import os
import logging
from fastmcp.server.auth.providers.bearer import RSAKeyPair
from pydantic import SecretStr

logger = logging.getLogger(__name__)

# Key file paths
PRIVATE_KEY_PATH = "mcpcp_private_key.pem"
PUBLIC_KEY_PATH = "mcpcp_public_key.pem"


def generate_and_save_keys():
    """Generate new RSA key pair and save to PEM files"""
    print("Generating new RSA key pair...")

    # Create directory if it doesn't exist
    os.makedirs("mcp_auth", exist_ok=True)

    key_pair = RSAKeyPair.generate()

    with open("mcp_auth/private.pem", "w") as f:
        f.write(key_pair.private_key.get_secret_value())
    print("Saved private key to mcp_auth/private.pem")

    with open("mcp_auth/public.pem", "w") as f:
        f.write(key_pair.public_key)
    print("Saved public key to mcp_auth/public.pem")


def load_keys():
    """Load existing RSA key pair from PEM files"""
    if not (
        os.path.exists(PRIVATE_KEY_PATH) and os.path.exists(PUBLIC_KEY_PATH)
    ):
        raise FileNotFoundError(
            "Key files not found. Run generate_and_save_keys() first."
        )

    logger.info("Loading existing RSA key pair from files")
    with open(PRIVATE_KEY_PATH, "r") as f:
        private_key_pem = f.read()
    with open(PUBLIC_KEY_PATH, "r") as f:
        public_key_pem = f.read()

    return RSAKeyPair.from_pem(
        private_key=private_key_pem, public_key=public_key_pem
    )


def get_or_create_keys():
    """Get existing keys or create new ones if they don't exist"""
    try:
        return load_keys()
    except FileNotFoundError:
        return generate_and_save_keys()


def generate_test_token(
    key_pair: RSAKeyPair, client_id: str, scopes: list = None
):
    """Generate a test JWT token for the given client_id and scopes"""
    if scopes is None:
        scopes = ["read", "write"]

    token = key_pair.create_token(
        subject=client_id,
        issuer="https://mcpcp",
        audience="mcpcp-server",
        scopes=scopes,
        expires_in_seconds=3600,  # 1 hour
    )
    return token


if __name__ == "__main__":
    generate_and_save_keys()
