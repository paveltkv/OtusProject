import base64
import random
import string

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render

# Create your views here.
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.generic import DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from epg_app.models import EpgChannel, EpgItem, EpgProgramme
from playlist_app.models import PlayList
from user_app.models import CustomUser
from .async_download_playlists import download_playlists
from .forms import PlayListRulesEditForm, PlayListForm


# http://api.ttv.run/k/xng5nkpAaa/4100/tv.m3u
# https://iptvmaster.ru/russia.m3u


def dict_take_item_starts_with(dict_buf, str_start):

    # print("dict_take_item_starts_with", str_start)

    for item in dict_buf:
        # print("  item", item)

        if item.startswith(str_start):
            return dict_buf.pop(item)
    return None


def set_marker(channel_header, marker):
    header_split = channel_header.split(",")
    name = header_split.pop().strip()
    return ','.join(header_split) + "," + marker + " " + name


def get_channel_tvg_name(channel_header):
    # print(channel_header)
    tvg_name_split = channel_header.split("tvg-name=\"")

    # print(len(tvg_name_split))

    if len(tvg_name_split) > 1:
        tvg_name_split = tvg_name_split[1].split("\"")
        return tvg_name_split[0].lower()

    # print(channel_header.split(","))

    return channel_header.split(",")[-1].strip().lower()


def wrap_epg_programme_body(start, stop, tvg_id, programme_body) -> str:
    return "<programme start=\"" + \
           start.strftime("%Y%m%d%H%M%S") + \
           " +0300\" stop=\"" + \
           stop.strftime("%Y%m%d%H%M%S") + \
           " +0300\" channel=\"" + \
           str(tvg_id) + \
           "\">" + \
           programme_body + \
           "</programme>\n"


# Build programmes list for channel
# dict{start:str}
def get_programmes_for_channel(epg_items, tvg_id_str: str) -> str:
    channel_epg_programmes = {}
    for epg_item in epg_items:
        # print("  EPG item:", epg_channel.epg_item_id, epg_channel.epg_item.epg_id)

        programmes = EpgProgramme.objects.filter(epg_item=epg_item)

        for programme in programmes:

            programme_str = wrap_epg_programme_body(programme.start,
                                                    programme.stop,
                                                    tvg_id_str,
                                                    programme.data)

            # print("    EPG programme:", programme.start, programme.data)
            # take the longest description
            if programme.start not in channel_epg_programmes or \
                    len(channel_epg_programmes[programme.start]) < len(programme_str):
                channel_epg_programmes[programme.start] = programme_str

    # TODO: Is sorting necessary?
    return "\n".join(channel_epg_programmes.values())


# building user global channel list from all user's playlists
# dict{tvg_name -> [header[], line1, line2, ...]}
def build_user_full_channels_list(user):
    playlists_list = PlayList.objects.filter(user=user)

    playlist_buf = {}

    for playlist in playlists_list:
        if playlist.data is None or playlist.download_time is None:
            continue

        data = playlist.data.split("#EXTINF")
        # skip header
        data.pop(0)
        for channel in data:
            # print("------------------------")
            # print("#EXTINF"+channel)

            channel_data_list = channel.strip().split("\n")
            if len(channel_data_list):
                tvg_name = get_channel_tvg_name(channel_data_list[0])

                # returning EXTINF back
                channel_data_list[0] = "#EXTINF" + channel_data_list[0]

                # remove the initial tvg-id, just by replacing it with something else if it exists (for time being)
                channel_data_list[0] = channel_data_list[0].replace('tvg-id', 'prev-ti')

                # remove the initial tvg-name, just by replacing it with something else if it exists (for time being)
                channel_data_list[0] = channel_data_list[0].replace('tvg-name', 'prev-tn')

                # split channel header
                channel_data_list[0] = channel_data_list[0].split(",")

                # add playlist marker
                channel_data_list[0][-1] = playlist.marker + " " + channel_data_list[0][-1].strip()

                # channel_data_list[0] = set_marker(channel_data_list[0], playlist.marker)
                # channel = "\n".join(channel_data_list)

                # print("T:", tvg_name, channel_data_list)
                if tvg_name not in playlist_buf:
                    playlist_buf[tvg_name] = []

                playlist_buf[tvg_name].append(channel_data_list)
    return playlist_buf


