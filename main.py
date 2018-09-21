import asyncio
import os
import urllib.parse

import parse_header
from responses import AutoindexResponse, FileResponse, NonExistResponse

ROOT_PATH = '.'
LISTEN_ADDR = '127.0.0.1'
LISTEN_PORT = 8080


def range_parser(part_range) -> (int, int):
    if part_range is not None:
        parts = part_range.split('=')
        if parts[0] == 'bytes':
            range_int = parts[1].split('-')
            if range_int[0] != '':
                start = int(range_int[0])
            else:
                start = 0
            if range_int[1] != '\r\n':
                end = int(range_int[1])
            else:
                end = -1
            return start, end
        return None


async def dispatch(reader, writer):
    headers_data = []
    while True:
        data = await reader.readline()
        headers_data.append(data.decode())
        # print(data)
        if data == b'\r\n' or data == b'':
            break

    client_headers = parse_header.HTTPHeader()
    for line in headers_data:
        client_headers.parse_header(line)
    path = urllib.parse.unquote(client_headers.get('path'))
    part_range = range_parser(client_headers.get('range'))
    session_id = client_headers.get('session_id')

    real_path = ROOT_PATH + path

    try:
        if not os.path.isfile(real_path):
            response = AutoindexResponse(path, real_path)
            response.add_entry('..')
            for filename in os.listdir(real_path):
                if filename[0:1] != '.':
                    response.add_entry(filename)
            writer.write(response.get_response())

        else:
            response = FileResponse(real_path, part_range, session_id)
            writer.write(response.get_response())

    except FileNotFoundError:
        response = NonExistResponse()
        writer.writelines(response.get_response())

    await writer.drain()
    writer.close()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    coro = asyncio.start_server(dispatch, LISTEN_ADDR, LISTEN_PORT, loop=loop)
    server = loop.run_until_complete(coro)

    # Serve requests until Ctrl+C is pressed
    print('Serving on {}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    # Close the server
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()
