import html
import os
import urllib.parse

from mime_types import mime_types


class AutoindexResponse(object):
    def __init__(self, path, real_path):
        self.headers = ('HTTP/1.0 200 OK\r\n'
                        'Content-Type:text/html; charset=utf-8\r\n'
                        'Server: GH-Autoindex\r\n'
                        'Connection: close\r\n'
                        '\r\n')
        self.path = path
        self.real_path = real_path
        title = html.escape(path)
        self.content = ('<html><head><title>Index of ' + title + '</title></head>\r\n'
                       '<body bgcolor="white">\r\n'
                       '<h1>Index of ' + title + '</h1><hr>\r\n'
                       '<pre>\r\n')

    def add_entry(self, name):
        if not os.path.isfile(self.real_path + name):
            name += '/'
        link = urllib.parse.quote(name)
        text = html.escape(name)
        html_code = str.format('<a href="%s">%s</a>\r\n' % (link, text))
        self.content += html_code

    def get_response(self) -> bytes:
        self.content += ('</pre>\r\n'
                        '<hr>\r\n'
                        '</body></html>\r\n')
        return (self.headers + self.content).encode()


class FileResponse(object):
    def __init__(self, path, part_range, session_id):
        self.path = path
        self.size = os.path.getsize(path)
        self.start = None
        self.end = None

        if part_range is not None:
            self.start, self.end = part_range[0], part_range[1]
            if self.end < 0:
                self.end = self.size + self.end
            self.headers = ('HTTP/1.0 206 Partial Content\r\n'
                            'Server: GH-Autoindex\r\n')
            self.headers += 'Content-Type: ' + self.__file_type() + '\r\n'
            self.headers += str.format('Content-Range: bytes %d-%d/%d\r\n' %
                                       (self.start, self.end, self.size))
            self.headers += 'Connection: close\r\n'
            self.headers += 'Content-Length: ' + str(self.end - self.start + 1) + '\r\n\r\n'

        else:
            self.headers = ('HTTP/1.0 200 OK\r\n'
                            'Server: GH-Autoindex\r\n')
            self.headers += 'Content-Type: ' + self.__file_type() + '\r\n'
            self.headers += 'Connection: close\r\n'
            self.headers += 'Content-Length: ' + str(self.size) + '\r\n'
            self.headers += 'Accept-Ranges: bytes\r\n\r\n'

    def __file_type(self) -> str:
        f_type = mime_types.get(self.path.split('.')[-1])
        if not f_type:
            f_type = 'Application/octet-stream'
        return f_type

    def get_headers(self) -> bytes:
        return self.headers.encode()

    def get_content(self) -> bytes:
        file = open(self.path, 'rb')
        if self.start is not None:
            file.seek(self.start, 0)
            ret = file.read(self.end - self.start + 1)
        else:
            ret = file.read()
        file.close()
        return ret

    def get_response(self) -> bytes:
        return self.get_headers() + self.get_content()


class NonExistResponse(object):
    def __init__(self):
        self.response = [b'HTTP/1.0 404 Not Found\r\n',
                         b'Content-Type:text/html; charset=utf-8\r\n',
                         b'Server: GH-Autoindex\r\n',
                         b'Connection: close\r\n',
                         b'\r\n',
                         b'<html>\r\n',
                         b'<head><title>404 Not Found</title></head>\r\n',
                         b'<body bgcolor="white">\r\n',
                         b'<center><h1>404 Not Found</h1></center>\r\n',
                         b'<hr><center>GH-Autoindex/0.0.1</center>\r\n',
                         b'</body>\r\n',
                         b'</html>\r\n']

    def get_response(self):
        return self.response