def update_user_playlist(request):
    # building user global channel list from all user's playlists
    # dict{tvg_name -> [header[], line1, line2, ...]}
    playlist_buf = build_user_full_channels_list(request.user)

    # print(playlist_buf)
    #
    # print("------------------------")

    playlist_rules = request.user.playlist_rules.split("\n")
    # print(playlist_rules)
    # print("------------------------")

    logos_epg_id = None
    if request.user.icons_source:
        logos_epg_id = request.user.icons_source.id
    print("icons_source", request.user.icons_source, logos_epg_id)

    result_playlist_str = ""
    result_epg_list_str = ""
    result_epg_programmes_list_str = ""

    epg_programme_list_buf: str = ""
    epg_channels_list_buf: str = ""

    tvg_id = 0

    for tvg_name in playlist_rules:
        if len(tvg_name) == 0:
            continue

        tvg_id_str = str(tvg_id)+"_epg_display-name"

        tvg_name = tvg_name.strip().lower()
        # print("tvg_name", tvg_name)
        epg_channels = EpgChannel.objects.filter(tvg_name_synonyms__has_key=tvg_name)
        # print("DDF", epg_channels)

        epg_items = [channel.epg_item for channel in epg_channels]

        # print("-----------------------------------")
        # print("EPG channel:", tvg_name, epg_items)

        # Build programmes list for channel
        epg_programme_list_buf += get_programmes_for_channel(epg_items, tvg_id_str)

        # print("EPG programmes:", channel_epg_programmes)

        logo = ""
        for channel in epg_channels:
            # print("channel.epg_item.id:", channel.epg_item.id)
            if channel.epg_item.epg_id == logos_epg_id:
                logo = "<icon src=\"" + channel.icon_url + "\" />"
                break

        epg_channels_list_buf += "<channel id=\"" + tvg_id_str + \
                                 "\">" + \
                                 "<display-name>" + tvg_id_str + "</display-name>" + \
                                 logo + \
                                 "</channel>\n"

        channels = dict_take_item_starts_with(playlist_buf, tvg_name)
        while channels:
            for channel in channels:
                # result_playlist_str += "\n" + channel
                channel[0][-2] += " tvg-name=\"" + tvg_id_str + "\""
                channel[0] = ','.join(channel[0])
                # channel = "\n".join(channel)

                result_playlist_str += "\n".join(channel) + "\n"

                # print("Channel:", channel)

            channels = dict_take_item_starts_with(playlist_buf, tvg_name)

        tvg_id += 1

    request.user.generated_playlist = result_playlist_str

    request.user.generated_epg = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" + \
                                 "<!DOCTYPE tv SYSTEM \"xmltv.dtd\">\n" + \
                                 "<tv>" + \
                                 epg_channels_list_buf + \
                                 epg_programme_list_buf + \
                                 "</tv>"
    request.user.save()


def index(request):
    if request.user.id:
        all_playlists = PlayList.objects.filter(user=request.user)

        if request.method == "POST":
            form = PlayListRulesEditForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                update_user_playlist(request)
                # To do not resend form data on reload
                # return HttpResponseRedirect(reverse_lazy('playlist_app:playlist_main'))

        form = PlayListRulesEditForm(instance=request.user)

        # Update User API key
        if len(request.user.api_key) < 5:
            request.user.api_key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
            request.user.save()

        context = {
            'user_id': request.user.id,
            'all_playlists': all_playlists,
            'api_key': request.user.api_key,
            'form': form
        }

        return render(request, 'playlist_app/index.html', context=context)

    else:
        context = {}
        return render(request, 'playlist_app/index.html', context=context)


