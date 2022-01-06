from django.views.generic.base import TemplateView


class AboutAuth(TemplateView):
    template_name = 'about/author.html'


class AboutTech(TemplateView):
    template_name = 'about/tech.html'
