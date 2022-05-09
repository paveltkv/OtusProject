import io
import zipfile
import gzip
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime
import time
import pytz

read_buf = ""
read_channel = False
read_programme = False


def xmldict(t):
    d = {t.tag: {} if t.attrib else None}
    children = list(t)

    for attrib in t.attrib:
        # print(attrib, t.attrib[attrib])
        d[t.tag]['@' + attrib] = t.attrib[attrib]

    if children:
        dd = defaultdict(list)
        for dc in map(xmldict, children):
            for k, v in dc.items():
                dd[k].append(v)
        d = {t.tag: {k: v[0] if len(v) == 1 else v
                     for k, v in dd.items()}}
    if t.text:
        text = t.text.strip()
        if text == '\\n\'b\'':
            text = ''
        if children or t.attrib:
            if text:
                # print("TEXT:", str(text))
                d[t.tag]['#text'] = text
        else:
            d[t.tag] = text
    return d


def to_datetime(time_str: str):
    # 20180713080000 +0300

    # time
    # year = int(time_str[0] + time_str[1] + time_str[2] + time_str[3])
    # month = int(time_str[4] + time_str[5])
    # day = int(time_str[6] + time_str[7])
    # hour = int(time_str[8] + time_str[9])
    # minute = int(time_str[10] + time_str[11])
    # second = int(time_str[12] + time_str[13])

    # time shift
    sh_hour = int(time_str[15] + time_str[16] + time_str[17])
    sh_min = int(time_str[15] + time_str[18] + time_str[19])
    shift_sec = sh_hour * 60 + sh_min

    posix_timestamp = time.mktime(time.strptime(time_str[0:14], '%Y%m%d%H%M%S')) - shift_sec
    return datetime.utcfromtimestamp(posix_timestamp).replace(tzinfo=pytz.utc)


def load_line(line, channel_callback, programme_callback):
    global read_buf, read_channel, read_programme
    read_buf += str(line)
    if read_channel is False and read_programme is False:
        pos = read_buf.find("<channel ")
        if pos >= 0:
            read_buf = read_buf[pos:]
            read_channel = True
        else:
            pos = read_buf.find("<programme ")
            if pos >= 0:
                read_buf = read_buf[pos:]
                read_programme = True
    if read_channel:
        pos = read_buf.find("</channel>")
        if pos >= 0:
            work_buf = read_buf[:pos + 10]
            read_buf = read_buf[pos + 10:]
            read_channel = False

            # print("--------------------")
            # print(work_buf)
            root = ET.fromstring(work_buf)
            if root.attrib['id']:
                # print(root.tag, root.attrib['id'])
                display_name = ""
                display_name_synonyms = {}
                icon = ""
                for child in root:
                    # print(child.tag, child.attrib, child.text)
                    if child.tag == "display-name":
                        if display_name == "":
                            display_name = child.text
                        display_name_synonyms[child.text.lower()] = True
                    if child.tag == "icon":
                        icon = child.attrib['src']

                # print(display_names)
                if display_name != "":
                    channel_callback(root.attrib['id'], display_name, display_name_synonyms, icon)
                else:
                    print("display_names is empty", root.attrib['id'])
            else:
                print("id tag error")
    elif read_programme:
        pos = read_buf.find("</programme>")
        if pos >= 0:
            work_buf = read_buf[:pos + 12]
            read_buf = read_buf[pos + 12:]
            read_programme = False

            # print("--------------------")
            # print("work_buf:", work_buf)
            # print("--------------------")

            root = ET.fromstring(work_buf)

            # print("ROOT channel", root.attrib['channel'])

            # Header will be generated later with proper tvg-id - drop it
            epg_without_header = ""
            for child in root.iter():
                if child is not root:
                    epg_without_header += ET.tostring(child, encoding="unicode")
                    # print("    child:", ET.tostring(child, encoding="unicode"))

            if root.attrib['channel'] and root.attrib['start'] and root.attrib['stop']:
                # print(root.tag, root.attrib['id'])

                # d = xmldict(root)

                # json_str = json.dumps(d)
                # print(d['programme'])
                programme_callback(root.attrib['channel'],
                                   to_datetime(root.attrib['start']),
                                   to_datetime(root.attrib['stop']),
                                   epg_without_header)
                # d['programme'])
                # print(display_names)

            else:
                print("channel/start/stop tag error")


def load_file(file, original_name, channel_callback, programme_callback):
    global read_buf, read_channel, read_programme
    print("START")
    read_buf = ""
    read_channel = False
    read_programme = False

    file_format = file.split(".")[-1]

    if file_format == "zip":
        xml_file_name = '.'.join(original_name.split(".")[:-1]) + ".xml"
        print(xml_file_name)

        with zipfile.ZipFile(file, mode='r') as z:
            with z.open(xml_file_name) as f:
                for line in io.TextIOWrapper(f, 'utf-8'):
                    load_line(line, channel_callback, programme_callback)

    elif file_format == "gz":
        print("GZ format")
        with gzip.open(file, 'rt') as f:
            for line in f:
                load_line(line, channel_callback, programme_callback)
