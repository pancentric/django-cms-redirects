from django.contrib import admin
from django.conf.urls.defaults import patterns
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.sites.models import Site
from django.utils.translation import ugettext as _

from cms_redirects.models import CMSRedirect
from cms_redirects.forms import UploadCSVForm
from cms_redirects.utils import process_csv_import, CsvImportError


class CMSRedirectAdmin(admin.ModelAdmin):
    list_display = ('old_path', 'new_path', 'page', 'page_site', 'site', 'actual_response_code',)
    list_filter = ('site',)
    search_fields = ('old_path', 'new_path', 'page__title_set__title')
    radio_fields = {'site': admin.VERTICAL}
    fieldsets = [
        ('Source', {
            "fields": ('site', 'old_path',)
        }),
        ('Destination', {
            "fields": ('new_path', 'page', 'response_code',)
        }),
    ]

    def get_urls(self):
        urls = super(CMSRedirectAdmin, self).get_urls()
        custom_urls = patterns('',
                              (r'^upload_csv/$', self.admin_site.admin_view(self.upload_csv))
                               )
        return custom_urls + urls

    def upload_csv(self, request):
        feedback = None
        file_has_errors = False
        if request.method == 'POST':
            form = UploadCSVForm(request.POST, request.FILES)
            if form.is_valid():
                current_site = Site.objects.get_current()
                try:
                    process_csv_import(request.FILES['csv_file'],
                                       current_site)
                    feedback = _('The file has been successfully processed.')
                except CsvImportError, err:
                    feedback = err
                    file_has_errors = True
                # Redisplay the page with an empty form and some feedback.
                form = UploadCSVForm()
        else:
            form = UploadCSVForm()
        return render_to_response('admin/cms_redirects/cmsredirect/upload_csv.html',
                                  {'form': form,
                                  'title': _('Upload a redirects CSV'),
                                  'feedback': feedback,
                                  'file_has_errors': file_has_errors},
                                  context_instance=RequestContext(request))


admin.site.register(CMSRedirect, CMSRedirectAdmin)
