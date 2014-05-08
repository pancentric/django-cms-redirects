import os
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist

from cms_redirects.utils import process_csv_import, CsvImportError


class Command(BaseCommand):
    can_import_settings = True
    help = '''Import redirects'''
    args = "<csv_path>"

    option_list = BaseCommand.option_list + (
        make_option('--site',
                    dest="site",
                    default=Site.objects.get_current(),
                    help="Use to specify the domain of the site you are importing redirects into.  Defaults to current site."),
    )

    def execute(self, *args, **options):
        if len(args) != 1:
            raise CommandError("Must pass in the absolute path to the csv import file")
        csv_path = args[0]

        if not os.path.exists(csv_path):
            raise CommandError("File not found, invalid path: %s" % csv_path)

        with open(csv_path, "rb") as csv_file:

            current_site = options["site"]
            if not isinstance(current_site, Site):
                try:
                    current_site = Site.objects.get(domain=options["site"])
                except ObjectDoesNotExist:
                    raise CommandError("No site found, invalid domain: %s" % options["site"])

            try:
                process_csv_import(csv_file, current_site)
            except CsvImportError, err:
                raise CommandError(err)
