# Copyright 2026 DataRobot, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import socket

from app.main import _is_port_in_use

_HOST = "127.0.0.1"


def test_port_with_live_listener_is_in_use() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind((_HOST, 0))
        listener.listen()
        port = listener.getsockname()[1]

        assert _is_port_in_use(port, host=_HOST) is True


def test_port_with_only_time_wait_connections_is_free() -> None:
    # Reproduce what a crashed server leaves behind: the side that closes first
    # holds the connection in TIME_WAIT on the server port for about a minute.
    # The listener sets SO_REUSEADDR like uvicorn does; accepted connections
    # inherit it, which is what lets a later SO_REUSEADDR bind succeed.
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind((_HOST, 0))
    listener.listen()
    port = listener.getsockname()[1]

    client = socket.create_connection((_HOST, port))
    server_side, _ = listener.accept()
    server_side.close()
    client.close()
    listener.close()

    assert _is_port_in_use(port, host=_HOST) is False
