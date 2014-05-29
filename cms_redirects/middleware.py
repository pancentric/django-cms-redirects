from cms_redirects.models import CMSRedirect
from django import http
from django.conf import settings


def get_redirect(old_path):
    try:
        redirect = CMSRedirect.objects.get(site__id__exact=settings.SITE_ID,
                                           old_path=old_path,
                                           active=True)
    except CMSRedirect.DoesNotExist:
        redirect = None
    return redirect


def remove_slash(path):
    return path[:path.rfind('/')] + path[path.rfind('/') + 1:]


def remove_query(path):
    return path.split('?', 1)[0]


class RedirectFallbackMiddleware(object):

    def process_exception(self, request, exception):
        if isinstance(exception, http.Http404):

            # First try the whole path.
            path = request.get_full_path()
            redirect = get_redirect(path)

            # It could be that we need to try without a trailing slash.
            if redirect is None and settings.APPEND_SLASH:
                redirect = get_redirect(remove_slash(path))

            # It could be that the redirect is defined without a query string.
            if redirect is None and path.count('?'):
                redirect = get_redirect(remove_query(path))

            # It could be that we need to try without query string and without a trailing slash.
            if redirect is None and path.count('?') and settings.APPEND_SLASH:
                redirect = get_redirect(remove_slash(remove_query(path)))

            if redirect is not None:
                if redirect.page:
                    if redirect.response_code == '302':
                        return http.HttpResponseRedirect(redirect.page.get_absolute_url())
                    else:
                        return http.HttpResponsePermanentRedirect(redirect.page.get_absolute_url())
                if redirect.new_path == '':
                    return http.HttpResponseGone()
                if redirect.response_code == '302':
                    return http.HttpResponseRedirect(redirect.new_path)
                else:
                    return http.HttpResponsePermanentRedirect(redirect.new_path)