def user_playlist(request, pk, api_key):
    user = CustomUser.objects.filter(pk=pk, api_key=api_key).first()
    if user:
        all_playlists = PlayList.objects.filter(user=user)

        # EXTM3U m3uautoload=1 url-tvg="http://epg.it999.ru/edem.xml.gz?1" tvg-shift=0 refresh=28800

        playlist = "#EXTM3U m3uautoload=1 url-tvg=\"" + \
                   "http://" + \
                   request.get_host() + \
                   reverse('playlist_app:user_epg', kwargs={'pk': pk}) + \
                   "\" tvg-shift=0 refresh=28800\n" + \
                   user.generated_playlist

        context = {
            'playlist': playlist
        }
        return render(request, 'playlist_app/source_html.html', context=context)

    else:
        raise Http404


def user_epg(request, pk):
    user = CustomUser.objects.filter(pk=pk).first()
    if user:
        all_playlists = PlayList.objects.filter(user=user)

        form = PlayListRulesEditForm(instance=user)
        # print(all_playlists)

        context = {
            'playlist': user.generated_epg
        }
        return render(request, 'playlist_app/source_html.html', context=context)

    else:
        raise Http404


class PlayListDetailView(LoginRequiredMixin, DetailView):
    model = PlayList

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # print(self.object.data.split("#EXTINF:"))
        context['list_data'] = []
        if self.object.data:
            context['list_data'] = self.object.data.split("\n")
        return context


class PlayListCreateView(LoginRequiredMixin, CreateView):
    form_class = PlayListForm
    model = PlayList
    success_url = reverse_lazy('playlist_app:playlist_main')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class PlayListUpdateView(LoginRequiredMixin, UpdateView):
    form_class = PlayListForm
    model = PlayList
    success_url = reverse_lazy('playlist_app:playlist_main')


class PlayListDeleteView(LoginRequiredMixin, DeleteView):
    model = PlayList
    success_url = reverse_lazy('playlist_app:playlist_main')


def init(request):
    PlayList.objects.bulk_create([PlayList(user=request.user,
                                           name="iptvmaster.ru",
                                           url="https://iptvmaster.ru/russia.m3u",
                                           marker="★"),
                                  PlayList(user=request.user,
                                           name="ttv.run",
                                           url="http://api.ttv.run/k/xng5nkpAaa/4100/tv.m3u",
                                           marker="◆")],
                                 ignore_conflicts=True)

    return HttpResponseRedirect(reverse_lazy('playlist_app:playlist_main'))


def init_build_rules(request):
    request.user.playlist_rules = str("Amedia Premium HD\n"
                                      "National Geographic HD\n"
                                      "Кинопоказ HD\n"
                                      "Nickelodeon HD\n"
                                      "Viasat Explore\n"
                                      "Viasat History\n"
                                      "Viasat Nature\n"
                                      "National Geographic Wild\n"
                                      "Russian Travel Guide\n"
                                      "Deutsche Welle")
    request.user.save()
    return HttpResponseRedirect(reverse_lazy('playlist_app:playlist_main'))


def change_api_key(request):
    request.user.api_key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    request.user.save()
    return HttpResponseRedirect(reverse_lazy('playlist_app:playlist_main'))


def download(request):
    download_status_list = []

    def update_success_callback(info, data):
        print("playlist update_success_callback, info:", info, ", data:", data)
        download_status_list.append({'info': info, 'data': data})

    def update_error_callback(info, error_message):
        print("playlist update_error_callback, info:", info, ", error_message:", error_message)
        download_status_list.append({'info': info, 'error_message': error_message})

    all_playlists = PlayList.objects.all()

    playlist_list = [{'pk': pl.pk, 'name': pl.name, 'url': pl.url} for pl in all_playlists]

    print("Playlist LIST:", playlist_list)
    download_playlists(playlist_list, update_success_callback, update_error_callback)

    for item in download_status_list:
        print("Store in db:", item)
        playlist = PlayList.objects.get(pk=item['info']['pk'])
        if 'error_message' not in item.keys():
            playlist.download_time = timezone.now()
            playlist.data = item['data']
            playlist.error_message = ""
        else:
            playlist.error_message = item['error_message']

        playlist.save()

    update_user_playlist(request)
    return HttpResponseRedirect(reverse_lazy('playlist_app:playlist_main'))
