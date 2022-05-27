from datetime import timedelta
from os.path import exists

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import DetailView, CreateView, UpdateView, DeleteView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .forms import EpgAddForm
from .models import Epg, EpgChannel, EpgProgramme, EpgItem

from .async_download_files import download_files, EPGService, get_file_path, extractall_to_static
from .epg_file_parser import load_file, xmldict
import xml.etree.ElementTree as ET
from django.utils import timezone
from django.db.models import Q

# EPG_LINK_LIST = [
#     EPGService("it999", "http://epg.it999.ru/edem.xml.gz"),
#     EPGService("iptvx.one", "http://iptvx.one/epg/epg.xml.gz"),
#     EPGService("programtv.ru", "http://programtv.ru/xmltv.xml.gz"),
#     EPGService("k210.org", "http://tv.k210.org/xmltv.xml.gz"),
#     EPGService("free.fr", "http://kevinpato.free.fr/xmltv/download/complet.zip"),
# ]
from .pretty_size import pretty_size


def process_logo_path(channel):
    icon_url = channel.icon_url
    epg_id = channel.epg_item.epg_id

    if icon_url.startswith('http://localhost/') or \
            icon_url.startswith('http://127.0.0.1/') or \
            icon_url.startswith('http://0.0.0.0/') or \
            icon_url.startswith('/'):
        file_path = icon_url.replace('http://localhost/', '/static/logos/'+str(epg_id)+'-free.fr.logos.zip/logos/')
        file_path = file_path.replace('http://127.0.0.1/', '/static/logos/'+str(epg_id)+'-free.fr.logos.zip/logos/')
        file_path = file_path.replace('http://0.0.0.0/', '/static/logos/'+str(epg_id)+'-free.fr.logos.zip/logos/')
        if exists("epg_app/" + file_path):
            return file_path
        return None

    return icon_url


def channel_display_names_to_text(display_names):
    channels = list(display_names.keys())
    if len(channels):
        channels.pop(0)

    res = ""

    if len(channels):
        res += " (" + ','.join(channels) + ")"

    return res


def index(request):
    return epg_channels(request)


def epg_channels(request, pk=None):

    all_channels = EpgChannel.objects.all().order_by('id')

    epg = None
    if pk:
        epg = Epg.objects.get(pk=pk)
        all_channels = EpgChannel.objects.filter(epg_item__epg_id=pk).order_by('id')

    tvg_name = request.GET.get("tvg_name")
    if tvg_name:
        print(tvg_name.lower())
        tn = tvg_name.lower()
        if pk:
            all_channels = EpgChannel.objects.filter(Q(epg_item__epg_id=pk) &
                                                     (Q(tvg_name_synonyms__has_key=tn) | Q(tvg_name__contains=tn)))
        else:
            all_channels = EpgChannel.objects.filter(Q(tvg_name_synonyms__has_key=tn) | Q(tvg_name__contains=tn))

    paginator = Paginator(all_channels, 10)
    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)

    current_time = timezone.now() + timedelta(hours=3)

    def current_programme(channel):
        programme = EpgProgramme.objects.filter(epg_item=channel.epg_item,
                                                start__lte=current_time).order_by('start').last()
        if programme:
            return programme.start.strftime("%H:%M:%S - ") + get_title_from_xml(programme.data)
        return None

    channel_list = [{'epg_name': channel.epg_item.epg.name,
                     'epg_item_id': channel.epg_item_id,
                     'programme': current_programme(channel),
                     'pk': channel.pk,
                     'channel_id': channel.tvg_name + channel_display_names_to_text(channel.tvg_name_synonyms),
                     'icon_url': process_logo_path(channel)}
                    for channel in posts]

    context = {
        'epg': epg,
        'all_channels': channel_list,
        'page': page,
        'posts': posts,
        'search_tvg_name': tvg_name
    }
    return render(request, 'epg_app/channels.html', context=context)


def get_title_from_xml(data):
    root = ET.fromstring("<programme>" + data + "</programme>")

    for child in root.iter():
        if child is not root:
            if child.tag == "title":
                return child.text
                # print("text", child.text, ET.tostring(child, encoding="unicode"))
            # epg_without_header += ET.tostring(child, encoding="unicode")
            # print("    child:", ET.tostring(child, encoding="unicode"))

    # d = xmldict(root)
    # data = d['programme']
    #
    # if "title" in data:
    #     if isinstance(data['title'], dict):
    #         if "#text" in data['title']:
    #             return data['title']['#text']
    #     elif isinstance(data['title'], str):
    #         return data['title']

    return '"unnamed'


