from .be import BeLoader
from .lda_bb import LdaBbLoader

LOADERS = {
    "be": BeLoader,
    "lda_bb": LdaBbLoader,
}


def get_loader(loader_slug: str):
    return LOADERS[loader_slug]
