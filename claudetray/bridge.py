"""Servidor local (socket Unix) al que se conectan los hooks y la status line."""
import json
import uuid

from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket


def another_instance_running(path):
    probe = QLocalSocket()
    probe.connectToServer(path)
    alive = probe.waitForConnected(300)
    probe.abort()
    return alive


MAX_BUFFER = 4 * 1024 * 1024     # un mensaje de hook nunca deberia acercarse a esto


class Bridge(QObject):
    message = Signal(object, str)   # (mensaje, id de conexion)
    closed = Signal(str)            # la conexion se cerro (p. ej. Claude mato el hook)

    def __init__(self, path, parent=None):
        super().__init__(parent)
        self._conns = {}
        self._bufs = {}
        self.server = QLocalServer(self)
        self.server.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)
        QLocalServer.removeServer(path)
        if not self.server.listen(path):
            raise RuntimeError(f"No se pudo abrir {path}: {self.server.errorString()}")
        self.server.newConnection.connect(self._accept)

    def _accept(self):
        while self.server.hasPendingConnections():
            sock = self.server.nextPendingConnection()
            cid = uuid.uuid4().hex
            self._conns[cid] = sock
            self._bufs[cid] = b""
            sock.readyRead.connect(lambda cid=cid: self._read(cid))
            sock.disconnected.connect(lambda cid=cid: self._drop(cid))

    def _read(self, cid):
        sock = self._conns.get(cid)
        if sock is None:
            return
        self._bufs[cid] += bytes(sock.readAll())
        if len(self._bufs[cid]) > MAX_BUFFER and b"\n" not in self._bufs[cid]:
            sock.abort()                  # cliente que manda datos sin fin: se corta
            return
        while b"\n" in self._bufs[cid]:
            line, self._bufs[cid] = self._bufs[cid].split(b"\n", 1)
            try:
                msg = json.loads(line)
            except ValueError:
                continue
            self.message.emit(msg, cid)

    def _drop(self, cid):
        sock = self._conns.pop(cid, None)
        self._bufs.pop(cid, None)
        if sock is not None:
            sock.deleteLater()
            self.closed.emit(cid)

    def reply(self, cid, obj):
        sock = self._conns.get(cid)
        if sock is None:
            return False
        sock.write((json.dumps(obj) + "\n").encode())
        sock.flush()
        sock.disconnectFromServer()
        return True