def programmes(request, epg_channel_id):
    return epg_item_programmes(request, epg_channel_id, main=True)


def epg_item_programmes(request, epg_channel_id, main=False):
    channel = EpgChannel.objects.filter(pk=epg_channel_id).first()

    programme_list = EpgProgramme.objects.filter(epg_item_id=channel.epg_item_id).order_by('id')

    paginator = Paginator(programme_list, 15)
    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)

    programme_list_page = [{'pk': programme.pk,
                            'start': programme.start.strftime("%Y-%m-%d %H:%M:%S"),
                            'data': get_title_from_xml(programme.data)}
                           for programme in posts]

    context = {
        'from_main': main,
        'epg_id': channel.epg_item.epg.id,
        'channel_name': channel.tvg_name,
        'programmes': programme_list_page,
        'page': page,
        'posts': posts
    }
    return render(request, 'epg_app/programmes.html', context=context)


def epg_sources(request):
    all_epg = Epg.objects.all()

    epg_list = [{'pk': epg.pk,
                 'name': epg.name,
                 'url': epg.url,
                 'download_time': epg.download_time,
                 'update_time': epg.update_time,
                 'size_str': pretty_size(epg.size)}
                for epg in all_epg]

    context = {
        'all_epg': epg_list
    }
    return render(request, 'epg_app/epg_sources.html', context=context)


def download_epg(request):
    download_status_list = []

    def update_success_callback(info, data_size):
        print("epg update_success_callback, info:", info, ", size:", data_size)
        download_status_list.append({'info': info, 'size': data_size, 'size_str': pretty_size(data_size)})

    def update_error_callback(info, error_message):
        print("epg update_error_callback, info:", info, ", error_message:", error_message)
        download_status_list.append({'info': info, 'error_message': error_message})

    all_epg = Epg.objects.all()

    # epg_list = [{'pk': epg.pk, 'name': epg.name, 'url': epg.url, 'logos_url': epg.logos_url} for epg in all_epg]

    epg_list = []
    for epg in all_epg:
        if epg.logos_url:
            epg_list.append({'pk': epg.pk, 'name': epg.name, 'url': epg.logos_url, 'is_epg': False})
        if epg.url:
            epg_list.append({'pk': epg.pk, 'name': epg.name, 'url': epg.url, 'is_epg': True})

    print("EPG LIST:", epg_list)
    download_files(epg_list, update_success_callback, update_error_callback)

    for item in download_status_list:
        if item['info']['is_epg'] is True:
            print("Store in db:", item)
            epg, created = Epg.objects.get_or_create(pk=item['info']['pk'])
            if 'error_message' not in item.keys():
                epg.download_time = timezone.now()
                epg.update_time = None
                epg.size = item['size']
                epg.error_message = ""
            else:
                epg.error_message = item['error_message']

            epg.save()

    context = {
        'download_status': download_status_list
    }
    return render(request, 'epg_app/epg_download.html', context=context)


# dict[tvg_id: EpgItem.id]
def get_channel_tvg_ids(epg_id):
    channel_qs = EpgItem.objects.filter(epg_id=epg_id).values('tvg_id', 'id')
    return {epg_channel["tvg_id"]: epg_channel["id"] for epg_channel in channel_qs}


# returns False if tvg_id exists
# otherwise True
def add_channel(epg_channel_dict, tvg_id):
    if tvg_id not in epg_channel_dict:
        epg_channel_dict[tvg_id] = None  # added id not used
        return True

    return False


# dict[epg_item_id: [start: pk]]
def get_programme_ids(epg_id):
    programme_qs = EpgProgramme.objects.filter(epg_item__epg=epg_id).values('epg_item_id', 'start', 'pk')

    epg_programme_dict = {}
    for epg_programme in programme_qs:
        if epg_programme["epg_item_id"] not in epg_programme_dict:
            epg_programme_dict[epg_programme["epg_item_id"]] = {}

        epg_programme_dict[epg_programme["epg_item_id"]][epg_programme["start"]] = epg_programme["pk"]
    return epg_programme_dict


