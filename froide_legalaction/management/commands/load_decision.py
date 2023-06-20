from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import translation


class Command(BaseCommand):
    help = "Moves files to content hash based directory structure"

    def add_arguments(self, parser):
        parser.add_argument("loader", type=str)
        parser.add_argument("path", type=str)

    def handle(self, *args, **options):
        translation.activate(settings.LANGUAGE_CODE)

        from ...loaders import get_loader

        loader_slug = options["loader"]
        options_path = Path(options["path"])

        loader = get_loader(loader_slug)()
        loader.load(options_path)
