import csv

from django.utils.translation import ugettext as _

from cms_redirects.models import CMSRedirect


class CsvImportError(Exception):

    def __init__(self, value):
        self.parameter = value

    def __str__(self):
        return self.parameter


def process_csv_import(csv_file, current_site):
    """Process a supplied CSV file and generate new redirects from it."""

    reader = csv.reader(csv_file)
    header_row = reader.next()
    if header_row != ["Old Url", "New Url", "Response Code"]:
        raise CsvImportError(
            _("CSV file is missing the correct header row. Should be %(format)s"
                % {'format': '"Old Url", "New Url", "Response Code".'}))
    reader = csv.DictReader(csv_file, header_row)

    counter = 1
    for row in reader:
        old_url = row["Old Url"]
        new_url = row["New Url"]
        if not old_url or not new_url:
            raise CsvImportError(_("Missing URL in row %(counter)s." % {'counter': counter}))
        resp_code = row["Response Code"]
        if resp_code not in ['301', '302']:
            resp_code = '301'
        redirect, created = CMSRedirect.objects.get_or_create(site=current_site, old_path=old_url)
        redirect.new_path = new_url
        redirect.response_code = resp_code
        redirect.save()
        counter += 1