# returns pk if programme exists
# returns False if exists and can't be updated
# otherwise None
def add_programme(epg_programme_dict, epg_item_id, start):
    if epg_item_id not in epg_programme_dict:
        epg_programme_dict[epg_item_id] = {}

    if start not in epg_programme_dict[epg_item_id]:
        epg_programme_dict[epg_item_id][start] = None  # Usually this value is not needed
        return None

    # duplicate -> shouldn't happen, mistake in EPG -> receive pk for update
    if epg_programme_dict[epg_item_id][start] is None:
        print("EPG programme duplicate, epg_item_id:", epg_item_id, ", start:", start)
        epg_programme = EpgProgramme.objects.filter(epg_item_id=epg_item_id, start=start).first()

        # duplicate in current cycle, can't be updated
        if epg_programme is None:
            return False

        epg_programme_dict[epg_item_id][start] = epg_programme.pk

    return epg_programme_dict[epg_item_id][start]


def load_epg(request, pk):
    epg = Epg.objects.get(pk=pk)

    print("LOAD EPG:", epg)

    channel_list = []
    programme_list = []

    channel_num = 0
    programme_num = 0

    # channels = EpgChannel.objects.filter(epg_id=epg.id).only('id')
    # display_names = EpgChannelDisplayName.objects.only('pk', 'channels')

    # Clear all tvg names
    EpgChannel.objects.filter(epg_item__epg_id=epg.id).delete()

    def store_objects_in_db():
        print("store_objects_in_db", len(channel_list), len(programme_list),
              channel_num, programme_num)
        # if len(channel_insert_list):
        #     EpgChannel.objects.bulk_create(channel_insert_list)
        #     channel_insert_list.clear()
        #
        # if len(channel_update_list):
        #     EpgChannel.objects.bulk_update(channel_update_list, fields=["icon_url"])
        #     channel_update_list.clear()

        # add EpgId's in DB
        if len(channel_list):
            epg_channel_set = get_channel_tvg_ids(epg.id)  # dict[tvg_id: EpgItem.id]

            # print("store_objects_in_db, update channel", epg_channel_dict)

            channel_insert_list = []
            for channel in channel_list:
                # check if channel exists in db
                # return pk if exists
                channel_added = add_channel(epg_channel_set, channel["tvg_id"])

                if channel_added is True:
                    channel_insert_list.append(EpgItem(epg_id=epg.id,
                                                       tvg_id=channel["tvg_id"]))

            # print("store_objects_in_db, write channel")

            if len(channel_insert_list):
                EpgItem.objects.bulk_create(channel_insert_list)
                channel_insert_list.clear()

        # add EpgChannel's in DB
        if len(channel_list):
            epg_channel_set = get_channel_tvg_ids(epg.id)  # dict[tvg_id: EpgItem.id]

            # print("store_objects_in_db, update channel", epg_channel_set)

            channel_insert_list = []
            for channel in channel_list:
                # check if channel exists in db
                if channel["tvg_id"] not in epg_channel_set:
                    # print("tvg_id not found", channel["tvg_id"])
                    continue

                # print("---------------------------")
                # print(type(channel["tvg_name_synonyms"]))
                # print(channel["tvg_name_synonyms"])
                # print(json.dumps(channel["tvg_name_synonyms"], ensure_ascii=False))

                #    tvg_name_synonyms = json.dumps(channel["tvg_name_synonyms"], ensure_ascii=False).replace('\"', "\'") \
                #        .replace("'", "\'").replace('"', "'")
                #    print(tvg_name_synonyms)

                epg_channel = EpgChannel(epg_item_id=epg_channel_set[channel["tvg_id"]],
                                         tvg_name=channel["tvg_name"],
                                         tvg_name_synonyms=channel["tvg_name_synonyms"],
                                         icon_url=channel["icon"])

                channel_insert_list.append(epg_channel)

            # print("store_objects_in_db, write channel")

            if len(channel_insert_list):
                EpgChannel.objects.bulk_create(channel_insert_list)
                channel_insert_list.clear()

        if len(programme_list):
            epg_channel_set = get_channel_tvg_ids(epg.id)  # dict[tvg_id: EpgItem:id]
            epg_programme_dict = get_programme_ids(epg.id)  # dict[epg_item_id: [start: pk]]

            # print("store_objects_in_db, update programme")

            programme_insert_list = []
            programme_update_list = []
            for programme in programme_list:
                # check channel existence
                if programme["tvg_id"] not in epg_channel_set:
                    continue

                # convert tvg_id to channel epg_item_id
                epg_item_id = epg_channel_set[programme["tvg_id"]]

                # check if programme exists in db
                # return pk if exists
                programme_pk = add_programme(epg_programme_dict, epg_item_id, programme["start"])

                epg_programme = EpgProgramme(epg_item_id=epg_item_id,
                                             start=programme["start"],
                                             stop=programme["stop"],
                                             data=programme["data"])

                if programme_pk is None:
                    programme_insert_list.append(epg_programme)
                elif programme_pk is not False:
                    epg_programme.pk = programme_pk
                    programme_update_list.append(epg_programme)

            # print("store_objects_in_db, write programme")

            if len(programme_insert_list):
                EpgProgramme.objects.bulk_create(programme_insert_list)
                programme_insert_list.clear()

            if len(programme_update_list):
                EpgProgramme.objects.bulk_update(programme_update_list, fields=["start", "data"])
                programme_update_list.clear()

        channel_list.clear()
        programme_list.clear()

        # print("store_objects_in_db fin", len(channel_list), len(programme_list))

    def channel_callback(tvg_id, tvg_name, tvg_name_synonyms, icon):
        nonlocal channel_num
        # generating list of parameters to create objects later
        channel_list.append({'tvg_id': tvg_id, 'tvg_name': tvg_name, 'tvg_name_synonyms': tvg_name_synonyms,
                             'icon': icon})
        channel_num += 1

        if len(channel_list) > 10000:
            store_objects_in_db()

    def programme_callback(tvg_id, start, stop, data):
        nonlocal programme_num
        # generating list of parameters to create objects later
        programme_list.append({'tvg_id': tvg_id, 'start': start, 'stop': stop, 'data': data})
        programme_num += 1

        if len(programme_list) > 10000:
            store_objects_in_db()

    file = get_file_path(pk, epg.name, epg.url, is_epg=True)

    load_file(file, epg.url.split("/")[-1], channel_callback, programme_callback)

    store_objects_in_db()

    if epg.logos_url:
        extractall_to_static(epg)

    epg.update_time = timezone.now()
    epg.channels_num = channel_num
    epg.programme_num = programme_num
    epg.error_message = ""
    epg.save()

    return HttpResponseRedirect(reverse_lazy('epg_app:epg_detail', kwargs={'pk': epg.pk}))


def init_epg(request):
    Epg.objects.bulk_create([Epg(name="programtv.ru",
                                 url="http://programtv.ru/xmltv.xml.gz"),
                             Epg(name="free.fr",
                                 url="http://kevinpato.free.fr/xmltv/download/complet.zip",
                                 logos_url="http://kevinpato.free.fr/xmltv/download/logos.zip"),
                             Epg(name="it999",
                                 url="http://epg.it999.ru/edem.xml.gz"),
                             Epg(name="iptvx.one",
                                 url="http://iptvx.one/epg/epg.xml.gz"),
                             Epg(name="k210.org",
                                 url="http://tv.k210.org/xmltv.xml.gz"),
                             Epg(name="error test",
                                 url="aaaaa"),
                             Epg(name="not found test",
                                 url="http://kevinpato.free.fr/xmltv/download/complet.zipppppppp")],
                            ignore_conflicts=True)

    return HttpResponseRedirect(reverse_lazy('epg_sources'))


class EpgDetailView(DetailView):
    model = Epg

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.size:
            context['size_str'] = pretty_size(self.object.size)
        return context


class EpgAddView(CreateView):
    form_class = EpgAddForm
    model = Epg
    success_url = reverse_lazy('epg_sources')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['header_str'] = "Add EPG source"
        return context


class EpgEditView(UpdateView):
    form_class = EpgAddForm
    model = Epg

    def get_success_url(self):
        return reverse_lazy('epg_app:epg_detail', args=(self.object.pk,))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['header_str'] = "Update EPG source"
        return context


class EpgDeleteView(DeleteView):
    model = Epg
    success_url = reverse_lazy('epg_sources')
